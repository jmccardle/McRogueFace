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

// #230 - Hover callbacks (on_enter, on_exit, on_move) take only position
class PyHoverCallable: public PyCallable
{
public:
    void call(sf::Vector2f mousepos);
    PyObject* borrow();
    PyHoverCallable(PyObject*);
    PyHoverCallable();
    PyHoverCallable(const PyHoverCallable& other) : PyCallable(other) {}
    PyHoverCallable& operator=(const PyHoverCallable& other) {
        PyCallable::operator=(other);
        return *this;
    }
};

// #230 - Cell hover callbacks (on_cell_enter, on_cell_exit) take only cell position
class PyCellHoverCallable: public PyCallable
{
public:
    void call(sf::Vector2i cellpos);
    PyObject* borrow();
    PyCellHoverCallable(PyObject*);
    PyCellHoverCallable();
    PyCellHoverCallable(const PyCellHoverCallable& other) : PyCallable(other) {}
    PyCellHoverCallable& operator=(const PyCellHoverCallable& other) {
        PyCallable::operator=(other);
        return *this;
    }
};
