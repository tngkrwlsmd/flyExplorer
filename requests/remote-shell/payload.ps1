$ErrorActionPreference = "Stop"
$dirty = @(git status --porcelain)
if ($dirty.Count -eq 0) {
    throw "Expected Known Folder artwork development changes."
}

$script = Join-Path $env:TEMP "fly_known_folder_icon_factory_fix.py"
@'
from pathlib import Path
ROOT=Path(r"C:\dev\flyExplorer")

helper_path=ROOT/"app/winui/helper/FlyShellIsolationHelper.cpp"
helper=helper_path.read_text(encoding="utf-8")
start=helper.find('    if(argc>=4&&!wcscmp(argv[1],L"--known-folder-visuals")){')
end=helper.find('    const bool requestVisuals=argc>=4&&!wcscmp(argv[1],L"--file-visuals");',start)
if start<0 or end<0:
    raise RuntimeError("Known Folder helper branch anchors missing")
branch=r'''    if(argc>=4&&!wcscmp(argv[1],L"--known-folder-visuals")){
        wchar_t* end=nullptr;
        const auto parsed=::wcstoul(argv[2],&end,10);
        if(!end||*end||parsed<16||parsed>64||argc>9)return 18;
        const auto visualPixels=static_cast<std::uint32_t>(parsed);
        auto output=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!output||output==INVALID_HANDLE_VALUE)return 19;
        const auto apt=::CoInitializeEx(
            nullptr,COINIT_APARTMENTTHREADED|COINIT_DISABLE_OLE1DDE);
        if(FAILED(apt))return 24;
        int resultCode=0;
        for(int i=3;i<argc&&resultCode==0;++i){
            std::wstring key(argv[i]);
            KNOWNFOLDERID const* id=nullptr;
            if(key==L"desktop")id=&FOLDERID_Desktop;
            else if(key==L"documents")id=&FOLDERID_Documents;
            else if(key==L"downloads")id=&FOLDERID_Downloads;
            else if(key==L"pictures")id=&FOLDERID_Pictures;
            else if(key==L"music")id=&FOLDERID_Music;
            else if(key==L"videos")id=&FOLDERID_Videos;
            else {resultCode=20;break;}

            PWSTR path=nullptr;
            const auto pathHr=::SHGetKnownFolderPath(
                *id,KF_FLAG_DEFAULT,nullptr,&path);
            SHFILEINFOW info{};
            const auto typeResult=SUCCEEDED(pathHr)&&path?
                ::SHGetFileInfoW(path,0,&info,sizeof(info),SHGFI_TYPENAME):0;
            std::wstring readable=typeResult?info.szTypeName:L"";
            if(readable.size()>79)readable.clear();
            const int count=readable.empty()?0: ::WideCharToMultiByte(
                CP_UTF8,WC_ERR_INVALID_CHARS,readable.data(),
                static_cast<int>(readable.size()),nullptr,0,nullptr,nullptr);
            if(count<0||count>320){
                if(path)::CoTaskMemFree(path);
                resultCode=22;break;
            }

            std::string line=std::to_string(i-3)+"\t";
            if(count){
                std::string utf8(static_cast<size_t>(count),'\0');
                if(::WideCharToMultiByte(CP_UTF8,WC_ERR_INVALID_CHARS,
                      readable.data(),static_cast<int>(readable.size()),
                      utf8.data(),count,nullptr,nullptr)!=count){
                    if(path)::CoTaskMemFree(path);
                    resultCode=22;break;
                }
                line+=utf8;
            }
            line+="\t";

            HBITMAP bitmap=nullptr;
            if(SUCCEEDED(pathHr)&&path){
                Microsoft::WRL::ComPtr<IShellItem> item;
                if(SUCCEEDED(::SHCreateItemFromParsingName(
                     path,nullptr,IID_PPV_ARGS(&item)))){
                    Microsoft::WRL::ComPtr<IShellItemImageFactory> factory;
                    if(SUCCEEDED(item.As(&factory))){
                        SIZE requested{static_cast<LONG>(visualPixels),
                                       static_cast<LONG>(visualPixels)};
                        factory->GetImage(
                            requested,SIIGBF_ICONONLY,&bitmap);
                    }
                }
            }
            if(path)::CoTaskMemFree(path);

            if(bitmap){
                BITMAP bm{};
                if(::GetObjectW(bitmap,sizeof(bm),&bm)==sizeof(bm)&&
                   bm.bmWidth==static_cast<LONG>(visualPixels)&&
                   bm.bmHeight==static_cast<LONG>(visualPixels)){
                    BITMAPINFO dib{};
                    dib.bmiHeader.biSize=sizeof(BITMAPINFOHEADER);
                    dib.bmiHeader.biWidth=bm.bmWidth;
                    dib.bmiHeader.biHeight=-bm.bmHeight;
                    dib.bmiHeader.biPlanes=1;
                    dib.bmiHeader.biBitCount=32;
                    dib.bmiHeader.biCompression=BI_RGB;
                    std::vector<unsigned char> pixels(
                        visualPixels*visualPixels*4);
                    HDC screen=::GetDC(nullptr);
                    if(screen&&::GetDIBits(screen,bitmap,0,visualPixels,
                         pixels.data(),&dib,DIB_RGB_COLORS)==visualPixels){
                        bool anyAlpha=false;
                        for(size_t p=3;p<pixels.size();p+=4)
                            anyAlpha|=pixels[p]!=0;
                        if(!anyAlpha)
                            for(size_t p=3;p<pixels.size();p+=4)
                                pixels[p]=255;
                        DWORD required=0;
                        ::CryptBinaryToStringA(pixels.data(),
                            static_cast<DWORD>(pixels.size()),
                            CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                            nullptr,&required);
                        if(required>0&&required<40000){
                            std::string encoded(required,'\0');
                            if(::CryptBinaryToStringA(pixels.data(),
                                static_cast<DWORD>(pixels.size()),
                                CRYPT_STRING_BASE64|CRYPT_STRING_NOCRLF,
                                encoded.data(),&required)){
                                encoded.resize(std::strlen(encoded.c_str()));
                                line+=encoded;
                            }
                        }
                    }
                    if(screen)::ReleaseDC(nullptr,screen);
                }
                ::DeleteObject(bitmap);
            }

            line+="\n";
            DWORD sent=0;
            if(!::WriteFile(output,line.data(),
                 static_cast<DWORD>(line.size()),&sent,nullptr)||
               sent!=line.size())resultCode=23;
        }
        ::CoUninitialize();
        return resultCode;
    }
'''
helper=helper[:start]+branch+helper[end:]
helper_path.write_text(helper,encoding="utf-8",newline="")
print("EDITED app/winui/helper/FlyShellIsolationHelper.cpp")

test_path=ROOT/"tests/winui/test_known_folder_artwork_contract.py"
test=test_path.read_text(encoding="utf-8")
old='''        self.assertIn("SHGetFileInfoW(path,0",helper)
        self.assertIn("SHGFI_ICON",helper)
        self.assertIn("DrawIconEx",helper)
        self.assertIn("CryptBinaryToStringA",helper)
'''
new='''        self.assertIn("SHGetFileInfoW(path,0",helper)
        self.assertIn("IShellItemImageFactory",helper)
        self.assertIn("SIIGBF_ICONONLY",helper)
        self.assertIn("SHCreateItemFromParsingName",helper)
        self.assertIn("GetDIBits",helper)
        self.assertIn("CryptBinaryToStringA",helper)
'''
if old not in test:
    raise RuntimeError("Known Folder helper contract anchor missing")
test=test.replace(old,new,1)
test_path.write_text(test,encoding="utf-8",newline="")
print("EDITED tests/winui/test_known_folder_artwork_contract.py")
print("KNOWN_FOLDER_ICON_FACTORY_FIX_COMPLETE")
'@ | Set-Content -LiteralPath $script -Encoding utf8

python -X utf8 $script
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue

git diff --check
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

python -X utf8 -m unittest tests.winui.test_known_folder_artwork_contract tests.winui.test_registered_file_type_contract tests.winui.test_file_detail_controller_contract tests.winui.test_m26_fluent_contract
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\test.bat source
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

.\build.bat Release
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Output "KNOWN_FOLDER_ICON_FACTORY_BUILD_PASS"
git diff --stat
