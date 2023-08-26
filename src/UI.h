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
    sf::RectangleShape box;
    std::vector<UIDrawable*> children;
    void render(sf::Vector2f) override final;
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
        float w, h;
        if (!PyArg_ParseTuple(args, "ff", &w, &h)) return (PyObject*)-1;
        self->box.setSize(sf::Vector2f(w, h));
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
        //.tp_base = NULL,
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
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_init = (initproc)PyUIFrame_init,
        .tp_new = PyUIFrame_new, //PyType_GenericNew ?
    };
         
    // module
    /*
    static PyModuleDef ui_module = {
        PyModuleDef_HEAD_INIT,
        .m_name = "ui",
        .m_size = -1,
    };
    PyMODINIT_FUNC PyInit_my_module(void) {
        PyObject* module = PyModule_Create(&my_module);
        if (module == NULL) {
            return NULL;
        }
    
        if (PyType_Ready(&MyType_Type) < 0) {
            return NULL;
        }
    
        Py_INCREF(&MyType_Type);
        PyModule_AddObject(module, "UIFrame", (PyObject*)&MyType_Type);
        return module;
    }
    */
    
    // Point class example
    
    class Point
{
public:
    float x, y;
    float magnitude() {
        return std::sqrt(x*x + y*y);
    }
};



static PyObject* PyPoint_new(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    Point* self;
    self = (Point*)type->tp_alloc(type, 0);
    if (self != nullptr)
    {   
        self->x = 0.0f;
        self->y = 0.0f;
    }
    return (PyObject*)self;
}


// Method to initialize the Point object
static int PyPoint_init(Point* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = { "x", "y", nullptr };
    float x = 0.0f, y = 0.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ff", const_cast<char**>(keywords), &x, &y))
    {
        return -1;
    }

    self->x = x;
    self->y = y;

    return 0;
}

// Method to calculate the magnitude of the Point
static PyObject* PyPoint_magnitude(Point* self)
{
    float mag = self->magnitude();
    return PyFloat_FromDouble(mag);
}

static PyMethodDef PyPoint_methods[] = {
    {"magnitude", (PyCFunction)PyPoint_magnitude, METH_NOARGS,
        "Vector length, or distance from origin."},
    {NULL, NULL, 0, NULL}
};

static PyMemberDef PyPoint_members[] = {
    {"x", T_FLOAT, offsetof(Point, x), 0},
    {"y", T_FLOAT, offsetof(Point, y), 0},
    {NULL}
};


static PyTypeObject PyPointType = {
    .tp_name = "mcrfpy.Point",
    .tp_basicsize = sizeof(Point),
    //.tp_itemsize = 0,
    //.tp_dealloc = NULL,
    //.tp_repr = NULL,
    //.tp_hash = NULL,
    //.tp_iter
    //.tp_iternext
    .tp_flags = Py_TPFLAGS_DEFAULT,
    //.tp_doc = PyDoc_STR("Custom point object. (x, y)"),
    //.tp_methods = PyPoint_methods,
    //.tp_members = PyPoint_members,
    //.tp_init = (initproc)PyPoint_init,
    //.tp_new = PyPoint_new, //PyType_GenericNew ?
};

/*
static PyModuleDef PyPointModule = {
    PyModuleDef_HEAD_INIT,
    .m_name = "point",
    .m_doc = "Custom point module.",
    .m_size = -1,
    //.m_methods = PyPoint_methods,
};
*/
         
}