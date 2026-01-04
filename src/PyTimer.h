#pragma once
#include "Common.h"
#include "Python.h"
#include <memory>
#include <string>

class Timer;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<Timer> data;
    std::string name;
    PyObject* weakreflist;  // Weak reference support
} PyTimerObject;

class PyTimer
{
public:
    // Python type methods
    static PyObject* repr(PyObject* self);
    static int init(PyTimerObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args=NULL, PyObject* kwds=NULL);
    static void dealloc(PyTimerObject* self);
    
    // Timer control methods
    static PyObject* start(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* stop(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* pause(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* resume(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* restart(PyTimerObject* self, PyObject* Py_UNUSED(ignored));
    
    // Timer property getters
    static PyObject* get_name(PyTimerObject* self, void* closure);
    static PyObject* get_interval(PyTimerObject* self, void* closure);
    static int set_interval(PyTimerObject* self, PyObject* value, void* closure);
    static PyObject* get_remaining(PyTimerObject* self, void* closure);
    static PyObject* get_paused(PyTimerObject* self, void* closure);
    static PyObject* get_stopped(PyTimerObject* self, void* closure);
    static PyObject* get_active(PyTimerObject* self, void* closure);
    static int set_active(PyTimerObject* self, PyObject* value, void* closure);
    static PyObject* get_callback(PyTimerObject* self, void* closure);
    static int set_callback(PyTimerObject* self, PyObject* value, void* closure);
    static PyObject* get_once(PyTimerObject* self, void* closure);
    static int set_once(PyTimerObject* self, PyObject* value, void* closure);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    static PyTypeObject PyTimerType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Timer",
        .tp_basicsize = sizeof(PyTimerObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyTimer::dealloc,
        .tp_repr = PyTimer::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Timer(name, callback, interval, once=False, start=True)\n\n"
                            "Create a timer that calls a function at regular intervals.\n\n"
                            "Args:\n"
                            "    name (str): Unique identifier for the timer\n"
                            "    callback (callable): Function to call - receives (timer, runtime) args\n"
                            "    interval (int): Time between calls in milliseconds\n"
                            "    once (bool): If True, timer stops after first call. Default: False\n"
                            "    start (bool): If True, timer starts immediately. Default: True\n\n"
                            "Attributes:\n"
                            "    interval (int): Time between calls in milliseconds\n"
                            "    remaining (int): Time until next call in milliseconds (read-only)\n"
                            "    paused (bool): Whether timer is paused (read-only)\n"
                            "    stopped (bool): Whether timer is stopped (read-only)\n"
                            "    active (bool): Running state (read-write). Set True to start, False to pause\n"
                            "    callback (callable): The callback function (preserved when stopped)\n"
                            "    once (bool): Whether timer stops after firing once\n\n"
                            "Methods:\n"
                            "    start(): Start the timer, adding to engine tick loop\n"
                            "    stop(): Stop the timer (removes from engine, preserves callback)\n"
                            "    pause(): Pause the timer, preserving time remaining\n"
                            "    resume(): Resume a paused timer\n"
                            "    restart(): Reset timer and ensure it's running\n\n"
                            "Example:\n"
                            "    def on_timer(timer, runtime):\n"
                            "        print(f'Timer {timer} fired at {runtime}ms')\n"
                            "        if runtime > 5000:\n"
                            "            timer.stop()  # Stop but can restart later\n"
                            "    \n"
                            "    timer = mcrfpy.Timer('my_timer', on_timer, 1000)\n"
                            "    timer.pause()  # Pause timer\n"
                            "    timer.resume() # Resume timer\n"
                            "    timer.stop()   # Stop completely\n"
                            "    timer.start()  # Restart from beginning"),
        .tp_methods = PyTimer::methods,
        .tp_getset = PyTimer::getsetters,
        .tp_init = (initproc)PyTimer::init,
        .tp_new = PyTimer::pynew,
    };
}