#include "PyWrap.h"
#include <iostream>
#include <atomic>
#include <climits>
#include <cmath>
#include <cfloat>
#include "PyVector.h"
#include "McRFPy_API.h"
#include "PyPositionHelper.h"
#include "UIDrawable.h"
#include "UIEntity.h"
#include "PyGridData.h"

namespace mcrf {

// #468: see python_alive(). Written only on the main thread (module creation, and the
// Py_AtExit handler at the end of Py_Finalize); read from destructors.
static std::atomic<bool> g_python_alive{false};

static void python_gone() { g_python_alive.store(false); }

bool python_alive() { return g_python_alive.load(std::memory_order_relaxed); }

void mark_python_alive()
{
    if (g_python_alive.exchange(true)) return;
    // Runs after Py_Finalize is done, whichever way it was reached (api_shutdown(), or
    // sys.exit() finalizing inside PyErr_Print()).
    Py_AtExit(python_gone);
}

int register_wrapper(uint64_t& serial, PyObject* self)
{
    if (serial == 0) serial = PythonObjectCache::getInstance().assignSerial();
    PyObject* weakref = PyWeakref_NewRef(self, nullptr);
    if (!weakref) return -1;  // the type lacks tp_weaklistoffset: a binding bug
    PythonObjectCache::getInstance().registerObject(serial, weakref);
    Py_DECREF(weakref);  // the cache holds its own reference
    return 0;
}

void unregister_wrapper(uint64_t serial)
{
    if (!python_alive()) return;
    PythonObjectCache::getInstance().remove(serial);
}

std::vector<PyRef> live_wrappers()
{
    std::vector<PyRef> out;
    for (PyObject* o : PythonObjectCache::getInstance().liveObjects()) out.emplace_back(o);
    return out;
}

PyObject* live_wrapper(uint64_t serial)
{
    return PythonObjectCache::getInstance().lookup(serial);
}

PyObject* to_python(const std::shared_ptr<UIDrawable>& drawable)
{
    return UIDrawable::pyobject_for(drawable);
}

PyObject* to_python(const std::shared_ptr<UIEntity>& entity)
{
    if (!entity) Py_RETURN_NONE;
    PyObject* obj = cached_wrapper<PyUIEntityObject>(entity->serial_number, &mcrfpydef::PyUIEntityType,
        [&](PyUIEntityObject* o) { o->data = entity; o->weakreflist = nullptr; });
    if (obj) entity->syncIdentityPin();  // #443: pin a new wrapper for an entity on a grid
    return obj;
}

PyObject* to_python(const std::shared_ptr<GridData>& grid)
{
    return PyGridData::pyobject_for(grid);
}

void PyIdentityPin::sync(bool pinned, uint64_t serial)
{
    if (!pinned) {
        release();
        return;
    }
    if (wrapper || serial == 0 || !python_alive()) return;
    // A miss means no wrapper exists (an object attached from C++, or one whose
    // wrapper was already collected). The converter pins the one it makes later.
    wrapper = live_wrapper(serial);  // new reference
}

void PyIdentityPin::release()
{
    if (!wrapper) return;
    // Null the member BEFORE the DECREF: the wrapper's dealloc drops its shared_ptr
    // to the owning object, which can re-enter here if that was the last strong ref.
    PyObject* tmp = wrapper;
    wrapper = nullptr;
    if (python_alive()) Py_DECREF(tmp);
}

bool require_finite(double value, const char* what)
{
    if (!std::isfinite(value)) {
        PyErr_Format(PyExc_ValueError, "%s must be finite (got %s)", what,
                     std::isnan(value) ? "nan" : (value > 0 ? "inf" : "-inf"));
        return false;
    }
    if (std::fabs(value) > static_cast<double>(FLT_MAX)) {
        PyErr_Format(PyExc_OverflowError, "%s is out of range for a float", what);
        return false;
    }
    return true;
}

void raise_got(PyObject* exc, const char* msg, double value)
{
    char buf[256];
    snprintf(buf, sizeof buf, "%s (got %g)", msg, value);
    PyErr_SetString(exc, buf);
}

bool to_float(PyObject* value, float& out, const char* what, bool check_finite)
{
    // Anything real-valued: float, int, bool, numpy scalars, Decimal-like (__float__ / __index__).
    if (!PyNumber_Check(value) && !PyIndex_Check(value)) {
        PyErr_Format(PyExc_TypeError, "%s must be a number (int or float)", what);
        return false;
    }
    double d = PyFloat_AsDouble(value);
    if (d == -1.0 && PyErr_Occurred()) return false;
    if (check_finite && !require_finite(d, what)) return false;
    if (std::isfinite(d) && std::fabs(d) > static_cast<double>(FLT_MAX)) {
        PyErr_Format(PyExc_OverflowError, "%s is out of range for a float", what);
        return false;
    }
    out = static_cast<float>(d);
    return true;
}

bool to_vector2f(PyObject* arg, sf::Vector2f& out, const char* what)
{
    // Exactly a Vector (by type) or a 2-sequence of real numbers, through the position helper:
    // new references to both items before any conversion (#543), nan/inf is ValueError and a
    // value beyond float range OverflowError (#540 item 12), anything else a TypeError naming
    // the argument. No fallback through Vector()'s own parser.
    float x, y;
    if (!PyPositionHelper::FromObject(arg, &x, &y, what)) return false;
    out = sf::Vector2f(x, y);
    return true;
}

bool to_int(double value, int& out, const char* what)
{
    if (!std::isfinite(value)) {
        PyErr_Format(PyExc_ValueError, "%s must be a finite number", what);
        return false;
    }
    if (value <= static_cast<double>(INT_MIN) - 1.0 || value >= static_cast<double>(INT_MAX) + 1.0) {
        PyErr_Format(PyExc_OverflowError, "%s is out of range for a C int", what);
        return false;
    }
    out = static_cast<int>(value);
    return true;
}

bool to_int(PyObject* value, int& out, const char* what)
{
    if (PyLong_Check(value)) {
        int overflow = 0;
        long v = PyLong_AsLongAndOverflow(value, &overflow);
        if (v == -1 && PyErr_Occurred()) return false;
        if (overflow || v < INT_MIN || v > INT_MAX) {
            PyErr_Format(PyExc_OverflowError, "%s is out of range for a C int", what);
            return false;
        }
        out = static_cast<int>(v);
        return true;
    }
    if (PyFloat_Check(value)) return to_int(PyFloat_AsDouble(value), out, what);
    if (PyIndex_Check(value)) {  // numpy integers and other __index__ objects (#558)
        PyObject* idx = PyNumber_Index(value);
        if (!idx) return false;
        const bool ok = to_int(idx, out, what);
        Py_DECREF(idx);
        return ok;
    }
    PyErr_Format(PyExc_TypeError, "%s must be a number", what);
    return false;
}

bool to_cell(PyObject* value, int& out, const char* what)
{
    return PyPositionHelper::IntFromObject(value, &out, what);
}

bool to_cell_pos(PyObject* value, sf::Vector2i& out, const char* what)
{
    int x, y;
    if (!PyPositionHelper::FromObjectInt(value, &x, &y, what)) return false;
    out = sf::Vector2i(x, y);
    return true;
}

bool float_to_cell(double value, int& out, const char* what)
{
    if (!std::isfinite(value)) {
        PyErr_Format(PyExc_ValueError, "%s must be finite (got %s)", what,
                     std::isnan(value) ? "nan" : (value > 0 ? "inf" : "-inf"));
        return false;
    }
    const double f = std::floor(value);
    if (!(f >= static_cast<double>(INT_MIN) && f <= static_cast<double>(INT_MAX))) {
        PyErr_Format(PyExc_OverflowError, "%s is out of range for a C int", what);
        return false;
    }
    out = static_cast<int>(f);
    return true;
}

void print_callback_exception()
{
    if (McRFPy_API::deferSystemExit()) return;
    PyErr_Print();
}

void print_callback_error(const char* what)
{
    if (!PyErr_ExceptionMatches(PyExc_SystemExit)) {
        std::cerr << what << " callback raised an exception:" << std::endl;
    }
    print_callback_exception();
}

int dict_steal(PyObject* dict, const char* key, PyObject* value)
{
    if (!value) return -1;  // the producer already set the error
    if (!dict) {             // PyDict_New() failed and set the error
        Py_DECREF(value);
        return -1;
    }
    int rc = PyDict_SetItemString(dict, key, value);
    Py_DECREF(value);
    return rc;
}

} // namespace mcrf
