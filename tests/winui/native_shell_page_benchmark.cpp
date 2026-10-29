// Read-only timing of the real product supervisor; no XAML or user data writes.
#include "shell_isolated_supervisor.h"
#include <algorithm>
#include <chrono>
#include <condition_variable>
#include <cstdio>
#include <cwchar>
#include <memory>
#include <mutex>
#include <optional>
#include <set>
#include <string>

namespace {
struct Inbox {
    std::mutex mutex;
    std::condition_variable ready;
    std::optional<fxfile::shellnav::IsolatedResult> result;
};
}

int wmain(int argc,wchar_t** argv){
    if(argc!=4)return 2;
    const unsigned count=static_cast<unsigned>(std::wcstoul(argv[3],nullptr,10));
    if(count!=200&&count!=8000)return 2;
    const HRESULT com=::CoInitializeEx(nullptr,COINIT_MULTITHREADED);
    if(FAILED(com))return 3;
    int code=0;
    {
        auto inbox=std::make_shared<Inbox>();
        fxfile::shellnav::IsolatedShellSupervisor supervisor([inbox](auto result){
            std::lock_guard<std::mutex> lock(inbox->mutex);
            inbox->result=std::move(result);
            inbox->ready.notify_one();
        });
        if(!supervisor.start(argv[1]))code=4;
        std::set<std::wstring> seen;
        fxfile::shellnav::Location folder;
        std::uint32_t offset=0;
        double total=0;
        while(!code&&offset<count){
            const auto started=std::chrono::steady_clock::now();
            const auto ticket=offset?
                supervisor.submitPage(0,1,folder,offset,1024):
                supervisor.submitParsing(0,1,argv[2]);
            if(!ticket){code=5;break;}
            fxfile::shellnav::IsolatedResult result;
            {
                std::unique_lock<std::mutex> lock(inbox->mutex);
                if(!inbox->ready.wait_for(lock,std::chrono::seconds(12),
                    [&]{return inbox->result.has_value();})){code=6;break;}
                result=std::move(*inbox->result);
                inbox->result.reset();
            }
            const double ms=std::chrono::duration<double,std::milli>(
                std::chrono::steady_clock::now()-started).count();
            const auto expected=(std::min)(1024u,count-offset);
            if(result.request!=ticket||result.route!=1||FAILED(result.hr)||
               result.pageOffset!=offset||result.recovered||result.timedOut||
               result.snapshot.children.size()!=expected||
               result.snapshot.truncated!=(offset+expected<count)){
                std::fprintf(stderr,"PX13_SUPERVISOR_PAGE_FAILED offset=%u hr=%08lx\n",
                    offset,static_cast<unsigned long>(result.hr));
                code=7;break;
            }
            for(auto const& item:result.snapshot.children){
                if(!seen.insert(item.label).second){code=8;break;}
            }
            if(code)break;
            folder=std::move(result.snapshot.folder);
            if(!folder.valid()){code=9;break;}
            std::printf("PX13_SUPERVISOR_PAGE offset=%u items=%u ms=%.3f\n",
                offset,expected,ms);
            offset+=expected;
            total+=ms;
        }
        if(!code){
            for(unsigned i=0;i<count;++i){
                wchar_t expected[32]{};
                swprintf_s(expected,L"bench-%05u.txt",i);
                if(seen.count(expected)!=1){code=10;break;}
            }
        }
        supervisor.shutdown();
        if(!code)std::printf("PX13_SUPERVISOR_COMPLETE items=%u pages=%u ms=%.3f\n",
            count,(count+1023)/1024,total);
    }
    ::CoUninitialize();
    return code;
}
