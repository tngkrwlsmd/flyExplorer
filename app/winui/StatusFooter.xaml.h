#pragma once
#include "StatusFooter.g.h"
namespace winrt::FlyExplorer::implementation {
struct StatusFooter : StatusFooterT<StatusFooter> {
 StatusFooter();
};
}
namespace winrt::FlyExplorer::factory_implementation {
struct StatusFooter : StatusFooterT<StatusFooter,implementation::StatusFooter>{};
}
