#include "Timer.h"

Timer::Timer(PyObject* _target, int _interval, int now)
: target(_target), interval(_interval), last_ran(now)
{
    //Py_INCREF(target);
}

Timer::Timer()
: target(Py_None), interval(0), last_ran(0)
{}

Timer::Timer(Timer& other)
: target(other.target), interval(other.interval), last_ran(other.last_ran)
{
    //Py_INCREF(target);
}

Timer::~Timer()
{
    //if (target && target != Py_None)
    //    Py_DECREF(target);
}

bool Timer::test(int now)
{
    if (!target || target == Py_None) return false;
    if (now > last_ran + interval)
    {
        last_ran = now;
        PyObject* args = Py_BuildValue("(i)", now);
        std::cout << PyUnicode_AsUTF8(PyObject_Repr(args)) << std::endl;
        PyObject_Call(target, args, NULL);
        return true;
    }
    return false;
}
