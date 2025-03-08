#include "UICaption.h"
#include "GameEngine.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

UIDrawable* UICaption::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if (text.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

void UICaption::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    text.move(offset);
    //Resources::game->getWindow().draw(text);
    target.draw(text);
    text.move(-offset);
}

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}

PyObject* UICaption::get_float_member(PyUICaptionObject* self, void* closure)
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

int UICaption::set_float_member(PyUICaptionObject* self, PyObject* value, void* closure)
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

PyObject* UICaption::get_vec_member(PyUICaptionObject* self, void* closure)
{
    return PyVector(self->data->text.getPosition()).pyObject();
}

int UICaption::set_vec_member(PyUICaptionObject* self, PyObject* value, void* closure)
{
    self->data->text.setPosition(PyVector::fromPy(value));
    return 0;
}

PyObject* UICaption::get_color_member(PyUICaptionObject* self, void* closure)
{
    // TODO: migrate this code to a switch statement - validate closure & return values in one tighter, more extensible structure

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

int UICaption::set_color_member(PyUICaptionObject* self, PyObject* value, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
    int r, g, b, a;
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color")  /*(PyObject*)&mcrfpydef::PyColorType)*/))
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


//TODO: evaluate use of Resources::caption_buffer... can't I do this with a std::string?
PyObject* UICaption::get_text(PyUICaptionObject* self, void* closure)
{
    Resources::caption_buffer = self->data->text.getString();
    return PyUnicode_FromString(Resources::caption_buffer.c_str());
}

int UICaption::set_text(PyUICaptionObject* self, PyObject* value, void* closure)
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

PyGetSetDef UICaption::getsetters[] = {
    {"x", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "X coordinate of top-left corner",   (void*)0},
    {"y", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "Y coordinate of top-left corner",   (void*)1},
    {"pos", (getter)UICaption::get_vec_member, (setter)UICaption::set_vec_member, "(x, y) vector", (void*)0},
    //{"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
    //{"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
    {"outline", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "Thickness of the border",   (void*)4},
    {"fill_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member, "Fill color of the text", (void*)0},
    {"outline_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member, "Outline color of the text", (void*)1},
    //{"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
    {"text", (getter)UICaption::get_text, (setter)UICaption::set_text, "The text displayed", NULL},
    {"size", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "Text size (integer) in points", (void*)5},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UICAPTION},
    {NULL}
};

PyObject* UICaption::repr(PyUICaptionObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Caption (invalid internal object)>";
    else {
        auto text = self->data->text;
        auto fc = text.getFillColor();
        auto oc = text.getOutlineColor();
        ss << "<Caption (x=" << text.getPosition().x << ", y=" << text.getPosition().y << ", " <<
            "text='" << (std::string)text.getString() << "', " <<
            "outline=" << text.getOutlineThickness() << ", " <<
            "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", " << (int)fc.b << ", " << (int)fc.a <<"), " <<
            "outline_color=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UICaption::init(PyUICaptionObject* self, PyObject* args, PyObject* kwds)
{
    using namespace mcrfpydef;
    // Constructor switch to Vector position
    //static const char* keywords[] = { "x", "y", "text", "font", "fill_color", "outline_color", "outline", nullptr };
    //float x = 0.0f, y = 0.0f, outline = 0.0f;
    static const char* keywords[] = { "pos", "text", "font", "fill_color", "outline_color", "outline", nullptr };
    PyObject* pos;
    float outline = 0.0f;
    char* text;
    PyObject* font=NULL, *fill_color=NULL, *outline_color=NULL;

    //if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffzOOOf",
    //    const_cast<char**>(keywords), &x, &y, &text, &font, &fill_color, &outline_color, &outline))
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|zOOOf",
        const_cast<char**>(keywords), &pos, &text, &font, &fill_color, &outline_color, &outline))
    {
        return -1;
    }
    
    PyVectorObject* pos_result = PyVector::from_arg(pos);
    if (!pos_result)
    {
        PyErr_SetString(PyExc_TypeError, "pos must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
        return -1;
    }
    self->data->text.setPosition(pos_result->data);
    // check types for font, fill_color, outline_color

    //std::cout << PyUnicode_AsUTF8(PyObject_Repr(font)) << std::endl;
    if (font != NULL && !PyObject_IsInstance(font, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Font")/*(PyObject*)&PyFontType)*/)){
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

    self->data->text.setString((std::string)text);
    self->data->text.setOutlineThickness(outline);
    if (fill_color) {
        auto fc = PyColor::from_arg(fill_color);
        if (!fc) {
            PyErr_SetString(PyExc_TypeError, "fill_color must be mcrfpy.Color or arguments to mcrfpy.Color.__init__");
            return -1;
        }
        self->data->text.setFillColor(PyColor::fromPy(fc));
        //Py_DECREF(fc);
    } else {
        self->data->text.setFillColor(sf::Color(0,0,0,255));
    }

    if (outline_color) {
        auto oc = PyColor::from_arg(outline_color);
        if (!oc) {
            PyErr_SetString(PyExc_TypeError, "outline_color must be mcrfpy.Color or arguments to mcrfpy.Color.__init__");
            return -1;
        }
        self->data->text.setOutlineColor(PyColor::fromPy(oc));
        //Py_DECREF(oc);
    } else {
        self->data->text.setOutlineColor(sf::Color(128,128,128,255));
    }

    return 0;
}

