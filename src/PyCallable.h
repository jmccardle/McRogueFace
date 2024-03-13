#pragma once
#include "Common.h"
#include "Python.h"

class PyCallable
{
private:
    PyObject* target;
protected:
    PyCallable(PyObject*);
    ~PyCallable();
    PyObject* call(PyObject*, PyObject*);
};

class PyTimerCallable: public PyCallable
{
private:
    int interval;
    int last_ran;
    void call(int);
public:
    bool hasElapsed(int);
    bool test(int);
    PyTimerCallable(PyObject*, int, int);
    PyTimerCallable();
};
