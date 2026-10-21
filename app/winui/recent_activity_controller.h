// F07: bounded, opt-in activity history for this process only.
// No OS Explorer history, persistence, registry, background I/O or shell calls.
#pragma once
#include <algorithm>
#include <cstdint>
#include <cwctype>
#include <filesystem>
#include <limits>
#include <string>
#include <vector>

namespace fxfile::previewactivity {
class RecentActivityController final {
public:
 struct FolderVisit final {
  std::wstring path;
  std::uint32_t visits=0;
  std::uint64_t last=0;
 };
 static constexpr std::size_t kMaxRecentFiles=16;
 static constexpr std::size_t kMaxFolders=16;
 bool enabled() const noexcept {return enabled_;}
 void enable(bool yes) {
  if(enabled_==yes)return;
  enabled_=yes;
  if(!yes)clear();
 }
 void clear() noexcept {files_.clear();folders_.clear();sequence_=0;}
 std::vector<std::wstring> const& files() const noexcept {return files_;}
 std::vector<FolderVisit> const& folders() const noexcept {return folders_;}

 // Only normalized absolute drive paths from accepted native browsing/opening.
 // Do not follow links, query the filesystem or record UNC/virtual namespaces.
 static bool acceptable(std::wstring const& name) {
  if(name.size()<3||name.size()>1024||name[1]!=L':'||
     name[2]!=L'\\'||name.find(L'\0')!=std::wstring::npos||
     !((name[0]>=L'A'&&name[0]<=L'Z')||
       (name[0]>=L'a'&&name[0]<=L'z')))return false;
  try {
   std::filesystem::path path(name);
   return path.is_absolute()&&path.lexically_normal().native()==name;
  }catch(...){return false;}
 }
 void recordFile(std::wstring const& path) {
  if(!enabled_||!acceptable(path))return;
  auto it=std::find_if(files_.begin(),files_.end(),
     [&path](auto const& prev){return equal(prev,path);});
  if(it!=files_.end())files_.erase(it);
  files_.insert(files_.begin(),path);
  if(files_.size()>kMaxRecentFiles)files_.resize(kMaxRecentFiles);
 }
 void recordFolder(std::wstring const& path) {
  if(!enabled_||!acceptable(path))return;
  ++sequence_;
  auto it=std::find_if(folders_.begin(),folders_.end(),
     [&path](FolderVisit const& old){return equal(old.path,path);});
  if(it!=folders_.end()){
   if(it->visits<(std::numeric_limits<std::uint32_t>::max)())++it->visits;
   it->last=sequence_;
  }else{
   if(folders_.size()==kMaxFolders){
    auto evict=std::min_element(folders_.begin(),folders_.end(),
     [](FolderVisit const& a,FolderVisit const& b){
      return a.visits==b.visits?a.last<b.last:a.visits<b.visits;
     });
    folders_.erase(evict);
   }
   folders_.push_back({path,1,sequence_});
  }
  std::sort(folders_.begin(),folders_.end(),
   [](FolderVisit const& a,FolderVisit const& b){
    return a.visits==b.visits?a.last>b.last:a.visits>b.visits;
   });
 }
private:
 static bool equal(std::wstring const& a,std::wstring const& b) {
  if(a.size()!=b.size())return false;
  for(std::size_t i=0;i<a.size();++i)
   if(std::towlower(a[i])!=std::towlower(b[i]))return false;
  return true;
 }
 bool enabled_=false;
 std::uint64_t sequence_=0;
 std::vector<std::wstring> files_{};
 std::vector<FolderVisit> folders_{};
};
} // namespace fxfile::previewactivity
