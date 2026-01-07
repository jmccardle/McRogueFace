#pragma once
#include "Common.h"
#include "Python.h"
#include <memory>
#include <string>

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

    // Stopped state: timer is not in engine map, but callback is preserved
    bool stopped;

public:
    uint64_t serial_number = 0;  // For Python object cache
    std::string name;  // Store name for creating Python wrappers (#180)

    Timer(); // for map to build
    Timer(PyObject* target, int interval, int now, bool once = false, bool start = true, const std::string& name = "");
    ~Timer();

    // Core timer functionality
    bool test(int now);
    bool hasElapsed(int now) const;

    // Timer control methods
    void pause(int current_time);
    void resume(int current_time);
    void restart(int current_time);
    void start(int current_time);   // Clear stopped flag, reset progress
    void stop();                     // Set stopped flag, preserve callback

    // Timer state queries
    bool isPaused() const { return paused; }
    bool isStopped() const { return stopped; }
    bool isActive() const;  // Running: not paused AND not stopped AND has callback
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
