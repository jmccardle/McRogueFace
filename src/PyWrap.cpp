#include "PyWrap.h"
#include <iostream>
#include <atomic>
#include <climits>
#include <cmath>
#include "PyVector.h"
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

static bool number_pair(PyObject* seq, sf::Vector2f& out)
{
    if (!(PyTuple_Check(seq) || PyList_Check(seq)) || PySequence_Fast_GET_SIZE(seq) != 2) {
        return false;
    }
    PyObject* x = PySequence_Fast_GET_ITEM(seq, 0);
    PyObject* y = PySequence_Fast_GET_ITEM(seq, 1);
    if (!(PyFloat_Check(x) || PyLong_Check(x)) || !(PyFloat_Check(y) || PyLong_Check(y))) {
        return false;
    }
    double fx = PyFloat_AsDouble(x), fy = PyFloat_AsDouble(y);
    if (PyErr_Occurred()) {
        PyErr_Clear();  // e.g. an int too large for a double: let Vector() report it
        return false;
    }
    out = sf::Vector2f((float)fx, (float)fy);
    return true;
}

bool to_vector2f(PyObject* arg, sf::Vector2f& out, const char* what)
{
    if (PyObject_TypeCheck(arg, &mcrfpydef::PyVectorType)) {
        out = ((PyVectorObject*)arg)->data;
        return true;
    }
    if (number_pair(arg, out)) return true;
    // Anything else Vector() accepts, with Vector()'s own validation.
    PyVectorObject* vec = PyVector::from_arg(arg);
    if (!vec) {
        if (!PyErr_Occurred() || PyErr_ExceptionMatches(PyExc_TypeError)) {
            PyErr_Format(PyExc_TypeError, "%s must be a Vector or a (x, y) pair", what);
        }
        return false;
    }
    out = vec->data;
    Py_DECREF(vec);
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
    PyErr_Format(PyExc_TypeError, "%s must be a number", what);
    return false;
}

static bool integral_to_cell(double value, int& out, const char* what)
{
    if (!std::isfinite(value) || std::floor(value) != value) {
        PyErr_Format(PyExc_ValueError, "%s must be a whole number of cells, got %R",
                     what, mcrf::PyRef(PyFloat_FromDouble(value)).get());
        return false;
    }
    return to_int(value, out, what);
}

bool to_cell(PyObject* value, int& out, const char* what)
{
    if (PyFloat_Check(value)) {
        double d = PyFloat_AsDouble(value);
        if (d == -1.0 && PyErr_Occurred()) return false;
        return integral_to_cell(d, out, what);
    }
    if (PyLong_Check(value)) return to_int(value, out, what);
    PyErr_Format(PyExc_TypeError, "%s must be an int (or a whole-number float), not %.200s",
                 what, Py_TYPE(value)->tp_name);
    return false;
}

bool to_cell_pos(PyObject* value, sf::Vector2i& out, const char* what)
{
    if (PyObject_TypeCheck(value, &mcrfpydef::PyVectorType)) {
        const sf::Vector2f& v = ((PyVectorObject*)value)->data;
        return integral_to_cell(v.x, out.x, what) && integral_to_cell(v.y, out.y, what);
    }
    if ((PyTuple_Check(value) || PyList_Check(value)) && PySequence_Fast_GET_SIZE(value) == 2) {
        PyObject** items = PySequence_Fast_ITEMS(value);
        return to_cell(items[0], out.x, what) && to_cell(items[1], out.y, what);
    }
    PyErr_Format(PyExc_TypeError, "%s must be a Vector or an (x, y) pair of ints, not %.200s",
                 what, Py_TYPE(value)->tp_name);
    return false;
}

void print_callback_error(const char* what)
{
    if (!PyErr_ExceptionMatches(PyExc_SystemExit)) {
        std::cerr << what << " callback raised an exception:" << std::endl;
    }
    PyErr_Print();
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
