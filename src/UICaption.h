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
#include "UIDrawable.h"

class UICaption: public UIDrawable
{
public:
    sf::Text text;
    void render(sf::Vector2f) override final;
    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UICaption;  };
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UICaption> data;
    PyObject* font;
} PyUICaptionObject;

namespace mcrfpydef {
    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICaption_get_float_member(PyUICaptionObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyFloat_FromDouble(self->data->text.getPosition().x);
        else if (member_ptr == 1)
            return PyFloat_FromDouble(self->data->text.getPosition().y);
        else if (member_ptr == 4)
            return PyFloat_FromDouble(self->data->text.getOutlineThickness());
        else if (member_ptr == 5)
            return PyLong_FromLong(self->data->text.getCharacterSize());
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICaption_set_float_member(PyUICaptionObject* self, PyObject* value, void* closure)
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
            self->data->text.setPosition(val, self->data->text.getPosition().y);
        else if (member_ptr == 1) //y
            self->data->text.setPosition(self->data->text.getPosition().x, val);
        else if (member_ptr == 4) //outline
            self->data->text.setOutlineThickness(val);
        else if (member_ptr == 5) // character size
            self->data->text.setCharacterSize(val);
        return 0;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICaption_get_vec_member(PyUICaptionObject* self, void* closure)
    {
        return PyVector(self->data->text.getPosition()).pyObject();
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICaption_set_vec_member(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        self->data->text.setPosition(PyVector::fromPy(value));
        return 0;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICaption_get_color_member(PyUICaptionObject* self, void* closure)
    {
        // validate closure (should be impossible to be wrong, but it's thorough)
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr != 0 && member_ptr != 1)
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }

        // TODO: manually calling tp_alloc to create a PyColorObject seems like an antipattern
        // fetch correct member data
        sf::Color color;

        if (member_ptr == 0)
        {
            color = self->data->text.getFillColor();
        }
        else if (member_ptr == 1)
        {
            color = self->data->text.getOutlineColor();
        }

        return PyColor(color).pyObject();
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICaption_set_color_member(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            // get value from mcrfpy.Color instance
            auto c = ((PyColorObject*)value)->data;
            r = c.r; g = c.g; b = c.b; a = c.a;
            std::cout << "got " << int(r) << ", " << int(g) << ", " << int(b) << ", " << int(a) << std::endl;
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
            self->data->text.setFillColor(sf::Color(r, g, b, a));
        }
        else if (member_ptr == 1)
        {
            self->data->text.setOutlineColor(sf::Color(r, g, b, a));
        }
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return -1;
        }

        return 0;
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICaption_get_text(PyUICaptionObject* self, void* closure)
    {
        Resources::caption_buffer = self->data->text.getString();
        return PyUnicode_FromString(Resources::caption_buffer.c_str());
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICaption_set_text(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        PyObject* s = PyObject_Str(value);
        PyObject * temp_bytes = PyUnicode_AsEncodedString(s, "UTF-8", "strict"); // Owned reference
        if (temp_bytes != NULL) {
            Resources::caption_buffer = PyBytes_AS_STRING(temp_bytes); // Borrowed pointer
            Py_DECREF(temp_bytes);
        }
        self->data->text.setString(Resources::caption_buffer);
        return 0;
    }

    //TODO: add this static array to class scope; move implementation to .cpp file
    static PyGetSetDef PyUICaption_getsetters[] = {
        {"x", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        {"pos", (getter)PyUICaption_get_vec_member, (setter)PyUICaption_set_vec_member, "(x, y) vector", (void*)0},
        //{"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
        //{"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
        {"outline", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Thickness of the border",   (void*)4},
        {"fill_color", (getter)PyUICaption_get_color_member, (setter)PyUICaption_set_color_member, "Fill color of the text", (void*)0},
        {"outline_color", (getter)PyUICaption_get_color_member, (setter)PyUICaption_set_color_member, "Outline color of the text", (void*)1},
        //{"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
        {"text", (getter)PyUICaption_get_text, (setter)PyUICaption_set_text, "The text displayed", NULL},
        {"size", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Text size (integer) in points", (void*)5},
        {"click", (getter)PyUIDrawable_get_click, (setter)PyUIDrawable_set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UICAPTION},
        {NULL}
    };

    //TODO: add this method to class scope; move implementation to .cpp file
    static PyObject* PyUICaption_repr(PyUICaptionObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<Frame (invalid internal object)>";
        else {
            auto text = self->data->text;
            auto fc = text.getFillColor();
            auto oc = text.getOutlineColor();
            ss << "<Caption (x=" << text.getPosition().x << ", y=" << text.getPosition().y << ", " <<
                "text='" << (std::string)text.getString() << "', " <<
                "outline=" << text.getOutlineThickness() << ", " <<
                "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", " << (int)fc.b << ", " << (int)fc.a <<"), " <<
                "outlinecolor=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
                ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    //TODO: add this method to class scope; move implementation to .cpp file
    static int PyUICaption_init(PyUICaptionObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", "text", "font", "fill_color", "outline_color", nullptr };
        float x = 0.0f, y = 0.0f;
        char* text;
        PyObject* font, fill_color, outline_color;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffzOOO", 
            const_cast<char**>(keywords), &x, &y, &text, &font, &fill_color, &outline_color))
        {
            return -1;
        }

        // check types for font, fill_color, outline_color

        std::cout << PyUnicode_AsUTF8(PyObject_Repr(font)) << std::endl;
        if (font != NULL && !PyObject_IsInstance(font, (PyObject*)&PyFontType)){
            PyErr_SetString(PyExc_TypeError, "font must be a mcrfpy.Font instance");
            return -1;
        } else if (font != NULL)
        {
            auto font_obj = (PyFontObject*)font;
            self->data->text.setFont(font_obj->data->font);
            self->font = font;
            Py_INCREF(font);
        } else
        {
            // default font
            //self->data->text.setFont(Resources::game->getFont());
        }

        self->data->text.setPosition(sf::Vector2f(x, y));
        self->data->text.setString((std::string)text);
        self->data->text.setFillColor(sf::Color(0,0,0,255));
        self->data->text.setOutlineColor(sf::Color(128,128,128,255));

        return 0;
    }

    static PyTypeObject PyUICaptionType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Caption",
        .tp_basicsize = sizeof(PyUICaptionObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUICaptionObject* obj = (PyUICaptionObject*)self;
            // release reference to font object
            if (obj->font) Py_DECREF(obj->font);
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUICaption_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = PyUICaption_getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUICaption_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUICaptionObject* self = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    };
}
