// F03 test-only executable. It never opens user files or spawns processes.
// The real shipping helper is used for success cases; this fixture is only
// for corrupted-wire and an unresponsive *owned* child.
#include "../../src/base/file_preview_worker_wire.h"
#include <Windows.h>
#include <cwchar>
int wmain(int argc,wchar_t** argv) {
    if(argc!=2||std::wcscmp(argv[1],L"--preview-read")!=0)return 21;
    wchar_t mode[24]{};
    if(!::GetEnvironmentVariableW(L"FLY_F03_OWNED_STUB_MODE",
                                   mode,24))return 22;
    if(std::wcscmp(mode,L"hang")==0) {
        ::Sleep(30000);
        return 0;
    }
    if(std::wcscmp(mode,L"corrupt")==0) {
        fxfile::previewwire::Reply reply{};
        reply.status=0;
        reply.kind=1;
        reply.byteCount=1;
        reply.checksum=123; // intentionally wrong
        DWORD sent=0;
        const auto out=::GetStdHandle(STD_OUTPUT_HANDLE);
        if(!::WriteFile(out,&reply,sizeof(reply),&sent,nullptr)||
           sent!=sizeof(reply))return 23;
        const unsigned char body=0x41;
        if(!::WriteFile(out,&body,1,&sent,nullptr)||sent!=1)return 24;
        return 0;
    }
    return 25;
}
