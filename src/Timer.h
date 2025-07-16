#pragma once
#include "Common.h"
#include "Python.h"
#include <memory>

class PyCallable;
class GameEngine; // forward declare

class Timer
{
private:
    std::shared_ptr<PyCallable> callback;
    int interval;
    int last_ran;
    
    // Pause/resume support
    bool paused;
    int pause_start_time;
    int total_paused_time;
    
    // One-shot timer support
    bool once;
    
public:
    uint64_t serial_number = 0;  // For Python object cache
    
    Timer(); // for map to build
    Timer(PyObject* target, int interval, int now, bool once = false);
    ~Timer();
    
    // Core timer functionality
    bool test(int now);
    bool hasElapsed(int now) const;
    
    // Timer control methods
    void pause(int current_time);
    void resume(int current_time);
    void restart(int current_time);
    void cancel();
    
    // Timer state queries
    bool isPaused() const { return paused; }
    bool isActive() const;
    int getInterval() const { return interval; }
    void setInterval(int new_interval) { interval = new_interval; }
    int getRemaining(int current_time) const;
    int getElapsed(int current_time) const;
    bool isOnce() const { return once; }
    void setOnce(bool value) { once = value; }
    
    // Callback management
    PyObject* getCallback();
    void setCallback(PyObject* new_callback);
};
