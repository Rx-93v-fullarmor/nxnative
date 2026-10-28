#include <stdbool.h>

// The Windows cross-build compiles no Swift, so upstream's Launcher.swift (which
// defines dm_show_launcher) is absent. Returning false starts the game at once with
// the build's defaults and the bundled env file (dm/env.txt).
bool dm_show_launcher(void *view_controller, void (*done)(void)) {
    (void)view_controller;
    (void)done;
    return false;
}
