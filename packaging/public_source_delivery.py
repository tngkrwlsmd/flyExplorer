from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "packaging" / "PUBLIC_SOURCE_DELIVERY.json"
IDENTITY_PATH = ROOT / "packaging" / "RELEASE_IDENTITY.json"
PRODUCT_VERSION_PATH = ROOT / "app" / "winui" / "product_version.h"
FORMAT = "flyexplorer-public-source-delivery-v1"
METHOD = "6(d)-network-equivalent-access"
MIN_RETENTION_DAYS = 1095


class PublicSourcePolicyError(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise PublicSourcePolicyError(f"expected JSON object: {path}")
    return value


def _product_version(path: Path = PRODUCT_VERSION_PATH) -> str:
    text = path.read_text(encoding="utf-8")
    match = re.search(
        r'#define\s+FLYEXPLORER_VERSION_STRING\s+"([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)"',
        text,
    )
    if not match:
        raise PublicSourcePolicyError("product version is missing or malformed")
    return match.group(1)


def _git(root: Path, *args: str, allow_failure: bool = False) -> tuple[int, str]:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        check=False,
    )
    if result.returncode and not allow_failure:
        raise PublicSourcePolicyError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.returncode, result.stdout.strip()


def validate_policy(
    *,
    policy_path: Path = POLICY_PATH,
    identity_path: Path = IDENTITY_PATH,
    product_version_path: Path = PRODUCT_VERSION_PATH,
) -> tuple[dict[str, object], dict[str, object]]:
    policy = _load_json(policy_path)
    identity = _load_json(identity_path)

    if policy.get("format") != FORMAT:
        raise PublicSourcePolicyError("public-source policy format mismatch")
    if policy.get("license") != "GPL-3.0-or-later":
        raise PublicSourcePolicyError("public-source policy license mismatch")
    if policy.get("selected_gplv3_section_6_method") != METHOD:
        raise PublicSourcePolicyError("public-source policy must select GPLv3 section 6(d)")

    version = _product_version(product_version_path)
    expected_tag = f"v{version}"
    if policy.get("release_tag") != expected_tag:
        raise PublicSourcePolicyError(
            f"release tag must match product version: expected {expected_tag}"
        )

    binary_source = str(identity.get("binary_source_revision") or "")
    source_tree = str(identity.get("source_tree_sha") or "")
    if policy.get("binary_source_revision") != binary_source:
        raise PublicSourcePolicyError("policy binary source revision differs from release identity")
    if policy.get("source_tree_sha") != source_tree:
        raise PublicSourcePolicyError("policy source tree differs from release identity")

    tag_policy = policy.get("tag_policy")
    if not isinstance(tag_policy, dict):
        raise PublicSourcePolicyError("tag policy is missing")
    required_tag_flags = {
        "precreate_tag": False,
        "create_on_publish": True,
        "immutable_releases_required": True,
        "tag_must_resolve_to_binary_source_revision": True,
        "tag_name_reuse_forbidden": True,
    }
    for key, expected in required_tag_flags.items():
        if tag_policy.get(key) is not expected:
            raise PublicSourcePolicyError(f"tag policy {key} must be {expected}")

    place = policy.get("designated_public_place")
    if not isinstance(place, dict):
        raise PublicSourcePolicyError("designated public place is missing")
    if place.get("provider") != "GitHub Releases":
        raise PublicSourcePolicyError("public delivery provider must be GitHub Releases")
    if place.get("repository") != "tngkrwlsmd/flyExplorer":
        raise PublicSourcePolicyError("public delivery repository mismatch")
    if place.get("repository_must_be_public_before_publish") is not True:
        raise PublicSourcePolicyError("repository must be public before release publication")
    if place.get("binary_and_source_on_same_release_page") is not True:
        raise PublicSourcePolicyError("binary and source must share one release page")
    if place.get("authentication_required") is not False:
        raise PublicSourcePolicyError("public source access must not require authentication")
    if place.get("source_additional_charge") is not False:
        raise PublicSourcePolicyError("source access must have no additional charge")

    retention = policy.get("retention_policy")
    if not isinstance(retention, dict):
        raise PublicSourcePolicyError("retention policy is missing")
    if retention.get("source_available_for_full_binary_availability_period") is not True:
        raise PublicSourcePolicyError("source must remain available while binary is available")
    if retention.get("source_must_not_be_removed_while_binary_is_available") is not True:
        raise PublicSourcePolicyError("source must not be removed before binary")
    if retention.get("release_assets_must_remain_immutable") is not True:
        raise PublicSourcePolicyError("release assets must remain immutable")
    days = retention.get("minimum_days_after_last_public_binary_availability")
    if not isinstance(days, int) or days < MIN_RETENTION_DAYS:
        raise PublicSourcePolicyError("post-withdrawal source retention must be at least 1095 days")

    assets = policy.get("required_release_assets")
    if not isinstance(assets, list) or len(assets) < 6:
        raise PublicSourcePolicyError("required release asset list is incomplete")
    expected_assets = {
        "flyExplorer-Setup-x64.exe",
        str(identity["source_bundle"]["file"]),
        str(identity["source_bundle"]["manifest_file"]),
        "RELEASE_IDENTITY.json",
        "PAYLOAD_PROVENANCE.json",
        "PAYLOAD_PROVENANCE.md",
    }
    if set(str(item) for item in assets) != expected_assets:
        raise PublicSourcePolicyError("required release assets do not match release identity")

    gates = policy.get("prepublication_gates")
    if not isinstance(gates, list) or len(gates) < 6:
        raise PublicSourcePolicyError("prepublication gates are incomplete")
    return policy, identity


def validate_git_phase(
    *,
    policy: dict[str, object],
    identity: dict[str, object],
    phase: str,
    root: Path = ROOT,
) -> None:
    tag = str(policy["release_tag"])
    code, _ = _git(root, "show-ref", "--verify", "--quiet", f"refs/tags/{tag}", allow_failure=True)
    tag_exists = code == 0
    recorded_tag = identity.get("release_tag")

    if phase == "prepublish":
        if tag_exists:
            raise PublicSourcePolicyError(
                "reserved release tag already exists before immutable publication"
            )
        if recorded_tag is not None:
            raise PublicSourcePolicyError(
                "release identity must keep release_tag null before immutable publication"
            )
        return

    if phase != "published":
        raise PublicSourcePolicyError(f"unsupported phase: {phase}")
    if not tag_exists:
        raise PublicSourcePolicyError("published release tag is missing")
    _, target = _git(root, "rev-parse", f"refs/tags/{tag}^{{commit}}")
    if target.lower() != str(identity["binary_source_revision"]).lower():
        raise PublicSourcePolicyError("published release tag target differs from binary source revision")
    if recorded_tag != tag:
        raise PublicSourcePolicyError("published release identity does not record the immutable tag")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("prepublish", "published"), default="prepublish")
    parser.add_argument("--policy", type=Path, default=POLICY_PATH)
    parser.add_argument("--identity", type=Path, default=IDENTITY_PATH)
    args = parser.parse_args()
    try:
        policy, identity = validate_policy(
            policy_path=args.policy,
            identity_path=args.identity,
        )
        validate_git_phase(policy=policy, identity=identity, phase=args.phase)
    except (OSError, ValueError, json.JSONDecodeError, PublicSourcePolicyError) as exc:
        print(f"ERROR: {exc}")
        return 1

    print(f"PUBLIC_SOURCE_METHOD={policy['selected_gplv3_section_6_method']}")
    print(f"PUBLIC_RELEASE_TAG={policy['release_tag']}")
    print(f"PUBLIC_RELEASE_SOURCE_REVISION={identity['binary_source_revision']}")
    print(
        "PUBLIC_SOURCE_RETENTION_DAYS="
        + str(policy["retention_policy"]["minimum_days_after_last_public_binary_availability"])
    )
    print(f"PUBLIC_RELEASE_PHASE={args.phase}")
    print("PUBLIC_SOURCE_POLICY_CHECK=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
