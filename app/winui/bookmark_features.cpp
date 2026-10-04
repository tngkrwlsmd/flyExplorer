#include "pch.h"
#include "MainWindow.xaml.h"
#include <filesystem>
#include <winrt/Microsoft.UI.Xaml.Automation.h>

using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
using namespace Microsoft::UI::Xaml::Automation;

namespace winrt::FlyExplorer::implementation {
namespace {

std::wstring defaultBookmarkName(std::wstring const& path)
{
    try {
        const std::filesystem::path value(path);
        auto name = value.filename().native();
        if (!name.empty()) return name;
        name = value.root_name().native();
        if (!name.empty()) return name;
    } catch (...) {
    }
    return path;
}

} // namespace

void MainWindow::InitializeBookmarks()
{
    const bool loaded = mBookmarks.load();
    RefreshBookmarks();
    RefreshBookmarkManager(-1);
    if (!loaded)
        StatusText().Text(
            L"북마크 파일이 손상되어 기존 항목을 불러오지 않았습니다.");
}

void MainWindow::RefreshBookmarks()
{
    auto children = BookmarkButtonsPanel().Children();
    children.Clear();
    auto const& items = mBookmarks.items();
    if (items.empty()) {
        TextBlock empty;
        empty.Text(L"북마크 없음");
        empty.Opacity(0.58);
        empty.VerticalAlignment(VerticalAlignment::Center);
        children.Append(empty);
        return;
    }

    const auto weak = get_weak();
    for (auto const& item : items) {
        Button button;
        button.Height(28);
        button.MinWidth(36);
        button.MaxWidth(180);
        button.Padding(Thickness{8, 0, 8, 0});
        button.Content(box_value(hstring(item.name)));
        ToolTipService::SetToolTip(button, box_value(hstring(item.path)));
        AutomationProperties::SetName(
            button, hstring(L"북마크 " + item.name));
        const auto target = item.path;
        button.Click([weak, target](IInspectable const&,
                                   RoutedEventArgs const&) {
            if (auto ui = weak.get()) {
                if (!ui->OpenFolder(target))
                    ui->StatusText().Text(
                        L"북마크 위치를 열 수 없습니다.");
            }
        });
        children.Append(button);
    }
}

void MainWindow::RefreshBookmarkManager(int selected)
{
    struct Guard final {
        bool& value;
        explicit Guard(bool& target) : value(target) { value = true; }
        ~Guard() { value = false; }
    } guard(mPopulatingBookmarks);

    auto comboItems = BookmarkManagerBox().Items();
    comboItems.Clear();
    for (auto const& item : mBookmarks.items()) {
        ComboBoxItem row;
        row.Content(box_value(hstring(item.name)));
        ToolTipService::SetToolTip(row, box_value(hstring(item.path)));
        comboItems.Append(row);
    }

    if (mBookmarks.items().empty()) {
        BookmarkManagerBox().SelectedIndex(-1);
        BookmarkNameEdit().Text(L"");
        BookmarkSelectedPathText().Text(L"선택한 북마크가 없습니다.");
        return;
    }

    if (selected < 0 ||
        static_cast<std::size_t>(selected) >= mBookmarks.items().size())
        selected = 0;
    BookmarkManagerBox().SelectedIndex(selected);
    auto const& item = mBookmarks.items()[static_cast<std::size_t>(selected)];
    BookmarkNameEdit().Text(hstring(item.name));
    BookmarkSelectedPathText().Text(hstring(item.path));
}

void MainWindow::OnAddBookmark(
    IInspectable const&, RoutedEventArgs const&)
{
    auto const& model = ActiveWindowTab().model;
    auto const& pane = model.panes[
        static_cast<std::size_t>(model.activePane)];
    if (pane.active >= pane.filesystemPaths.size() ||
        pane.filesystemPaths[pane.active].empty()) {
        StatusText().Text(
            L"파일 시스템 폴더에서만 북마크를 추가할 수 있습니다.");
        return;
    }

    const auto path = pane.filesystemPaths[pane.active];
    auto backup = mBookmarks;
    const auto result = mBookmarks.add(defaultBookmarkName(path), path);
    using Result = fxfile::bookmarks::MutationResult;
    if (result == Result::Duplicate) {
        StatusText().Text(L"이미 등록된 북마크입니다.");
        return;
    }
    if (result == Result::Full) {
        StatusText().Text(L"북마크는 최대 100개까지 저장할 수 있습니다.");
        return;
    }
    if (result != Result::Applied) {
        StatusText().Text(L"현재 위치를 북마크로 저장할 수 없습니다.");
        return;
    }
    if (!mBookmarks.save()) {
        mBookmarks = std::move(backup);
        StatusText().Text(L"북마크 파일을 안전하게 저장하지 못했습니다.");
        return;
    }

    RefreshBookmarks();
    RefreshBookmarkManager(
        static_cast<int>(mBookmarks.items().size() - 1));
    StatusText().Text(L"현재 폴더를 북마크에 추가했습니다.");
}

void MainWindow::OnToggleBookmarks(
    IInspectable const&, RoutedEventArgs const&)
{
    const auto next = BookmarkPanel().Visibility() == Visibility::Collapsed
        ? Visibility::Visible : Visibility::Collapsed;
    WorkspacePanel().Visibility(Visibility::Collapsed);
    SearchPanel().Visibility(Visibility::Collapsed);
    FilterRulePanel().Visibility(Visibility::Collapsed);
    BookmarkPanel().Visibility(next);
    if (next == Visibility::Visible) {
        RefreshBookmarkManager(BookmarkManagerBox().SelectedIndex());
        StatusText().Text(
            L"북마크 이름을 바꾸거나 삭제하고 기존 북마크 파일을 가져올 수 있습니다.");
    }
}

void MainWindow::OnBookmarkSelectionChanged(
    IInspectable const&, SelectionChangedEventArgs const&)
{
    if (mPopulatingBookmarks) return;
    const int selected = BookmarkManagerBox().SelectedIndex();
    if (selected < 0 ||
        static_cast<std::size_t>(selected) >= mBookmarks.items().size()) {
        BookmarkNameEdit().Text(L"");
        BookmarkSelectedPathText().Text(L"선택한 북마크가 없습니다.");
        return;
    }
    auto const& item = mBookmarks.items()[static_cast<std::size_t>(selected)];
    BookmarkNameEdit().Text(hstring(item.name));
    BookmarkSelectedPathText().Text(hstring(item.path));
}

void MainWindow::OnRenameBookmark(
    IInspectable const&, RoutedEventArgs const&)
{
    const int selected = BookmarkManagerBox().SelectedIndex();
    if (selected < 0) {
        StatusText().Text(L"이름을 바꿀 북마크를 선택하세요.");
        return;
    }
    auto backup = mBookmarks;
    const auto result = mBookmarks.rename(
        static_cast<std::size_t>(selected),
        std::wstring(BookmarkNameEdit().Text().c_str()));
    using Result = fxfile::bookmarks::MutationResult;
    if (result != Result::Applied) {
        StatusText().Text(L"북마크 이름은 1~256자의 한 줄 텍스트여야 합니다.");
        return;
    }
    if (!mBookmarks.save()) {
        mBookmarks = std::move(backup);
        StatusText().Text(L"북마크 이름 변경을 저장하지 못했습니다.");
        return;
    }
    RefreshBookmarks();
    RefreshBookmarkManager(selected);
    StatusText().Text(L"북마크 이름을 변경했습니다.");
}

void MainWindow::OnDeleteBookmark(
    IInspectable const&, RoutedEventArgs const&)
{
    const int selected = BookmarkManagerBox().SelectedIndex();
    if (selected < 0) {
        StatusText().Text(L"삭제할 북마크를 선택하세요.");
        return;
    }
    auto backup = mBookmarks;
    if (!mBookmarks.erase(static_cast<std::size_t>(selected))) {
        StatusText().Text(L"선택한 북마크를 찾지 못했습니다.");
        return;
    }
    if (!mBookmarks.save()) {
        mBookmarks = std::move(backup);
        StatusText().Text(L"북마크 삭제를 저장하지 못했습니다.");
        return;
    }
    RefreshBookmarks();
    RefreshBookmarkManager(selected);
    StatusText().Text(L"북마크를 삭제했습니다.");
}

void MainWindow::OnImportBookmarks(
    IInspectable const&, RoutedEventArgs const&)
{
    const auto source = std::wstring(BookmarkImportPathBox().Text().c_str());
    if (source.empty()) {
        StatusText().Text(L"가져올 기존 북마크 파일의 전체 경로를 입력하세요.");
        return;
    }

    auto backup = mBookmarks;
    const auto imported = mBookmarks.importLegacy(source);
    if (!imported.loaded) {
        StatusText().Text(
            L"기존 북마크 파일을 읽지 못했거나 bookmark 섹션이 없습니다.");
        return;
    }
    if (imported.added && !mBookmarks.save()) {
        mBookmarks = std::move(backup);
        StatusText().Text(L"가져온 북마크를 안전하게 저장하지 못했습니다.");
        return;
    }

    RefreshBookmarks();
    RefreshBookmarkManager(-1);
    StatusText().Text(hstring(
        L"기존 북마크 " + std::to_wstring(imported.added) +
        L"개를 가져왔고 " + std::to_wstring(imported.skipped) +
        L"개를 건너뛰었습니다."));
}

} // namespace winrt::FlyExplorer::implementation
