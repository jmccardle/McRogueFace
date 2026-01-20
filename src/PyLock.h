#pragma once
// #219 - Thread synchronization context manager for mcrfpy.lock()

#include <Python.h>

// Forward declaration
class GameEngine;

// PyLockContext - the context manager object returned by mcrfpy.lock()
typedef struct {
    PyObject_HEAD
    bool acquired;  // Track if we've acquired the lock
} PyLockContextObject;

// The type object for the context manager
extern PyTypeObject PyLockContextType;

// Module initialization function - adds lock() function to module
namespace PyLock {
    // Create the lock() function that returns a context manager
    PyObject* lock(PyObject* self, PyObject* args);

    // Initialize the type (call PyType_Ready)
    int init();
}
