#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"

enum PyObjectsEnum
{
    UIFRAME = 1,
    UICAPTION,
    UISPRITE,
    UIGRID
};

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
    virtual PyObjectsEnum derived_type() = 0;
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
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    void render(sf::Vector2f) override final;
    void move(sf::Vector2f);
    
    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UIFrame;  };
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
    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UICaption;  };
};

class UISprite: public UIDrawable
{
public:
    UISprite();
    UISprite(IndexTexture*, int, float, float, float);
    UISprite(IndexTexture*, int, sf::Vector2f, float);
    void update();
    void render(sf::Vector2f) override final;
    int /*texture_index,*/ sprite_index;
    IndexTexture* itex;
    //float x, y, scale;
    sf::Sprite sprite;
    void setPosition(float, float);
    void setPosition(sf::Vector2f);
    void setScale(float);
    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UISprite;  };
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
    PyObject* font;
} PyUICaptionObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UISprite> data;
    PyObject* texture;
} PyUISpriteObject;


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
        PyUIFrameObject* o = (PyUIFrameObject*)((&PyUIFrameType)->tp_alloc(&PyUIFrameType, 0)); \
        if (o)                                          \
        {                                               \
            auto p = std::static_pointer_cast<UIFrame>(target); \
            o->data = p;                                \
            auto utarget = o->data;                     \
        }                                               \
        return (PyObject*)o;                            \
    }                                                   \
}                                                       \
}
// end macro definition

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

    /*
     *
     * Begin PyFontType defs
     *
     */

    typedef struct {
        PyObject_HEAD
        std::shared_ptr<sf::Font> data;
    } PyFontObject;

    static int PyFont_init(PyFontObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "filename", nullptr };
        char* filename;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &filename))
        {
            return -1;
        }
        self->data->loadFromFile((std::string)filename);
        return 0;
    }

     static PyTypeObject PyFontType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Font",
        .tp_basicsize = sizeof(PyFontObject),
        .tp_itemsize = 0,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Font Object"),
        .tp_init = (initproc)PyFont_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyFontObject* self = (PyFontObject*)type->tp_alloc(type, 0);
            self->data = std::make_shared<sf::Font>();
            return (PyObject*)self;
        }
    };

    /*
     *
     * End PyFontType defs
     *
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
     * Begin template generation for PyUICaptionType
     *
     */

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

    static PyObject* PyUICaption_get_color_member(PyUICaptionObject* self, void* closure)
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
            color = self->data->text.getFillColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
        }
        else if (member_ptr == 1)
        {
            color = self->data->text.getOutlineColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
        }

        // initialize new mcrfpy.Color instance
        pyColorObj->data = std::make_shared<sf::Color>(color);
        
        return pyColor;
    }

    static int PyUICaption_set_color_member(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            // get value from mcrfpy.Color instance
            PyColorObject* color = reinterpret_cast<PyColorObject*>(value);
            r = color->data->r;
            g = color->data->g;
            b = color->data->b;
            a = color->data->a;
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

    static PyObject* PyUICaption_get_text(PyUICaptionObject* self, void* closure)
    {
        return PyUnicode_FromString("Test String, Please Ignore");
    }

    static int PyUICaption_set_text(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        // asdf
        return 0;
    }

    static PyGetSetDef PyUICaption_getsetters[] = {
        {"x", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        //{"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
        //{"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
        {"outline", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Thickness of the border",   (void*)4},
        {"fill_color", (getter)PyUICaption_get_color_member, (setter)PyUICaption_set_color_member, "Fill color of the text", (void*)0},
        {"outline_color", (getter)PyUICaption_get_color_member, (setter)PyUICaption_set_color_member, "Outline color of the text", (void*)1},
        //{"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
        {"text", (getter)PyUICaption_get_text, (setter)PyUICaption_set_text, "The text displayed", NULL},
        {"size", (getter)PyUICaption_get_float_member, (setter)PyUICaption_set_float_member, "Text size (integer) in points", (void*)5},
        {NULL}
    };

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
        //
        // Set Font
        //
        if (font != NULL && !PyObject_IsInstance(font, (PyObject*)&PyFontType)){
            PyErr_SetString(PyExc_TypeError, "font must be a mcrfpy.Font instance");
            return -1;
        } else if (font != NULL)
        {
            auto font_obj = (PyFontObject*)font;
            self->data->text.setFont(*font_obj->data);
            self->font = font;
            Py_INCREF(font);
        } else
        {
            // default font
            //self->data->text.setFont(Resources::game->getFont());
        }

        //
        // Set Color
        //
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

    /*
     *
     * End PyUICaptionType generation
     *
     */


    /*
     *
     * Begin template generation for PyUIFrameType
     *
     */

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
        
        // initialize new mcrfpy.Color instance
        pyColorObj->data = std::make_shared<sf::Color>(color);

        return pyColor;
    }

    static int PyUIFrame_set_color_member(PyUIFrameObject* self, PyObject* value, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            // get value from mcrfpy.Color instance
            PyColorObject* color = reinterpret_cast<PyColorObject*>(value);
            r = color->data->r;
            g = color->data->g;
            b = color->data->b;
            a = color->data->a;
            std::cout << "using color: " << r << " " << g << " " << b << " " << a << std::endl;
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

    static PyObject* PyUIFrame_get_children(PyUIFrameObject*, void*);
    // implementation after the PyUICollectionType definition

    static PyGetSetDef PyUIFrame_getsetters[] = {
        {"x", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        {"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
        {"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
        {"outline", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "Thickness of the border",   (void*)4},
        {"fill_color", (getter)PyUIFrame_get_color_member, (setter)PyUIFrame_set_color_member, "Fill color of the rectangle", (void*)0},
        {"outline_color", (getter)PyUIFrame_get_color_member, (setter)PyUIFrame_set_color_member, "Outline color of the rectangle", (void*)1},
        {"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
        {NULL}
    };
    
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
                "outlinecolor=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
                self->data->children->size() << " child objects" <<
                ")>";
        }
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
        self->data->box.setFillColor(sf::Color(0,0,0,255));
        self->data->box.setOutlineColor(sf::Color(128,128,128,255));
    
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

    /*
     *
     * Begin Python Class Instantiator (iterator helper)
     *
     */

    /* // definition can't go in the header file
    PyObject* py_instance(UIDrawable* obj)
    {

    }
    */

    /*
     *
     * End Python Class Instantitator (iterator helper)
     *
     */

    /*
     *
     * Begin PyTextureType defs
     *
     */

    typedef struct {
        PyObject_HEAD
        std::shared_ptr<IndexTexture> data;
    } PyTextureObject;

    static int PyTexture_init(PyTextureObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "filename", "grid_size", "grid_width", "grid_height", nullptr };
        char* filename;
        int grid_size, grid_width, grid_height;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "siii", const_cast<char**>(keywords), &filename, &grid_size, &grid_width, &grid_height))
        {
            return -1;
        }
        sf::Texture t = sf::Texture();
        t.loadFromFile((std::string)filename);
        self->data = std::make_shared<IndexTexture>(t, grid_size, grid_width, grid_height);
        return 0;
    }

     static PyTypeObject PyTextureType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Texture",
        .tp_basicsize = sizeof(PyTextureObject),
        .tp_itemsize = 0,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("SFML Texture Object"),
        .tp_init = (initproc)PyTexture_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyTextureObject* self = (PyTextureObject*)type->tp_alloc(type, 0);
            return (PyObject*)self;
        }
    };

    /*
     *
     * End PyTextureType defs
     *
     */

    /*
     *
     * Begin template generation for PyUISpriteType
     *
     */

    static PyObject* PyUISprite_get_float_member(PyUISpriteObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyFloat_FromDouble(self->data->sprite.getPosition().x);
        else if (member_ptr == 1)
            return PyFloat_FromDouble(self->data->sprite.getPosition().y);
        else if (member_ptr == 2)
            return PyFloat_FromDouble(self->data->sprite.getScale().x); // scale X and Y are identical, presently
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
    }


    static int PyUISprite_set_float_member(PyUISpriteObject* self, PyObject* value, void* closure)
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
        if (member_ptr == 0) //x
            self->data->sprite.setPosition(val, self->data->sprite.getPosition().y);
        else if (member_ptr == 1) //y
            self->data->sprite.setPosition(self->data->sprite.getPosition().x, val);
        else if (member_ptr == 2) // scale
            self->data->sprite.setScale(sf::Vector2f(val, val));
        return 0;
    }
    
    static PyObject* PyUISprite_get_int_member(PyUISpriteObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (true) {}
        else
        {
            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
            return nullptr;
        }
        
        return PyLong_FromDouble(self->data->sprite_index);
    }


    static int PyUISprite_set_int_member(PyUISpriteObject* self, PyObject* value, void* closure)
    {
        int val;
        auto member_ptr = reinterpret_cast<long>(closure);
        if (PyLong_Check(value))
        {
            val = PyLong_AsLong(value);
        }
        else
        {
            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
            return -1;
        }
        self->data->sprite_index = val;
        self->data->sprite.setTextureRect(self->data->itex->spriteCoordinates(val));
        return 0;
    }
    
    static PyObject* PyUISprite_get_texture(PyUISpriteObject* self, void* closure)
    {
        return NULL;
    }
    
    static int PyUISprite_set_texture(PyUISpriteObject* self, PyObject* value, void* closure)
    {
        return -1;
    }

    static PyGetSetDef PyUISprite_getsetters[] = {
        {"x", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "X coordinate of top-left corner",   (void*)0},
        {"y", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "Y coordinate of top-left corner",   (void*)1},
        {"scale", (getter)PyUISprite_get_float_member, (setter)PyUISprite_set_float_member, "Size factor",                   (void*)2},
        {"sprite_number", (getter)PyUISprite_get_int_member, (setter)PyUISprite_set_int_member, "Which sprite on the texture is shown", NULL},
        {"texture", (getter)PyUISprite_get_texture, (setter)PyUISprite_set_texture,     "Texture object",                    NULL},
        {NULL}
    };
    
    static PyObject* PyUISprite_repr(PyUISpriteObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<Sprite (invalid internal object)>";
        else {
            auto sprite = self->data->sprite;
            ss << "<Sprite (x=" << sprite.getPosition().x << ", y=" << sprite.getPosition().y << ", " <<
                "scale=" << sprite.getScale().x << ", " <<
                "sprite_number=" << self->data->sprite_index << ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

    static int PyUISprite_init(PyUISpriteObject* self, PyObject* args, PyObject* kwds)
    {
        //std::cout << "Init called\n";
        static const char* keywords[] = { "x", "y", "texture", "sprite_index", "scale", nullptr };
        float x = 0.0f, y = 0.0f, scale = 1.0f;
        int sprite_index;
        PyObject* texture;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOif",
            const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &scale))
        {
            return -1;
        }

        // check types for texture
        //
        // Set Texture
        //
        if (texture != NULL && !PyObject_IsInstance(texture, (PyObject*)&PyTextureType)){
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
            return -1;
        } else if (texture != NULL)
        {   
            self->texture = texture;
            Py_INCREF(texture);
        } else
        {
            // default tex?
        }
        auto pytexture = (PyTextureObject*)texture;
        self->data = std::make_shared<UISprite>(pytexture->data.get(), sprite_index, sf::Vector2f(x, y), scale);
        self->data->sprite.setPosition(sf::Vector2f(x, y));

        return 0;
    }
    
    static PyTypeObject PyUISpriteType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Sprite",
        .tp_basicsize = sizeof(PyUISpriteObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUISpriteObject* obj = (PyUISpriteObject*)self;
            // release reference to font object
            if (obj->texture) Py_DECREF(obj->texture);
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUISprite_repr,
        //.tp_hash = NULL,
        //.tp_iter
        //.tp_iternext
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("docstring"),
        //.tp_methods = PyUIFrame_methods,
        //.tp_members = PyUIFrame_members,
        .tp_getset = PyUISprite_getsetters,
        //.tp_base = NULL,
        .tp_init = (initproc)PyUISprite_init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyUISpriteObject* self = (PyUISpriteObject*)type->tp_alloc(type, 0);
            //if (self) self->data = std::make_shared<UICaption>();
            return (PyObject*)self;
        }
    }; 
    /*
     *
     * End template for PyUISpriteType
     *
     */

    /*
     *
     * Begin PyUICollectionIter defs
     *
     */
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
        int index;
        int start_size;
    } PyUICollectionIterObject;

    static int PyUICollectionIter_init(PyUICollectionIterObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

    static PyObject* PyUICollectionIter_next(PyUICollectionIterObject* self)
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
        auto target = (*vec)[self->index-1];
        // TODO build PyObject* of the correct UIDrawable subclass to return
        //return py_instance(target);
        return NULL;
    }

	static PyObject* PyUICollectionIter_repr(PyUICollectionIterObject* self)
	{
		std::ostringstream ss;
		if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
		else {
		    ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
		}
		std::string repr_str = ss.str();
		return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
	}

    static PyTypeObject PyUICollectionIterType = {
        //PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.UICollectionIter",
        .tp_basicsize = sizeof(PyUICollectionIterObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyUICollectionIterObject* obj = (PyUICollectionIterObject*)self;
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyUICollectionIter_repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for a collection of UI objects"),
        .tp_iternext = (iternextfunc)PyUICollectionIter_next,
        //.tp_getset = PyUICollection_getset,
        .tp_init = (initproc)PyUICollectionIter_init, // just raise an exception
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
            return NULL;
        }
    };

    /*
     *
     * End PyUICollectionIter defs
     *
     */


    /*
	 *
	 * Begin PyUICollection defs
	 *
	 */
	typedef struct {
		PyObject_HEAD
		std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
	} PyUICollectionObject;

	static Py_ssize_t PyUICollection_len(PyUICollectionObject* self) {
		return self->data->size();
	}

	static PyObject* PyUICollection_getitem(PyUICollectionObject* self, Py_ssize_t index) {
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
            PyErr_SetString(PyExc_IndexError, "UICollection index out of range");
            return NULL;
        }
        auto target = (*vec)[index];
        RET_PY_INSTANCE(target);

    // copy-pasted object determination & instantiation

    /*
    PyObject* newobj = NULL;
    std::cout << "Instantiating object\n";
    switch (target->derived_type())
    {
        case PyObjectsEnum::UIFRAME:
        {
            std::cout << "UIFRAME case\n" << std::flush;
			PyUIFrameObject* o = (PyUIFrameObject*)((&PyUIFrameType)->tp_alloc(&PyUIFrameType, 0));
            if (o)
            {
                std::cout << "Casting data...\n" << std::flush;
                auto p = std::static_pointer_cast<UIFrame>(target);
                std::cout << "casted. Assigning...\n" << std::flush;
                //o->data = std::make_shared<UIFrame>();

                o->data = p;
                //std::cout << "assigned.\n" << std::flush;
                auto utarget = o->data; //(UIFrame*)target.get();
                std::cout << "Loaded data into object. " << utarget->box.getPosition().x << " " << utarget->box.getPosition().y << " " <<
                    utarget->box.getSize().x << " " << utarget->box.getSize().y << std::endl;
            }
            else
            {
                std::cout << "Allocation failed.\n" << std::flush;
            }
            return (PyObject*)o;
		}
	}
    */






    return NULL;


	}

	static PySequenceMethods PyUICollection_sqmethods = {
		.sq_length = (lenfunc)PyUICollection_len,
		.sq_item = (ssizeargfunc)PyUICollection_getitem,
		//.sq_item_by_index = PyUICollection_getitem
		//.sq_slice - return a subset of the iterable
		//.sq_ass_item - called when `o[x] = y` is executed (x is any object type)
		//.sq_ass_slice - cool; no thanks, for now
		//.sq_contains - called when `x in o` is executed
		//.sq_ass_item_by_index - called when `o[x] = y` is executed (x is explictly an integer)
	};

	static PyObject* PyUICollection_append(PyUICollectionObject* self, PyObject* o)
	{
		// if not UIDrawable subclass, reject it
		// self->data->push_back( c++ object inside o );

        // this would be a great use case for .tp_base
        if (!PyObject_IsInstance(o, (PyObject*)&PyUIFrameType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUISpriteType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUICaptionType) // &&
            //!PyObject_IsInstance(o, (PyObject*)&PyUIGridType)
            )
        {
            PyErr_SetString(PyExc_TypeError, "Only Frame, Caption, Sprite, and Grid objects can be added to UICollection");
            return NULL;
        }

        if (PyObject_IsInstance(o, (PyObject*)&PyUIFrameType))
        {
            PyUIFrameObject* frame = (PyUIFrameObject*)o;
            self->data->push_back(frame->data);
        }
        if (PyObject_IsInstance(o, (PyObject*)&PyUICaptionType))
        {
            PyUICaptionObject* caption = (PyUICaptionObject*)o;
            self->data->push_back(caption->data);
        }
        if (PyObject_IsInstance(o, (PyObject*)&PyUISpriteType))
        {
            PyUISpriteObject* sprite = (PyUISpriteObject*)o;
            self->data->push_back(sprite->data);
        }

        Py_INCREF(Py_None);
        return Py_None;
	}

	static PyObject* PyUICollection_remove(PyUICollectionObject* self, PyObject* o)
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

		// release the shared pointer at self->data[index];
        self->data->erase(self->data->begin() + index);
        Py_INCREF(Py_None);
        return Py_None;
	}

	static PyMethodDef PyUICollection_methods[] = {
		{"append", (PyCFunction)PyUICollection_append, METH_O},
        //{"extend", (PyCFunction)PyUICollection_extend, METH_O}, // TODO
		{"remove", (PyCFunction)PyUICollection_remove, METH_O},
		{NULL, NULL, 0, NULL}
	};

	static PyObject* PyUICollection_repr(PyUICollectionObject* self)
	{
		std::ostringstream ss;
		if (!self->data) ss << "<UICollection (invalid internal object)>";
		else {
		    ss << "<UICollection (" << self->data->size() << " child objects)>";
		}
		std::string repr_str = ss.str();
		return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
	}

    static int PyUICollection_init(PyUICollectionObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

    static PyObject* PyUICollection_iter(PyUICollectionObject* self)
    {
        PyUICollectionIterObject* iterObj;
        iterObj = (PyUICollectionIterObject*)PyUICollectionIterType.tp_alloc(&PyUICollectionIterType, 0);
        if (iterObj == NULL) {
            return NULL;  // Failed to allocate memory for the iterator object
        }

        iterObj->data = self->data;
        iterObj->index = 0;
        iterObj->start_size = self->data->size();

        return (PyObject*)iterObj;
    }

    /*
    static PyGetSetDef PyUICollection_getsetters[] = {
        {NULL}
    };
    */

	static PyTypeObject PyUICollectionType = {
		//PyVarObject_HEAD_INIT(NULL, 0)
		.tp_name = "mcrfpy.UICollection",
		.tp_basicsize = sizeof(PyUICollectionObject),
		.tp_itemsize = 0,
		.tp_dealloc = (destructor)[](PyObject* self)
		{
		    PyUICollectionObject* obj = (PyUICollectionObject*)self;
		    obj->data.reset();
		    Py_TYPE(self)->tp_free(self);
		},
		.tp_repr = (reprfunc)PyUICollection_repr,
		.tp_as_sequence = &PyUICollection_sqmethods,
		.tp_flags = Py_TPFLAGS_DEFAULT,
		.tp_doc = PyDoc_STR("Iterable, indexable collection of UI objects"),
        .tp_iter = (getiterfunc)PyUICollection_iter,
		.tp_methods = PyUICollection_methods, // append, remove
        //.tp_getset = PyUICollection_getset,
		.tp_init = (initproc)PyUICollection_init, // just raise an exception
		.tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
		{
            // Does PyUICollectionType need __new__ if it's not supposed to be instantiable by the user? 
            // Should I just raise an exception? Or is the uninitialized shared_ptr enough of a blocker?
            PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
		    return NULL;
		}
	};
	/*
	 *
	 * End PyUICollection defs
	 *
	 */


    static PyObject* PyUIFrame_get_children(PyUIFrameObject* self, void* closure)
    {
        // create PyUICollection instance pointing to self->data->children
        PyUICollectionObject* o = (PyUICollectionObject*)PyUICollectionType.tp_alloc(&PyUICollectionType, 0);
        if (o)
            o->data = self->data->children;
        return (PyObject*)o;
    }




} // namespace mcrfpydef
