#include "pch.h"
#include "MainWindow.xaml.h"

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace winrt::FlyExplorer::implementation {

void MainWindow::InitializeFilterRules()
{
    const bool loaded=mFilterRules.load();
    RefreshFilterRuleManager(-1);
    if(!loaded)
        StatusText().Text(
            L"필터 프리셋 파일이 손상되어 기존 규칙을 불러오지 않았습니다.");
}

void MainWindow::RefreshFilterRuleManager(int selected)
{
    struct Guard final{
        bool& flag;
        explicit Guard(bool& value):flag(value){flag=true;}
        ~Guard(){flag=false;}
    } guard(mPopulatingFilterRules);

    auto rows=FilterRuleManagerBox().Items();
    rows.Clear();
    for(auto const& rule:mFilterRules.items()){
        ComboBoxItem item;
        item.Content(box_value(hstring(rule.name)));
        ToolTipService::SetToolTip(item,box_value(hstring(rule.masks)));
        rows.Append(item);
    }

    if(mFilterRules.items().empty()){
        FilterRuleManagerBox().SelectedIndex(-1);
        FilterRuleNameEdit().Text(L"");
        const int side=ActiveWindowTab().model.activePane;
        FilterRuleMasksEdit().Text(hstring(
            ActiveWindowTab().fileLists[side].filenameFilter));
        return;
    }

    if(selected<0||
       static_cast<std::size_t>(selected)>=mFilterRules.items().size())
        selected=0;
    FilterRuleManagerBox().SelectedIndex(selected);
    auto const& rule=mFilterRules.items()[static_cast<std::size_t>(selected)];
    FilterRuleNameEdit().Text(hstring(rule.name));
    FilterRuleMasksEdit().Text(hstring(rule.masks));
}

void MainWindow::OnToggleFilterRules(
    IInspectable const&,RoutedEventArgs const&)
{
    const auto next=FilterRulePanel().Visibility()==Visibility::Collapsed?
                    Visibility::Visible:Visibility::Collapsed;
    BookmarkPanel().Visibility(Visibility::Collapsed);
    WorkspacePanel().Visibility(Visibility::Collapsed);
    SearchPanel().Visibility(Visibility::Collapsed);
    FilterRulePanel().Visibility(next);
    if(next==Visibility::Visible){
        RefreshFilterRuleManager(FilterRuleManagerBox().SelectedIndex());
        EnsureExpandedPanelFits();
        StatusText().Text(
            L"이름 일부 또는 *.cpp;*.h 같은 마스크 규칙을 저장하고 활성 창에 적용할 수 있습니다.");
    }
}

void MainWindow::OnFilterRuleSelectionChanged(
    IInspectable const&,SelectionChangedEventArgs const&)
{
    if(mPopulatingFilterRules)return;
    const int selected=FilterRuleManagerBox().SelectedIndex();
    if(selected<0||
       static_cast<std::size_t>(selected)>=mFilterRules.items().size())
        return;
    auto const& rule=mFilterRules.items()[static_cast<std::size_t>(selected)];
    FilterRuleNameEdit().Text(hstring(rule.name));
    FilterRuleMasksEdit().Text(hstring(rule.masks));
}

void MainWindow::OnNewFilterRule(
    IInspectable const&,RoutedEventArgs const&)
{
    mPopulatingFilterRules=true;
    FilterRuleManagerBox().SelectedIndex(-1);
    mPopulatingFilterRules=false;
    FilterRuleNameEdit().Text(L"");
    const int side=ActiveWindowTab().model.activePane;
    FilterRuleMasksEdit().Text(hstring(
        ActiveWindowTab().fileLists[side].filenameFilter));
    FilterRuleNameEdit().Focus(FocusState::Programmatic);
}

void MainWindow::OnSaveFilterRule(
    IInspectable const&,RoutedEventArgs const&)
{
    const auto name=std::wstring(FilterRuleNameEdit().Text().c_str());
    const auto masks=std::wstring(FilterRuleMasksEdit().Text().c_str());
    auto backup=mFilterRules;
    const int selected=FilterRuleManagerBox().SelectedIndex();
    const auto result=selected>=0?
        mFilterRules.update(static_cast<std::size_t>(selected),name,masks):
        mFilterRules.add(name,masks);
    using Result=fxfile::filterrules::MutationResult;
    if(result==Result::Duplicate){
        StatusText().Text(L"같은 이름의 필터 프리셋이 이미 있습니다.");
        return;
    }
    if(result==Result::Full){
        StatusText().Text(L"필터 프리셋은 최대 20개까지 저장할 수 있습니다.");
        return;
    }
    if(result!=Result::Applied){
        StatusText().Text(
            L"이름은 1~56자, 규칙은 1~260자의 한 줄 텍스트여야 합니다.");
        return;
    }
    if(!mFilterRules.save()){
        mFilterRules=std::move(backup);
        StatusText().Text(L"필터 프리셋을 안전하게 저장하지 못했습니다.");
        return;
    }
    const int next=selected>=0?selected:
        static_cast<int>(mFilterRules.items().size()-1);
    RefreshFilterRuleManager(next);
    StatusText().Text(L"필터 프리셋을 저장했습니다.");
}

void MainWindow::OnApplyFilterRule(
    IInspectable const&,RoutedEventArgs const&)
{
    const auto masks=std::wstring(FilterRuleMasksEdit().Text().c_str());
    if(!fxfile::filterrules::Store::validExpression(masks)){
        StatusText().Text(
            L"필터 규칙을 확인하세요. 세미콜론 사이에는 비어 있지 않은 이름/마스크가 필요합니다.");
        return;
    }
    const int side=ActiveWindowTab().model.activePane;
    auto box=side==0?LeftNameFilterBox():RightNameFilterBox();
    if(box.Opacity()<0.5)ToggleNameFilter(side);
    box.Text(hstring(masks));
    box.Focus(FocusState::Programmatic);
    box.SelectAll();
    StatusText().Text(
        side==0?L"왼쪽 창에 필터 프리셋을 적용했습니다.":
                L"오른쪽 창에 필터 프리셋을 적용했습니다.");
}

void MainWindow::OnDeleteFilterRule(
    IInspectable const&,RoutedEventArgs const&)
{
    const int selected=FilterRuleManagerBox().SelectedIndex();
    if(selected<0){
        StatusText().Text(L"삭제할 필터 프리셋을 선택하세요.");
        return;
    }
    auto backup=mFilterRules;
    if(!mFilterRules.erase(static_cast<std::size_t>(selected))){
        StatusText().Text(L"선택한 필터 프리셋을 찾지 못했습니다.");
        return;
    }
    if(!mFilterRules.save()){
        mFilterRules=std::move(backup);
        StatusText().Text(L"필터 프리셋 삭제를 저장하지 못했습니다.");
        return;
    }
    RefreshFilterRuleManager(selected);
    StatusText().Text(L"필터 프리셋을 삭제했습니다.");
}

} // namespace winrt::FlyExplorer::implementation
