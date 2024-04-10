#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyColor.h"
#include "PyVector.h"
#include "UIDrawable.h"
#include "UIBase.h"

//class UIFrame;
//
//typedef struct {
//    PyObject_HEAD
//    std::shared_ptr<UIFrame> data;
//} PyUIFrameObject;

class UIFrame: public UIDrawable
{
public:
    UIFrame(float, float, float, float);
    UIFrame();
    ~UIFrame();
    sf::RectangleShape box;
    float outline;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    void render(sf::Vector2f) override final;
    void move(sf::Vector2f);
    PyObjectsEnum derived_type() override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;

    static PyObject* get_children(PyUIFrameObject* self, void* closure);
};

namespace mcrfpydef {
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUIFrame_get_float_member(PyUIFrameObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyFloat_FromDouble(self->data->box.getPosition().x);
        else if (member_ptr == 1)
            return PyFloat_FromDouble(self->data->box.getPosition().y);
        else if (member_ptr == 2)
            return PyFloat_FromDouble(self->data->box.getSize().x);
        else if (member_ptr == 3)
            return PyFloat_FromDouble(self->data->box.getSize().y);
        else if (member_ptr == 4)
            return PyFloat_FromDouble(self->data->box.getOutlineThickness());
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUIFrame_set_float_member(PyUIFrameObject* self, PyObject* value, void* closure)
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
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        if (member_ptr == 0) //x
            self->data->box.setPosition(val, self->data->box.getPosition().y);
        else if (member_ptr == 1) //y
            self->data->box.setPosition(self->data->box.getPosition().x, val);
        else if (member_ptr == 2) //w
            self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
        else if (member_ptr == 3) //h
            self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
        else if (member_ptr == 4) //outline
            self->data->box.setOutlineThickness(val);
        return 0;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUIFrame_get_color_member(PyUIFrameObject* self, void* closure)
    {
        // validate closure (should be impossible to be wrong, but it's thorough)
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr != 0 && member_ptr != 1)
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
        PyTypeObject* colorType = &PyColorType;
        PyObject* pyColor = colorType->tp_alloc(colorType, 0);
        if (pyColor == NULL)
        {
            std::cout << "failure to allocate mcrfpy.Color / PyColorType" << std::endl;
            return NULL;
        }
        PyColorObject* pyColorObj = reinterpret_cast<PyColorObject*>(pyColor);

        // fetch correct member data
        sf::Color color;
        if (member_ptr == 0)
        {
            color = self->data->box.getFillColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
        }
        else if (member_ptr == 1)
        {
            color = self->data->box.getOutlineColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
        }
        
        return PyColor(color).pyObject();
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUIFrame_set_color_member(PyUIFrameObject* self, PyObject* value, void* closure)
    {
        //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
        auto member_ptr = reinterpret_cast<long>(closure);
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            sf::Color c = ((PyColorObject*)value)->data;
            r = c.r; g = c.g; b = c.b; a = c.a;
        }
        else if (!PyTuple_Check(value) || PyTuple_Size(value) < 3 || PyTuple_Size(value) > 4)
        {
            // reject non-Color, non-tuple value
            PyErr_SetString(PyExc_TypeError, "Value must be a tuple of 3 or 4 integers or an mcrfpy.Color object.");
            return -1;
        }
        else // get value from tuples
        {
            r = PyLong_AsLong(PyTuple_GetItem(value, 0));
            g = PyLong_AsLong(PyTuple_GetItem(value, 1));
            b = PyLong_AsLong(PyTuple_GetItem(value, 2));
            a = 255;

            if (PyTuple_Size(value) == 4)
            {
                a = PyLong_AsLong(PyTuple_GetItem(value, 3));
            }
        }

        if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255)
        {
            PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255.");
            return -1;
        }

        if (member_ptr == 0)
        {
            self->data->box.setFillColor(sf::Color(r, g, b, a));
        }
        else if (member_ptr == 1)
        {
            self->data->box.setOutlineColor(sf::Color(r, g, b, a));
        }
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return -1;
        }

        return 0;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    //static PyObject* PyUIFrame_get_children(PyUIFrameObject*, void*); // forward declaration until UICollection is defined
    // implementation after the PyUICollectionType definition

    //TODO: add this static array to class scope; move implementation to .cpp file
    static PyGetSetDef PyUIFrame_getsetters[] = {
        {"x", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        {"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
        {"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
        {"outline", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "Thickness of the border",   (void*)4},
        {"fill_color", (getter)PyUIFrame_get_color_member, (setter)PyUIFrame_set_color_member, "Fill color of the rectangle", (void*)0},
        {"outline_color", (getter)PyUIFrame_get_color_member, (setter)PyUIFrame_set_color_member, "Outline color of the rectangle", (void*)1},
        {"children", (getter)UIFrame::get_children, NULL, "UICollection of objects on top of this one", NULL},
        {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UIFRAME},
        {NULL}
    };
    
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUIFrame_repr(PyUIFrameObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<Frame (invalid internal object)>";
        else {
            auto box = self->data->box;
            auto fc = box.getFillColor();
            auto oc = box.getOutlineColor();
            ss << "<Frame (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", x=" << 
                box.getSize().x << ", w=" << box.getSize().y << ", " <<
                "outline=" << box.getOutlineThickness() << ", " << 
                "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", " << (int)fc.b << ", " << (int)fc.a <<"), " <<
                "outline_color=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
                self->data->children->size() << " child objects" <<
                ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUIFrame_init(PyUIFrameObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", "w", "h", "fill_color", "outline_color", "outline", nullptr }; 
        float x = 0.0f, y = 0.0f, w = 0.0f, h=0.0f, outline=0.0f;
        PyObject* fill_color = 0;
        PyObject* outline_color = 0;
    
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "ffff|OOf", const_cast<char**>(keywords), &x, &y, &w, &h, &fill_color, &outline_color, &outline))
        {
            return -1;
        }
    
        self->data->box.setPosition(sf::Vector2f(x, y));
        self->data->box.setSize(sf::Vector2f(w, h));
        self->data->box.setOutlineThickness(outline);
        // getsetter abuse because I haven't standardized Color object parsing (TODO)
        int err_val = 0;
        if (fill_color && fill_color != Py_None) err_val = PyUIFrame_set_color_member(self, fill_color, (void*)0);
        else self->data->box.setFillColor(sf::Color(0,0,0,255));
        if (err_val) return err_val;
        if (outline_color && outline_color != Py_None) err_val = PyUIFrame_set_color_member(self, outline_color, (void*)1);
        else self->data->box.setOutlineColor(sf::Color(128,128,128,255));
        if (err_val) return err_val;
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
}
