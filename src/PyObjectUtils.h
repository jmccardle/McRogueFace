#pragma once
#include "Common.h"
#include "Python.h"
#include "McRFPy_API.h"
#include "PyRAII.h"

namespace PyObjectUtils {
    
    // Template for getting Python type object from module
    template<typename T>
    PyTypeObject* getPythonType(const char* typeName) {
        PyTypeObject* type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, typeName);
        if (!type) {
            PyErr_Format(PyExc_RuntimeError, "Could not find %s type in module", typeName);
        }
        return type;
    }
    
    // Generic function to create a Python object of given type
    inline PyObject* createPyObjectGeneric(const char* typeName) {
        PyTypeObject* type = getPythonType<void>(typeName);
        if (!type) return nullptr;
        
        PyObject* obj = type->tp_alloc(type, 0);
        Py_DECREF(type);
        
        return obj;
    }
    
    // Helper function to allocate and initialize a Python object with data
    template<typename PyObjType, typename DataType>
    PyObject* createPyObjectWithData(const char* typeName, DataType data) {
        PyTypeObject* type = getPythonType<void>(typeName);
        if (!type) return nullptr;
        
        PyObjType* obj = (PyObjType*)type->tp_alloc(type, 0);
        Py_DECREF(type);
        
        if (obj) {
            obj->data = data;
        }
        return (PyObject*)obj;
    }
    
    // Function to convert UIDrawable to appropriate Python object
    // This is moved to UICollection.cpp to avoid circular dependencies
    
    // RAII-based object creation example
    inline PyObject* createPyObjectGenericRAII(const char* typeName) {
        PyRAII::PyTypeRef type(typeName, McRFPy_API::mcrf_module);
        if (!type) {
            PyErr_Format(PyExc_RuntimeError, "Could not find %s type in module", typeName);
            return nullptr;
        }
        
        PyObject* obj = type->tp_alloc(type.get(), 0);
        // Return the new reference (caller owns it)
        return obj;
    }
    
    // Example of using PyObjectRef for safer reference management
    template<typename PyObjType, typename DataType>
    PyObject* createPyObjectWithDataRAII(const char* typeName, DataType data) {
        PyRAII::PyObjectRef obj = PyRAII::createObject<PyObjType>(typeName, McRFPy_API::mcrf_module);
        if (!obj) {
            PyErr_Format(PyExc_RuntimeError, "Could not create %s object", typeName);
            return nullptr;
        }
        
        // Access the object through the RAII wrapper
        ((PyObjType*)obj.get())->data = data;
        
        // Release ownership to return to Python
        return obj.release();
    }
}