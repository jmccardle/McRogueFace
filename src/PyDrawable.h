#pragma once
#include "Common.h"
#include "Python.h"
#include "UIDrawable.h"

// Python object structure for UIDrawable base class
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIDrawable> data;
} PyDrawableObject;

// Declare the Python type for Drawable base class
namespace mcrfpydef {
    extern PyTypeObject PyDrawableType;
}