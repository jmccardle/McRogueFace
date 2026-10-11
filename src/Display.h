#pragma once
// #451: whether this process can create GL resources.
//
// The SFML build creates every texture through a GL context, and on Linux SFML opens the X
// display for it and abort()s when there is none: no exception, no Python error. Anything that
// is about to create one checks display_available() first and raises instead.
// The headless and SDL2 builds always have what they need.

#include "Python.h"
#include <stdexcept>
#include <string>

namespace mcrf {

struct NoDisplayError : std::runtime_error {
    explicit NoDisplayError(const std::string& what);
};

// Probed once, then cached.
bool display_available();

// The message for `what` needing a display ("rendering a frame", "Texture()", ...).
std::string no_display_message(const char* what);

// Throws NoDisplayError when there is no display.
void require_display(const char* what);

// Python entry points: sets RuntimeError and returns false when there is no display.
bool require_display_py(const char* what);

} // namespace mcrf
