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
#include "UIEntity.h"
#include "UIDrawable.h"

class UIGrid: public UIDrawable
{
private:
    std::shared_ptr<PyTexture> ptex;
public:
    UIGrid();
    //UIGrid(int, int, IndexTexture*, float, float, float, float);
    UIGrid(int, int, std::shared_ptr<PyTexture>, sf::Vector2f, sf::Vector2f);
    void update();
    void render(sf::Vector2f) override final;
    UIGridPoint& at(int, int);
    PyObjectsEnum derived_type() override final;
    //void setSprite(int);
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

    int grid_x, grid_y;
    //int grid_size; // grid sizes are implied by IndexTexture now
    sf::RectangleShape box;
    float center_x, center_y, zoom;
    //IndexTexture* itex;
    std::shared_ptr<PyTexture> getTexture();
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    std::vector<UIGridPoint> points;
    std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> entities;
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> data;
    //PyObject* texture;
} PyUIGridObject;

namespace mcrfpydef {
//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGrid_init(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    int grid_x, grid_y;
    PyObject* textureObj;
    float box_x, box_y, box_w, box_h;

    if (!PyArg_ParseTuple(args, "iiOffff", &grid_x, &grid_y, &textureObj, &box_x, &box_y, &box_w, &box_h)) {
        return -1; // If parsing fails, return an error
    }

    // Convert PyObject texture to IndexTexture*
    // This requires the texture object to have been initialized similar to UISprite's texture handling
    if (!PyObject_IsInstance(textureObj, (PyObject*)&PyTextureType)) {
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    }
    PyTextureObject* pyTexture = reinterpret_cast<PyTextureObject*>(textureObj);
    // TODO (7DRL day 2, item 4.) use shared_ptr / PyTextureObject on UIGrid
    //IndexTexture* texture = pyTexture->data.get();
    
    // Initialize UIGrid
    //self->data = new UIGrid(grid_x, grid_y, texture, sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    self->data = std::make_shared<UIGrid>(grid_x, grid_y, pyTexture->data, 
            sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    return 0; // Success
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_grid_size(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_position(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getPosition().x, box.getPosition().y);
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGrid_set_position(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Position must be a tuple of two floats");
        return -1;
    }
    self->data->box.setPosition(x, y);
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_size(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getSize().x, box.getSize().y);
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGrid_set_size(PyUIGridObject* self, PyObject* value, void* closure) {
    float w, h;
    if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->box.setSize(sf::Vector2f(w, h));
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_center(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ff)", self->data->center_x, self->data->center_y);
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGrid_set_center(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->center_x = x;
    self->data->center_y = y;
    return 0;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_float_member(PyUIGridObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0) // x
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1) // y
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2) // w
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3) // h
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4) // center_x
        return PyFloat_FromDouble(self->data->center_x);
    else if (member_ptr == 5) // center_y
        return PyFloat_FromDouble(self->data->center_y);
    else if (member_ptr == 6) // zoom
        return PyFloat_FromDouble(self->data->zoom);
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

//TODO: add this method to class scope; move implementation to .cpp file
static int PyUIGrid_set_float_member(PyUIGridObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be a floating point number.");
        return -1;
    }
    if (member_ptr == 0) // x
        self->data->box.setPosition(val, self->data->box.getPosition().y);
    else if (member_ptr == 1) // y
        self->data->box.setPosition(self->data->box.getPosition().x, val);
    else if (member_ptr == 2) // w
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
    else if (member_ptr == 3) // h
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
    else if (member_ptr == 4) // center_x
        self->data->center_x = val;
    else if (member_ptr == 5) // center_y
        self->data->center_y = val;
    else if (member_ptr == 6) // zoom
        self->data->zoom = val;
    return 0;
}
// TODO (7DRL Day 2, item 5.) return Texture object
/*
static PyObject* PyUIGrid_get_texture(PyUIGridObject* self, void* closure) {
    Py_INCREF(self->texture);
    return self->texture;
}
*/
//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_get_texture(PyUIGridObject* self, void* closure) {
        //return self->data->getTexture()->pyObject();
        PyTextureObject* obj = (PyTextureObject*)((&PyTextureType)->tp_alloc(&PyTextureType, 0));
        obj->data = self->data->getTexture();
        return (PyObject*)obj;
}

//TODO: add this method to class scope; move implementation to .cpp file
static PyObject* PyUIGrid_at(PyUIGridObject* self, PyObject* o)
{
    int x, y;
    if (!PyArg_ParseTuple(o, "ii", &x, &y)) {
        PyErr_SetString(PyExc_TypeError, "UIGrid.at requires two integer arguments: (x, y)");
        return NULL;
    }
    if (x < 0 || x >= self->data->grid_x) {
        PyErr_SetString(PyExc_ValueError, "x value out of range (0, Grid.grid_y)");
        return NULL;
    }
    if (y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_ValueError, "y value out of range (0, Grid.grid_y)");
        return NULL;
    }

    PyUIGridPointObject* obj = (PyUIGridPointObject*)((&PyUIGridPointType)->tp_alloc(&PyUIGridPointType, 0));
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->points[x + self->data->grid_x * y]);
    obj->grid = self->data;
    return (PyObject*)obj;
}

//TODO: add this static array to class scope; move implementation to .cpp file
static PyMethodDef PyUIGrid_methods[] = {
    {"at", (PyCFunction)PyUIGrid_at, METH_O},
    {NULL, NULL, 0, NULL}
};

static PyObject* PyUIGrid_get_children(PyUIGridObject* self, void* closure); // forward declare

static PyGetSetDef PyUIGrid_getsetters[] = {

    // TODO - refactor into get_vector_member with field identifier values `(void*)n`
    {"grid_size", (getter)PyUIGrid_get_grid_size, NULL, "Grid dimensions (grid_x, grid_y)", NULL},
    {"position", (getter)PyUIGrid_get_position, (setter)PyUIGrid_set_position, "Position of the grid (x, y)", NULL},
    {"size", (getter)PyUIGrid_get_size, (setter)PyUIGrid_set_size, "Size of the grid (width, height)", NULL},
    {"center", (getter)PyUIGrid_get_center, (setter)PyUIGrid_set_center, "Grid coordinate at the center of the Grid's view (pan)", NULL},

    {"entities", (getter)PyUIGrid_get_children, NULL, "EntityCollection of entities on this grid", NULL},

    {"x", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "top-left corner X-coordinate", (void*)0},
    {"y", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "top-left corner Y-coordinate", (void*)1},
    {"w", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "visible widget width", (void*)2},
    {"h", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "visible widget height", (void*)3},
    {"center_x", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "center of the view X-coordinate", (void*)4},
    {"center_y", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "center of the view Y-coordinate", (void*)5},
    {"zoom", (getter)PyUIGrid_get_float_member, (setter)PyUIGrid_set_float_member, "zoom factor for displaying the Grid", (void*)6},

    {"click", (getter)PyUIDrawable_get_click, (setter)PyUIDrawable_set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UIGRID},

    {"texture", (getter)PyUIGrid_get_texture, NULL, "Texture of the grid", NULL}, //TODO 7DRL-day2-item5
    {NULL}  /* Sentinel */
};


/* // TODO standard pointer would need deleted, but I opted for a shared pointer. tp_dealloc currently not even defined in the PyTypeObject
static void PyUIGrid_dealloc(PyUIGridObject* self) {
    delete self->data; // Clean up the allocated UIGrid object
    Py_TYPE(self)->tp_free((PyObject*)self);
}
*/

    static PyTypeObject PyUIGridType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Grid",
        .tp_basicsize = sizeof(PyUIGridObject),
        .tp_itemsize = 0,
        //.tp_dealloc = (destructor)[](PyObject* self)
        //{
        //    PyUIGridObject* obj = (PyUIGridObject*)self;
        //    obj->data.reset();
        //    Py_TYPE(self)->tp_free(self);
        //},
        //TODO - PyUIGrid REPR def:
        // .tp_repr = (reprfunc)PyUIGrid_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        .tp_methods = PyUIGrid_methods,
        //.tp_members = PyUIGrid_members,
        .tp_getset = PyUIGrid_getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUIGrid_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIGridObject* self = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIGrid>();
            return (PyObject*)self;
        }
    };

    typedef struct {
        PyObject_HEAD
        std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
        int index;
        int start_size;
    } PyUIEntityCollectionIterObject;

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static int PyUIEntityCollectionIter_init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollectionIter_next(PyUIEntityCollectionIterObject* self)
    {
        if (self->data->size() != self->start_size)
        {
            PyErr_SetString(PyExc_RuntimeError, "collection changed size during iteration");
            return NULL;
        }

        if (self->index > self->start_size - 1)
        {
            PyErr_SetNone(PyExc_StopIteration);
            return NULL;
        }
        self->index++;
        auto vec = self->data.get();
        if (!vec)
        {
            PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
            return NULL;
        }
        // Advance list iterator since Entities are not stored in a vector (if this code even worked)
        // vectors only: //auto target = (*vec)[self->index-1];
        //auto l_front = (*vec).begin();
        //std::advance(l_front, self->index-1);

        // TODO build PyObject* of the correct UIDrawable subclass to return
        //return py_instance(target);
        return NULL;
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollectionIter_repr(PyUIEntityCollectionIterObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
        else {
            ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    static PyTypeObject PyUIEntityCollectionIterType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.UICollectionIter",
        .tp_basicsize = sizeof(PyUIEntityCollectionIterObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionIterObject* obj = (PyUIEntityCollectionIterObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUIEntityCollectionIter_repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for a collection of UI objects"),
        .tp_iternext = (iternextfunc)PyUIEntityCollectionIter_next,
        //.tp_getset = PyUIEntityCollection_getset,
        .tp_init = (initproc)PyUIEntityCollectionIter_init, // just raise an exception
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };


    typedef struct {
        PyObject_HEAD
        std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
        std::shared_ptr<UIGrid> grid;
    } PyUIEntityCollectionObject;

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static Py_ssize_t PyUIEntityCollection_len(PyUIEntityCollectionObject* self) {
        return self->data->size();
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollection_getitem(PyUIEntityCollectionObject* self, Py_ssize_t index) {
        // build a Python version of item at self->data[index]
        //  Copy pasted::
        auto vec = self->data.get();
        if (!vec)
        {
            PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
            return NULL;
        }
        while (index < 0) index += self->data->size();
        if (index > self->data->size() - 1)
        {
            PyErr_SetString(PyExc_IndexError, "EntityCollection index out of range");
            return NULL;
        }
        auto l_begin = (*vec).begin();
        std::advance(l_begin, index);
        auto target = *l_begin; //auto target = (*vec)[index];
        //RET_PY_INSTANCE(target);
        // construct and return an entity object that points directly into the UIGrid's entity vector
        PyUIEntityObject* o = (PyUIEntityObject*)((&PyUIEntityType)->tp_alloc(&PyUIEntityType, 0));
        auto p = std::static_pointer_cast<UIEntity>(target);
        o->data = p;
        return (PyObject*)o;
    return NULL;


    }

    //TODO: add this static array to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PySequenceMethods PyUIEntityCollection_sqmethods = {
        .sq_length = (lenfunc)PyUIEntityCollection_len,
        .sq_item = (ssizeargfunc)PyUIEntityCollection_getitem,
        //.sq_item_by_index = PyUIEntityCollection_getitem
        //.sq_slice - return a subset of the iterable
        //.sq_ass_item - called when `o[x] = y` is executed (x is any object type)
        //.sq_ass_slice - cool; no thanks, for now
        //.sq_contains - called when `x in o` is executed
        //.sq_ass_item_by_index - called when `o[x] = y` is executed (x is explictly an integer)
    };

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollection_append(PyUIEntityCollectionObject* self, PyObject* o)
    {
        // if not UIDrawable subclass, reject it
        // self->data->push_back( c++ object inside o );

        // this would be a great use case for .tp_base
        if (!PyObject_IsInstance(o, (PyObject*)&PyUIEntityType))
        {
            PyErr_SetString(PyExc_TypeError, "Only Entity objects can be added to EntityCollection");
            return NULL;
        }
        PyUIEntityObject* entity = (PyUIEntityObject*)o;
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;

        Py_INCREF(Py_None);
        return Py_None;
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollection_remove(PyUIEntityCollectionObject* self, PyObject* o)
    {
        if (!PyLong_Check(o))
        {
            PyErr_SetString(PyExc_TypeError, "UICollection.remove requires an integer index to remove");
            return NULL;
        }
        long index = PyLong_AsLong(o);
        if (index >= self->data->size())
        {
            PyErr_SetString(PyExc_ValueError, "Index out of range");
            return NULL;
        }
        else if (index < 0)
        {
            PyErr_SetString(PyExc_NotImplementedError, "reverse indexing is not implemented.");
            return NULL;
        }

        // release the shared pointer at correct part of the list
        self->data->erase(std::next(self->data->begin(), index));
        Py_INCREF(Py_None);
        return Py_None;
    }

    //TODO: add this static array to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyMethodDef PyUIEntityCollection_methods[] = {
        {"append", (PyCFunction)PyUIEntityCollection_append, METH_O},
        //{"extend", (PyCFunction)PyUIEntityCollection_extend, METH_O}, // TODO
        {"remove", (PyCFunction)PyUIEntityCollection_remove, METH_O},
        {NULL, NULL, 0, NULL}
    };

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollection_repr(PyUIEntityCollectionObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<UICollection (invalid internal object)>";
        else {
            ss << "<UICollection (" << self->data->size() << " child objects)>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static int PyUIEntityCollection_init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

    //TODO: add this method to class scope; move implementation to .cpp file; EntityCollection may need a larger refactor soon
    static PyObject* PyUIEntityCollection_iter(PyUIEntityCollectionObject* self)
    {
        PyUIEntityCollectionIterObject* iterObj;
        iterObj = (PyUIEntityCollectionIterObject*)PyUIEntityCollectionIterType.tp_alloc(&PyUIEntityCollectionIterType, 0);
        if (iterObj == NULL) {
            return NULL;  // Failed to allocate memory for the iterator object
        }

        iterObj->data = self->data;
        iterObj->index = 0;
        iterObj->start_size = self->data->size();

        return (PyObject*)iterObj;
    }
    static PyTypeObject PyUIEntityCollectionType = {
        //PyVarObject_/HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.EntityCollection",
        .tp_basicsize = sizeof(PyUIEntityCollectionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIEntityCollectionObject* obj = (PyUIEntityCollectionObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUIEntityCollection_repr,
        .tp_as_sequence = &PyUIEntityCollection_sqmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterable, indexable collection of Entities"),
        .tp_iter = (getiterfunc)PyUIEntityCollection_iter,
        .tp_methods = PyUIEntityCollection_methods, // append, remove
        //.tp_getset = PyUIEntityCollection_getset,
        .tp_init = (initproc)PyUIEntityCollection_init, // just raise an exception
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            // Does PyUIEntityCollectionType need __new__ if it's not supposed to be instantiable by the user?
            // Should I just raise an exception? Or is the uninitialized shared_ptr enough of a blocker?
            PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

    //TODO: add this method to class scope; move implementation to .cpp file
    // Grid's get_children def must follow the EntityCollection def
    static PyObject* PyUIGrid_get_children(PyUIGridObject* self, void* closure)
    {
        // create PyUICollection instance pointing to self->data->children
        PyUIEntityCollectionObject* o = (PyUIEntityCollectionObject*)PyUIEntityCollectionType.tp_alloc(&PyUIEntityCollectionType, 0);
        if (o) {
            o->data = self->data->entities; // todone. / BUGFIX - entities isn't a shared pointer on UIGrid, what to do? -- I made it a sp<list<sp<UIEntity>>>
            o->grid = self->data;
        }
        return (PyObject*)o;
    }


}
