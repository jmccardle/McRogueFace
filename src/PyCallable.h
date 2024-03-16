#pragma once
#include "Common.h"
#include "Python.h"

class PyCallable
{
protected:
    PyObject* target;
    PyCallable(PyObject*);
    ~PyCallable();
    PyObject* call(PyObject*, PyObject*);
public:
    bool isNone();
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

class PyClickCallable: public PyCallable
{
public:
    void call(sf::Vector2f, std::string, std::string);
    PyObject* borrow();
    PyClickCallable(PyObject*);
    PyClickCallable();
};

class PyKeyCallable: public PyCallable
{
public:
    void call(std::string, std::string);
    //PyObject* borrow(); // not yet implemented
    PyKeyCallable(PyObject*);
    PyKeyCallable();
};
