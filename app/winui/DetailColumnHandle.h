#pragma once
#include "DetailColumnHandle.g.h"

namespace winrt::FlyExplorer::implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle> {
    DetailColumnHandle();
};
}
namespace winrt::FlyExplorer::factory_implementation {
struct DetailColumnHandle : DetailColumnHandleT<DetailColumnHandle,implementation::DetailColumnHandle> {};
}
