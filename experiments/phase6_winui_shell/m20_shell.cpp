#include "pch.h"
#include "MainWindow.xaml.h"
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorerWinUIShell::implementation {
void MainWindow::OnThisPCClicked(IInspectable const&,RoutedEventArgs const&){
    OpenFolder(L"shell:MyComputerFolder");
}
void MainWindow::OnThemeSelectionChanged(
    IInspectable const& sender,SelectionChangedEventArgs const&){
    const auto selected=sender.as<ComboBox>().SelectedIndex();
    // Startup markup can raise SelectionChanged before all named
    // controls are materialized. Ignore that transient event safely.
    if(!RootShell()||!ThemeStateText())return;
    auto preference=ElementTheme::Default;
    hstring label=L"Theme: System";
    if(selected==1){
        preference=ElementTheme::Light;
        label=L"Theme: Light";
    }else if(selected==2){
        preference=ElementTheme::Dark;
        label=L"Theme: Dark";
    }else if(selected!=0)return;
    RootShell().RequestedTheme(preference);
    ThemeStateText().Text(label);
    // OS-enforced high contrast retains precedence. Per-user persisted
    // preview theme setting belongs in M2.1, not in legacy MFC conf.
}
}
