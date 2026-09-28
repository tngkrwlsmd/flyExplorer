#include "pch.h"
#include "App.xaml.h"
#include <winrt/Microsoft.UI.Xaml.Hosting.h>
#include <winrt/Microsoft.UI.Content.h>
#include <winrt/Microsoft.UI.Interop.h>
#include <winrt/Microsoft.UI.Xaml.Automation.h>
#include <winrt/Windows.Graphics.h>
#include <MddBootstrap.h>
#include <WindowsAppSDK-VersionInfo.h>
#pragma comment(lib, "Microsoft.WindowsAppRuntime.Bootstrap.lib")
#include "../../src/fxfile/resource.h"
#include <string>
#include <cstring>
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
class NavIsland final {
    HWND m_parent{};
    winrt::Microsoft::UI::Dispatching::DispatcherQueueController m_queue{nullptr};
    ui::Application m_app{nullptr};
    ui::Hosting::DesktopWindowXamlSource m_source{nullptr};
    ctl::Button m_up{nullptr}, m_back{nullptr}, m_forward{nullptr};
    ctl::TextBox m_title{nullptr};
    ctl::TextBlock m_status{nullptr};
public:
    explicit NavIsland(HWND parent):m_parent(parent){}
    bool Create() {
        try {
            // An ordinary MFC executable has no Windows App SDK package graph.
            // Only this explicitly opted-in DLL initializes its pinned runtime.
            Trace("dll-before-bootstrap");
            PACKAGE_VERSION minimum{};
            minimum.Version=WINDOWSAPPSDK_RUNTIME_VERSION_UINT64;
            HRESULT bootstrap=MddBootstrapInitialize2(WINDOWSAPPSDK_RELEASE_MAJORMINOR,
                WINDOWSAPPSDK_RELEASE_VERSION_TAG_W,minimum,
                MddBootstrapInitializeOptions_None);
            if (FAILED(bootstrap)) {
                auto reason=std::string("dll-bootstrap-failed-HRESULT=")
                           +std::to_string(bootstrap);
                Trace(reason.c_str());
                return false;
            }
            Trace("dll-after-bootstrap");
            Trace("dll-before-dispatcher");
            m_queue=winrt::Microsoft::UI::Dispatching::DispatcherQueueController::CreateOnCurrentThread();
            Trace("dll-after-dispatcher");
            // Source-first initialization avoids loading an App.xaml resource
            // URI from the foreign MFC executable (its PRI has no WinUI page).
            Trace("dll-creating-source-without-declarative-app");
            m_source=ui::Hosting::DesktopWindowXamlSource();
            m_source.Initialize(winrt::Microsoft::UI::GetWindowIdFromWindow(m_parent));
            Trace("dll-source-attached");
            ctl::StackPanel root;
            root.Padding(ui::ThicknessHelper::FromUniformLength(10));
            root.Spacing(7);
            ctl::StackPanel row;
            row.Orientation(ctl::Orientation::Horizontal);
            row.Spacing(7);
            m_up=ctl::Button();
            m_up.Content(winrt::box_value(L"Up"));
            ui::Automation::AutomationProperties::SetAutomationId(m_up,L"Phase5IslandUpButton");
            m_back=ctl::Button();
            m_back.Content(winrt::box_value(L"Back"));
            ui::Automation::AutomationProperties::SetAutomationId(m_back,L"Phase5IslandBackButton");
            m_forward=ctl::Button();
            m_forward.Content(winrt::box_value(L"Forward"));
            ui::Automation::AutomationProperties::SetAutomationId(m_forward,L"Phase5IslandForwardButton");
            m_title=ctl::TextBox();
            m_title.IsReadOnly(true);
            m_title.MinWidth(340);
            ui::Automation::AutomationProperties::SetAutomationId(m_title,L"Phase5IslandAddressBox");
            m_status=ctl::TextBlock();
            ui::Automation::AutomationProperties::SetAutomationId(m_status,L"Phase5IslandStatusText");
            m_up.Click([this](auto const&,auto const&){Send(ID_GO_UP);});
            m_back.Click([this](auto const&,auto const&){Send(ID_GO_BACK);});
            m_forward.Click([this](auto const&,auto const&){Send(ID_GO_FORWARD);});
            row.Children().Append(m_back);
            row.Children().Append(m_forward);
            row.Children().Append(m_up);
            row.Children().Append(m_title);
            root.Children().Append(row);
            root.Children().Append(m_status);
            m_source.Content(root);
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
                ::SetWindowPos(island,HWND_TOP,0,0,0,0,
                               SWP_NOMOVE|SWP_NOSIZE|SWP_NOACTIVATE|SWP_SHOWWINDOW);
                auto evidence=std::string("dll-island-hwnd=")+
                    std::to_string(reinterpret_cast<uintptr_t>(island))+
                    " visible="+std::to_string(::IsWindowVisible(island));
                Trace(evidence.c_str());
            } else Trace("dll-island-hwnd-unavailable");
        } else Trace("dll-resize-unavailable");
    }
    void Close() {
        Trace("dll-close-enter");
        // Close the hosting source before releasing child UI references.
        // The former explicit Content(nullptr) reproducibly crashed the
        // test-owned product and must not be treated as successful teardown.
        if (m_source) {m_source.Close();m_source=nullptr;}
        Trace("dll-close-after-source-close");
        m_status=nullptr; m_title=nullptr;
        m_up=nullptr;m_back=nullptr;m_forward=nullptr;
        m_app=nullptr;
        // Releasing dispatcher ownership must not block the host MFC WM_DESTROY.
        m_queue=nullptr;
        Trace("dll-close-complete");
    }
};
static NavIsland* s_island=nullptr;

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
extern "C" __declspec(dllexport) void WINAPI FlyIslandDestroy() {
    NavIsland* was=s_island;
    s_island=nullptr;
    if (was) {was->Close();delete was;}
}
