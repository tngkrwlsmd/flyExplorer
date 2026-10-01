#include "explorer_ui_state.h"
#include <limits>
#include <utility>
namespace fxfile { namespace explorerui {
namespace {
bool validSide(int side){return side==0||side==1;}
bool shape(Pane const& p){
 const size_t count=p.tabs.size();
 return count>=1&&count<=kMaxTabsPerPane&&
        p.routeIds.size()==count&&p.pending.size()==count&&
        p.filesystemPaths.size()==count&&p.active<count;
}
}
Model::Model(std::uint64_t routeBase){
 if(routeBase>(std::numeric_limits<std::uint64_t>::max)()-4)routeBase=0;
 nextRoute_=routeBase+1;
 reset(true,{{1,1}},{{0,0}});
}
bool Model::invariant() const {
 return validSide(activePane)&&(split||activePane==0)&&
        shape(panes[0])&&shape(panes[1]);
}
bool Model::reset(bool isSplit,std::array<size_t,2> counts,
                  std::array<size_t,2> selected){
 for(int side=0;side!=2;++side)
  if(counts[side]<1||counts[side]>kMaxTabsPerPane||
     selected[side]>=counts[side])return false;
 if(nextRoute_>(std::numeric_limits<std::uint64_t>::max)()-
               counts[0]-counts[1])return false;
 std::array<Pane,2> replacement{};
 for(int side=0;side!=2;++side){
  auto& pane=replacement[side];
  for(size_t i=0;i<counts[side];++i){
   pane.tabs.emplace_back();
   pane.routeIds.push_back(nextRoute_++);
   pane.pending.push_back(0);
   pane.filesystemPaths.emplace_back();
  }
  pane.active=selected[side];
 }
 panes=std::move(replacement);
 split=isSplit;
 activePane=0;
 return invariant();
}
Change Model::dispatch(Command command,int side,size_t tab){
 Change result{};
 if(!invariant())return result;
 if(command==Command::ToggleSplit){
  split=!split;
  if(!split)activePane=0;
  result.accepted=result.changed=true;
  return result;
 }
 if(!validSide(side)||(side==1&&!split))return result;
 auto& pane=panes[side];
 switch(command){
 case Command::ActivatePane:
  result.accepted=true;
  result.changed=activePane!=side;
  activePane=side;
  break;
 case Command::SelectTab:
  if(tab>=pane.tabs.size())break;
  result.accepted=true;
  result.changed=pane.active!=tab||activePane!=side;
  pane.active=tab;
  activePane=side;
  break;
 case Command::AddTab:
  if(pane.tabs.size()>=kMaxTabsPerPane||
     nextRoute_==(std::numeric_limits<std::uint64_t>::max)())break;
  pane.tabs.emplace_back();
  pane.routeIds.push_back(nextRoute_++);
  pane.pending.push_back(0);
  pane.filesystemPaths.emplace_back();
  pane.active=pane.tabs.size()-1;
  activePane=side;
  result.accepted=result.changed=true;
  result.createdRoute=pane.routeIds.back();
  break;
 case Command::CloseTab:
  if(pane.tabs.size()<=1)break;
  result.releasedRoute=pane.routeIds[pane.active];
  pane.tabs.erase(pane.tabs.begin()+pane.active);
  pane.routeIds.erase(pane.routeIds.begin()+pane.active);
  pane.pending.erase(pane.pending.begin()+pane.active);
  pane.filesystemPaths.erase(pane.filesystemPaths.begin()+pane.active);
  if(pane.active>=pane.tabs.size())pane.active=pane.tabs.size()-1;
  result.accepted=result.changed=true;
  break;
 default:break;
 }
 return result;
}
bool Model::markPending(int side,size_t tab,std::uint64_t request,
                        bool supersedeOthers){
 if(!validSide(side)||!request)return false;
 auto& pane=panes[side];
 if(tab>=pane.pending.size())return false;
 if(supersedeOthers)
  for(auto& id:pane.pending)id=0;
 pane.pending[tab]=request;
 return true;
}
bool Model::completeRequest(int side,size_t tab,std::uint64_t route,
                            std::uint64_t request){
 if(!validSide(side)||!request)return false;
 auto& pane=panes[side];
 if(tab>=pane.routeIds.size()||pane.routeIds[tab]!=route||
    pane.pending[tab]!=request)return false;
 pane.pending[tab]=0;
 return true;
}
} }
