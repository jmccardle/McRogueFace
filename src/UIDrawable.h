#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

#include "Resources.h"
#include "UIBase.h"
class UIFrame; class UICaption; class UISprite; class UIEntity; class UIGrid;

enum PyObjectsEnum : int
{
    UIFRAME = 1,
    UICAPTION,
    UISPRITE,
    UIGRID
};

class UIDrawable
{
public:
    void render();
    virtual void render(sf::Vector2f) = 0;
    virtual PyObjectsEnum derived_type() = 0;

    // Mouse input handling - callable object, methods to find event's destination
    std::unique_ptr<PyClickCallable> click_callable;
    virtual UIDrawable* click_at(sf::Vector2f point) = 0;
    void click_register(PyObject*);
    void click_unregister();

    UIDrawable();

    static PyObject* get_click(PyObject* self, void* closure);
    static int set_click(PyObject* self, PyObject* value, void* closure);
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
} PyUICollectionObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
    int index;
    int start_size;
} PyUICollectionIterObject;

namespace mcrfpydef {
    //PyObject* py_instance(std::shared_ptr<UIDrawable> source);
    // This function segfaults on tp_alloc for an unknown reason, but works inline with mcrfpydef:: methods.

#define RET_PY_INSTANCE(target) {                       \
switch (target->derived_type())                         \
{                                                       \
    case PyObjectsEnum::UIFRAME:                        \
    {                                                   \
        PyUIFrameObject* o = (PyUIFrameObject*)((&PyUIFrameType)->tp_alloc(&PyUIFrameType, 0)); \
        if (o)                                          \
        {                                               \
            auto p = std::static_pointer_cast<UIFrame>(target); \
            o->data = p;                                \
            auto utarget = o->data;                     \
        }                                               \
        return (PyObject*)o;                            \
    }                                                   \
    case PyObjectsEnum::UICAPTION:                        \
    {                                                   \
        PyUICaptionObject* o = (PyUICaptionObject*)((&PyUICaptionType)->tp_alloc(&PyUICaptionType, 0)); \
        if (o)                                          \
        {                                               \
            auto p = std::static_pointer_cast<UICaption>(target); \
            o->data = p;                                \
            auto utarget = o->data;                     \
        }                                               \
        return (PyObject*)o;                            \
    }                                                   \
    case PyObjectsEnum::UISPRITE:                        \
    {                                                   \
        PyUISpriteObject* o = (PyUISpriteObject*)((&PyUISpriteType)->tp_alloc(&PyUISpriteType, 0)); \
        if (o)                                          \
        {                                               \
            auto p = std::static_pointer_cast<UISprite>(target); \
            o->data = p;                                \
            auto utarget = o->data;                     \
        }                                               \
        return (PyObject*)o;                            \
    }                                                   \
    case PyObjectsEnum::UIGRID:                        \
    {                                                   \
        PyUIGridObject* o = (PyUIGridObject*)((&PyUIGridType)->tp_alloc(&PyUIGridType, 0)); \
        if (o)                                          \
        {                                               \
            auto p = std::static_pointer_cast<UIGrid>(target); \
            o->data = p;                                \
            auto utarget = o->data;                     \
        }                                               \
        return (PyObject*)o;                            \
    }                                                   \
}                                                       \
}
// end macro definition

//TODO: add this method to class scope; move implementation to .cpp file
/*
static PyObject* PyUIDrawable_get_click(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure)); // trust me bro, it's an Enum
    PyObject* ptr;

    switch (objtype)
    {
        case PyObjectsEnum::UIFRAME:
            ptr = ((PyUIFrameObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UICAPTION:
            ptr = ((PyUICaptionObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UISPRITE:
            ptr = ((PyUISpriteObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UIGRID:
            ptr = ((PyUIGridObject*)self)->data->click_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _get_click");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        return Py_None;
}*/

//TODO: add this method to class scope; move implementation to .cpp file
/*
static int PyUIDrawable_set_click(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure)); // trust me bro, it's an Enum
    UIDrawable* target;
    switch (objtype)
    {
        case PyObjectsEnum::UIFRAME:
            target = (((PyUIFrameObject*)self)->data.get());
            break;
        case PyObjectsEnum::UICAPTION:
            target = (((PyUICaptionObject*)self)->data.get());
            break;
        case PyObjectsEnum::UISPRITE:
            target = (((PyUISpriteObject*)self)->data.get());
            break;
        case PyObjectsEnum::UIGRID:
            target = (((PyUIGridObject*)self)->data.get());
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _set_click");
            return -1;
    }

	if (value == Py_None)
	{
		target->click_unregister();
	} else {
	    target->click_register(value);
	}
    return 0;
}
*/
}
