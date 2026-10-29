#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include "../../src/base/file_preview_policy.h"
#include <algorithm>
#include <filesystem>
#include <string>
#include <utility>

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace winrt::FlyExplorer::implementation {

void MainWindow::CancelTextPreview() noexcept {
    mTextPreviewController.cancel();
}

void MainWindow::OnRevealTextPreview(
    IInspectable const&,RoutedEventArgs const&) {
    if(mClosing||!ActiveWindowTab().fileInfoPaneVisible)return;
    // The disclosure is a focus/scroll gesture only; the original Preview
    // button remains the sole explicit opt-in that can read file bytes.
    auto button=TextPreviewToggleButton();
    button.Focus(FocusState::Keyboard);
    button.StartBringIntoView();
}

void MainWindow::OnFileInfoViewportSizeChanged(
    IInspectable const&,SizeChangedEventArgs const&) {
    auto pane=FileInfoPane();
    if(mClosing||!pane||pane.Visibility()!=Visibility::Visible)return;
    auto button=TextPreviewToggleButton();
    // Preserve the existing focus; resizing must never opt in or read bytes.
    if(button&&button.FocusState()!=FocusState::Unfocused)
        button.StartBringIntoView();
}

void MainWindow::OnToggleTextPreview(
    IInspectable const&,RoutedEventArgs const&) {
    if(mClosing||!ActiveWindowTab().fileInfoPaneVisible)return;
    mTextPreviewEnabled=!mTextPreviewEnabled;
    TextPreviewToggleButton().Content(winrt::box_value(
        mTextPreviewEnabled?L"텍스트 미리보기 끄기":L"텍스트 미리보기 켜기"));
    Microsoft::UI::Xaml::Automation::AutomationProperties::SetName(
        TextPreviewToggleButton(),
        mTextPreviewEnabled?L"텍스트 미리보기 끄기":L"텍스트 미리보기 켜기");
    if(!mTextPreviewEnabled){
        CancelTextPreview();
        TextPreviewBody().Text(L"");
        TextPreviewStatus().Text(L"텍스트 미리보기는 꺼져 있습니다.");
        return;
    }
    QueueTextPreview();
}

void MainWindow::QueueTextPreview() {
    // Only an explicit user click opts in. Never query file contents just
    // because the read-only Details pane is open or a row was highlighted.
    CancelTextPreview();
    if(mClosing)return;
    TextPreviewBody().Text(L"");
    if(!mTextPreviewEnabled||!ActiveWindowTab().fileInfoPaneVisible)return;
    TextPreviewStatus().Text(L"텍스트 파일 한 개를 선택하세요.");
    auto const windowIndex=mWorkspace.activeIndex();
    auto const& state=ActiveWindowTab();
    const int side=state.model.activePane;
    if(side<0||side>1||(side==1&&!state.model.split))return;
    auto const& pane=state.model.panes[side];
    const auto tab=pane.active;
    if(tab>=pane.tabs.size()||tab>=pane.pending.size()||
       tab>=pane.routeIds.size()||pane.pending[tab])return;
    const auto route=pane.routeIds[tab];
    if(!route)return;
    auto const& files=state.fileLists[side];
    if(files.visibleRoute!=route||files.visibleTab!=tab)return;
    auto view=side==0?LeftFiles():RightFiles();
    if(view.SelectedItems().Size()!=1)return;
    auto selected=view.SelectedItems().GetAt(0).try_as<ListViewItem>();
    if(!selected||!selected.Tag())return;
    const auto logical=winrt::unbox_value<std::uint64_t>(selected.Tag());
    const auto entry=std::find(
        files.renderedLogical.begin(),files.renderedLogical.end(),logical);
    if(entry==files.renderedLogical.end())return;
    const auto index=static_cast<std::size_t>(
        std::distance(files.renderedLogical.begin(),entry));
    if(index>=files.renderedPaths.size())return;
    const std::wstring path=files.renderedPaths[index];
    const auto& session=pane.tabs[tab];
    const auto& snapshot=session.snapshot();
    std::size_t resident=0;
    const bool onPage=snapshot.residentIndex(logical,resident);
    auto const* item=onPage?&snapshot.children[resident]:nullptr;
    auto const* indexed=session.indexedItem(static_cast<std::size_t>(logical));
    if(!item&&!indexed)return;
    if((item?item->isFolder():indexed->isFolder())||
       !(item?item->isFileSystem():indexed->isFileSystem())||
       path!=(item?item->parsingName:indexed->parsingName)||
       !fxfile::previewpolicy::canonicalLocalPath(path))return;
    const auto name=std::filesystem::path(path).extension().native();
    const bool textFile=fxfile::previewpolicy::endsWithAsciiNoCase(name,L".txt")||
        fxfile::previewpolicy::endsWithAsciiNoCase(name,L".md")||
        fxfile::previewpolicy::endsWithAsciiNoCase(name,L".log");
    if(!textFile){
        TextPreviewStatus().Text(L"텍스트 파일(.txt, .md, .log)만 미리 볼 수 있습니다.");
        return;
    }

    wchar_t executable[32768]{};
    const auto count=::GetModuleFileNameW(nullptr,executable,32768);
    if(!count||count>=32768){
        TextPreviewStatus().Text(L"미리보기 도우미를 확인하지 못했습니다.");
        return;
    }
    const std::wstring sibling=(std::filesystem::path(executable).parent_path()/
                                L"FlyShellIsolationHelper.exe").native();
    fxfile::previewctrl::PreviewController::Request request{};
    request.side=side;
    request.filePath=path;
    request.siblingHelper=sibling;
    request.key={
        static_cast<std::uint64_t>(windowIndex+1),
        static_cast<std::uint64_t>(side+1),
        static_cast<std::uint64_t>(tab+1),
        route,path
    };
    auto dispatcher=DispatcherQueue();
    auto weak=get_weak();
    TextPreviewStatus().Text(L"선택한 텍스트 파일을 읽는 중입니다.");
    if(!mTextPreviewController.start(
        std::move(request),
        [dispatcher](fxfile::previewctrl::PreviewController::UiTask task) {
            try{
                return dispatcher.TryEnqueue(
                    [task=std::move(task)]() mutable {task();});
            }catch(...){return false;}
        },
        [weak](fxfile::previewctrl::PreviewController::Completion result) {
            auto ui=weak.get();
            if(!ui||ui->mClosing||!ui->mTextPreviewEnabled||
               !ui->mTextPreviewController.accepts(result.ticket))return;
            auto const& key=result.ticket.key;
            if(ui->mWorkspace.activeIndex()+1!=key.window||
               !ui->ActiveWindowTab().fileInfoPaneVisible||
               ui->ActiveWindowTab().model.activePane!=result.side||
               key.pane!=static_cast<std::uint64_t>(result.side+1))return;
            auto const& pane=ui->ActiveWindowTab().model.panes[result.side];
            if(pane.active+1!=key.tab||
               pane.active>=pane.routeIds.size()||
               pane.routeIds[pane.active]!=key.generation||
               pane.pending[pane.active])return;
            auto const& files=ui->ActiveWindowTab().fileLists[result.side];
            if(files.visibleRoute!=key.generation||
               files.visibleTab!=pane.active)return;
            auto view=result.side==0?ui->LeftFiles():ui->RightFiles();
            if(view.SelectedItems().Size()!=1)return;
            auto selected=view.SelectedItems().GetAt(0).try_as<ListViewItem>();
            if(!selected||!selected.Tag())return;
            const auto logical=winrt::unbox_value<std::uint64_t>(selected.Tag());
            const auto index=std::find(
                files.renderedLogical.begin(),files.renderedLogical.end(),logical);
            if(index==files.renderedLogical.end())return;
            const auto slot=static_cast<std::size_t>(
                std::distance(files.renderedLogical.begin(),index));
            if(slot>=files.renderedPaths.size()||
               files.renderedPaths[slot]!=key.selectedIdentity)return;
            if(!result.result.ok()||
               result.result.kind!=fxfile::previewpolicy::Kind::Text){
                ui->TextPreviewStatus().Text(L"이 파일의 내용을 안전하게 표시할 수 없습니다.");
                return;
            }
            const auto& bytes=result.result.bytes;
            if(std::find(bytes.begin(),bytes.end(),static_cast<std::uint8_t>(0))
                    !=bytes.end()){
                ui->TextPreviewStatus().Text(L"텍스트에 이진 데이터가 포함되어 표시하지 않습니다.");
                return;
            }
            try{
                std::string utf8(bytes.begin(),bytes.end());
                auto decoded=winrt::to_hstring(utf8);
                std::wstring display(decoded.c_str(),decoded.size());
                bool clipped=display.size()>8192;
                if(clipped){
                    // Valid UTF-8 may decode to a UTF-16 surrogate pair.
                    // Never expose only its leading unit at the display cap.
                    const auto last=display[8191];
                    display.resize(last>=0xD800&&last<=0xDBFF?8191:8192);
                }
                ui->TextPreviewBody().Text(hstring(display));
                ui->TextPreviewStatus().Text(clipped?
                    L"파일 앞부분만 표시합니다.":L"텍스트 파일 미리보기");
            }catch(...){
                ui->TextPreviewBody().Text(L"");
                ui->TextPreviewStatus().Text(L"UTF-8 텍스트로 표시할 수 없습니다.");
            }
        })){
        TextPreviewStatus().Text(L"미리보기 작업을 시작하지 못했습니다.");
    }
}

} // namespace winrt::FlyExplorer::implementation
