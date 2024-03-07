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
        PyObject_Call(target, args, NULL);
        return true;
    }
    return false;
}
