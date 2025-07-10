#include "PyCallable.h"

PyCallable::PyCallable(PyObject* _target)
{
    target = Py_XNewRef(_target);
}

PyCallable::~PyCallable()
{
    if (target)
        Py_DECREF(target);
}

PyObject* PyCallable::call(PyObject* args, PyObject* kwargs)
{
    return PyObject_Call(target, args, kwargs);
}

bool PyCallable::isNone() const
{
    return (target == Py_None || target == NULL);
}

PyTimerCallable::PyTimerCallable(PyObject* _target, int _interval, int now)
: PyCallable(_target), interval(_interval), last_ran(now), 
  paused(false), pause_start_time(0), total_paused_time(0)
{}

PyTimerCallable::PyTimerCallable()
: PyCallable(Py_None), interval(0), last_ran(0),
  paused(false), pause_start_time(0), total_paused_time(0)
{}

bool PyTimerCallable::hasElapsed(int now)
{
    if (paused) return false;
    return now >= last_ran + interval;
}

void PyTimerCallable::call(int now)
{
    PyObject* args = Py_BuildValue("(i)", now);
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        PyErr_Print();
        PyErr_Clear();
    } else if (retval != Py_None)
    {
        std::cout << "timer returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        std::cout << PyUnicode_AsUTF8(PyObject_Repr(retval)) << std::endl;
    }
}

bool PyTimerCallable::test(int now)
{
    if(hasElapsed(now))
    {
        call(now);
        last_ran = now;
        return true;
    }
    return false;
}

void PyTimerCallable::pause(int current_time)
{
    if (!paused) {
        paused = true;
        pause_start_time = current_time;
    }
}

void PyTimerCallable::resume(int current_time)
{
    if (paused) {
        paused = false;
        int paused_duration = current_time - pause_start_time;
        total_paused_time += paused_duration;
        // Adjust last_ran to account for the pause
        last_ran += paused_duration;
    }
}

void PyTimerCallable::restart(int current_time)
{
    last_ran = current_time;
    paused = false;
    pause_start_time = 0;
    total_paused_time = 0;
}

void PyTimerCallable::cancel()
{
    // Cancel by setting target to None
    if (target && target != Py_None) {
        Py_DECREF(target);
    }
    target = Py_None;
    Py_INCREF(Py_None);
}

int PyTimerCallable::getRemaining(int current_time) const
{
    if (paused) {
        // When paused, calculate time remaining from when it was paused
        int elapsed_when_paused = pause_start_time - last_ran;
        return interval - elapsed_when_paused;
    }
    int elapsed = current_time - last_ran;
    return interval - elapsed;
}

void PyTimerCallable::setCallback(PyObject* new_callback)
{
    if (target && target != Py_None) {
        Py_DECREF(target);
    }
    target = Py_XNewRef(new_callback);
}

PyClickCallable::PyClickCallable(PyObject* _target)
: PyCallable(_target)
{}

PyClickCallable::PyClickCallable()
: PyCallable(Py_None)
{}

void PyClickCallable::call(sf::Vector2f mousepos, std::string button, std::string action)
{
    PyObject* args = Py_BuildValue("(iiss)", (int)mousepos.x, (int)mousepos.y, button.c_str(), action.c_str());
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        std::cout << "ClickCallable has raised an exception. It's going to STDERR and being dropped:" << std::endl;
        PyErr_Print();
        PyErr_Clear();
    } else if (retval != Py_None)
    {
        std::cout << "ClickCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        std::cout << PyUnicode_AsUTF8(PyObject_Repr(retval)) << std::endl;
    }
}

PyObject* PyClickCallable::borrow()
{
    return target;
}

PyKeyCallable::PyKeyCallable(PyObject* _target)
: PyCallable(_target)
{}

PyKeyCallable::PyKeyCallable()
: PyCallable(Py_None)
{}

void PyKeyCallable::call(std::string key, std::string action)
{
    if (target == Py_None || target == NULL) return;
    PyObject* args = Py_BuildValue("(ss)", key.c_str(), action.c_str());
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        std::cout << "KeyCallable has raised an exception. It's going to STDERR and being dropped:" << std::endl;
        PyErr_Print();
        PyErr_Clear();
    } else if (retval != Py_None)
    {
        std::cout << "KeyCallable returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
    }
}
