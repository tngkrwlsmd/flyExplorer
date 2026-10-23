"""Verify a retained Windows Release EXE against its exact CodeView PDB.

No debugger, network, registry writes, or process attachment is needed.
Read only the PE RSDS record and MSF7 PDB info stream (GUID + age).
Never print embedded PDB paths, addresses, memory, or symbol strings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import uuid


def get_u32(data: bytes, offset: int) -> int:
    if offset < 0 or offset + 4 > len(data):
        raise ValueError("out of bounds metadata")
    return struct.unpack_from("<I", data, offset)[0]


def pe_codeview(path: Path) -> tuple[uuid.UUID, int]:
    data = path.read_bytes()
    if len(data) < 1024 or data[:2] != b"MZ":
        raise ValueError("not a bounded PE image")
    pe = get_u32(data, 0x3C)
    if pe + 24 > len(data) or data[pe:pe+4] != b"PE\0\0":
        raise ValueError("missing PE header")
    sections = struct.unpack_from("<H", data, pe + 6)[0]
    optional_length = struct.unpack_from("<H", data, pe + 20)[0]
    if not 1 <= sections <= 96 or optional_length < 128:
        raise ValueError("unreasonable PE sections")
    opt = pe + 24
    if opt + optional_length + sections * 40 > len(data):
        raise ValueError("truncated section table")
    magic = struct.unpack_from("<H", data, opt)[0]
    directories_offset = {0x10B: 96, 0x20B: 112}.get(magic)
    if directories_offset is None:
        raise ValueError("not a supported PE optional header")
    debug_directory = opt + directories_offset + 6 * 8
    if debug_directory + 8 > opt + optional_length:
        raise ValueError("no debug data directory")
    debug_rva, debug_bytes = struct.unpack_from("<II", data, debug_directory)
    if not debug_rva or not 28 <= debug_bytes <= 4096 or debug_bytes % 28:
        raise ValueError("missing bounded debug entries")

    def rva_to_offset(rva: int, length: int) -> int:
        for section in range(sections):
            start = opt + optional_length + section * 40
            virtual_size, va, raw_size, raw_pointer = struct.unpack_from(
                "<IIII", data, start + 8
            )
            delta = rva - va
            if 0 <= delta and delta + length <= raw_size and (
                raw_pointer + delta + length <= len(data)
            ):
                return raw_pointer + delta
        raise ValueError("debug RVA outside available file section")

    offset = rva_to_offset(debug_rva, debug_bytes)
    records = []
    for i in range(debug_bytes // 28):
        entry = offset + i * 28
        kind, length = struct.unpack_from("<II", data, entry + 12)
        pointer = get_u32(data, entry + 24)
        if kind != 2:
            continue
        if length < 24 or length > 4096 or pointer + length > len(data):
            raise ValueError("unbounded CodeView entry")
        record = data[pointer:pointer+length]
        if record[:4] != b"RSDS":
            continue
        records.append((uuid.UUID(bytes_le=record[4:20]), get_u32(record, 20)))
    if len(records) != 1:
        raise ValueError("expected one PE CodeView RSDS identity")
    return records[0]


def msf_pdb_identity(path: Path) -> tuple[uuid.UUID, int]:
    with path.open("rb") as stream:
        size = path.stat().st_size
        header = stream.read(64)
        if len(header) < 56 or not header.startswith(
            b"Microsoft C/C++ MSF 7.00\r\n\x1aDS\x00\x00\x00"
        ):
            raise ValueError("not an MSF7 PDB")
        block_size, _, total, directory_bytes, _, directory_map = struct.unpack_from(
            "<6I", header, 32
        )
        if not (512 <= block_size <= 65536 and block_size & (block_size - 1) == 0):
            raise ValueError("unsupported MSF block size")
        if not (1 <= total <= 1000000 and total * block_size <= size
                and 32 <= directory_bytes <= 16 * 1024 * 1024):
            raise ValueError("unreasonable MSF stream directory")
        directory_blocks = math.ceil(directory_bytes / block_size)
        if directory_blocks * 4 > block_size or directory_map >= total:
            raise ValueError("unsupported MSF block-map span")

        def block_data(block: int) -> bytes:
            if block >= total:
                raise ValueError("MSF block outside PDB")
            stream.seek(block * block_size)
            chunk = stream.read(block_size)
            if len(chunk) != block_size:
                raise ValueError("short MSF block")
            return chunk

        mapping = block_data(directory_map)
        block_numbers = struct.unpack_from(
            f"<{directory_blocks}I", mapping, 0
        )
        directory = b"".join(block_data(b) for b in block_numbers)[:directory_bytes]
        streams = get_u32(directory, 0)
        if not 2 <= streams <= 100000 or 4 + 4 * streams > len(directory):
            raise ValueError("bad MSF stream directory count")
        lengths = struct.unpack_from(f"<{streams}I", directory, 4)
        cursor = 4 + 4 * streams
        pdb_size, pdb_pages = None, None
        for index, length in enumerate(lengths):
            count = 0 if length == 0xFFFFFFFF else math.ceil(length / block_size)
            if cursor + count * 4 > len(directory):
                raise ValueError("truncated MSF stream blocks")
            if index == 1:
                pdb_size = length
                pdb_pages = struct.unpack_from(f"<{count}I", directory, cursor)
            cursor += 4 * count
        if pdb_size is None or pdb_size < 28 or pdb_size > 1024 * 1024:
            raise ValueError("invalid PDB information stream")
        info = b"".join(block_data(b) for b in pdb_pages)[:pdb_size]
        age = get_u32(info, 8)
        guid = uuid.UUID(bytes_le=info[12:28])
        return guid, age


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def check(exe: Path, pdb: Path) -> dict:
    if not exe.is_file() or exe.name.casefold() != "flyexplorer.exe":
        raise ValueError("expected existing flyExplorer.exe")
    if not pdb.is_file() or pdb.name.casefold() != "flyexplorer.pdb":
        raise ValueError("expected existing flyExplorer.pdb")
    if not 0 < exe.stat().st_size < 128 * 1024 * 1024:
        raise ValueError("unexpected executable size")
    if not 1024 <= pdb.stat().st_size < 512 * 1024 * 1024:
        raise ValueError("unexpected PDB size")
    pe_identity = pe_codeview(exe)
    pdb_identity = msf_pdb_identity(pdb)
    if pe_identity != pdb_identity:
        raise ValueError("CodeView RSDS GUID/age does not match PDB Info stream")
    return {
        "status": "EXACT_PDB_MATCH",
        "guid": str(pe_identity[0]),
        "age": pe_identity[1],
        "exe_sha256": sha256(exe),
        "pdb_sha256": sha256(pdb),
        "exe_bytes": exe.stat().st_size,
        "pdb_bytes": pdb.stat().st_size,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--exe", type=Path, required=True)
    parser.add_argument("--pdb", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = check(args.exe, args.pdb)
    except (OSError, ValueError, struct.error) as error:
        print(json.dumps({"status": "SYMBOL_MATCH_FAILED",
                          "error": type(error).__name__}))
        return 2
    print("G01_RELEASE_SYMBOL_IDENTITY=" + json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
