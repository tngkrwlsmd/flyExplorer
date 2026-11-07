#include "pch.h"
#include "MainWindow.xaml.h"
#include "../../src/base/name_edit_guard.h"
#include <thread>
#include <string>
using namespace winrt;
using namespace Microsoft::UI::Xaml;
using namespace Microsoft::UI::Xaml::Controls;
namespace winrt::FlyExplorer::implementation {
namespace {
hstring koreanError(DWORD code){
 switch(code){
 case ERROR_ALREADY_EXISTS:
 case ERROR_FILE_EXISTS:return L"같은 이름의 파일 또는 폴더가 이미 존재합니다. 덮어쓰지 않았습니다.";
 case ERROR_ACCESS_DENIED:return L"이 위치를 변경할 권한이 없습니다.";
 case ERROR_NOT_SUPPORTED:return L"이 작업은 지원되는 로컬 일반 폴더와 파일에서만 사용할 수 있습니다.";
 case ERROR_INVALID_NAME:
 case ERROR_INVALID_PARAMETER:return L"이름 또는 폴더 경로가 올바르지 않습니다.";
 case ERROR_FILE_NOT_FOUND:
 case ERROR_PATH_NOT_FOUND:return L"원본 파일 또는 폴더를 찾을 수 없습니다.";
 default:return hstring(L"파일 작업에 실패했습니다. Windows 오류: "+
                          std::to_wstring(code));
 }
}
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
std::optional<std::wstring> readOwnedR07Environment(wchar_t const* name){
    const DWORD length=::GetEnvironmentVariableW(name,nullptr,0);
    if(length<2||length>32768)return std::nullopt;
    std::wstring value(length,L'\0');
    const DWORD written=::GetEnvironmentVariableW(
        name,value.data(),static_cast<DWORD>(value.size()));
    if(!written||written>=value.size())return std::nullopt;
    value.resize(written);
    return value;
}
std::optional<std::wstring> fullOwnedR07Path(std::wstring const& value){
    if(value.empty())return std::nullopt;
    const DWORD length=::GetFullPathNameW(value.c_str(),0,nullptr,nullptr);
    if(length<2||length>32768)return std::nullopt;
    std::wstring full(length,L'\0');
    const DWORD written=::GetFullPathNameW(
        value.c_str(),static_cast<DWORD>(full.size()),full.data(),nullptr);
    if(!written||written>=full.size())return std::nullopt;
    full.resize(written);
    return std::filesystem::path(full).lexically_normal().wstring();
}
bool ownedR07PathUnderTemp(std::wstring const& value){
    wchar_t rawTemp[MAX_PATH+1]{};
    const DWORD count=::GetTempPathW(MAX_PATH+1,rawTemp);
    if(!count||count>MAX_PATH)return false;
    auto path=fullOwnedR07Path(value);
    auto temp=fullOwnedR07Path(rawTemp);
    if(!path||!temp)return false;
    std::wstring prefix=*temp;
    if(!prefix.empty()&&prefix.back()!=L'\\')prefix.push_back(L'\\');
    if(path->size()<=prefix.size())return false;
    return ::CompareStringOrdinal(
        path->data(),static_cast<int>(prefix.size()),
        prefix.data(),static_cast<int>(prefix.size()),TRUE)==CSTR_EQUAL;
}
bool ownedR07PathEqual(std::wstring const& left,std::wstring const& right){
    return ::CompareStringOrdinal(
        left.c_str(),static_cast<int>(left.size()),
        right.c_str(),static_cast<int>(right.size()),TRUE)==CSTR_EQUAL;
}
bool writeOwnedR07Trace(
 std::wstring const& path,char const* text,bool create){
    const DWORD disposition=create?CREATE_NEW:OPEN_EXISTING;
    struct OwnedHandle final {
        HANDLE value=INVALID_HANDLE_VALUE;
        ~OwnedHandle(){if(value!=INVALID_HANDLE_VALUE)::CloseHandle(value);}
    } file{::CreateFileW(
        path.c_str(),FILE_APPEND_DATA|FILE_READ_ATTRIBUTES,
        FILE_SHARE_READ|FILE_SHARE_WRITE,
        nullptr,disposition,FILE_ATTRIBUTE_NORMAL|FILE_FLAG_OPEN_REPARSE_POINT,
        nullptr)};
    if(file.value==INVALID_HANDLE_VALUE)return false;
    FILE_ATTRIBUTE_TAG_INFO attributes{};
    if(!::GetFileInformationByHandleEx(
           file.value,FileAttributeTagInfo,&attributes,sizeof(attributes))||
       (attributes.FileAttributes&
        (FILE_ATTRIBUTE_DIRECTORY|FILE_ATTRIBUTE_REPARSE_POINT))!=0)
        return false;
    const DWORD length=static_cast<DWORD>(std::strlen(text));
    DWORD written=0;
    return ::WriteFile(file.value,text,length,&written,nullptr)&&written==length&&
           ::FlushFileBuffers(file.value);
}
#endif
}
fxfile::previewops::FileOperationController::Post MainWindow::FileOperationUiPost(){
    // The queue is obtained on the UI thread. TryEnqueue may be called by
    // a worker, but the weak window MUST only be resolved by the UI queue.
    auto dispatch=DispatcherQueue();
    auto weak=get_weak();
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
    std::wstring deliveryTrace;
    if(auto candidate=readOwnedR07Environment(
           L"FLYEXPLORER_R07_OWNED_DELIVERY_TRACE");
       candidate&&ownedR07PathUnderTemp(*candidate)&&
       ::GetFileAttributesW(candidate->c_str())==INVALID_FILE_ATTRIBUTES&&
       ::GetLastError()==ERROR_FILE_NOT_FOUND)
        deliveryTrace=*candidate;
    return [dispatch,weak,deliveryTrace=std::move(deliveryTrace)](
            FileOperationController::UiTask task) mutable {
        if(!deliveryTrace.empty())
            writeOwnedR07Trace(deliveryTrace,"POST_CALLED\n",true);
        if(!dispatch||!task){
            if(!deliveryTrace.empty())
                writeOwnedR07Trace(deliveryTrace,"POST_REJECTED\n",false);
            return false;
        }
        try{
            const bool queued=dispatch.TryEnqueue(
                [weak,task=std::move(task),deliveryTrace]() mutable {
                    if(!deliveryTrace.empty())
                        writeOwnedR07Trace(
                            deliveryTrace,"UI_TASK_ENTERED\n",false);
                    // The window may have been closed after TryEnqueue
                    // succeeded. Suppress all post-close UI callbacks.
                    if(auto ui=weak.get()){
                        if(!ui->mClosing){
                            if(!deliveryTrace.empty())
                                writeOwnedR07Trace(
                                    deliveryTrace,"UI_TASK_DISPATCH\n",false);
                            task();
                        }
                    }
                });
            if(!deliveryTrace.empty())
                writeOwnedR07Trace(
                    deliveryTrace,queued?"POST_ACCEPTED\n":"POST_REJECTED\n",
                    false);
            return queued;
        }catch(...){
            if(!deliveryTrace.empty())
                writeOwnedR07Trace(deliveryTrace,"POST_EXCEPTION\n",false);
            return false;
        }
    };
#else
    return [dispatch,weak](FileOperationController::UiTask task) mutable {
        if(!dispatch||!task)return false;
        try{
            return dispatch.TryEnqueue(
                [weak,task=std::move(task)]() mutable {
                    // The window may have been closed after TryEnqueue
                    // succeeded. Suppress all post-close UI callbacks.
                    if(auto ui=weak.get()){
                        if(!ui->mClosing)task();
                    }
                });
        }catch(...){return false;}
    };
#endif
}
fxfile::previewops::FileOperationController::RestoreCallback MainWindow::FileOperationRestoreCallback(){
    auto weak=get_weak();
    return [weak](FileOperationController::RestoreCompletion completion){
        if(auto ui=weak.get())ui->OnRenameRestoreCompleted(std::move(completion));
    };
}
fxfile::previewops::FileOperationController::StartStatus
MainWindow::StartPendingRenameRestoreForCurrentOwner(
 FileOperationController::Context liveContext){
    // Refuse before consuming the candidate if the visible owner already
    // changed. The controller repeats its own ticket/context checks.
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
    // Test-only stages: reject before moving/consuming an unverified claim.
    auto traceStartReject=[this](char const* stage){
        if(mOwnedR07RestoreRuntimeActive&&
           !mOwnedR07RestoreTracePath.empty()&&
           ownedR07PathUnderTemp(mOwnedR07RestoreTracePath))
            writeOwnedR07Trace(mOwnedR07RestoreTracePath,stage,false);
    };
#endif
    if(!RestoreCompletionContextCurrent(liveContext)){
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
        traceStartReject("START_CONTEXT_NOT_CURRENT\n");
        // Diagnostic-only: classify the existing fail-closed owner check.
        // Never change liveContext, relax a condition, or consume a candidate.
        char const* reason="START_CONTEXT_UNCLASSIFIED\n";
        if(mClosing)reason="START_CONTEXT_CLOSING\n";
        else if(liveContext.side<0||liveContext.side>1||!liveContext.route)
            reason="START_CONTEXT_INVALID_ORIGIN\n";
        else {
            bool found=false;
            for(std::size_t i=0;i<mWorkspace.count();++i){
                auto const& state=mWorkspace.state(i);
                if(state.identity!=liveContext.windowTabIdentity)continue;
                found=true;
                if(state.model.activePane!=liveContext.side)
                    reason="START_CONTEXT_INACTIVE_PANE\n";
                else {
                    auto const& pane=state.model.panes[
                        static_cast<std::size_t>(liveContext.side)];
                    if(pane.active!=liveContext.tab)
                        reason="START_CONTEXT_OTHER_TAB\n";
                    else if(liveContext.tab>=pane.tabs.size())
                        reason="START_CONTEXT_MISSING_TAB\n";
                    else if(liveContext.tab>=pane.pending.size())
                        reason="START_CONTEXT_MISSING_PENDING\n";
                    else if(pane.pending[liveContext.tab])
                        reason="START_CONTEXT_NAV_PENDING\n";
                    else if(liveContext.tab>=pane.routeIds.size())
                        reason="START_CONTEXT_MISSING_ROUTE\n";
                    else if(pane.routeIds[liveContext.tab]!=liveContext.route)
                        reason="START_CONTEXT_ROUTE_CHANGED\n";
                    else if(liveContext.tab>=pane.filesystemPaths.size())
                        reason="START_CONTEXT_MISSING_PATH\n";
                    else if(pane.filesystemPaths[liveContext.tab]!=liveContext.visibleFolder)
                        reason="START_CONTEXT_FOLDER_CHANGED\n";
                    else if(pane.tabs[liveContext.tab].snapshot().parsingName!=
                            liveContext.visibleShellFolder)
                        reason="START_CONTEXT_SHELL_CHANGED\n";
                }
                break;
            }
            if(!found)reason="START_CONTEXT_WINDOW_TAB_MISSING\n";
        }
        traceStartReject(reason);
#endif
        return FileOperationController::StartStatus::StaleConfirmation;
    }
    auto post=FileOperationUiPost();
    auto completion=FileOperationRestoreCallback();
    auto taken=mFileOperations.takeRenameRestoreCandidate(liveContext);
    if(!taken){
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
        traceStartReject("START_CANDIDATE_UNAVAILABLE\n");
#endif
        return FileOperationController::StartStatus::StaleConfirmation;
    }
    const auto status=mFileOperations.startTakenRenameRestoreAsync(
        std::move(*taken),std::move(liveContext),
        std::move(post),std::move(completion));
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
    if(status!=FileOperationController::StartStatus::Started){
        traceStartReject(status==FileOperationController::StartStatus::Busy?
            "START_ASYNC_BUSY\n":
            status==FileOperationController::StartStatus::StaleConfirmation?
            "START_ASYNC_STALE\n":"START_ASYNC_THREAD_FAILURE\n");
    }
#endif
    return status;
}
bool MainWindow::RestoreCompletionContextCurrent(
 FileOperationController::Context const& origin) const{
    // WindowWorkspaceController deliberately gives the first live WindowTab
    // identity 0. Only the route must be nonzero; the exact window identity
    // (including 0) is still matched against a live workspace state below.
    if(mClosing||origin.side<0||origin.side>1||!origin.route)return false;
    for(std::size_t i=0;i<mWorkspace.count();++i){
        auto const& state=mWorkspace.state(i);
        if(state.identity!=origin.windowTabIdentity)continue;
        // A completion from an inactive pane must not update its old tab.
        if(state.model.activePane!=origin.side)return false;
        auto const& pane=state.model.panes[static_cast<std::size_t>(origin.side)];
        if(pane.active!=origin.tab||origin.tab>=pane.tabs.size()||
           origin.tab>=pane.pending.size()||pane.pending[origin.tab]||
           origin.tab>=pane.routeIds.size()||
           pane.routeIds[origin.tab]!=origin.route||
           origin.tab>=pane.filesystemPaths.size()||
           pane.filesystemPaths[origin.tab]!=origin.visibleFolder)return false;
        return pane.tabs[origin.tab].snapshot().parsingName==
               origin.visibleShellFolder;
    }
    return false;
}
void MainWindow::OnRenameRestoreCompleted(
 FileOperationController::RestoreCompletion completion){
    if(!RestoreCompletionContextCurrent(completion.context))return;
    using Outcome=FileOperationController::RestoreOutcomeClass;
    std::wstring notice;
    if(completion.outcome==Outcome::VerifiedCommitted){
        notice=L"이름 변경을 안전하게 되돌렸습니다.";
    }else if(completion.outcome==Outcome::UncertainAfterAttempt){
        notice=L"되돌리기 결과를 확인할 수 없습니다. 원본 폴더에서 파일을 확인하세요.";
    }else{
        notice=L"이름 변경을 되돌리지 않았습니다.";
    }
    for(std::size_t i=0;i<mWorkspace.count();++i){
        auto& state=mWorkspace.state(i);
        if(state.identity==completion.context.windowTabIdentity){
            state.fileOperationNotice=notice;
            break;
        }
    }
    if(ActiveWindowTab().identity==completion.context.windowTabIdentity)
        StatusText().Text(hstring(notice));
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
    if(mOwnedR07RestoreRuntimeActive){
        auto trace=std::move(mOwnedR07RestoreTracePath);
        mOwnedR07RestoreTracePath.clear();
        mOwnedR07RestoreRuntimeActive=false;
        const char* outcome=completion.outcome==Outcome::VerifiedCommitted?
            "COMPLETE_VERIFIED\n":
            completion.outcome==Outcome::UncertainAfterAttempt?
            "COMPLETE_UNCERTAIN\n":"COMPLETE_NOT_ATTEMPTED\n";
        if(!trace.empty())writeOwnedR07Trace(trace,outcome,false);
        SetFileButtonsBusy(false,false);
        const int side=completion.context.side;
        auto const& pane=ActiveWindowTab().model.panes[side];
        QueuePidl(side,
          fxfile::shellnav::Location(
              pane.tabs[pane.active].snapshot().folder),
          fxfile::shellnav::NavigationAction::Refresh);
    }
#endif
}
void MainWindow::OnCreateFolder(
 IInspectable const&,RoutedEventArgs const&){
 BeginFileNameCommand(fxfile::filecommand::Kind::CreateFolder);
}
void MainWindow::OnRenameSelected(
 IInspectable const&,RoutedEventArgs const&){
 BeginFileNameCommand(fxfile::filecommand::Kind::RenameSelected);
}
void MainWindow::BeginFileNameCommand(fxfile::filecommand::Kind kind){
 if(mFileOperations.busy()||mFileOperations.pendingConfirmationToken()){
  StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
  return;
 }
 if(kind!=fxfile::filecommand::Kind::CreateFolder&&
    kind!=fxfile::filecommand::Kind::CreateTextFile&&
    kind!=fxfile::filecommand::Kind::CreateMarkdownFile&&
    kind!=fxfile::filecommand::Kind::CreateShortcut&&
    kind!=fxfile::filecommand::Kind::RenameSelected)return;
 // The toolbar is shared by all workspaces. Every new edit supersedes
 // the previous edit anchor, even when validation rejects this request.
 mPendingNameEdit.reset();
 const int editSide=ActiveWindowTab().model.activePane;
 if(editSide<0||editSide>1)return;
 auto const& editPane=ActiveWindowTab().model.panes[editSide];
 if(editPane.active>=editPane.tabs.size()||
    editPane.active>=editPane.pending.size()||
    editPane.active>=editPane.filesystemPaths.size()||
    editPane.pending[editPane.active]||
    editPane.filesystemPaths[editPane.active].empty()){
  StatusText().Text(L"폴더를 완전히 불러온 후 이름 작업을 시작하세요.");
  return;
 }
 const auto editContext=FileOperationContext(editSide);
 if(editContext.side!=editSide||editContext.visibleFolder.empty()){
  StatusText().Text(L"폴더를 완전히 불러온 후 이름 작업을 시작하세요.");
  return;
 }
 std::wstring initial;
 std::wstring renameSource;
 bool renameFolder=false;
 if(kind==fxfile::filecommand::Kind::CreateTextFile)
  initial=L"새 텍스트 문서.txt";
 if(kind==fxfile::filecommand::Kind::CreateMarkdownFile)
  initial=L"새 Markdown 문서.md";
 if(kind==fxfile::filecommand::Kind::RenameSelected||
    kind==fxfile::filecommand::Kind::CreateShortcut){
  const int side=ActiveWindowTab().model.activePane;
  auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
  const size_t tab=pane.active;
  const auto view=side==0?LeftFiles():RightFiles();
  if(view.SelectedItems().Size()!=1){
   StatusText().Text(L"파일 또는 폴더 하나를 선택하세요.");
   return;
  }
  const auto picked=view.SelectedItem();
  const auto row=picked.try_as<ListViewItem>();
  if(!row||!row.Tag()){
   StatusText().Text(L"파일 또는 폴더를 선택하세요.");
   return;
  }
  const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
  auto const* indexed=pane.tabs[tab].indexedItem(
      static_cast<std::size_t>(logical));
  if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
   StatusText().Text(L"이 파일 작업은 일반 파일 또는 폴더만 지원합니다.");
   return;
  }
  renameFolder=indexed->isFolder();
  renameSource=indexed->parsingName;
  try{initial=std::filesystem::path(
          indexed->parsingName).filename().wstring();}
  catch(...){initial=indexed->label;}
  if(kind==fxfile::filecommand::Kind::CreateShortcut){
   // The selected original remains untouched: edit only the new .lnk name.
   if(!renameFolder){
    try{initial=std::filesystem::path(initial).stem().wstring();}
    catch(...){}
   }
   initial+=L" - 바로 가기.lnk";
   renameFolder=false;
  }
 }
 mPendingNameEdit=PendingNameEdit{kind,editContext,std::move(renameSource)};
 fileBar()->BeginNameEdit(
     kind==fxfile::filecommand::Kind::CreateFolder?0:
     kind==fxfile::filecommand::Kind::CreateShortcut?4:
     kind==fxfile::filecommand::Kind::CreateMarkdownFile?3:
     kind==fxfile::filecommand::Kind::CreateTextFile?2:1,
     hstring(initial),renameFolder);
 StatusText().Text(kind==fxfile::filecommand::Kind::CreateFolder?
  L"새 폴더 이름을 입력하고 Enter로 확정하거나 Esc로 취소하세요.":
  kind==fxfile::filecommand::Kind::CreateTextFile?
  L"새 텍스트 문서의 .txt 파일 이름을 입력하세요. Enter 확정, Esc 취소.":
  kind==fxfile::filecommand::Kind::CreateMarkdownFile?
  L"새 Markdown 문서의 .md 파일 이름을 입력하세요. Enter 확정, Esc 취소.":
  kind==fxfile::filecommand::Kind::CreateShortcut?
  L"선택 항목의 .lnk 바로 가기 이름을 입력하세요. Enter 확정, Esc 취소.":
  hstring(L"이름 변경 대상: "+initial+
      L" (Enter 확정, Esc 취소)"));
}
void MainWindow::ExecuteFileCommand(fxfile::filecommand::Kind kind){
 if(mFileOperations.busy()||mFileOperations.pendingConfirmationToken()){
     StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
     return;
 }
 // Enter must commit the edit that was opened, not an action for the
 // workspace, pane or selection which happens to be active now.
 if(!mPendingNameEdit||mPendingNameEdit->kind!=kind||
    FileNameBox().Opacity()<0.5){
     StatusText().Text(L"이름 편집을 다시 시작한 후 확정하세요.");
     return;
 }
 const int side=ActiveWindowTab().model.activePane;
 if(side<0||side>1)return;
 const auto liveContext=FileOperationContext(side);
 auto const& editContext=mPendingNameEdit->context;
 if(!fxfile::nameedit::sameScope(editContext,liveContext)){
     mPendingNameEdit.reset();
     fileBar()->EndNameEdit();
     StatusText().Text(L"편집하는 동안 작업공간 또는 폴더가 변경됐습니다. 다시 선택하세요.");
     return;
 }
 auto& pane=ActiveWindowTab().model.panes[static_cast<size_t>(side)];
 const size_t tab=pane.active;
 if(tab>=pane.pending.size()||tab>=pane.filesystemPaths.size()||
    pane.pending[tab]||pane.filesystemPaths[tab].empty()){
     StatusText().Text(L"파일 작업은 불러오기가 끝난 실제 폴더에서만 사용할 수 있습니다.");
     return;
 }
 fxfile::filecommand::Request request{};
 request.kind=kind;
 request.parent=pane.filesystemPaths[tab];
 request.name=std::wstring(FileNameBox().Text().c_str());
 if(request.name.empty()&&kind==fxfile::filecommand::Kind::CreateFolder)
     request.name=L"새 폴더";
 if(request.name.empty()&&kind==fxfile::filecommand::Kind::CreateTextFile)
     request.name=L"새 텍스트 문서.txt";
 if(request.name.empty()&&kind==fxfile::filecommand::Kind::CreateMarkdownFile)
     request.name=L"새 Markdown 문서.md";
 if(!fxfile::filecommand::validLeaf(request.name)){
     StatusText().Text(L"파일 이름만 입력하세요. 경로나 특수 문자는 사용할 수 없습니다.");
     return;
 }
 if(kind==fxfile::filecommand::Kind::CreateTextFile&&
    !fxfile::filecommand::validTextDocumentLeaf(request.name)){
     StatusText().Text(L"새 텍스트 문서는 .txt 확장자로만 만들 수 있습니다.");
     return;
 }
 if(kind==fxfile::filecommand::Kind::CreateMarkdownFile&&
    !fxfile::filecommand::validMarkdownDocumentLeaf(request.name)){
     StatusText().Text(L"새 Markdown 문서는 .md 확장자로만 만들 수 있습니다.");
     return;
 }
 if(kind==fxfile::filecommand::Kind::CreateShortcut&&
    !fxfile::filecommand::validShortcutLeaf(request.name)){
     StatusText().Text(L"바로 가기는 .lnk 확장자로만 만들 수 있습니다.");
     return;
 }
 if(kind==fxfile::filecommand::Kind::RenameSelected||
    kind==fxfile::filecommand::Kind::CreateShortcut){
     const auto view=side==0?LeftFiles():RightFiles();
     if(view.SelectedItems().Size()!=1){
         StatusText().Text(L"파일 또는 폴더 하나를 선택하세요.");
         return;
     }
     const auto picked=view.SelectedItem();
     const auto row=picked.try_as<ListViewItem>();
     if(!row||!row.Tag()){
         StatusText().Text(L"파일 또는 폴더를 선택하세요.");
         return;
     }
     const auto logical=winrt::unbox_value<std::uint64_t>(row.Tag());
     auto const* indexed=pane.tabs[tab].indexedItem(
         static_cast<std::size_t>(logical));
     if(!indexed||!indexed->isFileSystem()||indexed->parsingName.empty()){
         StatusText().Text(L"가상 Shell 항목은 이 파일 작업에서 변경할 수 없습니다.");
         return;
     }
     // Selection can change while the filename box holds keyboard focus.
     // Never rename an unrelated new selection using the old edit text.
     if(!fxfile::nameedit::sameRenameSource(
         mPendingNameEdit->source,indexed->parsingName)){
         mPendingNameEdit.reset();
         fileBar()->EndNameEdit();
         StatusText().Text(L"선택 대상이 바뀌었습니다. 다시 선택해 주세요.");
         return;
     }
     request.source=mPendingNameEdit->source;
 }
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
 // Independent worker trace for the exact test-owned F2 rename only.
 FileOperationController::FileCommandWorkerTrace workerTrace{};
 if(kind==fxfile::filecommand::Kind::RenameSelected){
     auto expectedOriginal=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_ORIGINAL");
     auto expectedTarget=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_TARGET");
     auto candidate=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_WORKER_TRACE");
     if(expectedOriginal&&expectedTarget&&candidate&&
        ownedR07PathUnderTemp(*expectedOriginal)&&
        ownedR07PathUnderTemp(*expectedTarget)&&
        ownedR07PathUnderTemp(*candidate)&&
        ownedR07PathEqual(*expectedOriginal,request.source)&&
        ownedR07PathEqual(*expectedTarget,
            (std::filesystem::path(request.parent)/request.name).wstring())&&
        ::GetFileAttributesW(candidate->c_str())==INVALID_FILE_ATTRIBUTES&&
        ::GetLastError()==ERROR_FILE_NOT_FOUND){
         workerTrace=[path=*candidate](char const* stage){
             writeOwnedR07Trace(path,stage,
                 std::strcmp(stage,"WORKER_POST_PENDING\n")==0);
         };
     }
 }
#endif
 auto post=FileOperationUiPost();
 auto weak=get_weak();
 const auto status=mFileOperations.startFileCommand(
     std::move(request),FileOperationContext(side),std::move(post),
     [weak](FileOperationController::FileCommandCompletion completion){
         if(auto ui=weak.get())ui->OnFileCommandCompleted(std::move(completion));
     }
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
     ,std::move(workerTrace)
#endif
     );
 if(status==FileOperationController::StartStatus::Started){
     // Do not reassert an earlier failure after this new command finishes.
     ActiveWindowTab().fileOperationNotice.clear();
     SetFileButtonsBusy(true,false);
     StatusText().Text(L"선택한 파일 작업을 별도 스레드에서 처리하는 중입니다...");
 }else if(status==FileOperationController::StartStatus::Busy){
     StatusText().Text(L"이전 파일 작업이 완료될 때까지 기다려 주세요.");
 }else if(status==FileOperationController::StartStatus::InvalidVisibleContext){
     StatusText().Text(L"파일 작업을 시작한 폴더가 변경됐습니다.");
 }else{
     SetFileButtonsBusy(false,false);
     StatusText().Text(L"파일 작업 스레드를 시작하지 못했습니다.");
 }
}
void MainWindow::OnFileCommandCompleted(
 FileOperationController::FileCommandCompletion completion){
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
 if(auto deliveryTrace=readOwnedR07Environment(
        L"FLYEXPLORER_R07_OWNED_DELIVERY_TRACE");
    deliveryTrace&&ownedR07PathUnderTemp(*deliveryTrace))
     writeOwnedR07Trace(
         *deliveryTrace,"ON_FILE_COMPLETION\n",false);
#endif
 using Disposition=FileOperationController::CommandDisposition;
 const auto disposition=mFileOperations.acceptFileCommand(
     completion,FileOperationContext(completion.context.side));
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
 // Record an early controller rejection only for the exact test-owned rename.
 // Normal builds contain none of this path and no user file is inspected.
 if(disposition!=Disposition::Succeeded){
     auto expectedOriginal=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_ORIGINAL");
     auto expectedTarget=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_TARGET");
     auto trace=readOwnedR07Environment(L"FLYEXPLORER_R07_OWNED_TRACE");
     if(expectedOriginal&&expectedTarget&&trace&&
        ownedR07PathUnderTemp(*expectedOriginal)&&
        ownedR07PathUnderTemp(*expectedTarget)&&
        ownedR07PathUnderTemp(*trace)&&
        ownedR07PathEqual(*expectedOriginal,completion.originalRenameSource)&&
        ownedR07PathEqual(*expectedTarget,completion.result.target)){
         const char* stage=disposition==Disposition::Ignored?
             "DISPOSITION_IGNORED\n":
             disposition==Disposition::StaleContext?
             "DISPOSITION_STALE\n":"DISPOSITION_FAILED\n";
         writeOwnedR07Trace(*trace,stage,true);
     }
 }
#endif
 if(disposition==Disposition::Ignored)return;
 const bool originActive=completion.context.windowTabIdentity==
                         ActiveWindowTab().identity;
 auto rememberOrigin=[&](std::wstring const& message){
     for(std::size_t i=0;i<mWorkspace.count();++i){
         auto& state=mWorkspace.state(i);
         if(state.identity==completion.context.windowTabIdentity){
             state.fileOperationNotice=message;
             return;
         }
     }
 };
 SetFileButtonsBusy(false,false);
 if(disposition==Disposition::StaleContext){
     // Switching WindowTab, PaneTab or folder must never update another
     // workspace's visible status. Keep the warning in its original tab.
     const std::wstring notice=completion.result.error==ERROR_SUCCESS?
         L"파일 작업이 완료됐지만 화면이 변경됐습니다. 원본 폴더에서 결과를 확인하세요.":
         L"파일 작업에 실패했고 화면이 변경됐습니다. "
         L"원본 폴더에서 결과를 확인하세요. Windows 오류: "+
         std::to_wstring(completion.result.error);
     rememberOrigin(notice);
     if(originActive)StatusText().Text(hstring(notice));
     return;
 }
 if(disposition==Disposition::Failed){
     const std::wstring notice=koreanError(completion.result.error).c_str();
     rememberOrigin(notice);
     if(originActive)StatusText().Text(hstring(notice));
     return;
 }
 // Reveal is only an outcome of an explicitly accepted success.
 if(disposition!=Disposition::Succeeded)return;
 fileBar()->EndNameEdit();
 mPendingNameEdit.reset();
#if defined(FLYEXPLORER_R07_OWNED_RUNTIME_TEST)
 {
     auto expectedOriginal=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_ORIGINAL");
     auto expectedTarget=readOwnedR07Environment(
         L"FLYEXPLORER_R07_OWNED_TARGET");
     auto trace=readOwnedR07Environment(L"FLYEXPLORER_R07_OWNED_TRACE");
     // A diagnostic trace is permitted only after all three paths have passed
     // the same process-local TEMP boundary as the actual restore entry.
     if(expectedOriginal&&expectedTarget&&trace&&
        ownedR07PathUnderTemp(*expectedOriginal)&&
        ownedR07PathUnderTemp(*expectedTarget)&&
        ownedR07PathUnderTemp(*trace)){
         const char* rejected=
             completion.kind!=fxfile::filecommand::Kind::RenameSelected?
                 "REJECT_KIND\n":
             completion.result.error!=ERROR_SUCCESS?"REJECT_ERROR\n":
             !completion.result.renameEvidence.verified?
                 "REJECT_RENAME_EVIDENCE\n":
             !ownedR07PathEqual(*expectedOriginal,completion.originalRenameSource)?
                 "REJECT_ORIGINAL_PATH\n":
             !ownedR07PathEqual(*expectedTarget,completion.result.target)?
                 "REJECT_TARGET_PATH\n":nullptr;
         if(rejected){
             writeOwnedR07Trace(*trace,rejected,true);
         }else if(writeOwnedR07Trace(*trace,"BEGIN\n",true)){
             mOwnedR07RestoreRuntimeActive=true;
             mOwnedR07RestoreTracePath=*trace;
             const auto restore=StartPendingRenameRestoreForCurrentOwner(
                 completion.context);
             if(restore==FileOperationController::StartStatus::Started){
                 writeOwnedR07Trace(*trace,"STARTED\n",false);
                 SetFileButtonsBusy(true,false);
                 StatusText().Text(L"테스트 소유 이름 복원 동작을 확인하는 중입니다...");
                 return;
             }
             writeOwnedR07Trace(*trace,"START_REJECTED\n",false);
             mOwnedR07RestoreRuntimeActive=false;
             mOwnedR07RestoreTracePath.clear();
         }
     }
 }
#endif
 const std::wstring message=
     completion.kind==fxfile::filecommand::Kind::CreateFolder?
     L"새 폴더를 만들었습니다.":
     completion.kind==fxfile::filecommand::Kind::CreateTextFile?
     L"새 텍스트 문서를 만들었습니다.":
     completion.kind==fxfile::filecommand::Kind::CreateMarkdownFile?
     L"새 Markdown 문서를 만들었습니다.":
     completion.kind==fxfile::filecommand::Kind::CreateShortcut?
     L"선택 항목의 바로 가기를 만들었습니다.":L"이름을 변경했습니다.";
 // A matching Shell Refresh can replace the footer text; retain the
 // accepted result in the exact originating workspace until navigation.
 rememberOrigin(message);
 if(originActive)StatusText().Text(hstring(message));
 const int side=completion.context.side;
 auto const& pane=ActiveWindowTab().model.panes[side];
 // The worker supplied the actual target path. Defer selection until
 // the matching Shell Refresh has produced a new list, never select by
 // a stale row index or an unverified user-entered name.
 if(originActive&&!completion.result.target.empty()&&
    pane.active==completion.context.tab&&
    pane.active<pane.routeIds.size()&&
    pane.routeIds[pane.active]==completion.context.route){
     auto& reveal=ActiveWindowTab().fileLists[side].fileCommandReveal;
     reveal.clear();
     reveal.target=completion.result.target;
     reveal.folder=completion.context.visibleShellFolder;
     reveal.route=completion.context.route;
     reveal.tab=completion.context.tab;
     reveal.afterRefresh=false;
 }
 QueuePidl(side,
   fxfile::shellnav::Location(
       pane.tabs[pane.active].snapshot().folder),
   fxfile::shellnav::NavigationAction::Refresh);
}

}
