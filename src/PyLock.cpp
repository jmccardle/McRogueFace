// #219 - Thread synchronization context manager for mcrfpy.lock()
#include "PyLock.h"
#include "GameEngine.h"
#include "Resources.h"

// Forward declarations
static PyObject* PyLockContext_enter(PyLockContextObject* self, PyObject* args);
static PyObject* PyLockContext_exit(PyLockContextObject* self, PyObject* args);
static void PyLockContext_dealloc(PyLockContextObject* self);
static PyObject* PyLockContext_new(PyTypeObject* type, PyObject* args, PyObject* kwds);

// Context manager methods
static PyMethodDef PyLockContext_methods[] = {
    {"__enter__", (PyCFunction)PyLockContext_enter, METH_NOARGS,
     "Acquire the frame lock, blocking until safe window opens"},
    {"__exit__", (PyCFunction)PyLockContext_exit, METH_VARARGS,
     "Release the frame lock"},
    {NULL}
};

// Type definition
PyTypeObject PyLockContextType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy._LockContext",
    .tp_basicsize = sizeof(PyLockContextObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyLockContext_dealloc,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "Thread synchronization context manager for safe UI updates from background threads",
    .tp_methods = PyLockContext_methods,
    .tp_new = PyLockContext_new,
};

static PyObject* PyLockContext_new(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyLockContextObject* self = (PyLockContextObject*)type->tp_alloc(type, 0);
    if (self) {
        self->acquired = false;
    }
    return (PyObject*)self;
}

static void PyLockContext_dealloc(PyLockContextObject* self) {
    // Safety: if we're destroyed while holding the lock, release it
    if (self->acquired && Resources::game) {
        Resources::game->getFrameLock().release();
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

static PyObject* PyLockContext_enter(PyLockContextObject* self, PyObject* args) {
    if (!Resources::game) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }

    // #219 - If we're on the main thread, no-op (already synchronized)
    // This allows the same code to work from callbacks, script init, AND background threads
    if (Resources::game->isMainThread()) {
        self->acquired = false;  // Don't try to release what we didn't acquire
        Py_INCREF(self);
        return (PyObject*)self;
    }

    // Acquire the frame lock - this will block (with GIL released) until safe window
    Resources::game->getFrameLock().acquire();
    self->acquired = true;

    // Return self for the `with` statement
    Py_INCREF(self);
    return (PyObject*)self;
}

static PyObject* PyLockContext_exit(PyLockContextObject* self, PyObject* args) {
    // args contains (exc_type, exc_val, exc_tb) - we don't suppress exceptions
    if (self->acquired && Resources::game) {
        Resources::game->getFrameLock().release();
        self->acquired = false;
    }

    // Return False to not suppress any exceptions
    Py_RETURN_FALSE;
}

// The lock() function that users call - returns a new context manager
PyObject* PyLock::lock(PyObject* self, PyObject* args) {
    if (!Resources::game) {
        PyErr_SetString(PyExc_RuntimeError, "Game engine not initialized");
        return NULL;
    }

    // Create and return a new context manager object
    return PyObject_CallObject((PyObject*)&PyLockContextType, NULL);
}

int PyLock::init() {
    if (PyType_Ready(&PyLockContextType) < 0) {
        return -1;
    }
    return 0;
}
