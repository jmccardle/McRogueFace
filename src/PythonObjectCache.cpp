#include "PythonObjectCache.h"
#include <iostream>

PythonObjectCache* PythonObjectCache::instance = nullptr;

PythonObjectCache& PythonObjectCache::getInstance() {
    if (!instance) {
        instance = new PythonObjectCache();
    }
    return *instance;
}

PythonObjectCache::~PythonObjectCache() {
    clear();
}

uint64_t PythonObjectCache::assignSerial() {
    return next_serial.fetch_add(1, std::memory_order_relaxed);
}

void PythonObjectCache::registerObject(uint64_t serial, PyObject* weakref) {
    if (!weakref || serial == 0) return;
    
    std::lock_guard<std::mutex> lock(serial_mutex);
    
    // Clean up any existing entry
    auto it = cache.find(serial);
    if (it != cache.end()) {
        Py_DECREF(it->second);
    }
    
    // Store the new weak reference
    Py_INCREF(weakref);
    cache[serial] = weakref;
}

PyObject* PythonObjectCache::lookup(uint64_t serial) {
    if (serial == 0) return nullptr;
    
    // No mutex needed for read - GIL protects PyWeakref_GetObject
    auto it = cache.find(serial);
    if (it != cache.end()) {
        PyObject* obj = PyWeakref_GetObject(it->second);
        if (obj && obj != Py_None) {
            Py_INCREF(obj);
            return obj;
        }
    }
    return nullptr;
}

void PythonObjectCache::remove(uint64_t serial) {
    if (serial == 0) return;
    
    std::lock_guard<std::mutex> lock(serial_mutex);
    auto it = cache.find(serial);
    if (it != cache.end()) {
        Py_DECREF(it->second);
        cache.erase(it);
    }
}

void PythonObjectCache::cleanup() {
    std::lock_guard<std::mutex> lock(serial_mutex);
    
    auto it = cache.begin();
    while (it != cache.end()) {
        PyObject* obj = PyWeakref_GetObject(it->second);
        if (!obj || obj == Py_None) {
            Py_DECREF(it->second);
            it = cache.erase(it);
        } else {
            ++it;
        }
    }
}

void PythonObjectCache::clear() {
    std::lock_guard<std::mutex> lock(serial_mutex);
    
    for (auto& pair : cache) {
        Py_DECREF(pair.second);
    }
    cache.clear();
}