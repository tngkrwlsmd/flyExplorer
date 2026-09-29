// M2.0: native pane/tab state and command boundary, no MFC or XAML.
#pragma once
#ifndef FXFILE_EXPLORER_UI_STATE_H
#define FXFILE_EXPLORER_UI_STATE_H
#include "shell_navigation_core.h"
#include <array>
#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>
namespace fxfile { namespace explorerui {
constexpr size_t kMaxTabsPerPane=32;
struct Pane final {
 std::vector<shellnav::Session> tabs;
 std::vector<std::uint64_t> routeIds,pending;
 std::vector<std::wstring> filesystemPaths;
 size_t active=0;
};
enum class Command { ActivatePane,SelectTab,AddTab,CloseTab,ToggleSplit };
struct Change final {
 bool accepted=false,changed=false;
 std::uint64_t createdRoute=0,releasedRoute=0;
};
class Model final {
public:
 Model();
 std::array<Pane,2> panes;
 int activePane=0;
 bool split=true;
 Change dispatch(Command command,int side=0,size_t tab=0);
 bool reset(bool isSplit,std::array<size_t,2> counts,
            std::array<size_t,2> selected);
 bool markPending(int side,size_t tab,std::uint64_t request,
                  bool supersedeOthers);
 bool completeRequest(int side,size_t tab,std::uint64_t route,
                      std::uint64_t request);
 bool invariant() const;
private:
 std::uint64_t nextRoute_=1; // stable, NEVER reuse stale watcher/worker route
};
} }
#endif
