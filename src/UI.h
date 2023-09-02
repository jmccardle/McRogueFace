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
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> children;
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

    static PyObject* PyUIFrame_get_children(PyUIFrameObject* self, void* closure)
    {
        // create PyUICollection instance pointing to self->data->children
        return NULL;
    }

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

        if (self->index > self->start_size)
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
        auto target = vec[self->index-1];
        // TODO build PyObject* of the correct UIDrawable subclass to return
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
		if (index >= self->data->size())
		{
			// set exception text
			return NULL;
		}
		// build a Python version of item at self->data[index]
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
	}

	static PyObject* PyUICollection_remove(PyUICollectionObject* self, PyObject* o)
	{
		// if (!PyLong_Check(o)) { //exception text; return -1; }
		// long index = PyLong_AsLong(o);
		// if (index >= self->data->size()) { //exception text; return -1; }
		// release the shared pointer at self->data[index];
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




} // namespace mcrfpydef
