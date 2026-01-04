#include "PyTimer.h"
#include "Timer.h"
#include "GameEngine.h"
#include "Resources.h"
#include "PythonObjectCache.h"
#include "McRFPy_Doc.h"
#include <sstream>

PyObject* PyTimer::repr(PyObject* self) {
    PyTimerObject* timer = (PyTimerObject*)self;
    std::ostringstream oss;
    oss << "<Timer name='" << timer->name << "' ";

    if (timer->data) {
        oss << "interval=" << timer->data->getInterval() << "ms ";
        if (timer->data->isOnce()) {
            oss << "once=True ";
        }
        if (timer->data->isStopped()) {
            oss << "stopped";
        } else if (timer->data->isPaused()) {
            oss << "paused";
            // Get current time to show remaining
            int current_time = 0;
            if (Resources::game) {
                current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
            }
            oss << " (remaining=" << timer->data->getRemaining(current_time) << "ms)";
        } else if (timer->data->isActive()) {
            oss << "running";
        } else {
            oss << "inactive";
        }
    } else {
        oss << "uninitialized";
    }
    oss << ">";

    return PyUnicode_FromString(oss.str().c_str());
}

PyObject* PyTimer::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyTimerObject* self = (PyTimerObject*)type->tp_alloc(type, 0);
    if (self) {
        new(&self->name) std::string();  // Placement new for std::string
        self->data = nullptr;
        self->weakreflist = nullptr;  // Initialize weakref list
    }
    return (PyObject*)self;
}

int PyTimer::init(PyTimerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"name", "callback", "interval", "once", "start", NULL};
    const char* name = nullptr;
    PyObject* callback = nullptr;
    int interval = 0;
    int once = 0;      // Use int for bool parameter
    int start = 1;     // Default: start=True

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOi|pp", const_cast<char**>(kwlist),
                                     &name, &callback, &interval, &once, &start)) {
        return -1;
    }

    if (!PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return -1;
    }

    if (interval <= 0) {
        PyErr_SetString(PyExc_ValueError, "interval must be positive");
        return -1;
    }

    self->name = name;

    // Get current time from game engine
    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
    }

    // Create the timer with start parameter
    self->data = std::make_shared<Timer>(callback, interval, current_time, (bool)once, (bool)start);

    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }

    // Register with game engine only if starting
    if (Resources::game && start) {
        // If a timer with this name already exists, stop it first
        auto it = Resources::game->timers.find(self->name);
        if (it != Resources::game->timers.end() && it->second != self->data) {
            it->second->stop();
        }
        Resources::game->timers[self->name] = self->data;
    }

    return 0;
}

void PyTimer::dealloc(PyTimerObject* self) {
    // Clear weakrefs first
    if (self->weakreflist != nullptr) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }

    // Remove from game engine if still registered
    if (Resources::game && !self->name.empty()) {
        auto it = Resources::game->timers.find(self->name);
        if (it != Resources::game->timers.end() && it->second == self->data) {
            Resources::game->timers.erase(it);
        }
    }

    // Explicitly destroy std::string
    self->name.~basic_string();

    // Clear shared_ptr - this is the only place that truly destroys the Timer
    self->data.reset();

    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Timer control methods
PyObject* PyTimer::start(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }

    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();

        // If another timer has this name, stop it first
        auto it = Resources::game->timers.find(self->name);
        if (it != Resources::game->timers.end() && it->second != self->data) {
            it->second->stop();
        }

        // Add to engine map
        Resources::game->timers[self->name] = self->data;
    }

    self->data->start(current_time);
    Py_RETURN_NONE;
}

PyObject* PyTimer::stop(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }

    // Remove from game engine map (but preserve the Timer data!)
    if (Resources::game && !self->name.empty()) {
        auto it = Resources::game->timers.find(self->name);
        if (it != Resources::game->timers.end() && it->second == self->data) {
            Resources::game->timers.erase(it);
        }
    }

    self->data->stop();
    // NOTE: We do NOT reset self->data here - the timer can be restarted
    Py_RETURN_NONE;
}

PyObject* PyTimer::pause(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }

    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
    }

    self->data->pause(current_time);
    Py_RETURN_NONE;
}

PyObject* PyTimer::resume(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }

    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
    }

    self->data->resume(current_time);
    Py_RETURN_NONE;
}

PyObject* PyTimer::restart(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }

    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();

        // Ensure timer is in engine map
        auto it = Resources::game->timers.find(self->name);
        if (it == Resources::game->timers.end()) {
            // Timer was stopped, re-add it
            Resources::game->timers[self->name] = self->data;
        } else if (it->second != self->data) {
            // Another timer has this name, stop it and replace
            it->second->stop();
            Resources::game->timers[self->name] = self->data;
        }
    }

    self->data->restart(current_time);
    Py_RETURN_NONE;
}

// Property getters/setters
PyObject* PyTimer::get_interval(PyTimerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    return PyLong_FromLong(self->data->getInterval());
}

int PyTimer::set_interval(PyTimerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return -1;
    }
    
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "interval must be an integer");
        return -1;
    }
    
    long interval = PyLong_AsLong(value);
    if (interval <= 0) {
        PyErr_SetString(PyExc_ValueError, "interval must be positive");
        return -1;
    }
    
    self->data->setInterval(interval);
    return 0;
}

PyObject* PyTimer::get_remaining(PyTimerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
    }
    
    return PyLong_FromLong(self->data->getRemaining(current_time));
}

PyObject* PyTimer::get_paused(PyTimerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    return PyBool_FromLong(self->data->isPaused());
}

PyObject* PyTimer::get_stopped(PyTimerObject* self, void* closure) {
    if (!self->data) {
        return Py_True;  // Uninitialized is effectively stopped
    }

    return PyBool_FromLong(self->data->isStopped());
}

PyObject* PyTimer::get_active(PyTimerObject* self, void* closure) {
    if (!self->data) {
        return Py_False;
    }

    return PyBool_FromLong(self->data->isActive());
}

int PyTimer::set_active(PyTimerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return -1;
    }

    bool want_active = PyObject_IsTrue(value);

    int current_time = 0;
    if (Resources::game) {
        current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
    }

    if (want_active) {
        if (self->data->isStopped()) {
            // Reactivate a stopped timer
            if (Resources::game) {
                // Handle name collision
                auto it = Resources::game->timers.find(self->name);
                if (it != Resources::game->timers.end() && it->second != self->data) {
                    it->second->stop();
                }
                Resources::game->timers[self->name] = self->data;
            }
            self->data->start(current_time);
        } else if (self->data->isPaused()) {
            // Resume from pause
            self->data->resume(current_time);
        }
        // If already running, do nothing
    } else {
        // Setting active=False means pause
        if (!self->data->isPaused() && !self->data->isStopped()) {
            self->data->pause(current_time);
        }
    }

    return 0;
}

PyObject* PyTimer::get_callback(PyTimerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    PyObject* callback = self->data->getCallback();
    if (!callback) {
        Py_RETURN_NONE;
    }
    
    Py_INCREF(callback);
    return callback;
}

int PyTimer::set_callback(PyTimerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return -1;
    }
    
    if (!PyCallable_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return -1;
    }
    
    self->data->setCallback(value);
    return 0;
}

PyObject* PyTimer::get_once(PyTimerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    return PyBool_FromLong(self->data->isOnce());
}

int PyTimer::set_once(PyTimerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return -1;
    }
    
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "once must be a boolean");
        return -1;
    }
    
    self->data->setOnce(PyObject_IsTrue(value));
    return 0;
}

PyObject* PyTimer::get_name(PyTimerObject* self, void* closure) {
    return PyUnicode_FromString(self->name.c_str());
}

PyGetSetDef PyTimer::getsetters[] = {
    {"name", (getter)PyTimer::get_name, NULL,
     MCRF_PROPERTY(name, "Timer name (str, read-only). Unique identifier for this timer."), NULL},
    {"interval", (getter)PyTimer::get_interval, (setter)PyTimer::set_interval,
     MCRF_PROPERTY(interval, "Timer interval in milliseconds (int). Must be positive. Can be changed while timer is running."), NULL},
    {"remaining", (getter)PyTimer::get_remaining, NULL,
     MCRF_PROPERTY(remaining, "Time remaining until next trigger in milliseconds (int, read-only). Full interval when stopped."), NULL},
    {"paused", (getter)PyTimer::get_paused, NULL,
     MCRF_PROPERTY(paused, "Whether the timer is paused (bool, read-only). Paused timers preserve their remaining time."), NULL},
    {"stopped", (getter)PyTimer::get_stopped, NULL,
     MCRF_PROPERTY(stopped, "Whether the timer is stopped (bool, read-only). Stopped timers are not in the engine tick loop but preserve their callback."), NULL},
    {"active", (getter)PyTimer::get_active, (setter)PyTimer::set_active,
     MCRF_PROPERTY(active, "Running state (bool, read-write). True if running (not paused, not stopped). Set True to start/resume, False to pause."), NULL},
    {"callback", (getter)PyTimer::get_callback, (setter)PyTimer::set_callback,
     MCRF_PROPERTY(callback, "The callback function (callable). Preserved when stopped, allowing timer restart."), NULL},
    {"once", (getter)PyTimer::get_once, (setter)PyTimer::set_once,
     MCRF_PROPERTY(once, "Whether the timer stops after firing once (bool). One-shot timers can be restarted."), NULL},
    {NULL}
};

PyMethodDef PyTimer::methods[] = {
    {"start", (PyCFunction)PyTimer::start, METH_NOARGS,
     MCRF_METHOD(Timer, start,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start the timer, adding it to the engine tick loop."),
         MCRF_RETURNS("None")
         MCRF_NOTE("Resets progress and begins counting toward the next fire. If another timer has this name, it will be stopped.")
     )},
    {"stop", (PyCFunction)PyTimer::stop, METH_NOARGS,
     MCRF_METHOD(Timer, stop,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Stop the timer and remove it from the engine tick loop."),
         MCRF_RETURNS("None")
         MCRF_NOTE("The callback is preserved, so the timer can be restarted with start() or restart().")
     )},
    {"pause", (PyCFunction)PyTimer::pause, METH_NOARGS,
     MCRF_METHOD(Timer, pause,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Pause the timer, preserving the time remaining until next trigger."),
         MCRF_RETURNS("None")
         MCRF_NOTE("The timer can be resumed later with resume(). Time spent paused does not count toward the interval.")
     )},
    {"resume", (PyCFunction)PyTimer::resume, METH_NOARGS,
     MCRF_METHOD(Timer, resume,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Resume a paused timer from where it left off."),
         MCRF_RETURNS("None")
         MCRF_NOTE("Has no effect if the timer is not paused. Timer will fire after the remaining time elapses.")
     )},
    {"restart", (PyCFunction)PyTimer::restart, METH_NOARGS,
     MCRF_METHOD(Timer, restart,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Restart the timer from the beginning and ensure it's running."),
         MCRF_RETURNS("None")
         MCRF_NOTE("Resets progress and adds timer to engine if stopped. Equivalent to stop() followed by start().")
     )},
    {NULL}
};