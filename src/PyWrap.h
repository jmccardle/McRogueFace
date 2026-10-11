#pragma once
// PyWrap.h -- the one place the binding layer's CPython recipes live (#430, #436).
//
// tools/lint_bindings.py rejects hand-rolled copies of these recipes anywhere else:
//   * returning a C++ object to Python      -> to_python() / cached_wrapper()
//   * registering a wrapper in tp_init      -> register_wrapper()
//   * any other PythonObjectCache access    -> live_wrapper() / unregister_wrapper()
//   * keeping a subclass wrapper alive      -> PyIdentityPin
//   * Vector arguments                      -> to_vector2f()
//   * new references handed to non-stealing APIs -> PyRef / dict_steal()

#include "Common.h"
#include "Python.h"
#include "PythonObjectCache.h"
#include <cstdint>
#include <memory>

class UIDrawable;
class UIEntity;
class GridData;

namespace mcrf {

// ---------------------------------------------------------------------------
// Wrapper cache
// ---------------------------------------------------------------------------

// Record `self` as THE Python wrapper of the C++ object identified by `serial`,
// assigning a serial first if the object has none. Call it from tp_init (and it is
// called for you by cached_wrapper()). Returns 0, or -1 with a Python error set.
int register_wrapper(uint64_t& serial, PyObject* self);

// Drop the cache entry when the C++ object is destroyed.
void unregister_wrapper(uint64_t serial);

// The live wrapper for `serial` as a new reference, or nullptr if none exists.
// Never allocates; for callers that only want to reuse an existing wrapper.
PyObject* live_wrapper(uint64_t serial);

// The single cache-aware conversion recipe. Returns the live wrapper for `serial`
// if there is one; otherwise allocates a `type` instance, lets `fill(Obj*)` set its
// fields, and registers it so the next lookup returns the same object.
template <typename Obj, typename Fill>
PyObject* cached_wrapper(uint64_t& serial, PyTypeObject* type, Fill&& fill)
{
    if (PyObject* hit = live_wrapper(serial)) return hit;
    auto* obj = (Obj*)type->tp_alloc(type, 0);
    if (!obj) return nullptr;
    fill(obj);
    if (register_wrapper(serial, (PyObject*)obj) < 0) {
        Py_DECREF(obj);
        return nullptr;
    }
    return (PyObject*)obj;
}

// Return a C++ object to Python: the existing wrapper if one is alive (preserving
// identity and Python subclass), else a newly registered base-type wrapper.
// nullptr input returns None. New reference, or nullptr with an error set.
PyObject* to_python(const std::shared_ptr<UIDrawable>& drawable);
PyObject* to_python(const std::shared_ptr<UIEntity>& entity);
PyObject* to_python(const std::shared_ptr<GridData>& grid);

// ---------------------------------------------------------------------------
// Identity pin
// ---------------------------------------------------------------------------

// Holds a strong reference to an object's Python wrapper exactly while a C++
// container owns the object, so a Python subclass (and its attributes) survives the
// user dropping their last reference. #443: plain wrappers are pinned too, so a
// contained object never has two independent owners that the cycle collector would
// have to choose between (see owns_exclusively below).
//
// The pin is a cycle (wrapper -> shared_ptr -> object -> pin) that only the
// container's traverse reports, so the owning container must call sync(false, ...)
// on every exit. Objects route that through ONE choke point per kind
// (UIDrawable::updatePyIdentityPin, UIEntity/Entity3D::syncIdentityPin).
//
// There is deliberately no getter: never treat the pin as "the wrapper". Use
// to_python(), which hits the cache whenever the pin (or anyone) keeps it alive.
class PyIdentityPin {
public:
    PyIdentityPin() = default;
    ~PyIdentityPin() { release(); }
    PyIdentityPin(const PyIdentityPin&) = delete;
    PyIdentityPin& operator=(const PyIdentityPin&) = delete;

    // Pin the live wrapper for `serial` when `pinned` is true, release otherwise.
    // Idempotent.
    void sync(bool pinned, uint64_t serial);
    void release();
    bool pinned() const { return wrapper != nullptr; }
    bool holds(const PyObject* obj) const { return obj && wrapper == obj; }

    // #441: report the pinned wrapper to the cycle collector. Only the owning
    // container calls this, and only when it is itself exclusively owned (see below).
    int visit(visitproc visit, void* arg) const { Py_VISIT(wrapper); return 0; }

private:
    PyObject* wrapper = nullptr;
};

// ---------------------------------------------------------------------------
// GC ownership (#441)
// ---------------------------------------------------------------------------

// A wrapper's tp_traverse may report the Python objects held INSIDE its C++ object
// (callbacks, its children's pins, ...) only when every other strong owner of that
// object keeps the wrapper alive. Then the object cannot outlive the wrapper, so
// "the wrapper is garbage" really means "those references die with it".
//
//   * Reporting more than that lets the GC clear a callback that a scene or parent
//     still calls: the closure is wiped and the next call segfaults.
//   * Reporting less hides cycles that run through C++, which then leak.
//
// `keepers` counts the other owners that hold the wrapper: an identity pin (the
// container that pins it), a view's cached GridData wrapper (#348). Anything else
// holding a shared_ptr -- an animation, a collection view, a transient copy -- makes
// the wrapper report nothing, which is always safe: at worst a cycle survives.
//
// tp_clear applies the SAME test. The GC calls tp_clear on every wrapper it finds
// unreachable, including one whose C++ object a scene still owns.
inline bool owns_exclusively(long use_count, long keepers)
{
    return use_count == 1 + keepers;
}

// Propagate a nonzero result from a nested traverse, as Py_VISIT does for one object.
#define MCRF_VISIT(expr) do { int mcrf_visit_rc_ = (expr); if (mcrf_visit_rc_) return mcrf_visit_rc_; } while (0)

// Report the function held by a Py*Callable member (click, hover, key, cell ...).
template <typename Callable>
int visit_callable(const std::unique_ptr<Callable>& c, visitproc visit, void* arg)
{
    if (!c) return 0;
    PyObject* fn = c->borrow();
    if (fn && fn != Py_None) Py_VISIT(fn);
    return 0;
}

// ---------------------------------------------------------------------------
// Argument conversion and reference ownership
// ---------------------------------------------------------------------------

// Read a Vector, or anything Vector() accepts, into `out` without leaking.
// Vectors and 2-sequences of numbers take a fast path with no allocation.
// Returns false with a Python error set (TypeError naming `what`) on failure.
bool to_vector2f(PyObject* arg, sf::Vector2f& out, const char* what);

// Owns one new reference for the lifetime of the full expression or scope:
//     _click(self, PyRef(PyTuple_New(0)).get(), kwargs);
class PyRef {
public:
    explicit PyRef(PyObject* owned = nullptr) : p(owned) {}
    ~PyRef() { Py_XDECREF(p); }
    PyRef(const PyRef&) = delete;
    PyRef& operator=(const PyRef&) = delete;
    PyRef(PyRef&& o) noexcept : p(o.p) { o.p = nullptr; }
    PyRef& operator=(PyRef&& o) noexcept {
        if (this != &o) { Py_XDECREF(p); p = o.p; o.p = nullptr; }
        return *this;
    }
    PyObject* get() const { return p; }
    PyObject* release() { PyObject* t = p; p = nullptr; return t; }
    explicit operator bool() const { return p != nullptr; }

private:
    PyObject* p;
};

// A shared_ptr that holds one strong reference to a Python object, released when the
// last copy dies (#465: a no-op deleter here leaked every Shader ever assigned). The
// release takes the GIL, since a C++ owner can die outside it, and is skipped once the
// interpreter is finalized (the object is gone with it).
template <typename T>
std::shared_ptr<T> py_shared(T* obj)
{
    Py_INCREF((PyObject*)obj);
    return std::shared_ptr<T>(obj, [](T* p) {
        if (!Py_IsInitialized()) return;
        PyGILState_STATE gil = PyGILState_Ensure();
        Py_DECREF((PyObject*)p);
        PyGILState_Release(gil);
    });
}

// A number as a C int, without UB: ValueError for NaN/inf, OverflowError outside int's
// range (a float or long cast there is undefined; property_types fuzz target), and
// floats truncate toward zero. `what` names the value in the error. The PyObject
// form also accepts a Python int or float only (TypeError otherwise).
bool to_int(double value, int& out, const char* what);
bool to_int(PyObject* value, int& out, const char* what);

// Print the pending error from a Python callback, headed "<what> callback raised an
// exception:". sys.exit() in a callback is a request to quit, not an error: it gets
// no header, and PyErr_Print() exits as usual.
void print_callback_error(const char* what);

// PyDict_SetItemString that STEALS `value` (and fails cleanly if it is nullptr):
//     dict_steal(d, "fps", PyLong_FromLong(fps));
// Returns 0, or -1 with a Python error set.
int dict_steal(PyObject* dict, const char* key, PyObject* value);

} // namespace mcrf
