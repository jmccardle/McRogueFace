#include "UICaption.h"
#include "GameEngine.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"
#include <algorithm>

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
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int, "Z-order for rendering (lower values rendered first)", (void*)PyObjectsEnum::UICAPTION},
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
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Oz|OOOf",
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
    if (font != NULL && font != Py_None && !PyObject_IsInstance(font, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Font")/*(PyObject*)&PyFontType)*/)){
        PyErr_SetString(PyExc_TypeError, "font must be a mcrfpy.Font instance or None");
        return -1;
    } else if (font != NULL && font != Py_None)
    {
        auto font_obj = (PyFontObject*)font;
        self->data->text.setFont(font_obj->data->font);
        self->font = font;
        Py_INCREF(font);
    } else
    {
        // Use default font when None or not provided
        if (McRFPy_API::default_font) {
            self->data->text.setFont(McRFPy_API::default_font->font);
            // Store reference to default font
            PyObject* default_font_obj = PyObject_GetAttrString(McRFPy_API::mcrf_module, "default_font");
            if (default_font_obj) {
                self->font = default_font_obj;
                // Don't need to DECREF since we're storing it
            }
        }
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

// Property system implementation for animations
bool UICaption::setProperty(const std::string& name, float value) {
    if (name == "x") {
        text.setPosition(sf::Vector2f(value, text.getPosition().y));
        return true;
    }
    else if (name == "y") {
        text.setPosition(sf::Vector2f(text.getPosition().x, value));
        return true;
    }
    else if (name == "size") {
        text.setCharacterSize(static_cast<unsigned int>(value));
        return true;
    }
    else if (name == "outline") {
        text.setOutlineThickness(value);
        return true;
    }
    else if (name == "fill_color.r") {
        auto color = text.getFillColor();
        color.r = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setFillColor(color);
        return true;
    }
    else if (name == "fill_color.g") {
        auto color = text.getFillColor();
        color.g = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setFillColor(color);
        return true;
    }
    else if (name == "fill_color.b") {
        auto color = text.getFillColor();
        color.b = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setFillColor(color);
        return true;
    }
    else if (name == "fill_color.a") {
        auto color = text.getFillColor();
        color.a = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setFillColor(color);
        return true;
    }
    else if (name == "outline_color.r") {
        auto color = text.getOutlineColor();
        color.r = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setOutlineColor(color);
        return true;
    }
    else if (name == "outline_color.g") {
        auto color = text.getOutlineColor();
        color.g = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setOutlineColor(color);
        return true;
    }
    else if (name == "outline_color.b") {
        auto color = text.getOutlineColor();
        color.b = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setOutlineColor(color);
        return true;
    }
    else if (name == "outline_color.a") {
        auto color = text.getOutlineColor();
        color.a = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setOutlineColor(color);
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        return true;
    }
    return false;
}

bool UICaption::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        text.setFillColor(value);
        return true;
    }
    else if (name == "outline_color") {
        text.setOutlineColor(value);
        return true;
    }
    return false;
}

bool UICaption::setProperty(const std::string& name, const std::string& value) {
    if (name == "text") {
        text.setString(value);
        return true;
    }
    return false;
}

bool UICaption::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = text.getPosition().x;
        return true;
    }
    else if (name == "y") {
        value = text.getPosition().y;
        return true;
    }
    else if (name == "size") {
        value = static_cast<float>(text.getCharacterSize());
        return true;
    }
    else if (name == "outline") {
        value = text.getOutlineThickness();
        return true;
    }
    else if (name == "fill_color.r") {
        value = text.getFillColor().r;
        return true;
    }
    else if (name == "fill_color.g") {
        value = text.getFillColor().g;
        return true;
    }
    else if (name == "fill_color.b") {
        value = text.getFillColor().b;
        return true;
    }
    else if (name == "fill_color.a") {
        value = text.getFillColor().a;
        return true;
    }
    else if (name == "outline_color.r") {
        value = text.getOutlineColor().r;
        return true;
    }
    else if (name == "outline_color.g") {
        value = text.getOutlineColor().g;
        return true;
    }
    else if (name == "outline_color.b") {
        value = text.getOutlineColor().b;
        return true;
    }
    else if (name == "outline_color.a") {
        value = text.getOutlineColor().a;
        return true;
    }
    else if (name == "z_index") {
        value = static_cast<float>(z_index);
        return true;
    }
    return false;
}

bool UICaption::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = text.getFillColor();
        return true;
    }
    else if (name == "outline_color") {
        value = text.getOutlineColor();
        return true;
    }
    return false;
}

bool UICaption::getProperty(const std::string& name, std::string& value) const {
    if (name == "text") {
        value = text.getString();
        return true;
    }
    return false;
}

