#pragma once

#include <Python.h>
#include <unordered_map>
#include <mutex>
#include <atomic>
#include <cstdint>

class PythonObjectCache {
private:
    static PythonObjectCache* instance;
    std::mutex serial_mutex;
    std::atomic<uint64_t> next_serial{1};
    std::unordered_map<uint64_t, PyObject*> cache;
    
    PythonObjectCache() = default;
    ~PythonObjectCache();

public:
    static PythonObjectCache& getInstance();
    
    // Assign a new serial number
    uint64_t assignSerial();
    
    // Register a Python object with a serial number
    void registerObject(uint64_t serial, PyObject* weakref);
    
    // Lookup a Python object by serial number
    // Returns new reference or nullptr
    PyObject* lookup(uint64_t serial);
    
    // Remove an entry from the cache
    void remove(uint64_t serial);
    
    // Clean up dead weak references
    void cleanup();
    
    // Clear entire cache (for module cleanup)
    void clear();
};