#include "PyTimer.h"
#include "Timer.h"
#include "GameEngine.h"
#include "Resources.h"
#include "PythonObjectCache.h"
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
        if (timer->data->isPaused()) {
            oss << "paused";
            // Get current time to show remaining
            int current_time = 0;
            if (Resources::game) {
                current_time = Resources::game->runtime.getElapsedTime().asMilliseconds();
            }
            oss << " (remaining=" << timer->data->getRemaining(current_time) << "ms)";
        } else if (timer->data->isActive()) {
            oss << "active";
        } else {
            oss << "cancelled";
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
    static const char* kwlist[] = {"name", "callback", "interval", "once", NULL};
    const char* name = nullptr;
    PyObject* callback = nullptr;
    int interval = 0;
    int once = 0;  // Use int for bool parameter
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOi|p", const_cast<char**>(kwlist), 
                                     &name, &callback, &interval, &once)) {
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
    
    // Create the timer
    self->data = std::make_shared<Timer>(callback, interval, current_time, (bool)once);
    
    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }
    
    // Register with game engine
    if (Resources::game) {
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
    
    // Clear shared_ptr
    self->data.reset();
    
    Py_TYPE(self)->tp_free((PyObject*)self);
}

// Timer control methods
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

PyObject* PyTimer::cancel(PyTimerObject* self, PyObject* Py_UNUSED(ignored)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Timer not initialized");
        return nullptr;
    }
    
    // Remove from game engine
    if (Resources::game && !self->name.empty()) {
        auto it = Resources::game->timers.find(self->name);
        if (it != Resources::game->timers.end() && it->second == self->data) {
            Resources::game->timers.erase(it);
        }
    }
    
    self->data->cancel();
    self->data.reset();
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

PyObject* PyTimer::get_active(PyTimerObject* self, void* closure) {
    if (!self->data) {
        return Py_False;
    }
    
    return PyBool_FromLong(self->data->isActive());
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
     "Timer name (read-only)", NULL},
    {"interval", (getter)PyTimer::get_interval, (setter)PyTimer::set_interval,
     "Timer interval in milliseconds", NULL},
    {"remaining", (getter)PyTimer::get_remaining, NULL,
     "Time remaining until next trigger in milliseconds", NULL},
    {"paused", (getter)PyTimer::get_paused, NULL,
     "Whether the timer is paused", NULL},
    {"active", (getter)PyTimer::get_active, NULL,
     "Whether the timer is active and not paused", NULL},
    {"callback", (getter)PyTimer::get_callback, (setter)PyTimer::set_callback,
     "The callback function to be called", NULL},
    {"once", (getter)PyTimer::get_once, (setter)PyTimer::set_once,
     "Whether the timer stops after firing once", NULL},
    {NULL}
};

PyMethodDef PyTimer::methods[] = {
    {"pause", (PyCFunction)PyTimer::pause, METH_NOARGS,
     "pause() -> None\n\n"
     "Pause the timer, preserving the time remaining until next trigger.\n"
     "The timer can be resumed later with resume()."},
    {"resume", (PyCFunction)PyTimer::resume, METH_NOARGS,
     "resume() -> None\n\n"
     "Resume a paused timer from where it left off.\n"
     "Has no effect if the timer is not paused."},
    {"cancel", (PyCFunction)PyTimer::cancel, METH_NOARGS,
     "cancel() -> None\n\n"
     "Cancel the timer and remove it from the timer system.\n"
     "The timer will no longer fire and cannot be restarted."},
    {"restart", (PyCFunction)PyTimer::restart, METH_NOARGS,
     "restart() -> None\n\n"
     "Restart the timer from the beginning.\n"
     "Resets the timer to fire after a full interval from now."},
    {NULL}
};