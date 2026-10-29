#include "../../../src/base/ui_preferences.h"
#include "../../../src/base/file_command_core.h"
#include <windows.h>
#include <filesystem>
#include <cstdio>
#include <fstream>
#include <string>
using namespace fxfile;
int wmain(int argc,wchar_t**argv){
 setvbuf(stdout,nullptr,_IONBF,0);
 if(argc!=2)return 2;
 const std::filesystem::path root(argv[1]);
 int pass=0,fail=0;
 auto chk=[&](bool ok,const char*why){std::printf("M21_%s %s\n",ok?"PASS":"FAIL",why);
   if(ok)++pass;else ++fail;};
 uisettings::Preferences pref{};
 const auto config=uisettings::privatePath();
 chk(!config.empty()&&config.find(L"flyExplorer")!=std::wstring::npos,"isolated_product_profile");
 chk(!uisettings::load(pref)&&pref.language==L"ko-KR"&&
   pref.theme==uisettings::Theme::System,"korean_system_default_without_settings");
 pref.theme=uisettings::Theme::Dark;
 chk(uisettings::save(pref)&&std::filesystem::exists(config),"atomic_save_ko_dark");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Dark&&
   pref.language==L"ko-KR","reload_ko_dark");
 pref.theme=uisettings::Theme::Light;
 chk(uisettings::save(pref)&&uisettings::load(pref)&&
   pref.theme==uisettings::Theme::Light,"atomic_light_update");
 pref.language=L"en-US";
 chk(!uisettings::save(pref),"unsupported_locale_not_written");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Light&&
   pref.language==L"ko-KR","failed_save_keeps_previous_data");
 // New Ctrl+G / Ctrl+J focus choices persist in the existing schema=3
 // private store; duplicate/out-of-range choices cannot overwrite it.
 pref.addressShortcut=4;pref.searchShortcut=5;
 chk(uisettings::validFocusShortcuts(4,5)&&uisettings::save(pref),
     "extended_focus_choices_save");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.theme==uisettings::Theme::Light&&
     pref.addressShortcut==4&&pref.searchShortcut==5,
     "extended_focus_choices_reload");
 pref.searchShortcut=4;
 chk(!uisettings::validFocusShortcuts(4,4)&&!uisettings::save(pref),
     "duplicate_focus_choice_rejected");
 pref.searchShortcut=6;
 chk(!uisettings::validFocusShortcuts(4,6)&&!uisettings::save(pref),
     "out_of_range_focus_choice_rejected");
 pref=uisettings::Preferences{};
 chk(uisettings::load(pref)&&pref.addressShortcut==4&&
     pref.searchShortcut==5,"invalid_focus_save_preserves_previous");
 const auto dir=root/L"owned-directory";
 std::filesystem::create_directory(dir);
 filecommand::Request req;
 req.parent=dir.native();req.name=L"새 폴더";
 std::printf("M21_DEBUG_KOREAN_NAME_SAFE=%d PARENT_EXISTS=%d\\n",
  (int)filecommand::validLeaf(req.name),(int)std::filesystem::is_directory(dir));
 chk(filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_SUCCESS&&
   std::filesystem::is_directory(dir/L"새 폴더"),"create_korean_folder");
 chk(filecommand::execute(req).error==ERROR_ALREADY_EXISTS,
   "never_overwrite_existing_directory");
 req.name=L"..";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_parent_traversal");
 req.name=L"CON.txt";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_reserved_device");
 // Keep Win32 console aliases and superscript COM/LPT aliases out of all
 // file-mutating commands, including device stems followed by extensions.
 bool deviceNamesRejected=true;
 for(auto const* leaf:{
      L"CONIN$",L"conout$",L"CONIN$.txt",L"CONOUT$.bak",
      L"COM\u00B9",L"com\u00B2.log",L"LPT\u00B3.txt"}){
  req.name=leaf;
  deviceNamesRejected=deviceNamesRejected&&
     !filecommand::validLeaf(req.name)&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(deviceNamesRejected,"deny_console_and_superscript_device_names");
 chk(filecommand::validLeaf(L"COM10.txt")&&
     filecommand::validLeaf(L"LPT10.txt")&&
     filecommand::validLeaf(L"문서 ¹.txt"),
     "allow_non_device_leaf_names");
 req.name=L"no/paths";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_slash");
 req.name=L"이름.";
 chk(!filecommand::validLeaf(req.name)&&
   filecommand::execute(req).error==ERROR_INVALID_NAME,"deny_trailing_period");
 req.kind=filecommand::Kind::RenameSelected;
 req.source=(dir/L"새 폴더").native();req.name=L"이름 변경";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
    std::filesystem::is_directory(dir/L"이름 변경"),"rename_owned_korean_directory");
 std::filesystem::create_directory(dir/L"대상 존재");
 req.source=(dir/L"이름 변경").native();req.name=L"대상 존재";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS&&
    std::filesystem::is_directory(dir/L"이름 변경")&&
    std::filesystem::is_directory(dir/L"대상 존재"),"rename_never_replaces_existing");
 // Rejected device destination must not rename/delete the existing
 // test-owned source directory.
 req.source=(dir/L"이름 변경").native();req.name=L"lpt\u00B9";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME&&
     std::filesystem::is_directory(dir/L"이름 변경"),
     "rename_denies_superscript_device_destination");
 req.source=(root/L"foreign-source").native();req.name=L"safe";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,"rename_source_must_be_child");
 req.parent=L"shell:MyComputerFolder";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS,"reject_virtual_folder_mutations");
 // F13: create an empty text document only, never replace existing data.
 req.parent=dir.native();req.source.clear();
 req.kind=filecommand::Kind::CreateTextFile;req.name=L"새 문서.txt";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/L"새 문서.txt")&&
     std::filesystem::file_size(dir/L"새 문서.txt")==0,
     "create_empty_unicode_text_document");
 chk(filecommand::execute(req).error!=ERROR_SUCCESS&&
     std::filesystem::file_size(dir/L"새 문서.txt")==0,
     "text_document_never_overwrites_existing");
 req.name=L"메모.TXT";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::file_size(dir/L"메모.TXT")==0,
     "text_document_case_insensitive_extension");
 req.name=L"메모.md";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME&&
     !std::filesystem::exists(dir/L"메모.md"),
     "text_document_denies_other_extensions");
 req.name=L"..\\escape.txt";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,
     "text_document_denies_traversal");
 req.name=L"CON.txt";
 chk(filecommand::execute(req).error==ERROR_INVALID_NAME,
     "text_document_denies_reserved_device");
 bool textDevicesRejected=true;
 for(auto const* leaf:{L"CONIN$.txt",L"conout$.TXT",
                       L"COM\u00B3.txt",L"lpt\u00B2.TXT"}){
  req.name=leaf;
  textDevicesRejected=textDevicesRejected&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(textDevicesRejected,"text_document_denies_console_device_names");
 req.parent=L"shell:MyComputerFolder";req.name=L"virtual.txt";
 chk(filecommand::execute(req).error!=ERROR_SUCCESS,
     "text_document_denies_virtual_parent");
 // Markdown uses the same no-replace local creation path, with its own suffix.
 req.parent=dir.native();req.kind=filecommand::Kind::CreateMarkdownFile;
 req.name=L"새 문서.md";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::is_regular_file(dir/req.name)&&
     std::filesystem::file_size(dir/req.name)==0,
     "create_empty_unicode_markdown_document");
 { std::ofstream existing(dir/req.name,std::ios::binary);existing<<"owned markdown"; }
 const auto duplicateMarkdown=filecommand::execute(req);
 { std::ifstream existing(dir/req.name,std::ios::binary);std::string retained;
   std::getline(existing,retained);
   chk(duplicateMarkdown.error!=ERROR_SUCCESS&&retained=="owned markdown",
       "markdown_never_overwrites_existing"); }
 req.name=L"메모.MD";
 chk(filecommand::execute(req).error==ERROR_SUCCESS&&
     std::filesystem::file_size(dir/req.name)==0,
     "markdown_case_insensitive_extension");
 bool markdownNamesRejected=true;
 for(auto const* leaf:{L".md",L"wrong.txt",L"..\\escape.md",L"CON.md",L"a.md ",L"a.md.exe"}){
  req.name=leaf;
  markdownNamesRejected=markdownNamesRejected&&
     filecommand::execute(req).error==ERROR_INVALID_NAME;
 }
 chk(markdownNamesRejected,"markdown_rejects_unsafe_or_other_suffix_names");
 req.parent=dir.native();req.kind=static_cast<filecommand::Kind>(99);
 chk(filecommand::execute(req).error==ERROR_INVALID_PARAMETER,"unknown_mutation_denied");
 std::printf("M21_NATIVE_SUMMARY %d passed, %d failed.\n",pass,fail);
 return fail?1:0;
}
