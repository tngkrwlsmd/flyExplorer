"""Source contracts for bounded provider Copy-in (Pictures Library only)."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
def src(path):
    return (ROOT/path).read_text(encoding="utf-8")

class ProviderCopyInContracts(unittest.TestCase):
    def test_destination_mode_and_wire_are_bounded(self):
        h=src("src/base/shell_transfer_core.h")
        c=src("src/base/shell_transfer_core.cpp")
        for token in ("DestinationMode { Filesystem, ShellProvider }",
                      "std::vector<unsigned char> destinationPidl;",
                      "kMaxProviderPidlBytes=32768"):
            self.assertIn(token,h)
        for token in ("kTransferWireVersion=3","task.destinationPidl",
                      "appendBlob(body,task.destinationPidl,kMaxProviderPidlBytes)",
                      "task.destinationPidl=reader.blob(kMaxProviderPidlBytes)",
                      "DestinationMode::ShellProvider"):
            self.assertIn(token,c)
    def test_helper_revalidates_library_identity_and_collisions(self):
        c=src("src/base/shell_transfer_core.cpp")
        for token in ("SHGetKnownFolderIDList(","FOLDERID_PicturesLibrary",
                      "ILIsEqual(known,target)","LoadLibraryFromItem(",
                      "GetDefaultSaveFolder(","FOLDERID_Pictures,0,nullptr",
                      "safeFilesystemFolder(fs::path(targetPath),Kind::Copy)",
                      "GetFileAttributesW(targetFile.c_str())",
                      "Collision::Reject","IFileOperation"):
            self.assertIn(token,c)
        self.assertLess(c.index("verifyPicturesLibraryCopyIn(task,providerDestination)"),
                        c.index("operation->PerformOperations()"))
    def test_ui_routes_accepted_target_identity_and_keeps_move_closed(self):
        u=src("app/winui/m22_transfers.cpp")
        a=src("app/winui/file_operation_controller.cpp")
        for token in ("target.folder.get(),req.destinationPidl",
                      "DestinationMode::ShellProvider",
                      "req.destination=target.parsingName",
                      "kind==fxfile::shelltransfer::Kind::Copy"):
            self.assertIn(token,u)
        self.assertIn("context.visibleShellFolder==request.destination",a)
        self.assertIn("request.destinationMode==DestinationMode::ShellProvider",src("src/base/shell_transfer_core.cpp"))
if __name__=="__main__":
    unittest.main()
