#pragma once
#include "Common.h"
#include "Python.h"

class PyCallable
{
protected:
    PyObject* target;
    PyCallable(PyObject*);
    ~PyCallable();
    PyObject* call(PyObject*, PyObject*);
public:
    bool isNone() const;
};

class PyTimerCallable: public PyCallable
{
private:
    int interval;
    int last_ran;
    void call(int);
    
    // Pause/resume support
    bool paused;
    int pause_start_time;
    int total_paused_time;
    
public:
    bool hasElapsed(int);
    bool test(int);
    PyTimerCallable(PyObject*, int, int);
    PyTimerCallable();
    
    // Timer control methods
    void pause(int current_time);
    void resume(int current_time);
    void restart(int current_time);
    void cancel();
    
    // Timer state queries
    bool isPaused() const { return paused; }
    bool isActive() const { return !isNone() && !paused; }
    int getInterval() const { return interval; }
    void setInterval(int new_interval) { interval = new_interval; }
    int getRemaining(int current_time) const;
    PyObject* getCallback() { return target; }
    void setCallback(PyObject* new_callback);
};

class PyClickCallable: public PyCallable
{
public:
    void call(sf::Vector2f, std::string, std::string);
    PyObject* borrow();
    PyClickCallable(PyObject*);
    PyClickCallable();
};

class PyKeyCallable: public PyCallable
{
public:
    void call(std::string, std::string);
    //PyObject* borrow(); // not yet implemented
    PyKeyCallable(PyObject*);
    PyKeyCallable();
};
