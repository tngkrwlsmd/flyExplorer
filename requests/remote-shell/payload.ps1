$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -eq 0) {
    throw "Expected partial Known Folder artwork changes to resume."
}
Write-Output "RESUME_DIRTY_STATE"
$dirty | ForEach-Object { Write-Output $_ }

$script = Join-Path $env:TEMP "fly_known_folder_patch_resume.py"
@'
from pathlib import Path

ROOT=Path(r"C:\dev\flyExplorer")

def read(rel):
    return (ROOT/rel).read_text(encoding="utf-8")

def write(rel, content):
    (ROOT/rel).write_text(content,encoding="utf-8",newline="")
    print("EDITED",rel)

detail=read("app/winui/file_detail_controller.cpp")
anchor='''            using FileDetail=fxfile::previewlist::FileDetail;
            using FileViewMode=fxfile::previewlist::FileViewMode;
            std::vector<std::wstring> extensions{L".flyfolder"};
'''
if anchor not in detail:
    raise RuntimeError("file detail worker anchor missing")
detail=detail.replace(anchor,'''            using FileDetail=fxfile::previewlist::FileDetail;
            using FileViewMode=fxfile::previewlist::FileViewMode;
            static constexpr wchar_t const* knownFolderKeys[]{
                L"desktop",L"documents",L"downloads",
                L"pictures",L"music",L"videos"
            };
            std::vector<std::pair<std::wstring,std::wstring>> knownFolderPaths;
            knownFolderPaths.reserve(6);
            for(auto const* key:knownFolderKeys){
                auto path=fxfile::filetype::knownFolderPath(key);
                if(!path.empty())
                    knownFolderPaths.emplace_back(key,std::move(path));
            }
            std::vector<std::wstring> knownFolderKeyByIndex(
                request.paths.size());
            std::vector<std::wstring> requestedKnownFolderKeys;
            for(std::size_t i=0;i<request.paths.size();++i){
                auto const& candidate=request.paths[i];
                if(candidate.empty())continue;
                for(auto const& known:knownFolderPaths){
                    if(::CompareStringOrdinal(
                         candidate.c_str(),-1,known.second.c_str(),-1,TRUE)
                       !=CSTR_EQUAL)continue;
                    knownFolderKeyByIndex[i]=known.first;
                    if(std::find(requestedKnownFolderKeys.begin(),
                         requestedKnownFolderKeys.end(),known.first)
                       ==requestedKnownFolderKeys.end())
                        requestedKnownFolderKeys.push_back(known.first);
                    break;
                }
            }
            std::vector<std::wstring> extensions{L".flyfolder"};
''',1)

anchor='''            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::wstring visualHelper;
'''
if anchor not in detail:
    raise RuntimeError("visual maps anchor missing")
detail=detail.replace(anchor,'''            std::unordered_map<std::wstring,fxfile::filetype::Visual> windowsTypes;
            std::unordered_map<std::wstring,fxfile::filetype::Visual>
                knownFolderVisuals;
            std::wstring visualHelper;
''',1)

anchor='''                    for(auto const& ext:recover){
                        auto one=fxfile::filetype::queryVisuals(
                            visualHelper,{ext},1350,request.visualPixels);
                        auto found=one.find(ext);
                        if(found!=one.end())windowsTypes[ext]=std::move(found->second);
                    }
                }
            }
'''
if anchor not in detail:
    raise RuntimeError("visual recovery anchor missing")
detail=detail.replace(anchor,'''                    for(auto const& ext:recover){
                        auto one=fxfile::filetype::queryVisuals(
                            visualHelper,{ext},1350,request.visualPixels);
                        auto found=one.find(ext);
                        if(found!=one.end())windowsTypes[ext]=std::move(found->second);
                    }
                    if(!requestedKnownFolderKeys.empty())
                        knownFolderVisuals=fxfile::filetype::queryKnownFolderVisuals(
                            visualHelper,requestedKnownFolderKeys,
                            2500,request.visualPixels);
                }
            }
''',1)

old='''                if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                    entry.typeLabel=L"\uD3F4\uB354";
                    auto folder=windowsTypes.find(L".flyfolder");
                    if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                        entry.iconBgra=folder->second.bgra;
                        entry.iconWidth=folder->second.width;
                        entry.iconHeight=folder->second.height;
                    }
                }else{
'''
if old not in detail:
    raise RuntimeError("directory visual block missing")
detail=detail.replace(old,'''                if(data.dwFileAttributes&FILE_ATTRIBUTE_DIRECTORY){
                    entry.typeLabel=L"\uD3F4\uB354";
                    auto const& knownKey=knownFolderKeyByIndex[i];
                    auto known=knownKey.empty()?knownFolderVisuals.end():
                        knownFolderVisuals.find(knownKey);
                    if(known!=knownFolderVisuals.end()&&
                       !known->second.bgra.empty()){
                        entry.iconBgra=known->second.bgra;
                        entry.iconWidth=known->second.width;
                        entry.iconHeight=known->second.height;
                        entry.knownFolderVisual=true;
                    }else{
                        auto folder=windowsTypes.find(L".flyfolder");
                        if(folder!=windowsTypes.end()&&!folder->second.bgra.empty()){
                            entry.iconBgra=folder->second.bgra;
                            entry.iconWidth=folder->second.width;
                            entry.iconHeight=folder->second.height;
                        }
                    }
                }else{
''',1)
write("app/winui/file_detail_controller.cpp",detail)

main=read("app/winui/MainWindow.xaml.cpp")
old='''                                Microsoft::UI::Xaml::Automation::AutomationProperties::
                                    SetName(image,item.isFolder()?
                                        L"Windows Shell folder icon":
                                        L"Windows system registered file icon");
'''
if old not in main:
    raise RuntimeError("details image automation block missing")
main=main.replace(old,'''                                Microsoft::UI::Xaml::Automation::AutomationProperties::
                                    SetName(image,item.isFolder()?
                                        (iconMeta->knownFolderVisual?
                                            L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):
                                        L"Windows system registered file icon");
''',1)

old='''                                    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(image,realThumb?L"Windows Shell image thumbnail":
                                        item.isFolder()?L"Windows Shell folder icon":L"Windows system registered file icon");
'''
if old not in main:
    raise RuntimeError("icon-grid image automation block missing")
main=main.replace(old,'''                                    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(image,realThumb?L"Windows Shell image thumbnail":
                                        item.isFolder()?(iconMeta->knownFolderVisual?L"Windows Known Folder artwork":
                                            L"Windows Shell folder icon"):L"Windows system registered file icon");
''',1)
write("app/winui/MainWindow.xaml.cpp",main)

test=r'''"""Path-specific Known Folder artwork stays bounded and isolated."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]

def source(path):
    return (ROOT/path).read_text(encoding="utf-8")

class KnownFolderArtworkContract(unittest.TestCase):
    def test_fixed_known_folder_key_allowlist_and_os_resolution(self):
        header=source("src/base/shell_assoc_type_core.h")
        core=source("src/base/shell_assoc_type_core.cpp")
        self.assertIn("safeKnownFolderKey",header)
        self.assertIn("knownFolderPath",header)
        self.assertIn("queryKnownFolderVisuals",header)
        for key in ("desktop","documents","downloads","pictures","music","videos"):
            self.assertIn('L"'+key+'"',core)
        for token in (
            "FOLDERID_Desktop","FOLDERID_Documents","FOLDERID_Downloads",
            "FOLDERID_Pictures","FOLDERID_Music","FOLDERID_Videos",
            "SHGetKnownFolderPath",
        ):
            self.assertIn(token,core)

    def test_helper_accepts_only_fixed_tokens_and_returns_pixels(self):
        helper=source("app/winui/helper/FlyShellIsolationHelper.cpp")
        self.assertIn('L"--known-folder-visuals"',helper)
        self.assertIn("argc>9",helper)
        self.assertIn("SHGetKnownFolderPath",helper)
        self.assertIn("SHGetFileInfoW(path,0",helper)
        self.assertIn("SHGFI_ICON",helper)
        self.assertIn("DrawIconEx",helper)
        self.assertIn("CryptBinaryToStringA",helper)

    def test_file_detail_prefers_known_artwork_and_keeps_generic_fallback(self):
        worker=source("app/winui/file_detail_controller.cpp")
        state=source("app/winui/file_list_state.h")
        app=source("app/winui/MainWindow.xaml.cpp")
        self.assertIn("knownFolderKeyByIndex",worker)
        self.assertIn("queryKnownFolderVisuals(",worker)
        self.assertIn('windowsTypes.find(L".flyfolder")',worker)
        self.assertIn("entry.knownFolderVisual=true",worker)
        self.assertIn("bool knownFolderVisual=false",state)
        self.assertIn('L"Windows Known Folder artwork"',app)
        self.assertNotIn("SHGetFileInfoW",worker)
        self.assertNotIn("SHGetKnownFolderPath",app)

if __name__=="__main__":
    unittest.main()
'''
write("tests/winui/test_known_folder_artwork_contract.py",test)

for rel, token in [
    ("app/winui/MainWindow.xaml.cpp","SHGetFileInfoW"),
    ("app/winui/file_detail_controller.cpp","SHGetFileInfoW"),
]:
    if token in read(rel):
        raise RuntimeError(f"{rel}: direct Shell visual call leaked: {token}")

print("KNOWN_FOLDER_ARTWORK_PATCH_RESUMED")
'@ | Set-Content -LiteralPath $script -Encoding utf8

python -X utf8 $script
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue

git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -X utf8 -m unittest tests.winui.test_known_folder_artwork_contract tests.winui.test_registered_file_type_contract tests.winui.test_file_detail_controller_contract tests.winui.test_m26_fluent_contract
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

test.bat source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

build.bat Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "KNOWN_FOLDER_ARTWORK_BUILD_PASS"
git diff --stat
git status --short
