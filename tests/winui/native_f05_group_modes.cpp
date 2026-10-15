#include "../../app/winui/file_group_modes.h"
#include "../../app/winui/file_group_presentation.h"
#include <cassert>
#include <iostream>
#include <vector>
using namespace fxfile::filegroup;
static Request req(std::size_t count){return {44,44,1,1,count,true,false,0};}
static ClassifiedRow row(std::uint64_t id,std::wstring name,std::uint64_t bytes,
    std::wstring date,bool folder=false,bool size=true,bool knownDate=true) {
    return {{id,true,folder,true,L".txt"},std::move(name),bytes,size,std::move(date),knownDate};
}
int main(){
    std::vector<ClassifiedRow> data{
        row(5,L"Alpha.txt",100,L"2026-10-15 12:00"),
        row(7,L"Zebra.txt",15000,L"2026-09-10 15:30"),
        row(9,L"가나다.txt",1024*1024,L"2026-10-01 09:00"),
        row(11,L"Other.txt",0,L"invalid",false,false,false),
        row(17,L"Folder",0,L"",true,false,false)};
    auto names=projectBy(Mode::Name,req(data.size()),data);
    assert(names.ready()&&names.sections.size()==5);
    assert(names.sections[0].title==L"폴더");
    assert(names.sections[1].title==L"A–F");
    assert(names.sections[2].title==L"M–R");
    assert(names.sections[3].title==L"S–Z");
    assert(names.sections[4].title==L"가–힣");
    CollapseState folded;
    folded.resetFor(44,1,0);
    assert(folded.toggle(44,1,L"A–F",0));
    auto displayed=present(req(data.size()),names,folded,160);
    assert(displayed.ready()&&displayed.visibleFileRows==4);
    for(auto const& entry:displayed.entries)
        if(entry.kind==EntryKind::File)assert(entry.logical!=5);
    auto sizes=projectBy(Mode::Size,req(data.size()),data);
    assert(sizes.ready()&&sizes.sections[0].title==L"폴더");
    assert(sizes.sections[1].title==L"10 KB 미만");
    assert(sizes.sections[2].title==L"10 KB–1 MB");
    assert(sizes.sections[3].title==L"1–100 MB");
    assert(sizes.sections.back().title==L"크기 미상");
    auto dates=projectBy(Mode::ModifiedMonth,req(data.size()),data);
    assert(dates.ready()&&dates.sections.size()==4);
    assert(dates.sections[0].title==L"폴더");
    assert(dates.sections[1].title==L"2026년 10월");
    assert((dates.sections[1].logicalItems==std::vector<std::uint64_t>{5,9}));
    assert(dates.sections[2].title==L"2026년 9월");
    assert(dates.sections[3].title==L"수정 날짜 미상");
    data[1].source.logical=5;
    assert(projectBy(Mode::Name,req(data.size()),data).status==Status::DuplicateIdentity);
    data[1].source.logical=7;
    auto wrong=req(data.size());wrong.visibleRoute=45;
    assert(projectBy(Mode::Size,wrong,data).status==Status::MissingRoute);
    wrong=req(data.size());wrong.indexComplete=false;
    assert(projectBy(Mode::ModifiedMonth,wrong,data).status==Status::Incomplete);
    std::vector<ClassifiedRow> many;
    for(std::uint64_t i=0;i<25000;i++)many.push_back(row(i,L"A",i,L"2026-10-15 00:00"));
    auto full=projectBy(Mode::Size,req(many.size()),many);
    assert(full.ready());
    auto excess=req(many.size()+1);
    many.push_back(row(25000,L"A",10,L"2026-10-15 00:00"));
    assert(projectBy(Mode::Size,excess,many).status==Status::LimitReached);
    std::cout<<"F05_NATIVE_GROUP_NAME_SIZE_MONTH_PASS\n";
}
