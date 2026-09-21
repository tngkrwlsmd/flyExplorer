@echo off
if exist "bin" rmdir /s /q "bin"
mkdir bin
mkdir bin\x86-multibyte
mkdir bin\x86-unicode
mkdir bin\x64
mkdir bin\x86-multibyte\upchecker
mkdir bin\x86-unicode\upchecker
mkdir bin\x64\upchecker
mkdir bin\x86-multibyte\Languages
mkdir bin\x86-unicode\Languages
mkdir bin\x64\Languages



xcopy "..\bin\x86-multibyte\fxfile.exe"                  "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\fxfile-crash.dll"            "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\fxfile-keyhook.dll"          "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\fxfile-launcher.exe"         "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libcharset-1.dll"            "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libgcc_s_sjlj-1.dll"         "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libgfl340.dll"               "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libgfle340.dll"              "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libiconv-2.dll"              "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libwinpthread-1.dll"         "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libxml2-2.dll"               "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\libxpr.dll"                  "bin\x86-multibyte" /c /r /y
xcopy "..\bin\x86-multibyte\zlib1.dll"                   "bin\x86-multibyte" /c /r /y

xcopy "..\bin\x86-multibyte\upchecker\dbghelp.dll"         "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\fxfile-upchecker.exe"  "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libcurl.dll"         "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libgcc_s_sjlj-1.dll" "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libiconv-2.dll"      "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libwinpthread-1.dll" "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libxml2-2.dll"       "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\libxpr.dll"          "bin\x86-multibyte\upchecker" /c /r /y
xcopy "..\bin\x86-multibyte\upchecker\zlib1.dll"           "bin\x86-multibyte\upchecker" /c /r /y

xcopy "..\src\fxfile\Languages\*.xml"                    "bin\x86-multibyte\Languages" /c /e /r /y



xcopy "..\bin\x86-unicode\fxfile.exe"                    "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\fxfile-crash.dll"              "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\fxfile-keyhook.dll"            "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\fxfile-launcher.exe"           "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libcharset-1.dll"              "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libgcc_s_sjlj-1.dll"           "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libgfl340.dll"                 "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libgfle340.dll"                "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libiconv-2.dll"                "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libwinpthread-1.dll"           "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libxml2-2.dll"                 "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\libxprw.dll"                   "bin\x86-unicode" /c /r /y
xcopy "..\bin\x86-unicode\zlib1.dll"                     "bin\x86-unicode" /c /r /y

xcopy "..\bin\x86-unicode\upchecker\dbghelp.dll"           "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\fxfile-upchecker.exe"    "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libcurl.dll"           "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libgcc_s_sjlj-1.dll"   "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libiconv-2.dll"        "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libwinpthread-1.dll"   "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libxml2-2.dll"         "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\libxpr.dll"            "bin\x86-unicode\upchecker" /c /r /y
xcopy "..\bin\x86-unicode\upchecker\zlib1.dll"             "bin\x86-unicode\upchecker" /c /r /y

xcopy "..\src\fxfile\Languages\*.xml"                    "bin\x86-unicode\Languages" /c /e /r /y



xcopy "..\bin\x64\fxfile.exe"                           "bin\x64" /c /r /y
xcopy "..\bin\x64\fxfile-crash.dll"                     "bin\x64" /c /r /y
xcopy "..\bin\x64\fxfile-keyhook.dll"                   "bin\x64" /c /r /y
xcopy "..\bin\x64\fxfile-launcher.exe"                  "bin\x64" /c /r /y
xcopy "..\bin\x64\libcharset-1.dll"                     "bin\x64" /c /r /y
xcopy "..\bin\x64\libgcc_s_sjlj-1.dll"                  "bin\x64" /c /r /y
xcopy "..\bin\x64\libgfl340.dll"                        "bin\x64" /c /r /y
xcopy "..\bin\x64\libgfle340.dll"                       "bin\x64" /c /r /y
xcopy "..\bin\x64\libiconv-2.dll"                       "bin\x64" /c /r /y
xcopy "..\bin\x64\libwinpthread-1.dll"                  "bin\x64" /c /r /y
xcopy "..\bin\x64\libxml2-2.dll"                        "bin\x64" /c /r /y
xcopy "..\bin\x64\libxprw.dll"                          "bin\x64" /c /r /y
xcopy "..\bin\x64\zlib1.dll"                            "bin\x64" /c /r /y

xcopy "..\bin\x64\upchecker\dbghelp.dll"                  "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\fxfile-upchecker.exe"           "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libcurl.dll"                  "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libgcc_s_sjlj-1.dll"          "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libiconv-2.dll"               "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libwinpthread-1.dll"          "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libxml2-2.dll"                "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\libxpr.dll"                   "bin\x64\upchecker" /c /r /y
xcopy "..\bin\x64\upchecker\zlib1.dll"                    "bin\x64\upchecker" /c /r /y

xcopy "..\src\fxfile\Languages\*.xml"                   "bin\x64\Languages" /c /e /r /y
