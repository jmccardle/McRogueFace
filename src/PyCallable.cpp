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

PyTimerCallable::PyTimerCallable(PyObject* _target, int _interval, int now)
: PyCallable(_target), interval(_interval), last_ran(now)
{}

PyTimerCallable::PyTimerCallable()
: PyCallable(Py_None), interval(0), last_ran(0)
{}

bool PyTimerCallable::hasElapsed(int now)
{
    return now >= last_ran + interval;
}

void PyTimerCallable::call(int now)
{
    PyObject* args = Py_BuildValue("(i)", now);
    PyObject* retval = PyCallable::call(args, NULL);
    if (!retval)
    {
        std::cout << "timer has raised an exception. It's going to STDERR and being dropped:" << std::endl;
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
