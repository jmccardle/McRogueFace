// EmscriptenStubs.cpp - Stub implementations for missing POSIX functions in Emscripten
// These functions are referenced by Python's posixmodule and timemodule but not available in WASM

#ifdef __EMSCRIPTEN__

#include <sys/types.h>
#include <sys/resource.h>
#include <wchar.h>
#include <errno.h>
#include <emscripten.h>
#include <Python.h>
#include <string>
#include "Resources.h"
#include "GameEngine.h"

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

// =============================================================================
// JavaScript-callable Python execution functions
// =============================================================================

// Run a Python string and return the result code (0 = success, -1 = error)
EMSCRIPTEN_KEEPALIVE
int run_python_string(const char* code) {
    if (!Py_IsInitialized()) {
        return -1;
    }
    return PyRun_SimpleString(code);
}

// Run Python code and capture stdout/stderr as a string
// Returns a pointer to a static buffer (caller should copy immediately)
static std::string python_output_buffer;

// Helper to safely delete a key from a dict without leaving error state
static void safe_dict_del(PyObject* dict, const char* key) {
    PyObject* py_key = PyUnicode_FromString(key);
    if (py_key && PyDict_Contains(dict, py_key)) {
        PyDict_DelItem(dict, py_key);
    }
    Py_XDECREF(py_key);
    PyErr_Clear();  // Clear any error from Contains or Del
}

EMSCRIPTEN_KEEPALIVE
const char* run_python_string_with_output(const char* code) {
    if (!Py_IsInitialized()) {
        python_output_buffer = "Error: Python not initialized";
        return python_output_buffer.c_str();
    }

    // CRITICAL: Clear any lingering error state before execution
    // This prevents "clogged" interpreter state from previous errors
    if (PyErr_Occurred()) {
        PyErr_Clear();
    }

    // Redirect stdout and stderr to a StringIO, run code, capture output
    // Also capture repr of last expression (like Python REPL)
    const char* capture_code = R"(
import sys
import io

_mcrf_stdout_capture = io.StringIO()
_mcrf_stderr_capture = io.StringIO()
_mcrf_old_stdout = sys.stdout
_mcrf_old_stderr = sys.stderr
sys.stdout = _mcrf_stdout_capture
sys.stderr = _mcrf_stderr_capture

_mcrf_exec_error = None
_mcrf_last_repr = None

try:
    # Try to compile as eval (expression) first
    _mcrf_code_obj = compile(_mcrf_user_code, '<repl>', 'eval')
    _mcrf_result = eval(_mcrf_code_obj, globals())
    if _mcrf_result is not None:
        _mcrf_last_repr = repr(_mcrf_result)
except SyntaxError:
    # Not a simple expression, try exec
    try:
        exec(_mcrf_user_code, globals())
    except Exception as e:
        import traceback
        _mcrf_exec_error = traceback.format_exc()
except Exception as e:
    import traceback
    _mcrf_exec_error = traceback.format_exc()

sys.stdout = _mcrf_old_stdout
sys.stderr = _mcrf_old_stderr

_mcrf_captured_output = _mcrf_stdout_capture.getvalue()
if _mcrf_stderr_capture.getvalue():
    _mcrf_captured_output += _mcrf_stderr_capture.getvalue()
if _mcrf_exec_error:
    _mcrf_captured_output += _mcrf_exec_error
elif _mcrf_last_repr:
    _mcrf_captured_output += _mcrf_last_repr
)";

    // Set the user code as a Python variable
    PyObject* main_module = PyImport_AddModule("__main__");
    PyObject* main_dict = PyModule_GetDict(main_module);
    PyObject* py_code = PyUnicode_FromString(code);
    PyDict_SetItemString(main_dict, "_mcrf_user_code", py_code);
    Py_DECREF(py_code);

    // Run the capture code
    int result = PyRun_SimpleString(capture_code);

    // Check if capture code itself failed (e.g., internal error in REPL wrapper)
    if (result != 0 || PyErr_Occurred()) {
        // Capture the Python error before clearing
        PyObject *ptype, *pvalue, *ptraceback;
        PyErr_Fetch(&ptype, &pvalue, &ptraceback);

        python_output_buffer = "Internal REPL Error: ";
        if (pvalue) {
            PyObject* str = PyObject_Str(pvalue);
            if (str) {
                const char* err_str = PyUnicode_AsUTF8(str);
                if (err_str) {
                    python_output_buffer += err_str;
                }
                Py_DECREF(str);
            }
        } else {
            python_output_buffer += "Unknown error in capture code";
        }

        Py_XDECREF(ptype);
        Py_XDECREF(pvalue);
        Py_XDECREF(ptraceback);
        PyErr_Clear();  // Ensure clean state for next execution

        // Still clean up what we can
        safe_dict_del(main_dict, "_mcrf_user_code");
        return python_output_buffer.c_str();
    }

    // Get the captured output
    PyObject* output = PyDict_GetItemString(main_dict, "_mcrf_captured_output");
    if (output && PyUnicode_Check(output)) {
        const char* output_str = PyUnicode_AsUTF8(output);
        python_output_buffer = output_str ? output_str : "";
    } else {
        python_output_buffer = "";
    }

    // Clean up ALL temporary variables (including previously missed ones)
    safe_dict_del(main_dict, "_mcrf_user_code");
    safe_dict_del(main_dict, "_mcrf_stdout_capture");
    safe_dict_del(main_dict, "_mcrf_stderr_capture");
    safe_dict_del(main_dict, "_mcrf_old_stdout");
    safe_dict_del(main_dict, "_mcrf_old_stderr");
    safe_dict_del(main_dict, "_mcrf_exec_error");
    safe_dict_del(main_dict, "_mcrf_captured_output");
    safe_dict_del(main_dict, "_mcrf_last_repr");    // Previously leaked
    safe_dict_del(main_dict, "_mcrf_result");       // Previously leaked
    safe_dict_del(main_dict, "_mcrf_code_obj");     // Previously leaked

    // Final safety check - clear any residual error state
    if (PyErr_Occurred()) {
        PyErr_Clear();
    }

    return python_output_buffer.c_str();
}

// Reset the Python environment (re-run game.py)
EMSCRIPTEN_KEEPALIVE
int reset_python_environment() {
    if (!Py_IsInitialized()) {
        return -1;
    }

    // Clear any lingering error state first
    if (PyErr_Occurred()) {
        PyErr_Clear();
    }

    // Clear all scenes and reload game.py
    const char* reset_code = R"(
import mcrfpy
import sys

# Try to reload the game module
if 'game' in sys.modules:
    del sys.modules['game']

# Re-execute game.py
try:
    with open('/scripts/game.py', 'r') as f:
        exec(f.read(), globals())
    print("Environment reset successfully")
except Exception as e:
    print(f"Reset error: {e}")
)";

    int result = PyRun_SimpleString(reset_code);

    // Clear any error state from reset
    if (PyErr_Occurred()) {
        PyErr_Clear();
    }

    return result;
}

// =============================================================================
// Interpreter health check functions (for debugging)
// =============================================================================

static std::string python_state_buffer;

// Check the current state of the Python interpreter
// Returns: "OK", "NOT_INITIALIZED", or "ERROR_SET: <message>"
EMSCRIPTEN_KEEPALIVE
const char* get_python_state() {
    if (!Py_IsInitialized()) {
        return "NOT_INITIALIZED";
    }

    if (PyErr_Occurred()) {
        PyObject *ptype, *pvalue, *ptraceback;
        PyErr_Fetch(&ptype, &pvalue, &ptraceback);

        python_state_buffer = "ERROR_SET: ";
        if (pvalue) {
            PyObject* str = PyObject_Str(pvalue);
            if (str) {
                const char* err_str = PyUnicode_AsUTF8(str);
                if (err_str) {
                    python_state_buffer += err_str;
                }
                Py_DECREF(str);
            }
        } else {
            python_state_buffer += "Unknown error";
        }

        // Restore the error so caller can decide what to do
        PyErr_Restore(ptype, pvalue, ptraceback);
        return python_state_buffer.c_str();
    }

    return "OK";
}

// Clear any pending Python error state
EMSCRIPTEN_KEEPALIVE
void clear_python_error() {
    if (Py_IsInitialized() && PyErr_Occurred()) {
        PyErr_Clear();
    }
}

// Get a count of items in Python's global namespace (for debugging memory leaks)
EMSCRIPTEN_KEEPALIVE
int get_python_globals_count() {
    if (!Py_IsInitialized()) {
        return -1;
    }

    PyObject* main_module = PyImport_AddModule("__main__");
    PyObject* main_dict = PyModule_GetDict(main_module);
    return (int)PyDict_Size(main_dict);
}

// Flush IDBFS to IndexedDB (called from Python via mcrfpy._sync_storage())
EMSCRIPTEN_KEEPALIVE
void sync_storage() {
    EM_ASM(
        FS.syncfs(false, function(err) {
            if (err) {
                console.error('McRogueFace: Failed to sync /save/ to IndexedDB:', err);
            }
        });
    );
}

// Notify the engine that the browser canvas was resized (called from JS)
EMSCRIPTEN_KEEPALIVE
void notify_canvas_resize(int width, int height) {
    // Forward to SDL so it generates a proper resize event
    if (Resources::game) {
        auto& win = Resources::game->getWindow();
        win.setSize(sf::Vector2u(width, height));
    }
}

} // extern "C"

#endif // __EMSCRIPTEN__
