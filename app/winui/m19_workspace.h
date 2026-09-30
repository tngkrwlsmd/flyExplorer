// M1.9: standalone read-only/native UTF-16 legacy workspace bridge.
// Deliberately never opens or writes the running MFC user's conf directory.
#pragma once
#ifndef FLYEXPLORER_WINUI_PREVIEW_M19_WORKSPACE_H
#define FLYEXPLORER_WINUI_PREVIEW_M19_WORKSPACE_H
#include <array>
#include <string>
#include <vector>
namespace fxfile { namespace preview {
struct Workspace {
    std::array<std::vector<std::wstring>,2> paths;
    std::array<size_t,2> selected{{0,0}};
    bool split=true;
};
// Strict compatible SUBSET of existing MFC UXH-07 [main]/[workspace]
// .fxworkspace schema=1. Other legacy view/layout keys are read-only ignored.
// No modification of fxfile.conf, main.conf, dlg_state.conf or system registry.
bool loadWorkspace(std::wstring const& file,Workspace& value,
                   std::wstring& reason);
bool saveWorkspaceNew(std::wstring const& file,Workspace const& value,
                      std::wstring& reason);
} }
#endif
