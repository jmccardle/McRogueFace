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

#include "UIGridPoint.h"
#include "UIDrawable.h"

class UIGrid;

// TODO: make UIEntity a drawable
class UIEntity//: public UIDrawable
{
public:
    //PyObject* self;
    std::shared_ptr<UIGrid> grid;
    std::vector<UIGridPointState> gridstate;
    UISprite sprite;
    sf::Vector2f position; //(x,y) in grid coordinates; float for animation
    void render(sf::Vector2f); //override final;

    UIEntity();
    UIEntity(UIGrid&);
    
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIEntity> data;
    //PyObject* texture;
} PyUIEntityObject;

namespace mcrfpydef {
//TODO: add this method to class scope; move implementation to .cpp file; reconsider for moving to "UIBase.h/.cpp"
// TODO: sf::Vector2f convenience functions here might benefit from a PyVectorObject much like PyColorObject
// Utility function to convert sf::Vector2f to PyObject*
static PyObject* sfVector2f_to_PyObject(sf::Vector2f vector) {
    return Py_BuildValue("(ff)", vector.x, vector.y);
}

//TODO: add this method to class scope; move implementation to .cpp file; reconsider for moving to "UIBase.h/.cpp"
// Utility function to convert PyObject* to sf::Vector2f
static sf::Vector2f PyObject_to_sfVector2f(PyObject* obj) {
    float x, y;
    if (!PyArg_ParseTuple(obj, "ff", &x, &y)) {
        return sf::Vector2f(); // TODO / reconsider this default: Return default vector on parse error
    }
    return sf::Vector2f(x, y);
}

//TODO: add this method to class scope; move implementation to .cpp file
// Utility function to convert UIGridPointState to PyObject*
static PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state) {
    PyObject* obj = PyObject_New(PyObject, &PyUIGridPointStateType);
    if (!obj) return PyErr_NoMemory();

    // Assuming PyUIGridPointStateObject structure has a UIGridPointState* member called 'data'
    //((PyUIGridPointStateObject*)obj)->data = new UIGridPointState(state); // Copy constructor // wontimplement / feat - don't use new, get shared_ptr working

    return obj;
}
//TODO: add this method to class scope; move implementation to .cpp file
// Function to convert std::vector<UIGridPointState> to a Python list TODO need a PyUICollection style iterable
static PyObject* UIGridPointStateVector_to_PyList(const std::vector<UIGridPointState>& vec) {
    PyObject* list = PyList_New(vec.size());
    if (!list) return PyErr_NoMemory();

    for (size_t i = 0; i < vec.size(); ++i) {
        PyObject* obj = UIGridPointState_to_PyObject(vec[i]);
        if (!obj) { // Cleanup on failure
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, obj); // This steals a reference to obj
    }

    return list;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIEntity_get_position(PyUIEntityObject* self, void* closure) {
    return sfVector2f_to_PyObject(self->data->position);
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIEntity_set_position(PyUIEntityObject* self, PyObject* value, void* closure) {
    self->data->position = PyObject_to_sfVector2f(value);
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIEntity_get_gridstate(PyUIEntityObject* self, void* closure) {
    // Assuming a function to convert std::vector<UIGridPointState> to PyObject* list
    return UIGridPointStateVector_to_PyList(self->data->gridstate);
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIEntity_get_spritenumber(PyUIEntityObject* self, void* closure) {
    return PyLong_FromDouble(self->data->sprite.getSpriteIndex());
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIEntity_set_spritenumber(PyUIEntityObject* self, PyObject* value, void* closure) {
    int val;
    if (PyLong_Check(value))
        val = PyLong_AsLong(value);
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
        return -1;
    }
    //self->data->sprite.sprite_index = val;
    self->data->sprite.setSpriteIndex(val); // todone - I don't like ".sprite.sprite" in this stack of UIEntity.UISprite.sf::Sprite
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIEntity_at(PyUIEntityObject* self, PyObject* o)
{
    int x, y;
    if (!PyArg_ParseTuple(o, "ii", &x, &y)) {
        PyErr_SetString(PyExc_TypeError, "UIEntity.at requires two integer arguments: (x, y)");
        return NULL;
    }

    if (self->data->grid == NULL) {
        PyErr_SetString(PyExc_ValueError, "Entity cannot access surroundings because it is not associated with a grid");
        return NULL;
    }

    PyUIGridPointStateObject* obj = (PyUIGridPointStateObject*)((&PyUIGridPointStateType)->tp_alloc(&PyUIGridPointStateType, 0));
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->gridstate[y + self->data->grid->grid_x * x]);
    obj->grid = self->data->grid;
    obj->entity = self->data;
    return (PyObject*)obj;
}

//TODO: add this static array to class scope; move implementation to .cpp file
static PyMethodDef PyUIEntity_methods[] = {
    {"at", (PyCFunction)PyUIEntity_at, METH_O},
    {NULL, NULL, 0, NULL}
};

//TODO: add this static array to class scope; move implementation to .cpp file
// Define getters and setters
static PyGetSetDef PyUIEntity_getsetters[] = {
    {"position", (getter)PyUIEntity_get_position, (setter)PyUIEntity_set_position, "Entity position", NULL},
    {"gridstate", (getter)PyUIEntity_get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"sprite_number", (getter)PyUIEntity_get_spritenumber, (setter)PyUIEntity_set_spritenumber, "Sprite number (index) on the texture on the display", NULL},
    {NULL}  /* Sentinel */
};

//TODO: add this method to class scope; forward declaration not required after .h/.cpp split
static int PyUIEntity_init(PyUIEntityObject*, PyObject*, PyObject*); // forward declare


// Define the PyTypeObject for UIEntity
static PyTypeObject PyUIEntityType = {
    //PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.Entity",
    .tp_basicsize = sizeof(PyUIEntityObject),
    .tp_itemsize = 0,
    // Methods omitted for brevity
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "UIEntity objects",
    .tp_methods = PyUIEntity_methods,
    .tp_getset = PyUIEntity_getsetters,
    .tp_init = (initproc)PyUIEntity_init,
    .tp_new = PyType_GenericNew,
};
}
