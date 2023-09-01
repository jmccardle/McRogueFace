#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"

class UIDrawable
{
public:
    UIDrawable* parent;
    void render();
    virtual void render(sf::Vector2f) = 0;
    //virtual sf::Rect<int> aabb(); // not sure I care about this yet
    //virtual sf::Vector2i position();
    bool handle_event(/* ??? click, scroll, keystroke*/);
    std::string action;
};

//Python object types & forward declarations
/*
typedef struct {
    PyObject_HEAD
    sf::Color color;
} PyColorObject;
*/

typedef struct {
    PyObject_HEAD
    std::shared_ptr<sf::Color> data;
} PyColorObject;

class UIFrame: public UIDrawable
{
public:
    UIFrame(float, float, float, float);
    UIFrame();
    ~UIFrame();
    sf::RectangleShape box;

    //Simulate RectangleShape
    float x, y, w, h, outline;
    std::vector<std::shared_ptr<UIDrawable>> children;
    void render(sf::Vector2f) override final;
    void move(sf::Vector2f);
    
    /*
    sf::Color fillColor(); // getter
    void fillColor(sf::Color c); // C++ setter
    void fillColor(PyColorObject* pyColor); // Python setter
    
    sf::Color outlineColor(); // getter
    void outlineColor(sf::Color c); // C++ setter
    void outlineColor(PyColorObject* pyColor); // Python setter
    */
    
private:
    //std::shared_ptr<sf::Color> fillColor, outlineColor;
    /*
    sf::Color *_fillColor, *_outlineColor;
    PyColorObject *pyFillColor, *pyOutlineColor;
    */
};

class UICaption: public UIDrawable
{
public:
    sf::Text text;
    void render(sf::Vector2f) override final;
};

class UISprite: public UIDrawable
{
public:
    void render(sf::Vector2f) override final;
    int texture_index, sprite_index;
    float scale;
    sf::Sprite sprite;
};

/*
template<typename T>
struct CPythonSharedObject {
    PyObject_HEAD
    std::shared_ptr<T> data;
};

typedef CPythonSharedObject<UIFrame> PyUIFrameObject;
*/

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIFrame> data;
} PyUIFrameObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UICaption> data;
} PyUICaptionObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UISprite> data;
} PyUISpriteObject;

namespace mcrfpydef {
    
    // Color Definitions
    // struct, members, new, set_member, PyTypeObject

    /* for reference: the structs to implement
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<sf::Color> data;
    } PyColorObject;
    
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<UIFrame> data;
    } PyUIFrameObject;
    
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<UICaption> data;
    } PyUICaptionObject;
    
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<UISprite> data;
    } PyUISpriteObject;
    */
    
    static PyObject* PyColor_get_member(PyColorObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyLong_FromLong(self->data->r);
        else if (member_ptr == 1)
            return PyLong_FromLong(self->data->g);
        else if (member_ptr == 2)
            return PyLong_FromLong(self->data->b);
        else if (member_ptr == 3)
            return PyLong_FromLong(self->data->a);
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }
    
    static int PyColor_set_member(PyColorObject* self, PyObject* value, void* closure)
    {
        if (PyLong_Check(value))
        {
            long int_val = PyLong_AsLong(value);
            if (int_val < 0)
                int_val = 0;
            else if (int_val > 255)
                int_val = 255;
            auto member_ptr = reinterpret_cast<long>(closure);
            if (member_ptr == 0)
                self->data->r = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 1)
                self->data->g = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 2)
                self->data->b = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 3)
                self->data->a = static_cast<sf::Uint8>(int_val);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        return 0;
    }
    
    static PyGetSetDef PyColor_getsetters[] = {
        {"r", (getter)PyColor_get_member, (setter)PyColor_set_member, "Red component",   (void*)0},
        {"g", (getter)PyColor_get_member, (setter)PyColor_set_member, "Green component", (void*)1},
        {"b", (getter)PyColor_get_member, (setter)PyColor_set_member, "Blue component",  (void*)2},
        {"a", (getter)PyColor_get_member, (setter)PyColor_set_member, "Alpha component", (void*)3},
        {NULL}
    };

    
     static PyTypeObject PyColorType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Color",
        .tp_basicsize = sizeof(PyColorObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyColorObject* obj = (PyColorObject*)self;
            obj->data.reset(); 
            Py_TYPE(self)->tp_free(self); 
        },
        //.tp_repr = (reprfunc)PyUIFrame_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Color object (RGBA)"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyColor_members,
        .tp_getset = PyColor_getsetters,
        //.tp_base = NULL,
        //.tp_init = (initproc)PyUIFrame_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        { 
            PyColorObject* self = (PyColorObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<sf::Color>();
            return (PyObject*)self;
        }
    };

    /*
     *
     * Begin template generation for PyUIFrameType
     *
     */

    static PyObject* PyUIFrame_get_member(PyUIFrameObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyLong_FromLong(self->data->box.getPosition().x);
        else if (member_ptr == 1)
            return PyLong_FromLong(self->data->box.getPosition().y);
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }

    static int PyUIFrame_set_member(PyUIFrameObject* self, PyObject* value, void* closure)
    {
        if (PyLong_Check(value))
        {
            /*
            long int_val = PyLong_AsLong(value);
            if (int_val < 0)
                int_val = 0;
            else if (int_val > 255)
                int_val = 255;
            auto member_ptr = reinterpret_cast<long>(closure);
            if (member_ptr == 0)
                self->data->r = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 1)
                self->data->g = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 2)
                self->data->b = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == 3)
                self->data->a = static_cast<sf::Uint8>(int_val);
            */
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        return 0;
    }

    static PyGetSetDef PyUIFrame_getsetters[] = {
        {"x", (getter)PyUIFrame_get_member, (setter)PyUIFrame_set_member, "member desc",   (void*)0},
        {"y", (getter)PyUIFrame_get_member, (setter)PyUIFrame_set_member, "member desc",   (void*)1},
        {NULL}
    };
    
    static PyObject* PyUIFrame_repr(PyUIFrameObject* self)
    {
        std::ostringstream ss;
        ss << "<UIFrame ()>";
        
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    static int PyUIFrame_init(PyUIFrameObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", nullptr }; 
        float x = 0.0f, y = 0.0f;
    
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(keywords), &x, &y))
        {
            return -1;
        }
    
        //self->data->x = x;
        //self->data->y = y;
    
        return 0;
    }

    static PyTypeObject PyUIFrameType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Frame",
        .tp_basicsize = sizeof(PyUIFrameObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUIFrameObject* obj = (PyUIFrameObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUIFrame_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = PyUIFrame_getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUIFrame_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUIFrameObject* self = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UIFrame>();
            return (PyObject*)self;
        }
    };

    /*
     *
     * End auto-generated PyUIFrameType generation
     *
     */


} // namespace mcrfpydef
