#pragma once
#include "StatusFooter.g.h"
namespace winrt::FlyExplorerWinUIShell::implementation {
struct StatusFooter : StatusFooterT<StatusFooter> {
 StatusFooter();
};
}
namespace winrt::FlyExplorerWinUIShell::factory_implementation {
struct StatusFooter : StatusFooterT<StatusFooter,implementation::StatusFooter>{};
}
