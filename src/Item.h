#pragma once
#include "Common.h"
#include "Components.h"
#include "Python.h"

class Item
{
public:
    bool stackable;
    static int next_id;
    std::string name;
    PyObject* object;
};
