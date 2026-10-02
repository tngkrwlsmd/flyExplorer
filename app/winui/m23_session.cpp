#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Windows.Graphics.h>
#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <utility>

using namespace winrt;
using namespace Microsoft::UI::Xaml;

namespace winrt::FlyExplorer::implementation {
namespace {

using SessionCoordinator=fxfile::sessioncoord::SessionCoordinator;

SessionCoordinator::Post sessionPost(
    Microsoft::UI::Dispatching::DispatcherQueue const& dispatch)
{
    return [dispatch](SessionCoordinator::UiTask task){
        try{
            (void)dispatch.TryEnqueue([
                task=std::move(task)
            ]() mutable {
                task();
            });
        }catch(...){}
    };
}

}

void MainWindow::InitializePrivateSession()
{
    if(!mSessionCoordinator.autoRestoreAllowed())return;
    // Only an explicitly saved private profile opt-in restores on future
    // default starts. Empty/nonexistent/invalid sessions have no effect.
    LoadPrivateSession();
}

void MainWindow::OnSavePrivateSession(
    IInspectable const&,RoutedEventArgs const&)
{
    if(mFileOperations.busy()){
        StatusText().Text(
            L"진행 중인 파일 작업이 끝난 후 세션을 저장하세요.");
        return;
    }

    try{
        if(ActiveWindowTab().model.split){
            const auto total=
                PrimaryColumn().ActualWidth()+SecondaryColumn().ActualWidth();
            if(total>1){
                ActiveWindowTab().splitPermille=
                    static_cast<std::uint32_t>((std::clamp)(
                        PrimaryColumn().ActualWidth()/total*1000.,
                        300.,700.));
            }
        }
    }catch(...){}

    std::uint32_t width=0,height=0;
    try{
        const auto current=AppWindow().Size();
        width=static_cast<std::uint32_t>((std::max)(current.Width,0));
        height=static_cast<std::uint32_t>((std::max)(current.Height,0));
    }catch(...){
        StatusText().Text(
            L"현재 창 크기를 확인하지 못해 세션을 저장하지 않았습니다.");
        return;
    }

    auto captured=mSessionCoordinator.capture(
        mWorkspace,width,height);
    if(!captured){
        if(captured.error==SessionCoordinator::CaptureError::HistoryUnavailable){
            StatusText().Text(
                L"탐색 기록을 안전하게 저장할 수 없어 세션을 저장하지 않았습니다.");
        }else{
            StatusText().Text(
                L"개인 세션은 기존 로컬 폴더와 제한된 창/폴더 탭만 저장할 수 있습니다.");
        }
        return;
    }

    auto weak=get_weak();
    auto post=sessionPost(DispatcherQueue());
    StatusText().Text(
        L"WinUI 개인 세션을 별도 스레드에서 안전하게 저장하는 중입니다...");
    if(!mSessionCoordinator.save(
        std::move(captured.value),std::move(post),
        [weak](bool ok){
            if(auto ui=weak.get()){
                ui->StatusText().Text(ok?
                    L"개인 WinUI 세션을 저장했습니다. 다음 기본 실행에서 자동 복원합니다.":
                    L"개인 세션을 저장하지 못했습니다. 실제 로컬 폴더만 지원합니다.");
            }
        })){
        StatusText().Text(L"개인 세션 저장 스레드를 시작하지 못했습니다.");
    }
}

void MainWindow::LoadPrivateSession()
{
    auto weak=get_weak();
    auto post=sessionPost(DispatcherQueue());
    if(!mSessionCoordinator.load(
        std::move(post),
        [weak](std::shared_ptr<SessionCoordinator::RestorePayload> payload){
            if(auto ui=weak.get()){
                if(ui->mFileOperations.busy())return;
                ui->SuspendActiveWindowTab();
                for(std::size_t i=0;i<ui->mWorkspace.count();++i){
                    ui->ReleaseWindowTabRoutes(ui->mWorkspace.state(i));
                }
                if(!ui->mSessionCoordinator.applyRestore(
                    *payload,ui->mWorkspace))
                    return;
                try{
                    ui->AppWindow().Resize({
                        static_cast<int>(payload->session.width),
                        static_cast<int>(payload->session.height)});
                }catch(...){}
                ui->ApplyActiveWindowTab(
                    L"저장한 개인 WinUI 세션을 복원했습니다.");
                ui->RefreshWindowTabs();
            }
        })){
        StatusText().Text(L"개인 세션 복원 스레드를 시작하지 못했습니다.");
    }
}

void MainWindow::OnRestorePrivateSession(
    IInspectable const&,RoutedEventArgs const&)
{
    if(mFileOperations.busy()){
        StatusText().Text(
            L"진행 중인 작업이 끝난 후 세션을 복원하세요.");
        return;
    }
    LoadPrivateSession();
}

void MainWindow::OnClearPrivateSession(
    IInspectable const&,RoutedEventArgs const&)
{
    auto weak=get_weak();
    auto post=sessionPost(DispatcherQueue());
    if(!mSessionCoordinator.clear(
        std::move(post),
        [weak](bool ok){
            if(auto ui=weak.get()){
                ui->StatusText().Text(ok?
                    L"저장된 개인 세션을 지웠습니다. 다음 실행에서는 자동 복원하지 않습니다.":
                    L"개인 세션 파일을 지우지 못했습니다.");
            }
        })){
        StatusText().Text(L"개인 세션 삭제를 시작하지 못했습니다.");
    }
}

} // namespace winrt::FlyExplorer::implementation
