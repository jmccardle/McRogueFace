#include "Display.h"

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2) && !defined(_WIN32) && !defined(__APPLE__)
#define MCRF_PROBE_X11 1
#include <X11/Xlib.h>
#endif

namespace mcrf {

NoDisplayError::NoDisplayError(const std::string& what) : std::runtime_error(what) {}

bool display_available()
{
#ifdef MCRF_PROBE_X11
    // The same call SFML makes for its shared context (sf::priv::OpenDisplay).
    static const bool available = [] {
        Display* display = XOpenDisplay(nullptr);
        if (!display) return false;
        XCloseDisplay(display);
        return true;
    }();
    return available;
#else
    return true;
#endif
}

std::string no_display_message(const char* what)
{
    return std::string(what) + " needs a display, and none is available "
           "(DISPLAY is unset or the X server can't be reached). Pure-Python work runs "
           "without one; to render headlessly, run under a virtual display: xvfb-run -a mcrogueface ...";
}

void require_display(const char* what)
{
    if (!display_available()) throw NoDisplayError(no_display_message(what));
}

bool require_display_py(const char* what)
{
    if (display_available()) return true;
    PyErr_SetString(PyExc_RuntimeError, no_display_message(what).c_str());
    return false;
}

} // namespace mcrf
