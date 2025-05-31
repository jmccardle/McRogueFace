#pragma once
#include "Python.h"
#include <utility>

namespace PyRAII {
    
    // RAII wrapper for PyObject* that automatically manages reference counting
    class PyObjectRef {
    private:
        PyObject* ptr;
        
    public:
        // Constructors
        PyObjectRef() : ptr(nullptr) {}
        
        explicit PyObjectRef(PyObject* p, bool steal_ref = false) : ptr(p) {
            if (ptr && !steal_ref) {
                Py_INCREF(ptr);
            }
        }
        
        // Copy constructor
        PyObjectRef(const PyObjectRef& other) : ptr(other.ptr) {
            if (ptr) {
                Py_INCREF(ptr);
            }
        }
        
        // Move constructor  
        PyObjectRef(PyObjectRef&& other) noexcept : ptr(other.ptr) {
            other.ptr = nullptr;
        }
        
        // Destructor
        ~PyObjectRef() {
            Py_XDECREF(ptr);
        }
        
        // Copy assignment
        PyObjectRef& operator=(const PyObjectRef& other) {
            if (this != &other) {
                Py_XDECREF(ptr);
                ptr = other.ptr;
                if (ptr) {
                    Py_INCREF(ptr);
                }
            }
            return *this;
        }
        
        // Move assignment
        PyObjectRef& operator=(PyObjectRef&& other) noexcept {
            if (this != &other) {
                Py_XDECREF(ptr);
                ptr = other.ptr;
                other.ptr = nullptr;
            }
            return *this;
        }
        
        // Access operators
        PyObject* get() const { return ptr; }
        PyObject* operator->() const { return ptr; }
        PyObject& operator*() const { return *ptr; }
        operator bool() const { return ptr != nullptr; }
        
        // Release ownership (for returning to Python)
        PyObject* release() {
            PyObject* temp = ptr;
            ptr = nullptr;
            return temp;
        }
        
        // Reset with new pointer
        void reset(PyObject* p = nullptr, bool steal_ref = false) {
            if (p != ptr) {
                Py_XDECREF(ptr);
                ptr = p;
                if (ptr && !steal_ref) {
                    Py_INCREF(ptr);
                }
            }
        }
    };
    
    // Helper class for managing PyTypeObject* references from module lookups
    class PyTypeRef {
    private:
        PyTypeObject* type;
        
    public:
        PyTypeRef() : type(nullptr) {}
        
        explicit PyTypeRef(const char* typeName, PyObject* module) {
            type = (PyTypeObject*)PyObject_GetAttrString(module, typeName);
            // GetAttrString returns a new reference, so we own it
        }
        
        ~PyTypeRef() {
            Py_XDECREF((PyObject*)type);
        }
        
        // Delete copy operations to prevent accidental reference issues
        PyTypeRef(const PyTypeRef&) = delete;
        PyTypeRef& operator=(const PyTypeRef&) = delete;
        
        // Allow move operations
        PyTypeRef(PyTypeRef&& other) noexcept : type(other.type) {
            other.type = nullptr;
        }
        
        PyTypeRef& operator=(PyTypeRef&& other) noexcept {
            if (this != &other) {
                Py_XDECREF((PyObject*)type);
                type = other.type;
                other.type = nullptr;
            }
            return *this;
        }
        
        PyTypeObject* get() const { return type; }
        PyTypeObject* operator->() const { return type; }
        operator bool() const { return type != nullptr; }
    };
    
    // Convenience function to create a new object with RAII
    template<typename PyObjType>
    PyObjectRef createObject(const char* typeName, PyObject* module) {
        PyTypeRef type(typeName, module);
        if (!type) {
            return PyObjectRef();
        }
        
        PyObject* obj = type->tp_alloc(type.get(), 0);
        // tp_alloc returns a new reference, so we steal it
        return PyObjectRef(obj, true);
    }
}