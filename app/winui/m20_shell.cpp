#include "pch.h"
#include "MainWindow.xaml.h"
#include <thread>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
namespace winrt::FlyExplorerWinUIShell::implementation {
void MainWindow::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){
    OpenFolder(L"shell:MyComputerFolder");
}
void MainWindow::ApplyThemeChoice(int selection){
    using Theme=fxfile::previewsettings::Theme;
    if(selection<0||selection>2)return;
    const auto chosen=selection==2?Theme::Dark:
                      selection==1?Theme::Light:Theme::System;
    mPreferences.theme=chosen;
    RootShell().RequestedTheme(chosen==Theme::Dark?ElementTheme::Dark:
                               chosen==Theme::Light?ElementTheme::Light:
                               ElementTheme::Default);
    auto pref=mPreferences;
    auto guard=mPreferencesWriteMutex;
    auto revision=mPreferencesRevision;
    const auto ticket=revision->fetch_add(1)+1;
    const auto weak=get_weak();
    auto dispatch=DispatcherQueue();
    // Small local private settings writes still run off the UI thread.
    // Shared mutex and monotonically increasing tickets avoid stale
    // writes winning when a person rapidly changes the theme.
    try{
        std::thread([pref,guard,revision,ticket,weak,dispatch]{
            std::lock_guard<std::mutex> lock(*guard);
            if(ticket!=revision->load())return;
            const auto ok=fxfile::previewsettings::save(pref);
            if(!ok)dispatch.TryEnqueue([weak,revision,ticket]{
                if(auto ui=weak.get())
                    if(ticket==revision->load())
                        ui->StatusText().Text(
                            L"미리보기 테마 설정을 저장하지 못했습니다.");
            });
        }).detach();
    }catch(...){
        StatusText().Text(L"테마 설정 저장 작업을 시작할 수 없습니다.");
    }
}
}
