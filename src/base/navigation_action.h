// Product-owned navigation action values shared by the WinUI controller
// and the isolated Shell supervisor. No legacy worker implementation.
#pragma once
#include "shell_navigation_core.h"
namespace fxfile { namespace shellnav {
enum class NavigationAction { Open, Back, Forward, Up, Refresh, Continue };
} }
