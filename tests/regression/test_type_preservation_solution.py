#!/usr/bin/env python3
"""
Proof of concept test to demonstrate the solution for preserving Python derived types
in collections. This test outlines the approach that needs to be implemented in C++.

The solution involves:
1. Adding a PyObject* self member to UIDrawable (like UIEntity has)
2. Storing the Python object reference when objects are created from Python
3. Using the stored reference when retrieving from collections
"""

import mcrfpy
import sys

def demonstrate_solution():
    """Demonstrate how the solution should work"""
    print("=== Type Preservation Solution Demonstration ===\n")
    
    print("Current behavior (broken):")
    print("1. Python creates derived object (e.g., MyFrame extends Frame)")
    print("2. C++ stores only the shared_ptr<UIFrame>")
    print("3. When retrieved, C++ creates a NEW PyUIFrameObject with type 'Frame'")
    print("4. Original type and attributes are lost\n")
    
    print("Proposed solution (like UIEntity):")
    print("1. Add PyObject* self member to UIDrawable base class")
    print("2. In Frame/Sprite/Caption/Grid init, store: self->data->self = (PyObject*)self")
    print("3. In convertDrawableToPython, check if drawable->self exists")
    print("4. If it exists, return the stored Python object (with INCREF)")
    print("5. If not, create new base type object as fallback\n")
    
    print("Benefits:")
    print("- Preserves derived Python types")
    print("- Maintains object identity (same Python object)")
    print("- Keeps all Python attributes and methods")
    print("- Minimal performance impact (one pointer per object)")
    print("- Backwards compatible (C++-created objects still work)\n")
    
    print("Implementation steps:")
    print("1. Add 'PyObject* self = nullptr;' to UIDrawable class")
    print("2. Update Frame/Sprite/Caption/Grid init methods to store self")
    print("3. Update convertDrawableToPython in UICollection.cpp")
    print("4. Handle reference counting properly (INCREF/DECREF)")
    print("5. Clear self pointer in destructor to avoid circular refs\n")
    
    print("Example code change in UICollection.cpp:")
    print("""
    static PyObject* convertDrawableToPython(std::shared_ptr<UIDrawable> drawable) {
        if (!drawable) {
            Py_RETURN_NONE;
        }
        
        // Check if we have a stored Python object reference
        if (drawable->self != nullptr) {
            // Return the original Python object, preserving its type
            Py_INCREF(drawable->self);
            return drawable->self;
        }
        
        // Otherwise, create new object as before (fallback for C++-created objects)
        PyTypeObject* type = nullptr;
        PyObject* obj = nullptr;
        // ... existing switch statement ...
    }
    """)

def run_test(runtime):
    """Timer callback"""
    try:
        demonstrate_solution()
        print("\nThis solution approach is proven to work in UIEntityCollection.")
        print("It should be applied to UICollection for consistency.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    sys.exit(0)

# Set up scene and run
mcrfpy.createScene("test")
mcrfpy.setScene("test")
mcrfpy.setTimer("test", run_test, 100)