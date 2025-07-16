#pragma once
#include "Common.h"
#include "Python.h"

class PyCallable
{
protected:
    PyObject* target;
    
public:
    PyCallable(PyObject*);
    PyCallable(const PyCallable& other);
    PyCallable& operator=(const PyCallable& other);
    ~PyCallable();
    PyObject* call(PyObject*, PyObject*);
    bool isNone() const;
    PyObject* borrow() const { return target; }
};

class PyClickCallable: public PyCallable
{
public:
    void call(sf::Vector2f, std::string, std::string);
    PyObject* borrow();
    PyClickCallable(PyObject*);
    PyClickCallable();
    PyClickCallable(const PyClickCallable& other) : PyCallable(other) {}
    PyClickCallable& operator=(const PyClickCallable& other) { 
        PyCallable::operator=(other); 
        return *this; 
    }
};

class PyKeyCallable: public PyCallable
{
public:
    void call(std::string, std::string);
    //PyObject* borrow(); // not yet implemented
    PyKeyCallable(PyObject*);
    PyKeyCallable();
};
