#include "Timer.h"

Timer::Timer(PyObject* _target, int _interval, int now)
: target(_target), interval(_interval), last_ran(now)
{}

Timer::Timer()
: target(Py_None), interval(0), last_ran(0)
{}

bool Timer::test(int now)
{
    if (!target || target == Py_None) return false;
    if (now > last_ran + interval)
    {
        last_ran = now;
        PyObject* args = Py_BuildValue("(i)", now);
        PyObject* retval = PyObject_Call(target, args, NULL);
        if (!retval)
        {   
            std::cout << "timer has raised an exception. It's going to STDERR and being dropped:" << std::endl;
            PyErr_Print();
            PyErr_Clear();
        } else if (retval != Py_None)
        {   
            std::cout << "timer returned a non-None value. It's not an error, it's just not being saved or used." << std::endl;
        }
        return true;
    }
    return false;
}
