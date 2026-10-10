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
// user dropping their last reference. Only subclasses need it: base types have no
// __dict__, so re-creating their wrapper is unobservable.
//
// The pin is a cycle Python's GC cannot see (wrapper -> shared_ptr -> object -> pin),
// so the owning container must call sync(false, ...) on every exit. Objects route
// that through ONE ownership choke point (UIDrawable::setParent, UIEntity::setGrid).
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

private:
    PyObject* wrapper = nullptr;
};

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

// PyDict_SetItemString that STEALS `value` (and fails cleanly if it is nullptr):
//     dict_steal(d, "fps", PyLong_FromLong(fps));
// Returns 0, or -1 with a Python error set.
int dict_steal(PyObject* dict, const char* key, PyObject* value);

} // namespace mcrf
