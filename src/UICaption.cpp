#include "UICaption.h"
#include "GameEngine.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"
#include "PyArgHelpers.h"
// UIDrawable methods now in UIBase.h
#include <algorithm>

UICaption::UICaption()
{
    // Initialize text with safe defaults
    text.setString("");
    position = sf::Vector2f(0.0f, 0.0f);  // Set base class position
    text.setPosition(position);           // Sync text position
    text.setCharacterSize(12);
    text.setFillColor(sf::Color::White);
    text.setOutlineColor(sf::Color::Black);
    text.setOutlineThickness(0.0f);
}

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
    // Check visibility
    if (!visible) return;
    
    // Apply opacity
    auto color = text.getFillColor();
    color.a = static_cast<sf::Uint8>(255 * opacity);
    text.setFillColor(color);
    
    text.move(offset);
    //Resources::game->getWindow().draw(text);
    target.draw(text);
    text.move(-offset);
    
    // Restore original alpha
    color.a = 255;
    text.setFillColor(color);
}

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}

// Phase 1 implementations
sf::FloatRect UICaption::get_bounds() const
{
    return text.getGlobalBounds();
}

void UICaption::move(float dx, float dy)
{
    position.x += dx;
    position.y += dy;
    text.setPosition(position);  // Keep text in sync
}

void UICaption::resize(float w, float h)
{
    // Implement multiline text support by setting bounds
    // Width constraint enables automatic word wrapping in SFML
    if (w > 0) {
        // Store the requested width for word wrapping
        // Note: SFML doesn't have direct width constraint, but we can
        // implement basic word wrapping by inserting newlines
        
        // For now, we'll store the constraint for future use
        // A full implementation would need to:
        // 1. Split text into words
        // 2. Measure each word's width
        // 3. Insert newlines where needed
        // This is a placeholder that at least acknowledges the resize request
        
        // TODO: Implement proper word wrapping algorithm
        // For now, just mark that resize was called
        markDirty();
    }
}

void UICaption::onPositionChanged()
{
    // Sync text position with base class position
    text.setPosition(position);
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
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
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


// Define the PyObjectType alias for the macros
typedef PyUICaptionObject PyObjectType;

// Method definitions
PyMethodDef UICaption_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}  // Sentinel
};

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
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "X coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UICAPTION << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "Y coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UICAPTION << 8 | 1)},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos, "(x, y) vector", (void*)PyObjectsEnum::UICAPTION},
    //{"w", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "width of the rectangle",   (void*)2},
    //{"h", (getter)PyUIFrame_get_float_member, (setter)PyUIFrame_set_float_member, "height of the rectangle",   (void*)3},
    {"outline", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "Thickness of the border",   (void*)4},
    {"fill_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member, "Fill color of the text", (void*)0},
    {"outline_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member, "Outline color of the text", (void*)1},
    //{"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
    {"text", (getter)UICaption::get_text, (setter)UICaption::set_text, "The text displayed", NULL},
    {"font_size", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member, "Font size (integer) in points", (void*)5},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UICAPTION},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int, "Z-order for rendering (lower values rendered first)", (void*)PyObjectsEnum::UICAPTION},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name, "Name for finding elements", (void*)PyObjectsEnum::UICAPTION},
    UIDRAWABLE_GETSETTERS,
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
    
    // Try parsing with PyArgHelpers
    int arg_idx = 0;
    auto pos_result = PyArgHelpers::parsePosition(args, kwds, &arg_idx);
    
    // Default values
    float x = 0.0f, y = 0.0f, outline = 0.0f;
    char* text = nullptr;
    PyObject* font = nullptr;
    PyObject* fill_color = nullptr;
    PyObject* outline_color = nullptr;
    PyObject* click_handler = nullptr;
    
    // Case 1: Got position from helpers (tuple format)
    if (pos_result.valid) {
        x = pos_result.x;
        y = pos_result.y;
        
        // Parse remaining arguments
        static const char* remaining_keywords[] = { 
            "text", "font", "fill_color", "outline_color", "outline", "click", nullptr 
        };
        
        // Create new tuple with remaining args
        Py_ssize_t total_args = PyTuple_Size(args);
        PyObject* remaining_args = PyTuple_GetSlice(args, arg_idx, total_args);
        
        if (!PyArg_ParseTupleAndKeywords(remaining_args, kwds, "|zOOOfO", 
                                         const_cast<char**>(remaining_keywords),
                                         &text, &font, &fill_color, &outline_color, 
                                         &outline, &click_handler)) {
            Py_DECREF(remaining_args);
            if (pos_result.error) PyErr_SetString(PyExc_TypeError, pos_result.error);
            return -1;
        }
        Py_DECREF(remaining_args);
    }
    // Case 2: Traditional format
    else {
        PyErr_Clear();  // Clear any errors from helpers
        
        // First check if this is the old (text, x, y, ...) format
        PyObject* first_arg = args && PyTuple_Size(args) > 0 ? PyTuple_GetItem(args, 0) : nullptr;
        bool text_first = first_arg && PyUnicode_Check(first_arg);
        
        if (text_first) {
            // Pattern: (text, x, y, ...)
            static const char* text_first_keywords[] = { 
                "text", "x", "y", "font", "fill_color", "outline_color", 
                "outline", "click", "pos", nullptr 
            };
            PyObject* pos_obj = nullptr;
            
            if (!PyArg_ParseTupleAndKeywords(args, kwds, "|zffOOOfOO", 
                                             const_cast<char**>(text_first_keywords), 
                                             &text, &x, &y, &font, &fill_color, &outline_color, 
                                             &outline, &click_handler, &pos_obj)) {
                return -1;
            }
            
            // Handle pos keyword override
            if (pos_obj && pos_obj != Py_None) {
                if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                    PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                    PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                    if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                        (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                        x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                        y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                    }
                } else if (PyObject_TypeCheck(pos_obj, (PyTypeObject*)PyObject_GetAttrString(
                           PyImport_ImportModule("mcrfpy"), "Vector"))) {
                    PyVectorObject* vec = (PyVectorObject*)pos_obj;
                    x = vec->data.x;
                    y = vec->data.y;
                } else {
                    PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                    return -1;
                }
            }
        } else {
            // Pattern: (x, y, text, ...)
            static const char* xy_keywords[] = { 
                "x", "y", "text", "font", "fill_color", "outline_color", 
                "outline", "click", "pos", nullptr 
            };
            PyObject* pos_obj = nullptr;
            
            if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffzOOOfOO", 
                                             const_cast<char**>(xy_keywords), 
                                             &x, &y, &text, &font, &fill_color, &outline_color, 
                                             &outline, &click_handler, &pos_obj)) {
                return -1;
            }
            
            // Handle pos keyword override
            if (pos_obj && pos_obj != Py_None) {
                if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                    PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                    PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                    if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                        (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                        x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                        y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                    }
                } else if (PyObject_TypeCheck(pos_obj, (PyTypeObject*)PyObject_GetAttrString(
                           PyImport_ImportModule("mcrfpy"), "Vector"))) {
                    PyVectorObject* vec = (PyVectorObject*)pos_obj;
                    x = vec->data.x;
                    y = vec->data.y;
                } else {
                    PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                    return -1;
                }
            }
        }
    }
    
    self->data->position = sf::Vector2f(x, y);  // Set base class position
    self->data->text.setPosition(self->data->position);  // Sync text position
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

    // Handle text - default to empty string if not provided
    if (text && text != NULL) {
        self->data->text.setString((std::string)text);
    } else {
        self->data->text.setString("");
    }
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

    // Process click handler if provided
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

    return 0;
}

// Property system implementation for animations
bool UICaption::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        text.setPosition(position);  // Keep text in sync
        return true;
    }
    else if (name == "y") {
        position.y = value;
        text.setPosition(position);  // Keep text in sync
        return true;
    }
    else if (name == "font_size" || name == "size") { // Support both for backward compatibility
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
        value = position.x;
        return true;
    }
    else if (name == "y") {
        value = position.y;
        return true;
    }
    else if (name == "font_size" || name == "size") { // Support both for backward compatibility
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

