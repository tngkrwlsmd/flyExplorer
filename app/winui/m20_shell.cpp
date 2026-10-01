#include "pch.h"
#include "MainWindow.xaml.h"
#include <thread>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
namespace winrt::FlyExplorer::implementation {
void MainWindow::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){OpenFolder(L"shell:MyComputerFolder");}
void MainWindow::PersistPreferences(){
    auto pref=mPreferences;auto guard=mPreferencesWriteMutex;auto revision=mPreferencesRevision;
    const auto ticket=revision->fetch_add(1)+1;const auto weak=get_weak();auto dispatch=DispatcherQueue();
    try{std::thread([pref,guard,revision,ticket,weak,dispatch]{
        std::lock_guard<std::mutex> lock(*guard);if(ticket!=revision->load())return;
        const auto ok=fxfile::uisettings::save(pref);
        if(!ok)dispatch.TryEnqueue([weak,revision,ticket]{if(auto ui=weak.get())if(ticket==revision->load())ui->StatusText().Text(L"\uD654\uBA74 \uC124\uC815\uC744 \uC800\uC7A5\uD558\uC9C0 \uBABB\uD588\uC2B5\uB2C8\uB2E4.");});
    }).detach();}catch(...){StatusText().Text(L"\uD654\uBA74 \uC124\uC815 \uC800\uC7A5 \uC791\uC5C5\uC744 \uC2DC\uC791\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.");}
}
void MainWindow::ApplyThemeChoice(int selection){
    using Theme=fxfile::uisettings::Theme;if(selection<0||selection>2)return;
    const auto chosen=selection==2?Theme::Dark:selection==1?Theme::Light:Theme::System;
    mPreferences.theme=chosen;RootShell().RequestedTheme(chosen==Theme::Dark?ElementTheme::Dark:chosen==Theme::Light?ElementTheme::Light:ElementTheme::Default);PersistPreferences();
}
void MainWindow::UpdateView(int selection){
    if(selection<0||selection>3)return;const int side=mModel.activePane;
    mFileLists[side].viewMode=static_cast<FileViewMode>(selection);mPreferences.defaultViewMode=selection;
    ScheduleFileDetails(side);
    fileBar()->SetViewIndex(selection);FillFiles(side);UpdateSelectionChrome();UpdateFooterSummary();PersistPreferences();
    static constexpr wchar_t const* names[]={L"\uC790\uC138\uD788",L"\uBAA9\uB85D",L"\uC791\uC740 \uC544\uC774\uCF58",L"\uBCF4\uD1B5 \uC544\uC774\uCF58"};
    StatusText().Text(hstring(std::wstring(L"\uBCF4\uAE30: ")+names[selection]));
}
}
