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

class UIFrame: public UIDrawable
{
public:
    UIFrame(float, float, float, float);
    UIFrame();
    //sf::RectangleShape box;
    
    //Simulate RectangleShape
    sf::Color fillColor, outlineColor;
    float x, y, w, h, outline;
    std::vector<UIDrawable*> children;
    void render(sf::Vector2f) override final;
    void move(sf::Vector2f);
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

namespace mcrfpydef {
    
    // Color Definitions
    // struct, members, new, set_member, PyTypeObject
    typedef struct {
        PyObject_HEAD
        sf::Color color;
    } PyColorObject;
    
    static PyMemberDef PyColor_members[]
    {
        {"r", T_BYTE, offsetof(PyColorObject, color.r), 0},
        {"g", T_BYTE, offsetof(PyColorObject, color.g), 0},
        {"b", T_BYTE, offsetof(PyColorObject, color.b), 0},
        {"a", T_BYTE, offsetof(PyColorObject, color.a), 0},
        {NULL}
    };
    
    static PyObject* PyColor_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
    {
        PyColorObject* self = (PyColorObject*)type->tp_alloc(type, 0);
        if (self != NULL)
        {
            self->color.r = 0;
            self->color.g = 0;
            self->color.b = 0;
            self->color.a = 255;
        }
        return (PyObject*) self;
    }
    
    static PyObject* PyColor_get_member(PyColorObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == offsetof(PyColorObject, color.r))
            return PyLong_FromLong(self->color.r);
        else if (member_ptr == offsetof(PyColorObject, color.g))
            return PyLong_FromLong(self->color.g);
        else if (member_ptr == offsetof(PyColorObject, color.b))
            return PyLong_FromLong(self->color.b);
        else if (member_ptr == offsetof(PyColorObject, color.a))
            return PyLong_FromLong(self->color.a);
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
            if (member_ptr == offsetof(PyColorObject, color.r))
                self->color.r = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == offsetof(PyColorObject, color.g))
                self->color.g = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == offsetof(PyColorObject, color.b))
                self->color.b = static_cast<sf::Uint8>(int_val);
            else if (member_ptr == offsetof(PyColorObject, color.a))
                self->color.a = static_cast<sf::Uint8>(int_val);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        return 0;
    }
    
    static PyGetSetDef PyColor_getsetters[] = {
        {"r", (getter)PyColor_get_member, (setter)PyColor_set_member, "Red component", (void*)offsetof(PyColorObject, color.r)},
        {"g", (getter)PyColor_get_member, (setter)PyColor_set_member, "Green component", (void*)offsetof(PyColorObject, color.g)},
        {"b", (getter)PyColor_get_member, (setter)PyColor_set_member, "Blue component", (void*)offsetof(PyColorObject, color.b)},
        {"a", (getter)PyColor_get_member, (setter)PyColor_set_member, "Alpha component", (void*)offsetof(PyColorObject, color.a)},
        {NULL}
    };
    
    static PyTypeObject PyColorType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Color",
        .tp_basicsize = sizeof(PyColorObject),
        .tp_itemsize = 0,
        //.tp_dealloc = [](PyObject* obj) { Py_TYPE(obj)->tp_free(obj); },
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
        .tp_new = PyColor_new, //PyType_GenericNew ?
    };
    

    // UIFrame Definitions
    // new, init, repr, set_size, methods, members, PyTypeObject
    
    static PyObject* PyUIFrame_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
    {
        std::cout << "New called\n";
        UIFrame* self;
        self = (UIFrame*)type->tp_alloc(type, 0);
        if (self != nullptr)
        {   
        }
        return (PyObject*)self;
    }
    
    static int PyUIFrame_init(UIFrame* self, PyObject* args, PyObject* kwds)
    {
        std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", nullptr }; // TODO: keywords and other python objects to configure box (sf::RectangleShape)
        float x = 0.0f, y = 0.0f;
    
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(keywords), &x, &y))
        {
            return -1;
        }
    
        //self->x = x;
        //self->y = y;
    
        return 0;
    }
    
    static PyObject* PyUIFrame_repr(UIFrame* self)
    {
        std::ostringstream ss;
        ss << "<UIFrame ()>";
        
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }
   
    static PyObject* PyUIFrame_setSize(UIFrame* self, PyObject* args)
    {
        //float w, h;
        if (!PyArg_ParseTuple(args, "ff", &self->w, &self->h)) return (PyObject*)-1;
        //self->box.setSize(sf::Vector2f(w, h));
        Py_INCREF(Py_None);
        //return PyFloat_FromDouble(mag);
        return Py_None;
    }
         
    static PyMethodDef PyUIFrame_methods[] = {
        {"set_size", (PyCFunction)PyUIFrame_setSize, METH_VARARGS,
            "Set the width and height of the UIFrame's visible box"},
        {NULL, NULL, 0, NULL}
    };
    
    /*
    static PyMemberDef PyUIFrame_members[] = {
        {"box", T_OBJECT, offsetof(UIFrame, box), 0},
        {NULL}
    };
    */
      
    static PyTypeObject PyUIFrameType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.UIFrame",
        .tp_basicsize = sizeof(UIFrame),
        .tp_itemsize = 0,
        .tp_dealloc = [](PyObject* obj) { Py_TYPE(obj)->tp_free(obj); },
        //.tp_repr = (reprfunc)PyUIFrame_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Custom UIFrame object"),
        .tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUIFrame_init,
        .tp_new = PyUIFrame_new, //PyType_GenericNew ?
    };
         
         
}
