"""Emit a bounded Windows native benchmark using the current FillFiles comparator.

Synthetic projection/filter/sort only: no Shell enumeration, XAML, GUI or app RSS.
"""
from pathlib import Path
import argparse,hashlib
ROOT=Path(__file__).resolve().parents[2]

def emit(destination: Path):
    text=(ROOT/'app/winui/MainWindow.xaml.cpp').read_text(encoding='utf-8-sig')
    begin=text.index('// Removing hidden and nonmatching rows is a stable subsequence.')
    filter_start=text.index('        if(!state.showHiddenItems){',begin)
    filter_end=text.index('        if(mode<=1||metadataReady)',filter_start)
    filtering=text[filter_start:filter_end]
    sort_start=text.index('std::stable_sort(order.begin(),order.end(),[&]',filter_end)
    sort_end=text.index('            });',sort_start)+len('            });')
    sorting=text[sort_start:sort_end]
    assert 'CompareStringOrdinal' in sorting and 'state.metadata[lhs]' in sorting
    assert 'Store::matches' in filtering and 'SFGAO_HIDDEN' in filtering
    template=r'''#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlobj_core.h>
#include <psapi.h>
#include "filter_rule_store.h"
#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdio>
#include <iostream>
#include <numeric>
#include <random>
#include <string>
#include <vector>
struct Entry {std::wstring label; unsigned long attributes=0; bool folder=false;std::size_t id=0;};
struct Metadata {std::wstring typeKey;bool sizeKnown=true,dateKnown=true;std::uint64_t bytes=0,modified=0;};
struct State {bool showHiddenItems=false;std::wstring filenameFilter=L"keep-*";std::vector<Metadata> metadata;} state;
struct Result {std::vector<std::size_t> ids;double ms;};
int main(){
std::vector<Entry> items;
for(std::size_t i=0;i<8000;++i){
 wchar_t name[96]{};swprintf_s(name,L"%ls-%05zu-%ls.txt",i%100==0?L"keep":L"other",i,i%3==0?L"한글":L"ASCII");
 items.push_back({name,static_cast<unsigned long>(i%17==0&&i%100!=0?SFGAO_HIDDEN:0),i%97==0,i});
}
std::mt19937 rng(20261029);std::shuffle(items.begin(),items.end(),rng);
for(auto const& item:items)state.metadata.push_back({item.id%3==0?L"텍스트":item.id%3==1?L"TypeA":L"TypeB",item.id%11!=0,item.id%13!=0,item.id*37%12345,1000000+item.id%333});
const bool indexedProjection=false;const bool metadataReady=true;auto const& nameIndex=items;
auto labelAt=[&](std::size_t i)->std::wstring const&{return items[i].label;};
auto folderAt=[&](std::size_t i){return items[i].folder;};
auto lessName=[&](std::size_t lhs,std::size_t rhs){return ::CompareStringOrdinal(labelAt(lhs).c_str(),-1,labelAt(rhs).c_str(),-1,TRUE)==CSTR_LESS_THAN;};
std::cout<<"{\"items\":8000,\"matches\":80,\"seed\":20261029,\"trials\":5,\"modes\":[";
for(int mode=0;mode<8;++mode){
 auto run=[&](bool early){
  std::vector<std::size_t> order(items.size());std::iota(order.begin(),order.end(),std::size_t{0});
  auto filter=[&](){
@@FILTER@@
  };
  auto started=std::chrono::steady_clock::now();
  if(early)filter();
@@SORT@@
  if(!early)filter();
  auto elapsed=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count();
  std::vector<std::size_t> ids;for(auto index:order)ids.push_back(items[index].id);
  return Result{std::move(ids),elapsed};
 };
 auto warmBefore=run(false),warmAfter=run(true);
 if(warmBefore.ids!=warmAfter.ids||warmAfter.ids.size()!=80)return 11;
 std::vector<double> before,after;
 for(int trial=0;trial<5;++trial){
  Result a,b;if(trial%2==0){a=run(false);b=run(true);}else{b=run(true);a=run(false);}
  if(a.ids!=b.ids||b.ids!=warmAfter.ids)return 12;
  before.push_back(a.ms);after.push_back(b.ms);
 }
 auto median=[](std::vector<double> v){std::sort(v.begin(),v.end());return v[2];};
 if(mode)std::cout<<",";
 std::cout<<"{\"mode\":"<<mode<<",\"before_median_ms\":"<<median(before)<<",\"after_median_ms\":"<<median(after)<<",\"equivalent\":true,\"before_trials_ms\":[";
 for(int i=0;i<5;++i){if(i)std::cout<<",";std::cout<<before[i];}
 std::cout<<"],\"after_trials_ms\":[";
 for(int i=0;i<5;++i){if(i)std::cout<<",";std::cout<<after[i];}std::cout<<"]}";
}
PROCESS_MEMORY_COUNTERS memory{};memory.cb=sizeof(memory);
if(!GetProcessMemoryInfo(GetCurrentProcess(),&memory,sizeof(memory)))return 13;
std::cout<<"],\"process_peak_working_set_mib\":"<<static_cast<double>(memory.PeakWorkingSetSize)/1048576.0<<"}\n";
return 0;
}
'''
    generated=template.replace('@@FILTER@@',filtering).replace('@@SORT@@',sorting)
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_bytes(generated.encode('utf-8'))
    print('FILTER_SORT_CPP_SHA256='+hashlib.sha256(destination.read_bytes()).hexdigest())
    return filtering,sorting

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit',type=Path,required=True)
    emit(parser.parse_args().emit)
