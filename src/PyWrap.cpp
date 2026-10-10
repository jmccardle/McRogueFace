#include "PyWrap.h"
#include "PyVector.h"
#include "UIDrawable.h"
#include "UIEntity.h"
#include "PyGridData.h"

namespace mcrf {

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
    PythonObjectCache::getInstance().remove(serial);
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
    return cached_wrapper<PyUIEntityObject>(entity->serial_number, &mcrfpydef::PyUIEntityType,
        [&](PyUIEntityObject* o) { o->data = entity; o->weakreflist = nullptr; });
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
    if (wrapper || serial == 0 || !Py_IsInitialized()) return;
    // The wrapper exists whenever a subclass is attached: attaching happens from
    // Python, through that wrapper. A miss means it was already collected, and there
    // is nothing left to preserve.
    wrapper = live_wrapper(serial);  // new reference
}

void PyIdentityPin::release()
{
    if (!wrapper) return;
    // Null the member BEFORE the DECREF: the wrapper's dealloc drops its shared_ptr
    // to the owning object, which can re-enter here if that was the last strong ref.
    PyObject* tmp = wrapper;
    wrapper = nullptr;
    if (Py_IsInitialized()) Py_DECREF(tmp);
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
