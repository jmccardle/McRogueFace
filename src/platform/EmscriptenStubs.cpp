// EmscriptenStubs.cpp - Stub implementations for missing POSIX functions in Emscripten
// These functions are referenced by Python's posixmodule and timemodule but not available in WASM

#ifdef __EMSCRIPTEN__

#include <sys/types.h>
#include <sys/resource.h>
#include <wchar.h>
#include <errno.h>

extern "C" {

// wait3 and wait4 are BSD-style wait functions not available in Emscripten
// Python's posixmodule references them but they're not critical for WASM
pid_t wait3(int *status, int options, struct rusage *rusage) {
    errno = ENOSYS;
    return -1;
}

pid_t wait4(pid_t pid, int *status, int options, struct rusage *rusage) {
    errno = ENOSYS;
    return -1;
}

// wcsftime - wide character strftime, used by Python's timemodule
// Provide a minimal implementation that returns 0 (no characters written)
size_t wcsftime(wchar_t *wcs, size_t maxsize, const wchar_t *format, const struct tm *timeptr) {
    // In a full implementation, this would format time as wide chars
    // For WASM, just return 0 to indicate nothing written
    if (maxsize > 0) {
        wcs[0] = L'\0';
    }
    return 0;
}

} // extern "C"

#endif // __EMSCRIPTEN__
