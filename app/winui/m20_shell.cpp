#include "pch.h"
#include "MainWindow.xaml.h"
#include <winrt/Microsoft.UI.Windowing.h>
#include <winrt/Windows.UI.h>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
namespace winrt::FlyExplorer::implementation {
void MainWindow::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){OpenFolder(L"shell:MyComputerFolder");}
void MainWindow::PersistPreferences(){
    const auto weak=get_weak();
    const auto dispatch=DispatcherQueue();
    const bool started=mPreferencesCoordinator.persist(
        [dispatch](fxfile::previewprefs::PreferencesCoordinator::UiTask task){
            try{return dispatch.TryEnqueue(
                [task=std::move(task)]() mutable {task();});}
            catch(...){return false;}
        },
        [weak]{
            if(auto ui=weak.get())
                ui->StatusText().Text(L"\uD654\uBA74 \uC124\uC815\uC744 \uC800\uC7A5\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.");
        });
    if(!started)
        StatusText().Text(L"\uD654\uBA74 \uC124\uC815 \uC800\uC7A5 \uC791\uC5C5\uC744 \uC2DC\uC791\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.");
}
void MainWindow::ApplyThemeChoice(int selection){
    using Theme=fxfile::uisettings::Theme;if(selection<0||selection>2)return;
    const auto chosen=selection==2?Theme::Dark:selection==1?Theme::Light:Theme::System;
    mPreferencesCoordinator.setTheme(chosen);RootShell().RequestedTheme(chosen==Theme::Dark?ElementTheme::Dark:chosen==Theme::Light?ElementTheme::Light:ElementTheme::Default);PersistPreferences();
}
void MainWindow::UpdateCaptionButtonTheme(){
    if(mClosing||!Microsoft::UI::Windowing::AppWindowTitleBar::IsCustomizationSupported())return;
    auto title=AppWindow().TitleBar();
    HIGHCONTRASTW contrast{sizeof(HIGHCONTRASTW)};
    if(!::SystemParametersInfoW(SPI_GETHIGHCONTRAST,sizeof(contrast),&contrast,0)||
       (contrast.dwFlags&HCF_HIGHCONTRASTON)!=0){
        // Leave contrast-theme caption colors entirely to Windows.
        title.ButtonForegroundColor(nullptr);
        title.ButtonInactiveForegroundColor(nullptr);
        title.ButtonBackgroundColor(nullptr);
        title.ButtonInactiveBackgroundColor(nullptr);
        title.ButtonHoverForegroundColor(nullptr);
        title.ButtonHoverBackgroundColor(nullptr);
        title.ButtonPressedForegroundColor(nullptr);
        title.ButtonPressedBackgroundColor(nullptr);
        return;
    }
    using Windows::UI::Color;
    const bool dark=RootShell().ActualTheme()==ElementTheme::Dark;
    const Color foreground=dark?Color{255,255,255,255}:Color{255,32,32,32};
    title.ButtonForegroundColor(foreground);
    title.ButtonInactiveForegroundColor(
        dark?Color{255,160,160,160}:Color{255,104,104,104});
    title.ButtonBackgroundColor(Color{0,0,0,0});
    title.ButtonInactiveBackgroundColor(Color{0,0,0,0});
    title.ButtonHoverForegroundColor(foreground);
    title.ButtonHoverBackgroundColor(
        dark?Color{255,50,50,50}:Color{255,229,229,229});
    title.ButtonPressedForegroundColor(foreground);
    title.ButtonPressedBackgroundColor(
        dark?Color{255,70,70,70}:Color{255,204,204,204});
    // Windows still draws/handles Minimize, Maximize, Close and Snap Layouts.
}
void MainWindow::RememberCurrentFolderView(bool remember){
    if(mClosing)return;
    const int side=ActiveWindowTab().model.activePane;
    const auto& pane=ActiveWindowTab().model.panes[side];
    if(pane.active>=pane.tabs.size()||
       pane.active>=pane.pending.size()||pane.pending[pane.active]||
       pane.active>=pane.filesystemPaths.size()||
       pane.active>=pane.routeIds.size()){
        StatusText().Text(L"폴더를 불러온 다음 보기 기억을 설정하세요.");
        return;
    }
    const auto& shown=ActiveWindowTab().fileLists[side];
    if(shown.visibleRoute!=pane.routeIds[pane.active]||
       shown.visibleTab!=pane.active){
        StatusText().Text(L"현재 폴더 목록을 불러온 다음 다시 시도하세요.");
        return;
    }
    const auto& folder=pane.filesystemPaths[pane.active];
    if(!fxfile::previewfolderview::FolderViewController::validFolder(folder)){
        StatusText().Text(L"폴더별 보기는 일반 로컬 드라이브 경로만 지원합니다.");
        return;
    }
    const bool changed=remember?
        mFolderViews.remember(folder,static_cast<int>(shown.viewMode)):
        mFolderViews.forget(folder);
    StatusText().Text(remember?
        (changed?L"현재 폴더의 보기 모드를 이 세션에서 기억했습니다.":
                 L"현재 폴더의 보기 모드를 기억할 수 없습니다."):
        (changed?L"현재 폴더의 보기 기억을 해제했습니다. 화면은 유지됩니다.":
                 L"현재 폴더에는 기억된 보기 모드가 없습니다."));
}
void MainWindow::UpdateView(int selection){
    if(selection<0||selection>7)return;const int side=ActiveWindowTab().model.activePane;
    ActiveWindowTab().fileLists[side].viewMode=static_cast<FileViewMode>(selection);mPreferencesCoordinator.setDefaultViewMode(selection);
    ScheduleFileDetails(side);
    fileBar()->SetViewIndex(selection);FillFiles(side);UpdateSelectionChrome();UpdateFooterSummary();PersistPreferences();
    static constexpr wchar_t const* names[]={L"\uC790\uC138\uD788",L"\uBAA9\uB85D",L"\uC791\uC740 \uC544\uC774\uCF58",L"\uBCF4\uD1B5 \uC544\uC774\uCF58",L"\uD070 \uC544\uC774\uCF58",L"\uC544\uC8FC \uD070 \uC544\uC774\uCF58",L"\uD0C0\uC77C",L"\uB0B4\uC6A9"};
    StatusText().Text(hstring(std::wstring(L"\uBCF4\uAE30: ")+names[selection]));
}
}
