// libFuzzer entry points for McRogueFace Python API fuzzing (#283).
//
// One executable per process, one libFuzzer main, one embedded CPython.
// The active target is selected by MCRF_FUZZ_TARGET env var (e.g.
// "grid_entity"). On LLVMFuzzerInitialize we bootstrap Python, register
// the mcrfpy built-in module, import tests/fuzz/fuzz_<target>.py and
// resolve its `fuzz_one_input(data: bytes)` callable. On each
// LLVMFuzzerTestOneInput iteration we call it with the raw bytes.
//
// libFuzzer instruments the C++ engine code, so when Python operations
// drive mcrfpy into new C++ branches, libFuzzer sees the new edges and
// keeps the input. Python-level exceptions are swallowed here — only
// ASan/UBSan signal real bugs.

#include <Python.h>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <string>

#include "GameEngine.h"
#include "McRFPy_API.h"
#include "McRogueFaceConfig.h"
#include "PyFont.h"
#include "PyTexture.h"

namespace {

PyObject* g_target_fn = nullptr;     // fuzz_one_input callable from target module
PyObject* g_common_mod = nullptr;    // fuzz_common Python module (for safe_reset)
GameEngine* g_engine = nullptr;      // kept alive so mcrfpy can reach engine state
std::string g_target_name;

[[noreturn]] void fatal(const std::string& msg) {
    std::cerr << "[fuzz] FATAL: " << msg << std::endl;
    if (PyErr_Occurred()) {
        PyErr_Print();
    }
    std::exit(1);
}

std::string get_target_name_or_die() {
    const char* t = std::getenv("MCRF_FUZZ_TARGET");
    if (!t || !*t) {
        fatal("MCRF_FUZZ_TARGET env var not set. "
              "Expected one of: grid_entity, property_types, anim_timer_scene, "
              "maps_procgen, fov, pathfinding_behavior.");
    }
    return std::string(t);
}

// Walk up from cwd looking for tests/fuzz/fuzz_common.py. When invoked from
// build-fuzz/ that's one level up; this also works if someone runs the binary
// from the repo root or a sibling directory.
std::string find_tests_fuzz_dir() {
    namespace fs = std::filesystem;
    fs::path cwd = fs::current_path();
    for (int i = 0; i < 6; ++i) {
        fs::path candidate = cwd / "tests" / "fuzz";
        if (fs::exists(candidate / "fuzz_common.py")) {
            return candidate.string();
        }
        if (!cwd.has_parent_path() || cwd == cwd.parent_path()) {
            break;
        }
        cwd = cwd.parent_path();
    }
    fatal("Could not locate tests/fuzz/fuzz_common.py relative to cwd. "
          "Run the fuzzer from build-fuzz/ or repo root.");
}

}  // namespace

extern "C" int LLVMFuzzerInitialize(int* /*argc*/, char*** /*argv*/) {
    g_target_name = get_target_name_or_die();
    const std::string fuzz_dir = find_tests_fuzz_dir();

    McRogueFaceConfig config;
    config.headless = true;
    config.audio_enabled = false;
    config.python_mode = true;
    config.exec_scripts.push_back(
        std::filesystem::path(fuzz_dir) / ("fuzz_" + g_target_name + ".py"));

    // mcrfpy expects an engine instance to exist — several code paths reach
    // back into GameEngine via a global pointer. We never call engine->run().
    g_engine = new GameEngine(config);

    PyStatus status = McRFPy_API::init_python_with_config(config);
    if (PyStatus_Exception(status)) {
        fatal("Py_InitializeFromConfig failed");
    }

    McRFPy_API::mcrf_module = PyImport_ImportModule("mcrfpy");
    if (!McRFPy_API::mcrf_module) {
        fatal("Could not import mcrfpy");
    }

    // Load default_font/default_texture as main.cpp does. Assets must be
    // reachable from cwd — CMake post-build copies them to build-fuzz/assets.
    try {
        McRFPy_API::default_font =
            std::make_shared<PyFont>("assets/JetbrainsMono.ttf");
        McRFPy_API::default_texture = std::make_shared<PyTexture>(
            "assets/kenney_tinydungeon.png", 16, 16);
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_font",
                               McRFPy_API::default_font->pyObject());
        PyObject_SetAttrString(McRFPy_API::mcrf_module, "default_texture",
                               McRFPy_API::default_texture->pyObject());
    } catch (...) {
        std::cerr << "[fuzz] WARN: default_font/default_texture load failed "
                  << "(cwd=" << std::filesystem::current_path() << "). "
                  << "Targets that touch defaults may raise." << std::endl;
    }

    // Prepend fuzz_dir to sys.path so both fuzz_common and the target module
    // resolve without packaging.
    PyObject* sys_path = PySys_GetObject("path");
    if (!sys_path) {
        fatal("sys.path not accessible");
    }
    PyObject* py_fuzz_dir = PyUnicode_FromString(fuzz_dir.c_str());
    PyList_Insert(sys_path, 0, py_fuzz_dir);
    Py_DECREF(py_fuzz_dir);

    g_common_mod = PyImport_ImportModule("fuzz_common");
    if (!g_common_mod) {
        fatal("Could not import fuzz_common");
    }

    const std::string target_module_name = "fuzz_" + g_target_name;
    PyObject* target_mod = PyImport_ImportModule(target_module_name.c_str());
    if (!target_mod) {
        fatal("Could not import " + target_module_name);
    }

    g_target_fn = PyObject_GetAttrString(target_mod, "fuzz_one_input");
    Py_DECREF(target_mod);
    if (!g_target_fn || !PyCallable_Check(g_target_fn)) {
        fatal("Target module missing callable fuzz_one_input(data: bytes)");
    }

    std::cerr << "[fuzz] initialized target=" << g_target_name
              << " fuzz_dir=" << fuzz_dir << std::endl;
    return 0;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t* data, size_t size) {
    // Drop leaked state from the previous iteration. safe_reset failures are
    // non-fatal — keep the fuzz loop going.
    PyObject* safe_reset_fn = PyObject_GetAttrString(g_common_mod, "safe_reset");
    if (safe_reset_fn) {
        PyObject* r = PyObject_CallNoArgs(safe_reset_fn);
        Py_XDECREF(r);
        Py_DECREF(safe_reset_fn);
        if (PyErr_Occurred()) {
            PyErr_Clear();
        }
    }

    PyObject* py_data = PyBytes_FromStringAndSize(
        reinterpret_cast<const char*>(data), static_cast<Py_ssize_t>(size));
    if (!py_data) {
        PyErr_Clear();
        return 0;
    }

    PyObject* args = PyTuple_Pack(1, py_data);
    Py_DECREF(py_data);
    if (!args) {
        PyErr_Clear();
        return 0;
    }

    PyObject* result = PyObject_Call(g_target_fn, args, nullptr);
    Py_DECREF(args);

    if (!result) {
        // Python-level exception — target's try/except should swallow the usual
        // suspects (TypeError, ValueError, etc.). Anything reaching here is
        // either unexpected or a deliberate re-raise; clear and move on. Real
        // bugs come from ASan/UBSan, not Python tracebacks.
        PyErr_Clear();
    } else {
        Py_DECREF(result);
    }
    return 0;
}
