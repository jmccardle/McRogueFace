#include "PyTimer.h"
#include "PyCallable.h"
#include "GameEngine.h"
#include "Resources.h"
#include <sstream>

PyObject* PyTimer::repr(PyObject* self) {
    PyTimerObject* timer = (PyTimerObject*)self;
    std::ostringstream oss;
    oss << "<Timer name='" << timer->name << "' ";
    
    if (timer->data) {
        oss << "interval=" << timer->data->getInterval() << "ms ";
        oss << (timer->data->isPaused() ? "paused" : "active");
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
    }
    return (PyObject*)self;
}

int PyTimer::init(PyTimerObject* self, PyObject* args, PyObject* kwds) {
    static char* kwlist[] = {"name", "callback", "interval", NULL};
    const char* name = nullptr;
    PyObject* callback = nullptr;
    int interval = 0;
    
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOi", kwlist, 
                                     &name, &callback, &interval)) {
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
    
    // Create the timer callable
    self->data = std::make_shared<PyTimerCallable>(callback, interval, current_time);
    
    // Register with game engine
    if (Resources::game) {
        Resources::game->timers[self->name] = self->data;
    }
    
    return 0;
}

void PyTimer::dealloc(PyTimerObject* self) {
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

PyGetSetDef PyTimer::getsetters[] = {
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
    {NULL}
};

PyMethodDef PyTimer::methods[] = {
    {"pause", (PyCFunction)PyTimer::pause, METH_NOARGS,
     "Pause the timer"},
    {"resume", (PyCFunction)PyTimer::resume, METH_NOARGS,
     "Resume a paused timer"},
    {"cancel", (PyCFunction)PyTimer::cancel, METH_NOARGS,
     "Cancel the timer and remove it from the system"},
    {"restart", (PyCFunction)PyTimer::restart, METH_NOARGS,
     "Restart the timer from the current time"},
    {NULL}
};