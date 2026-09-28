#include "pch.h"
#include "App.xaml.h"
#include <winrt/Microsoft.UI.Xaml.Hosting.h>
#include <winrt/Microsoft.UI.Content.h>
#include <winrt/Microsoft.UI.Interop.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <winrt/Windows.Graphics.h>
#include <MddBootstrap.h>
#include <WindowsAppSDK-VersionInfo.h>
#include <Microsoft.UI.Dispatching.Interop.h>
#include <roapi.h>
#pragma comment(lib, "Microsoft.WindowsAppRuntime.Bootstrap.lib")
#include "../../src/fxfile/resource.h"
#include <string>
#include <cstring>
#include <cwchar>
using namespace winrt;
namespace ui=winrt::Microsoft::UI::Xaml;
namespace ctl=winrt::Microsoft::UI::Xaml::Controls;

static void Trace(char const* message) {
    wchar_t path[1024]{};
    if (!GetEnvironmentVariableW(L"FLYEXP_MFC_DLL_TRACE",path,_countof(path))) return;
    HANDLE f=CreateFileW(path,FILE_APPEND_DATA,FILE_SHARE_READ,nullptr,
                         OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if (f==INVALID_HANDLE_VALUE) return;
    DWORD size{};
    WriteFile(f,message,static_cast<DWORD>(strlen(message)),&size,nullptr);
    WriteFile(f,"\r\n",2,&size,nullptr);
    CloseHandle(f);
}

// An island host has an existing native message pump. Initialize the runtime
// and dispatcher first; creating DesktopWindowXamlSource before UIElement
// implicitly initializes the XAML framework on this same thread.
static winrt::Microsoft::UI::Dispatching::DispatcherQueueController s_queue{nullptr};
static ui::Application s_diagnosticApp{nullptr};
static bool s_bootstrapped=false;
static HRESULT s_roInitialize=E_FAIL;

static bool InitializeRuntime() {
    if (s_queue) return true;
    try {
        APTTYPE apt{}; APTTYPEQUALIFIER qualifier{};
        HRESULT aptHr=::CoGetApartmentType(&apt,&qualifier);
        auto aptEvidence=std::string("dll-runtime-apartment hr=")+
            std::to_string(static_cast<long long>(aptHr))+
            " type="+std::to_string(static_cast<int>(apt));
        Trace(aptEvidence.c_str());
        s_roInitialize=::RoInitialize(RO_INIT_SINGLETHREADED);
        Trace((std::string("dll-runtime-roinitialize hr=")+
              std::to_string(static_cast<long long>(s_roInitialize))).c_str());
        if (FAILED(s_roInitialize)) return false;
        PACKAGE_VERSION minimum{};
        minimum.Version=WINDOWSAPPSDK_RUNTIME_VERSION_UINT64;
        HRESULT bootstrap=MddBootstrapInitialize2(WINDOWSAPPSDK_RELEASE_MAJORMINOR,
            WINDOWSAPPSDK_RELEASE_VERSION_TAG_W,minimum,
            MddBootstrapInitializeOptions_None);
        if (FAILED(bootstrap)) return false;
        s_bootstrapped=true;
        Trace("dll-runtime-after-bootstrap");
        s_queue=winrt::Microsoft::UI::Dispatching::DispatcherQueueController::CreateOnCurrentThread();
        Trace("dll-runtime-after-dispatcher");
        wchar_t diagnosticMode[16]{};
        ::GetEnvironmentVariableW(L"FLYEXP_PHASE5_DIAG_TEXTBOX",
            diagnosticMode, _countof(diagnosticMode));
        if (::wcscmp(diagnosticMode,L"app")==0) {
            Trace("dll-diagnostic-generated-app-enter");
            s_diagnosticApp=winrt::make<winrt::FlyExplorerIslandBridge::implementation::App>();
            Trace("dll-diagnostic-generated-app-complete");
        }
        Trace("dll-runtime-source-first");
        return true;
    } catch (winrt::hresult_error const& error) {
        auto reason=std::string("dll-runtime-failed-HRESULT=")+
            std::to_string(error.code().value)+" message="+winrt::to_string(error.message());
        Trace(reason.c_str());
        return false;
    }
}

class NavIsland final {
    HWND m_parent{};
    ui::Hosting::DesktopWindowXamlSource m_source{nullptr};
    ctl::Button m_up{nullptr}, m_back{nullptr}, m_forward{nullptr};
    // The experimental read-only TextBox caused a runtime fault during XAML
    // loading here; a display-only label is sufficient for this scoped PoC.
    ctl::TextBlock m_title{nullptr};
    ctl::TextBlock m_status{nullptr};
    // Test-only: unchanged normal-path control tree unless explicitly enabled.
    ctl::TextBox m_textBoxProbe{nullptr};
public:
    explicit NavIsland(HWND parent):m_parent(parent){}
    bool Create() {
        try {
            if (!s_queue) {
                Trace("dll-create-before-runtime-initialize");
                return false;
            }
            Trace("dll-creating-source");
            m_source=ui::Hosting::DesktopWindowXamlSource();
            m_source.Initialize(winrt::Microsoft::UI::GetWindowIdFromWindow(m_parent));
            Trace("dll-source-attached");
            ctl::StackPanel root;
            root.Padding(ui::ThicknessHelper::FromUniformLength(10));
            root.Spacing(7);
            // Explicit opt-in diagnostic. The current normal product path is
            // unchanged. Compare default resources to a per-island dictionary.
            wchar_t probeMode[16]{};
            ::GetEnvironmentVariableW(L"FLYEXP_PHASE5_DIAG_TEXTBOX",
                probeMode, _countof(probeMode));
            bool const plainProbe = ::wcscmp(probeMode, L"plain") == 0;
            bool const resourceProbe = ::wcscmp(probeMode, L"resources") == 0;
            bool const appProbe = ::wcscmp(probeMode, L"app") == 0;
            if (resourceProbe) {
                Trace("dll-textbox-resource-merge-enter");
                root.Resources().MergedDictionaries().Append(
                    ctl::XamlControlsResources());
                Trace("dll-textbox-resource-merge-complete");
            }
            root.Loaded([](auto const&,auto const&){Trace("dll-root-loaded");});
            root.SizeChanged([](auto const&,ui::SizeChangedEventArgs const& e){
                auto s=e.NewSize();
                auto evidence=std::string("dll-root-size=")+std::to_string(s.Width)+
                              "x"+std::to_string(s.Height);
                Trace(evidence.c_str());
            });
            ctl::StackPanel row;
            row.Orientation(ctl::Orientation::Horizontal);
            row.Spacing(7);
            m_up=ctl::Button();
            m_up.Content(winrt::box_value(L"Up"));
            m_up.Width(72); m_up.Height(36);
            ui::Automation::AutomationProperties::SetAutomationId(m_up,L"Phase5IslandUpButton");
            m_back=ctl::Button();
            m_back.Content(winrt::box_value(L"Back"));
            m_back.Width(72); m_back.Height(36);
            ui::Automation::AutomationProperties::SetAutomationId(m_back,L"Phase5IslandBackButton");
            m_forward=ctl::Button();
            m_forward.Content(winrt::box_value(L"Forward"));
            m_forward.Width(72); m_forward.Height(36);
            ui::Automation::AutomationProperties::SetAutomationId(m_forward,L"Phase5IslandForwardButton");
            m_title=ctl::TextBlock();
            m_title.MinWidth(340);
            ui::Automation::AutomationProperties::SetAutomationId(m_title,L"Phase5IslandCurrentFolderText");
            m_status=ctl::TextBlock();
            ui::Automation::AutomationProperties::SetAutomationId(m_status,L"Phase5IslandStatusText");
            m_up.Click([this](auto const&,auto const&){Send(ID_GO_UP);});
            m_back.Click([this](auto const&,auto const&){Send(ID_GO_BACK);});
            m_forward.Click([this](auto const&,auto const&){Send(ID_GO_FORWARD);});
            m_up.GotFocus([](auto const&,auto const&){Trace("dll-focus-up");});
            m_back.GotFocus([](auto const&,auto const&){Trace("dll-focus-back");});
            m_forward.GotFocus([](auto const&,auto const&){Trace("dll-focus-forward");});
            row.Children().Append(m_back);
            row.Children().Append(m_forward);
            row.Children().Append(m_up);
            row.Children().Append(m_title);
            root.Children().Append(row);
            if (plainProbe || resourceProbe || appProbe) {
                Trace("dll-textbox-create-enter");
                m_textBoxProbe = ctl::TextBox();
                Trace("dll-textbox-create-complete");
                m_textBoxProbe.IsReadOnly(true);
                m_textBoxProbe.Text(L"Isolated WinUI 3 TextBox probe");
                ui::Automation::AutomationProperties::SetAutomationId(
                    m_textBoxProbe, L"Phase5IslandDiagnosticTextBox");
                m_textBoxProbe.Loaded([](auto const&, auto const&) {
                    Trace("dll-textbox-loaded");
                });
                root.Children().Append(m_textBoxProbe);
                Trace("dll-textbox-appended");
            }
            root.Children().Append(m_status);
            m_source.Content(root);
            Trace("dll-island-content-set");
            Refresh(L"Test-only same-process product adapter ready");
            Trace("dll-island-ready");
            return true;
        } catch (winrt::hresult_error const& error) {
            auto reason=std::string("dll-initialize-failed-HRESULT=")+std::to_string(error.code().value)+" message="+winrt::to_string(error.message());
            Trace(reason.c_str());
            ::OutputDebugStringW(error.message().c_str());
            Close();
            return false;
        }
    }
    void Refresh(wchar_t const* message) {
        if (!m_title) return;
        wchar_t title[1024]{};
        ::GetWindowTextW(m_parent,title,_countof(title));
        m_title.Text(title);
        m_status.Text(message);
    }
    void Send(UINT id) {
        if (id!=ID_GO_UP && id!=ID_GO_BACK && id!=ID_GO_FORWARD) return;
        DWORD pid{};
        ::GetWindowThreadProcessId(m_parent,&pid);
        if (pid!=::GetCurrentProcessId()) return;
        LRESULT result=::SendMessageW(m_parent,WM_COMMAND,MAKEWPARAM(id,0),0);
        auto evidence=std::string("dll-command=")+std::to_string(id)+
                      " result="+std::to_string(static_cast<long long>(result));
        Trace(evidence.c_str());
        Refresh(result?L"Actual product command handled":L"Product command unavailable");
    }
    void Resize(int x,int y,int width,int height) {
        if (m_source && width>0 && height>0) {
            Trace("dll-resize-positive");
            auto bridge=m_source.SiteBridge();
            bridge.MoveAndResize(winrt::Windows::Graphics::RectInt32{
                x,y,width,height});
            HWND island=winrt::Microsoft::UI::GetWindowFromWindowId(bridge.WindowId());
            if (island && ::IsChild(m_parent,island)) {
                LONG_PTR style=::GetWindowLongPtrW(island,GWL_STYLE);
                ::SetWindowLongPtrW(island,GWL_STYLE,
                    style|WS_CHILD|WS_VISIBLE|WS_TABSTOP);
                ::SetWindowPos(island,HWND_TOP,0,0,0,0,
                               SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|
                               SWP_SHOWWINDOW|SWP_FRAMECHANGED);
                auto evidence=std::string("dll-island-hwnd=")+
                    std::to_string(reinterpret_cast<uintptr_t>(island))+
                    " visible="+std::to_string(::IsWindowVisible(island));
                Trace(evidence.c_str());
            } else Trace("dll-island-hwnd-unavailable");
        } else Trace("dll-resize-unavailable");
    }
    void Close() {
        Trace("dll-close-enter");
        // The runtime objects outlive every island and are shut down only
        // after the host MFC message loop exits.
        if (m_source) {
            m_source.Content(nullptr);
            Trace("dll-close-after-content-detach");
        }
        m_textBoxProbe=nullptr;
        m_status=nullptr; m_title=nullptr;
        m_up=nullptr;m_back=nullptr;m_forward=nullptr;
        Trace("dll-close-after-control-release");
        if (m_source) {m_source.Close();m_source=nullptr;}
        Trace("dll-close-after-source-close");
        Trace("dll-close-complete");
    }
};
static NavIsland* s_island=nullptr;

extern "C" __declspec(dllexport) BOOL WINAPI FlyIslandInitialize() {
    return InitializeRuntime() ? TRUE : FALSE;
}
extern "C" __declspec(dllexport) BOOL WINAPI FlyIslandCreate(HWND hwnd) {
    if (s_island || !::IsWindow(hwnd)) return FALSE;
    DWORD pid{};
    DWORD thread=::GetWindowThreadProcessId(hwnd,&pid);
    if (pid!=::GetCurrentProcessId() || thread!=::GetCurrentThreadId()) return FALSE;
    NavIsland* candidate=new NavIsland(hwnd);
    if (!candidate->Create()) {delete candidate;return FALSE;}
    s_island=candidate;
    return TRUE;
}
extern "C" __declspec(dllexport) void WINAPI FlyIslandResize(
    int x,int y,int width,int height) {
    if (s_island) s_island->Resize(x,y,width,height);
}
extern "C" __declspec(dllexport) BOOL WINAPI FlyIslandPreTranslate(MSG const* message) {
    if (!s_island || !message) return FALSE;
    // Resolve only after the Windows App SDK bootstrap has initialized the
    // framework graph. A static call would make this bridge DLL depend on
    // Microsoft.UI.Windowing.Core.dll before its own bootstrap can run.
    typedef BOOL (__stdcall *PreTranslateFn)(MSG const*);
    HMODULE module=::GetModuleHandleW(L"Microsoft.UI.Windowing.Core.dll");
    if (!module) return FALSE;
    auto fn=reinterpret_cast<PreTranslateFn>(
        ::GetProcAddress(module,"ContentPreTranslateMessage"));
    return fn ? fn(message) : FALSE;
}
extern "C" __declspec(dllexport) void WINAPI FlyIslandDestroy() {
    NavIsland* was=s_island;
    s_island=nullptr;
    if (was) {was->Close();delete was;}
}
extern "C" __declspec(dllexport) void WINAPI FlyIslandShutdown() {
    if (s_island) return;
    Trace("dll-runtime-shutdown-enter");
    // The generated App exists only in the explicitly enabled diagnostic mode.
    if (s_diagnosticApp) {
        Trace("dll-diagnostic-app-exit-enter");
        s_diagnosticApp.Exit();
        s_diagnosticApp=nullptr;
        Trace("dll-diagnostic-app-exit-complete");
    }
    if (s_queue) {s_queue.ShutdownQueue();s_queue=nullptr;}
    if (s_bootstrapped) {MddBootstrapShutdown();s_bootstrapped=false;}
    if (SUCCEEDED(s_roInitialize)) {::RoUninitialize();s_roInitialize=E_FAIL;}
    Trace("dll-runtime-shutdown-complete");
}
