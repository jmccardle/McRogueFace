#pragma once
#include "Common.h"
#include "Python.h"
class GameEngine; // forward declare

class Timer
{
public:
    PyObject* target;
    int interval;
    int last_ran;
    Timer(); // for map to build
    Timer(Timer& other); // copy constructor
    Timer(PyObject*, int, int);
    ~Timer();
    bool test(int);
};
