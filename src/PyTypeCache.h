#pragma once
// PyTypeCache.h - Thread-safe caching of Python type objects
//
// This module provides a centralized, thread-safe way to cache Python type
// references. It eliminates the refcount leaks from repeated
// PyObject_GetAttrString calls and is compatible with free-threading (PEP 703).
//
// Usage:
//   PyTypeObject* entity_type = PyTypeCache::Entity();
//   if (!entity_type) return NULL;  // Error already set
//
// The cache is populated during module initialization and the types are
// held for the lifetime of the interpreter.

#include "Python.h"
#include <mutex>
#include <atomic>

class PyTypeCache {
public:
    // Initialize the cache - call once during module init after types are ready
    // Returns false and sets Python error on failure
    static bool initialize(PyObject* module);

    // Finalize - release references (call during module cleanup if needed)
    static void finalize();

    // Type accessors - return borrowed references (no DECREF needed)
    // These are thread-safe and lock-free after initialization
    static PyTypeObject* Entity();
    static PyTypeObject* Grid();
    static PyTypeObject* Frame();
    static PyTypeObject* Caption();
    static PyTypeObject* Sprite();
    static PyTypeObject* Texture();
    static PyTypeObject* Color();
    static PyTypeObject* Vector();
    static PyTypeObject* Font();

    // Check if initialized
    static bool isInitialized();

private:
    // Cached type pointers - atomic for thread-safe reads
    static std::atomic<PyTypeObject*> entity_type;
    static std::atomic<PyTypeObject*> grid_type;
    static std::atomic<PyTypeObject*> frame_type;
    static std::atomic<PyTypeObject*> caption_type;
    static std::atomic<PyTypeObject*> sprite_type;
    static std::atomic<PyTypeObject*> texture_type;
    static std::atomic<PyTypeObject*> color_type;
    static std::atomic<PyTypeObject*> vector_type;
    static std::atomic<PyTypeObject*> font_type;

    // Initialization flag
    static std::atomic<bool> initialized;

    // Mutex for initialization (only used during init, not for reads)
    static std::mutex init_mutex;

    // Helper to fetch and cache a type
    static PyTypeObject* cacheType(PyObject* module, const char* name,
                                   std::atomic<PyTypeObject*>& cache);
};
