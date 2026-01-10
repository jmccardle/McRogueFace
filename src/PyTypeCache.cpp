// PyTypeCache.cpp - Thread-safe Python type caching implementation
#include "PyTypeCache.h"

// Static member definitions
std::atomic<PyTypeObject*> PyTypeCache::entity_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::grid_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::frame_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::caption_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::sprite_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::texture_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::color_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::vector_type{nullptr};
std::atomic<PyTypeObject*> PyTypeCache::font_type{nullptr};
std::atomic<bool> PyTypeCache::initialized{false};
std::mutex PyTypeCache::init_mutex;

PyTypeObject* PyTypeCache::cacheType(PyObject* module, const char* name,
                                      std::atomic<PyTypeObject*>& cache) {
    PyObject* type_obj = PyObject_GetAttrString(module, name);
    if (!type_obj) {
        PyErr_Format(PyExc_RuntimeError,
                     "PyTypeCache: Failed to get type '%s' from module", name);
        return nullptr;
    }

    if (!PyType_Check(type_obj)) {
        Py_DECREF(type_obj);
        PyErr_Format(PyExc_TypeError,
                     "PyTypeCache: '%s' is not a type object", name);
        return nullptr;
    }

    // Store in cache - we keep the reference permanently
    // Using memory_order_release ensures the pointer is visible to other threads
    // after they see initialized=true
    cache.store((PyTypeObject*)type_obj, std::memory_order_release);

    return (PyTypeObject*)type_obj;
}

bool PyTypeCache::initialize(PyObject* module) {
    std::lock_guard<std::mutex> lock(init_mutex);

    // Double-check pattern - might have been initialized while waiting for lock
    if (initialized.load(std::memory_order_acquire)) {
        return true;
    }

    // Cache all types
    if (!cacheType(module, "Entity", entity_type)) return false;
    if (!cacheType(module, "Grid", grid_type)) return false;
    if (!cacheType(module, "Frame", frame_type)) return false;
    if (!cacheType(module, "Caption", caption_type)) return false;
    if (!cacheType(module, "Sprite", sprite_type)) return false;
    if (!cacheType(module, "Texture", texture_type)) return false;
    if (!cacheType(module, "Color", color_type)) return false;
    if (!cacheType(module, "Vector", vector_type)) return false;
    if (!cacheType(module, "Font", font_type)) return false;

    // Mark as initialized - release ensures all stores above are visible
    initialized.store(true, std::memory_order_release);

    return true;
}

void PyTypeCache::finalize() {
    std::lock_guard<std::mutex> lock(init_mutex);

    if (!initialized.load(std::memory_order_acquire)) {
        return;
    }

    // Release all cached references
    auto release = [](std::atomic<PyTypeObject*>& cache) {
        PyTypeObject* type = cache.exchange(nullptr, std::memory_order_acq_rel);
        if (type) {
            Py_DECREF(type);
        }
    };

    release(entity_type);
    release(grid_type);
    release(frame_type);
    release(caption_type);
    release(sprite_type);
    release(texture_type);
    release(color_type);
    release(vector_type);
    release(font_type);

    initialized.store(false, std::memory_order_release);
}

bool PyTypeCache::isInitialized() {
    return initialized.load(std::memory_order_acquire);
}

// Type accessors - lock-free reads after initialization
// Using memory_order_acquire ensures we see the pointer stored during init

PyTypeObject* PyTypeCache::Entity() {
    return entity_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Grid() {
    return grid_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Frame() {
    return frame_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Caption() {
    return caption_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Sprite() {
    return sprite_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Texture() {
    return texture_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Color() {
    return color_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Vector() {
    return vector_type.load(std::memory_order_acquire);
}

PyTypeObject* PyTypeCache::Font() {
    return font_type.load(std::memory_order_acquire);
}
