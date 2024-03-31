#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#define ui_h

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
//#include "PyLinkedColor.h"

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
    //UIDrawable* parent;
    void render();
    virtual void render(sf::Vector2f) = 0;
    //virtual sf::Rect<int> aabb(); // not sure I care about this yet
    //virtual sf::Vector2i position();
    //bool handle_event(/* ??? click, scroll, keystroke*/);
    //std::string action;
    virtual PyObjectsEnum derived_type() = 0;

    // Mouse input handling - callable object, methods to find event's destination
    //PyObject* click_callable;
    std::unique_ptr<PyClickCallable> click_callable;
    virtual UIDrawable* click_at(sf::Vector2f point) = 0;
    void click_register(PyObject*);
    void click_unregister();

    UIDrawable();
};

//Python object types & forward declarations
/*
typedef struct {
    PyObject_HEAD
    sf::Color color;
} PyColorObject;
*/

/* // Moved to PyColor.h
typedef struct {
    PyObject_HEAD
    std::shared_ptr<sf::Color> data;
} PyColorObject;
*/

class UIFrame: public UIDrawable
{
public:
    UIFrame(float, float, float, float);
    UIFrame();
    ~UIFrame();
    sf::RectangleShape box;
    // todone: why does UIFrame have x,y,w,h AND a box? Which one should be used for bounds checks? (floats removed)

    //Simulate RectangleShape
    //float x, y, w, h, 
    float outline;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
    void render(sf::Vector2f) override final;
    void move(sf::Vector2f);
    
    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UIFrame;  };
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
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
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
};

class UISprite: public UIDrawable
{
private:
    int sprite_index;
    sf::Sprite sprite;
protected:
    std::shared_ptr<PyTexture> ptex;
public:
    UISprite();
    //UISprite(IndexTexture*, int, float, float, float);
    //UISprite(IndexTexture*, int, sf::Vector2f, float);
    UISprite(std::shared_ptr<PyTexture>, int, sf::Vector2f, float);
    void update();
    void render(sf::Vector2f) override final;
    virtual UIDrawable* click_at(sf::Vector2f point) override final;
    
    // 7DRL hack - TODO apply RenderTexture concept to all UIDrawables (via `sf::RenderTarget`)
    void render(sf::Vector2f, sf::RenderTexture&);
    //IndexTexture* itex;
    //sf::Vector2f pos;
    //float scale;
    //void setPosition(float, float);
    void setPosition(sf::Vector2f);
    sf::Vector2f getPosition();
    void setScale(sf::Vector2f);
    sf::Vector2f getScale();
    void setSpriteIndex(int);
    int getSpriteIndex();

    void setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index=-1);
    std::shared_ptr<PyTexture> getTexture();

    PyObjectsEnum derived_type() override final; // { return PyObjectsEnum::UISprite;  };
};

// UIGridPoint - revised grid data for each point
class UIGridPoint
{
public:
    sf::Color color, color_overlay;
    bool walkable, transparent;
    int tilesprite, tile_overlay, uisprite;
    UIGridPoint();
};

// UIGridPointState - entity-specific info for each cell
class UIGridPointState
{
public:
    bool visible, discovered;
};

class UIGrid;

// TODO: make UIEntity a drawable(?) Maybe just rely on UISprite/UIGrid to
// somehow properly render the thing? Poorly designed interface
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
    //PyObject* texture;
} PyUISpriteObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
} PyUICollectionObject;

typedef struct {
    PyObject_HEAD
    UIGridPoint* data;
    std::shared_ptr<UIGrid> grid;
} PyUIGridPointObject;

typedef struct {
    PyObject_HEAD
    UIGridPointState* data;
    std::shared_ptr<UIGrid> grid;
    std::shared_ptr<UIEntity> entity;
} PyUIGridPointStateObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIEntity> data;
    //PyObject* texture;
} PyUIEntityObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> data;
    //PyObject* texture;
} PyUIGridObject;

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

//
// Clickable / Callable Object Assignment
//
static PyObject* PyUIDrawable_get_click(PyUIGridObject* self, void* closure) {
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
}

static int PyUIDrawable_set_click(PyUIGridObject* self, PyObject* value, void* closure) {
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

// End Clickability implementation


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


//    static PyObject* PyColor_get_member(PyColorObject* self, void* closure)
//    {
//        auto member_ptr = reinterpret_cast<long>(closure);
//        if (member_ptr == 0)
//            return PyLong_FromLong(self->data->r);
//        else if (member_ptr == 1)
//            return PyLong_FromLong(self->data->g);
//        else if (member_ptr == 2)
//            return PyLong_FromLong(self->data->b);
//        else if (member_ptr == 3)
//            return PyLong_FromLong(self->data->a);
//        else
//        {
//            PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
//            return nullptr;
//        }
//    }
//    
//    static int PyColor_set_member(PyColorObject* self, PyObject* value, void* closure)
//    {
//        if (PyLong_Check(value))
//        {
//            long int_val = PyLong_AsLong(value);
//            if (int_val < 0)
//                int_val = 0;
//            else if (int_val > 255)
//                int_val = 255;
//            auto member_ptr = reinterpret_cast<long>(closure);
//            if (member_ptr == 0)
//                self->data->r = static_cast<sf::Uint8>(int_val);
//            else if (member_ptr == 1)
//                self->data->g = static_cast<sf::Uint8>(int_val);
//            else if (member_ptr == 2)
//                self->data->b = static_cast<sf::Uint8>(int_val);
//            else if (member_ptr == 3)
//                self->data->a = static_cast<sf::Uint8>(int_val);
//        }
//        else
//        {
//            PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
//            return -1;
//        }
//        return 0;
//    }
//    
//    static PyGetSetDef PyColor_getsetters[] = {
//        {"r", (getter)PyColor_get_member, (setter)PyColor_set_member, "Red component",   (void*)0},
//        {"g", (getter)PyColor_get_member, (setter)PyColor_set_member, "Green component", (void*)1},
//        {"b", (getter)PyColor_get_member, (setter)PyColor_set_member, "Blue component",  (void*)2},
//        {"a", (getter)PyColor_get_member, (setter)PyColor_set_member, "Alpha component", (void*)3},
//        {NULL}
//    };
//
//    
//     static PyTypeObject PyColorType = {
//        //PyVarObject_HEAD_INIT(NULL, 0)
//        .tp_name = "mcrfpy.Color",
//        .tp_basicsize = sizeof(PyColorObject),
//        .tp_itemsize = 0,
//        .tp_dealloc = (destructor)[](PyObject* self)
//        {
//            PyColorObject* obj = (PyColorObject*)self;
//            obj->data.reset(); 
//            Py_TYPE(self)->tp_free(self); 
//        },
//        //.tp_repr = (reprfunc)PyUIFrame_repr,
//        //.tp_hash = NULL,
//        //.tp_iter
//        //.tp_iternext
//        .tp_flags = Py_TPFLAGS_DEFAULT,
//        .tp_doc = PyDoc_STR("SFML Color object (RGBA)"),
//        //.tp_methods = PyUIFrame_methods,
//        //.tp_members = PyColor_members,
//        .tp_getset = PyColor_getsetters,
//        //.tp_base = NULL,
//        //.tp_init = (initproc)PyUIFrame_init,
//        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
//        { 
//            PyColorObject* self = (PyColorObject*)type->tp_alloc(type, 0);
//            if (self) self->data = std::make_shared<sf::Color>();
//            return (PyObject*)self;
//        }
//    };

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

        // TODO: manually calling tp_alloc to create a PyColorObject seems like an antipattern
        /*
        PyTypeObject* colorType = &PyLinkedColorType;
        PyObject* pyColor = colorType->tp_alloc(colorLinkedType, 0);
        if (pyColor == NULL)
        {
            std::cout << "failure to allocate mcrfpy.LinkedColor / PyLinkedColorType" << std::endl;
            return NULL;
        }
        PyColorObject* pyColorObj = reinterpret_cast<PyLinkedColorObject*>(pyColor);
        */

        // fetch correct member data
        sf::Color color;
        //sf::Color (*cgetter)();
        //void (*csetter)(sf::Color);
        //std::function<void(sf::Color)> csetter;
        //std::function<sf::Color()> cgetter;
        if (member_ptr == 0)
        {
            color = self->data->text.getFillColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
            //csetter = &self->data->text.setFillColor;
            //cgetter = &self->data->text.getFillColor;
            //csetter = [s = self->data](sf::Color c){s->text.setFillColor(c);};
            //cgetter = [s = self->data](){return s->text.getFillColor();};
        }
        else if (member_ptr == 1)
        {
            color = self->data->text.getOutlineColor();
            //return Py_BuildValue("(iii)", color.r, color.g, color.b);
            //csetter = &self->data->text.setOutlineColor;
            //cgetter = &self->data->text.getOutlineColor;
            //csetter = [s = self->data](sf::Color c){s->text.setOutlineColor(c);};
            //cgetter = [s = self->data](){return s->text.getOutlineColor();};
        }

        // initialize new mcrfpy.Color instance
        //pyColorObj->data = std::make_shared<sf::Color>(color);
        //PyLinkedColor::fromPy(pyColorObj).set(color);
        //auto linkedcolor = PyLinkedColor(csetter, cgetter, self->data, member_ptr);
        //linkedcolor.set(color); // don't need to set a linked color!
        
        //return pyColor;
        return PyColor(color).pyObject();
    }

    static int PyUICaption_set_color_member(PyUICaptionObject* self, PyObject* value, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            // get value from mcrfpy.Color instance
            /*
            PyColorObject* color = reinterpret_cast<PyColorObject*>(value);
            r = color->data->r;
            g = color->data->g;
            b = color->data->b;
            a = color->data->a;
            */
            //std::cout << "Build LinkedColor" << std::endl;
            //auto lc  = PyLinkedColor::fromPy(value);
            auto c = ((PyColorObject*)value)->data;
            //std::cout << "Fetch value" << std::endl;
            //auto c = lc.get();
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

    static PyObject* PyUICaption_get_text(PyUICaptionObject* self, void* closure)
    {
        Resources::caption_buffer = self->data->text.getString();
        return PyUnicode_FromString(Resources::caption_buffer.c_str());
    }

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
        {"click", (getter)PyUIDrawable_get_click, (setter)PyUIDrawable_set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UICAPTION},
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
        //pyColorObj->data = std::make_shared<sf::Color>(color);
        //PyColor::fromPy(pyColorObj).set(color);

        // TODO - supposed to return Linked
        return PyColor(color).pyObject();
    }

    static int PyUIFrame_set_color_member(PyUIFrameObject* self, PyObject* value, void* closure)
    {
        //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
        auto member_ptr = reinterpret_cast<long>(closure);
        int r, g, b, a;
        if (PyObject_IsInstance(value, (PyObject*)&PyColorType))
        {
            // get value from mcrfpy.Color instance
            /*
            PyColorObject* color = reinterpret_cast<PyColorObject*>(value);
            r = color->data->r;
            g = color->data->g;
            b = color->data->b;
            a = color->data->a;
            std::cout << "using color: " << r << " " << g << " " << b << " " << a << std::endl;
            */
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
        {"click", (getter)PyUIDrawable_get_click, (setter)PyUIDrawable_set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UIFRAME},
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
                "outline_color=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
                self->data->children->size() << " child objects" <<
                ")>";
        }
        std::string repr_str = ss.str();
        return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
    }

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
    
        //self->data->x = x;
        //self->data->y = y;
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
     * Begin template generation for PyUISpriteType
     *
     */

    static PyObject* PyUISprite_get_float_member(PyUISpriteObject* self, void* closure)
    {
        auto member_ptr = reinterpret_cast<long>(closure);
        if (member_ptr == 0)
            return PyFloat_FromDouble(self->data->getPosition().x);
        else if (member_ptr == 1)
            return PyFloat_FromDouble(self->data->getPosition().y);
        else if (member_ptr == 2)
            return PyFloat_FromDouble(self->data->getScale().x); // scale X and Y are identical, presently
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
            self->data->setPosition(sf::Vector2f(val, self->data->getPosition().y));
        else if (member_ptr == 1) //y
            self->data->setPosition(sf::Vector2f(self->data->getPosition().x, val));
        else if (member_ptr == 2) // scale
            self->data->setScale(sf::Vector2f(val, val));
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
        
        return PyLong_FromDouble(self->data->getSpriteIndex());
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
        //self->data->sprite_index = val;
        //self->data->sprite.setTextureRect(self->data->itex->spriteCoordinates(val));
        self->data->setSpriteIndex(val);
        return 0;
    }
    
    static PyObject* PyUISprite_get_texture(PyUISpriteObject* self, void* closure)
    {
        return self->data->getTexture()->pyObject();
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
        {"click", (getter)PyUIDrawable_get_click, (setter)PyUIDrawable_set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UISPRITE},
        {NULL}
    };
    
    static PyObject* PyUISprite_repr(PyUISpriteObject* self)
    {
        std::ostringstream ss;
        if (!self->data) ss << "<Sprite (invalid internal object)>";
        else {
            //auto sprite = self->data->sprite;
            ss << "<Sprite (x=" << self->data->getPosition().x << ", y=" << self->data->getPosition().y << ", " <<
                "scale=" << self->data->getScale().x << ", " <<
                "sprite_number=" << self->data->getSpriteIndex() << ")>";
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
        } /*else if (texture != NULL) // to be removed: UIObjects don't manage texture references
        {   
            self->texture = texture;
            Py_INCREF(texture);
        } else
        {
            // default tex?
        }*/
        auto pytexture = (PyTextureObject*)texture;
        self->data = std::make_shared<UISprite>(pytexture->data, sprite_index, sf::Vector2f(x, y), scale);
        self->data->setPosition(sf::Vector2f(x, y));

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
            //if (obj->texture) Py_DECREF(obj->texture);
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
     * PyUIGridPoint defs
     *
     */

// TODO: question: are sfColor_to_PyObject and PyObject_to_sfColor duplicitive? How does UIFrame get/set colors?

// Utility function to convert sf::Color to PyObject*
static PyObject* sfColor_to_PyObject(sf::Color color) {
    return Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
}

// Utility function to convert PyObject* to sf::Color
static sf::Color PyObject_to_sfColor(PyObject* obj) {
    int r, g, b, a = 255; // Default alpha to fully opaque if not specified
    if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
        return sf::Color(); // Return default color on parse error
    }
    return sf::Color(r, g, b, a);
}

static PyObject* PyUIGridPoint_get_color(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // color
        return sfColor_to_PyObject(self->data->color);
    } else { // color_overlay
        return sfColor_to_PyObject(self->data->color_overlay);
    }
}

static int PyUIGridPoint_set_color(PyUIGridPointObject* self, PyObject* value, void* closure) {
    sf::Color color = PyObject_to_sfColor(value);
    if (reinterpret_cast<long>(closure) == 0) { // color
        self->data->color = color;
    } else { // color_overlay
        self->data->color_overlay = color;
    }
    return 0;
}

static PyObject* PyUIGridPoint_get_bool_member(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // walkable
        return PyBool_FromLong(self->data->walkable);
    } else { // transparent
        return PyBool_FromLong(self->data->transparent);
    }
}

static int PyUIGridPoint_set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    if (value == Py_True) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = true;
        } else { // transparent
            self->data->transparent = true;
        }
    } else if (value == Py_False) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = false;
        } else { // transparent
            self->data->transparent = false;
        }
    } else {
        PyErr_SetString(PyExc_ValueError, "Expected a boolean value");
        return -1;
    }
    return 0;
}

static PyObject* PyUIGridPoint_get_int_member(PyUIGridPointObject* self, void* closure) {
    switch(reinterpret_cast<long>(closure)) {
        case 0: return PyLong_FromLong(self->data->tilesprite);
        case 1: return PyLong_FromLong(self->data->tile_overlay);
        case 2: return PyLong_FromLong(self->data->uisprite);
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return nullptr;
    }
}

static int PyUIGridPoint_set_int_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;

    switch(reinterpret_cast<long>(closure)) {
        case 0: self->data->tilesprite = val; break;
        case 1: self->data->tile_overlay = val; break;
        case 2: self->data->uisprite = val; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return -1;
    }
    return 0;
}

static PyGetSetDef PyUIGridPoint_getsetters[] = {
    {"color", (getter)PyUIGridPoint_get_color, (setter)PyUIGridPoint_set_color, "GridPoint color", (void*)0},
    {"color_overlay", (getter)PyUIGridPoint_get_color, (setter)PyUIGridPoint_set_color, "GridPoint color overlay", (void*)1},
    {"walkable", (getter)PyUIGridPoint_get_bool_member, (setter)PyUIGridPoint_set_bool_member, "Is the GridPoint walkable", (void*)0},
    {"transparent", (getter)PyUIGridPoint_get_bool_member, (setter)PyUIGridPoint_set_bool_member, "Is the GridPoint transparent", (void*)1},
    {"tilesprite", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "Tile sprite index", (void*)0},
    {"tile_overlay", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "Tile overlay sprite index", (void*)1},
    {"uisprite", (getter)PyUIGridPoint_get_int_member, (setter)PyUIGridPoint_set_int_member, "UI sprite index", (void*)2},
    {NULL}  /* Sentinel */
};

static PyTypeObject PyUIGridPointType = {
    //PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.GridPoint",
    .tp_basicsize = sizeof(PyUIGridPointObject),
    .tp_itemsize = 0,
    // Methods omitted for brevity
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "UIGridPoint objects",
    .tp_getset = PyUIGridPoint_getsetters,
    //.tp_init = (initproc)PyUIGridPoint_init, // TODO Define the init function
    .tp_new = PyType_GenericNew,
};

    /*
     *
     * end PyUIGridPoint defs
     *
     */



    /*
     *
     * PyUIGridPointState defs
     *
     */

static PyObject* PyUIGridPointState_get_bool_member(PyUIGridPointStateObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // visible
        return PyBool_FromLong(self->data->visible);
    } else { // discovered
        return PyBool_FromLong(self->data->discovered);
    }
}

static int PyUIGridPointState_set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure) {
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a boolean");
        return -1;
    }

    int truthValue = PyObject_IsTrue(value);
    if (truthValue < 0) {
        return -1; // PyObject_IsTrue returns -1 on error
    }

    if (reinterpret_cast<long>(closure) == 0) { // visible
        self->data->visible = truthValue;
    } else { // discovered
        self->data->discovered = truthValue;
    }

    return 0;
}

static PyGetSetDef PyUIGridPointState_getsetters[] = {
    {"visible", (getter)PyUIGridPointState_get_bool_member, (setter)PyUIGridPointState_set_bool_member, "Is the GridPointState visible", (void*)0},
    {"discovered", (getter)PyUIGridPointState_get_bool_member, (setter)PyUIGridPointState_set_bool_member, "Has the GridPointState been discovered", (void*)1},
    {NULL}  /* Sentinel */
};

static PyTypeObject PyUIGridPointStateType = {
    //PyVarObject_HEAD_INIT(NULL, 0)
    .tp_name = "mcrfpy.GridPointState",
    .tp_basicsize = sizeof(PyUIGridPointStateObject),
    .tp_itemsize = 0,
    // Methods omitted for brevity
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = "UIGridPointState objects", // TODO: Add PyUIGridPointState tp_init
    .tp_getset = PyUIGridPointState_getsetters,
    .tp_new = PyType_GenericNew,
};


    /*
     *
     * end PyUIGridPointState defs
     *
     */

    /*
     *
     * PyUIEntity defs
     *
     */

// TODO: sf::Vector2f convenience functions here might benefit from a PyVectorObject much like PyColorObject
// Utility function to convert sf::Vector2f to PyObject*
static PyObject* sfVector2f_to_PyObject(sf::Vector2f vector) {
    return Py_BuildValue("(ff)", vector.x, vector.y);
}

// Utility function to convert PyObject* to sf::Vector2f
static sf::Vector2f PyObject_to_sfVector2f(PyObject* obj) {
    float x, y;
    if (!PyArg_ParseTuple(obj, "ff", &x, &y)) {
        return sf::Vector2f(); // TODO / reconsider this default: Return default vector on parse error
    }
    return sf::Vector2f(x, y);
}

// Utility function to convert UIGridPointState to PyObject*
static PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state) {
    PyObject* obj = PyObject_New(PyObject, &PyUIGridPointStateType);
    if (!obj) return PyErr_NoMemory();

    // Assuming PyUIGridPointStateObject structure has a UIGridPointState* member called 'data'
    //((PyUIGridPointStateObject*)obj)->data = new UIGridPointState(state); // Copy constructor // wontimplement / feat - don't use new, get shared_ptr working

    return obj;
}

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

static PyObject* PyUIEntity_get_position(PyUIEntityObject* self, void* closure) {
    return sfVector2f_to_PyObject(self->data->position);
}

static int PyUIEntity_set_position(PyUIEntityObject* self, PyObject* value, void* closure) {
    self->data->position = PyObject_to_sfVector2f(value);
    return 0;
}

static PyObject* PyUIEntity_get_gridstate(PyUIEntityObject* self, void* closure) {
    // Assuming a function to convert std::vector<UIGridPointState> to PyObject* list
    return UIGridPointStateVector_to_PyList(self->data->gridstate);
}

static PyObject* PyUIEntity_get_spritenumber(PyUIEntityObject* self, void* closure) {
    return PyLong_FromDouble(self->data->sprite.getSpriteIndex());
}

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

static PyMethodDef PyUIEntity_methods[] = {
    {"at", (PyCFunction)PyUIEntity_at, METH_O},
    {NULL, NULL, 0, NULL}
};

// Define getters and setters
static PyGetSetDef PyUIEntity_getsetters[] = {
    {"position", (getter)PyUIEntity_get_position, (setter)PyUIEntity_set_position, "Entity position", NULL},
    {"gridstate", (getter)PyUIEntity_get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"sprite_number", (getter)PyUIEntity_get_spritenumber, (setter)PyUIEntity_set_spritenumber, "Sprite number (index) on the texture on the display", NULL},
    {NULL}  /* Sentinel */
};

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


    /*
     *
     * end PyUIEntity defs
     *
     */

    /*
     *
     * PyUIGrid defs
     *
     */

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

static PyObject* PyUIGrid_get_grid_size(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

static PyObject* PyUIGrid_get_position(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getPosition().x, box.getPosition().y);
}

static int PyUIGrid_set_position(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Position must be a tuple of two floats");
        return -1;
    }
    self->data->box.setPosition(x, y);
    return 0;
}

static PyObject* PyUIGrid_get_size(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getSize().x, box.getSize().y);
}

static int PyUIGrid_set_size(PyUIGridObject* self, PyObject* value, void* closure) {
    float w, h;
    if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->box.setSize(sf::Vector2f(w, h));
    return 0;
}

static PyObject* PyUIGrid_get_center(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ff)", self->data->center_x, self->data->center_y);
}

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
static PyObject* PyUIGrid_get_texture(PyUIGridObject* self, void* closure) {
        //return self->data->getTexture()->pyObject();
        PyTextureObject* obj = (PyTextureObject*)((&PyTextureType)->tp_alloc(&PyTextureType, 0));
        obj->data = self->data->getTexture();
        return (PyObject*)obj;
}

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


    /*
     *
     * end PyUIGrid defs
     *
     */

// PyUIEntity_init defined here because it depends on the PyUIGridType (to accept grid optional keyword argument)
static int PyUIEntity_init(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = { "x", "y", "texture", "sprite_index", "grid", nullptr };
    float x = 0.0f, y = 0.0f, scale = 1.0f;
    int sprite_index = -1;
    PyObject* texture = NULL;
    PyObject* grid = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ffOi|O",
        const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &grid))
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
    } /*else if (texture != NULL) // this section needs to go; texture isn't optional and isn't managed by the UI objects anymore
    {   
        self->texture = texture;
        Py_INCREF(texture);
    } else
    {
        // default tex?
    }*/

    if (grid != NULL && !PyObject_IsInstance(grid, (PyObject*)&PyUIGridType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }

    auto pytexture = (PyTextureObject*)texture;
    if (grid == NULL)
        self->data = std::make_shared<UIEntity>(); 
    else
        self->data = std::make_shared<UIEntity>(*((PyUIGridObject*)grid)->data);

    // TODO - PyTextureObjects and IndexTextures are a little bit of a mess with shared/unshared pointers
    self->data->sprite = UISprite(pytexture->data, sprite_index, sf::Vector2f(0,0), 1.0);
    self->data->position = sf::Vector2f(x, y);
    if (grid != NULL) {
        PyUIGridObject* pygrid = (PyUIGridObject*)grid;
        self->data->grid = pygrid->data;
        // todone - on creation of Entity with Grid assignment, also append it to the entity list
        pygrid->data->entities->push_back(self->data);
    }
    return 0;
}

/*
     *
     * Begin PyUIEntityCollectionIter defs
     *
     */
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
        int index;
        int start_size;
    } PyUIEntityCollectionIterObject;

    static int PyUIEntityCollectionIter_init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

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

    /*
     *
     * End PyUIEntityCollectionIter defs
     *
     */

/*
     *
     * Begin PyUIEntityCollection defs
     *
     */
    typedef struct {
        PyObject_HEAD
        std::shared_ptr<std::list<std::shared_ptr<UIEntity>>> data;
        std::shared_ptr<UIGrid> grid;
    } PyUIEntityCollectionObject;

    static Py_ssize_t PyUIEntityCollection_len(PyUIEntityCollectionObject* self) {
        return self->data->size();
    }

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

    static PyMethodDef PyUIEntityCollection_methods[] = {
        {"append", (PyCFunction)PyUIEntityCollection_append, METH_O},
        //{"extend", (PyCFunction)PyUIEntityCollection_extend, METH_O}, // TODO
        {"remove", (PyCFunction)PyUIEntityCollection_remove, METH_O},
        {NULL, NULL, 0, NULL}
    };

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

    static int PyUIEntityCollection_init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds)
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
        return -1;
    }

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

    /*
     *
     * End PyUIEntityCollection defs
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
            !PyObject_IsInstance(o, (PyObject*)&PyUICaptionType) &&
            !PyObject_IsInstance(o, (PyObject*)&PyUIGridType)
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
        if (PyObject_IsInstance(o, (PyObject*)&PyUIGridType))
        {
            PyUIGridObject* grid = (PyUIGridObject*)o;
            self->data->push_back(grid->data);
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
		//PyVarObject_/HEAD_INIT(NULL, 0)
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
