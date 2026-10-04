#include "pch.h"
#include "MainWindow.xaml.h"

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;

namespace winrt::FlyExplorer::implementation {
namespace {

fxfile::preview::SearchQuery queryFromPreset(
    fxfile::searchpresets::Preset const& p)
{
    fxfile::preview::SearchQuery q{};
    q.term=p.term;
    q.extension=p.extension;
    q.minSizeKb=p.minSizeKb;
    q.maxSizeKb=p.maxSizeKb;
    q.modifiedAfter=p.modifiedAfter;
    q.modifiedBefore=p.modifiedBefore;
    q.regex=p.regex;
    q.caseSensitive=p.caseSensitive;
    q.kind=p.kind==1?fxfile::preview::SearchEntryKind::Folders:
           p.kind==2?fxfile::preview::SearchEntryKind::FilesAndFolders:
                     fxfile::preview::SearchEntryKind::Files;
    return q;
}

} // namespace

void MainWindow::InitializeSearchPresets()
{
    const bool loaded=mSearchPresets.load();
    RefreshSearchPresetManager(-1);
    if(!loaded)
        StatusText().Text(
            L"저장된 검색 조건 파일이 손상되어 기존 조건을 불러오지 않았습니다.");
}

fxfile::searchpresets::Preset MainWindow::SearchPresetFromUi()
{
    fxfile::searchpresets::Preset p{};
    p.name=std::wstring(SearchPresetNameBox().Text().c_str());
    p.term=std::wstring(SearchTermBox().Text().c_str());
    p.extension=std::wstring(SearchExtensionBox().Text().c_str());
    p.minSizeKb=std::wstring(SearchMinSizeBox().Text().c_str());
    p.maxSizeKb=std::wstring(SearchMaxSizeBox().Text().c_str());
    p.modifiedAfter=std::wstring(SearchModifiedAfterBox().Text().c_str());
    p.modifiedBefore=std::wstring(SearchModifiedBeforeBox().Text().c_str());
    p.regex=SearchRegexBox().IsChecked().GetBoolean();
    p.caseSensitive=SearchCaseBox().IsChecked().GetBoolean();
    p.kind=SearchTargetBox().SelectedIndex();
    if(p.kind<0||p.kind>2)p.kind=0;
    return p;
}

void MainWindow::ApplySearchPresetToUi(
    fxfile::searchpresets::Preset const& p)
{
    SearchTermBox().Text(hstring(p.term));
    SearchExtensionBox().Text(hstring(p.extension));
    SearchMinSizeBox().Text(hstring(p.minSizeKb));
    SearchMaxSizeBox().Text(hstring(p.maxSizeKb));
    SearchModifiedAfterBox().Text(hstring(p.modifiedAfter));
    SearchModifiedBeforeBox().Text(hstring(p.modifiedBefore));
    SearchRegexBox().IsChecked(p.regex);
    SearchCaseBox().IsChecked(p.caseSensitive);
    SearchTargetBox().SelectedIndex((std::clamp)(p.kind,0,2));
}

void MainWindow::RefreshSearchPresetManager(int selected)
{
    struct Guard final{
        bool& value;
        explicit Guard(bool& target):value(target){value=true;}
        ~Guard(){value=false;}
    } guard(mPopulatingSearchPresets);

    auto rows=SearchPresetBox().Items();
    rows.Clear();
    for(auto const& p:mSearchPresets.items()){
        ComboBoxItem item;
        item.Content(box_value(hstring(p.name)));
        rows.Append(item);
    }
    if(mSearchPresets.items().empty()){
        SearchPresetBox().SelectedIndex(-1);
        SearchPresetNameBox().Text(L"");
        return;
    }
    if(selected<0||
       static_cast<std::size_t>(selected)>=mSearchPresets.items().size())
        selected=0;
    SearchPresetBox().SelectedIndex(selected);
    auto const& p=mSearchPresets.items()[static_cast<std::size_t>(selected)];
    SearchPresetNameBox().Text(hstring(p.name));
}

void MainWindow::OnSearchPresetSelectionChanged(
    IInspectable const&,SelectionChangedEventArgs const&)
{
    if(mPopulatingSearchPresets)return;
    const int selected=SearchPresetBox().SelectedIndex();
    if(selected<0||
       static_cast<std::size_t>(selected)>=mSearchPresets.items().size())
        return;
    auto const& p=mSearchPresets.items()[static_cast<std::size_t>(selected)];
    SearchPresetNameBox().Text(hstring(p.name));
    ApplySearchPresetToUi(p);
    StatusText().Text(L"저장된 검색 조건을 입력란에 불러왔습니다.");
}

void MainWindow::OnNewSearchPreset(
    IInspectable const&,RoutedEventArgs const&)
{
    mPopulatingSearchPresets=true;
    SearchPresetBox().SelectedIndex(-1);
    mPopulatingSearchPresets=false;
    SearchPresetNameBox().Text(L"");
    SearchPresetNameBox().Focus(FocusState::Programmatic);
}

void MainWindow::OnSaveSearchPreset(
    IInspectable const&,RoutedEventArgs const&)
{
    auto value=SearchPresetFromUi();
    const auto validation=fxfile::preview::validateSearchQuery(
        queryFromPreset(value));
    if(validation!=fxfile::preview::SearchQueryValidation::Valid){
        StatusText().Text(
            L"검색 조건을 먼저 확인하세요. 잘못된 크기/날짜/정규식 조건은 저장하지 않습니다.");
        return;
    }

    auto backup=mSearchPresets;
    const int selected=SearchPresetBox().SelectedIndex();
    const auto result=selected>=0?
        mSearchPresets.update(static_cast<std::size_t>(selected),value):
        mSearchPresets.add(value);
    using Result=fxfile::searchpresets::MutationResult;
    if(result==Result::Duplicate){
        StatusText().Text(L"같은 이름의 검색 조건 세트가 이미 있습니다.");
        return;
    }
    if(result==Result::Full){
        StatusText().Text(L"검색 조건 세트는 최대 20개까지 저장할 수 있습니다.");
        return;
    }
    if(result!=Result::Applied){
        StatusText().Text(L"검색 조건 세트 이름과 입력 길이를 확인하세요.");
        return;
    }
    if(!mSearchPresets.save()){
        mSearchPresets=std::move(backup);
        StatusText().Text(L"검색 조건 세트를 안전하게 저장하지 못했습니다.");
        return;
    }
    const int next=selected>=0?selected:
        static_cast<int>(mSearchPresets.items().size()-1);
    RefreshSearchPresetManager(next);
    StatusText().Text(L"검색 조건 세트를 저장했습니다.");
}

void MainWindow::OnApplySearchPreset(
    IInspectable const&,RoutedEventArgs const&)
{
    const int selected=SearchPresetBox().SelectedIndex();
    if(selected<0||
       static_cast<std::size_t>(selected)>=mSearchPresets.items().size()){
        StatusText().Text(L"적용할 검색 조건 세트를 선택하세요.");
        return;
    }
    ApplySearchPresetToUi(
        mSearchPresets.items()[static_cast<std::size_t>(selected)]);
    StatusText().Text(L"검색 조건 세트를 적용했습니다. 검색 위치는 변경하지 않았습니다.");
}

void MainWindow::OnDeleteSearchPreset(
    IInspectable const&,RoutedEventArgs const&)
{
    const int selected=SearchPresetBox().SelectedIndex();
    if(selected<0){
        StatusText().Text(L"삭제할 검색 조건 세트를 선택하세요.");
        return;
    }
    auto backup=mSearchPresets;
    if(!mSearchPresets.erase(static_cast<std::size_t>(selected))){
        StatusText().Text(L"선택한 검색 조건 세트를 찾지 못했습니다.");
        return;
    }
    if(!mSearchPresets.save()){
        mSearchPresets=std::move(backup);
        StatusText().Text(L"검색 조건 세트 삭제를 저장하지 못했습니다.");
        return;
    }
    RefreshSearchPresetManager(selected);
    StatusText().Text(L"검색 조건 세트를 삭제했습니다.");
}

} // namespace winrt::FlyExplorer::implementation
