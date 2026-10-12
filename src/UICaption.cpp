#include "UICaption.h"
#include <algorithm>
#include <cmath>
#include "PyWrap.h"
#include "Utf8.h"  // #477
#include "GameEngine.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"
#include "PythonObjectCache.h"
#include "PyAlignment.h"
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support
#include "UIFrame.h"          // parent= kwarg: Frame parent type
#include "PyGridData.h"           // parent= kwarg: Grid/GridView parent type
#include "PySceneObject.h"    // parent= kwarg: Scene parent type
// UIDrawable methods now in UIBase.h
#include "McRFPy_Doc.h"
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
    // #184: Also check for Python subclass (might have on_click method)
    if (!click_callable && !is_python_subclass) return nullptr;

    // Get text dimensions from local bounds
    sf::FloatRect localBounds = text.getLocalBounds();
    float w = localBounds.width;
    float h = localBounds.height;
    // Account for text origin offset (SFML text has non-zero left/top in local bounds)
    float textOffsetX = localBounds.left;
    float textOffsetY = localBounds.top;

    // Transform click point to local coordinates accounting for rotation
    sf::Vector2f localPoint;
    if (rotation != 0.0f) {
        // Build transform: translate to position, then rotate around origin
        sf::Transform transform;
        transform.translate(position);
        transform.translate(origin);
        transform.rotate(rotation);
        transform.translate(-origin);

        // Apply inverse transform to get local coordinates
        sf::Transform inverse = transform.getInverse();
        localPoint = inverse.transformPoint(point);
    } else {
        // No rotation - simple subtraction
        localPoint = point - position;
    }

    // Check if local point is within bounds (accounting for text offset)
    if (localPoint.x >= textOffsetX && localPoint.y >= textOffsetY &&
        localPoint.x < textOffsetX + w && localPoint.y < textOffsetY + h) {
        return this;
    }
    return nullptr;
}

void UICaption::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    // Check visibility
    if (!visible) return;

    // Apply opacity (multiply with fill_color alpha)
    auto color = text.getFillColor();
    sf::Uint8 original_alpha = color.a;
    color.a = static_cast<sf::Uint8>(original_alpha * opacity);
    text.setFillColor(color);

    // Apply rotation and origin
    text.setOrigin(origin);
    text.setRotation(rotation);

    // #106: Shader rendering path
    if (shader && shader->shader) {
        // Get the text bounds for rendering
        auto bounds = text.getGlobalBounds();
        sf::Vector2f screen_pos = offset + position;

        // Get or create intermediate texture
        auto& intermediate = GameEngine::getShaderIntermediate();
        intermediate.clear(sf::Color::Transparent);

        // Render text at origin in intermediate texture
        sf::Text temp_text = text;
        temp_text.setPosition(0, 0);  // Render at origin of intermediate texture
        intermediate.draw(temp_text);
        intermediate.display();

        // Create result sprite from intermediate texture
        sf::Sprite result_sprite(intermediate.getTexture());
        result_sprite.setPosition(screen_pos);

        // Apply engine uniforms
        sf::Vector2f resolution(bounds.width, bounds.height);
        PyShader::applyEngineUniforms(*shader->shader, resolution);

        // Apply user uniforms
        if (uniforms) {
            uniforms->applyTo(*shader->shader);
        }

        // Draw with shader
        target.draw(result_sprite, shader->shader.get());
    } else {
        // Standard rendering path (no shader)
        text.move(offset);
        target.draw(text);
        text.move(-offset);
    }

    // Restore original alpha
    color.a = original_alpha;
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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
    if (member_ptr == 0) { //x
        self->data->text.setPosition(val, self->data->text.getPosition().y);
        self->data->markCompositeDirty(); // #289: position change invalidates parent cache
    }
    else if (member_ptr == 1) { //y
        self->data->text.setPosition(self->data->text.getPosition().x, val);
        self->data->markCompositeDirty(); // #289: position change invalidates parent cache
    }
    else if (member_ptr == 4) { //outline
        if (!checkGlyphSize("outline", val)) return -1;  // #463
        self->data->text.setOutlineThickness(val);
        self->data->markDirty(); // #289: content change invalidates own + parent cache
    }
    else if (member_ptr == 5) { // character size
        if (!checkGlyphSize("font_size", val)) return -1;  // #463 (was a silent clamp, #309)
        self->data->text.setCharacterSize(static_cast<unsigned int>(val));
        self->data->markDirty(); // #289: content change invalidates own + parent cache
    }
    return 0;
}

PyObject* UICaption::get_vec_member(PyUICaptionObject* self, void* closure)
{
    return PyVector(self->data->text.getPosition()).pyObject();
}

int UICaption::set_vec_member(PyUICaptionObject* self, PyObject* value, void* closure)
{
    self->data->text.setPosition(PyVector::fromPy(value));
    self->data->markCompositeDirty(); // #289: position change invalidates parent cache
    return 0;
}

PyObject* UICaption::get_color_member(PyUICaptionObject* self, void* closure)
{
    // TODO: migrate this code to a switch statement - validate closure & return values in one tighter, more extensible structure

    // validate closure (should be impossible to be wrong, but it's thorough)
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    sf::Color color;
    if (!PyColor::to_color(value, color)) return -1;  // #450

    if (member_ptr == 0)
    {
        self->data->text.setFillColor(color);
        self->data->markDirty(); // #289: color change invalidates own + parent cache
    }
    else if (member_ptr == 1)
    {
        self->data->text.setOutlineColor(color);
        self->data->markDirty(); // #289: color change invalidates own + parent cache
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

PyObject* UICaption::get_text(PyUICaptionObject* self, void* closure)
{
    const std::string text = mcrf::to_utf8(self->data->text.getString());  // #477
    return PyUnicode_FromStringAndSize(text.data(), text.size());
}

int UICaption::set_text(PyUICaptionObject* self, PyObject* value, void* closure)
{
    mcrf::PyRef s(PyObject_Str(value));
    if (!s) return -1;
    Py_ssize_t len = 0;
    const char* utf8 = PyUnicode_AsUTF8AndSize(s.get(), &len);  // fails on lone surrogates
    if (!utf8) return -1;
    self->data->text.setString(mcrf::from_utf8(std::string(utf8, len)));  // #477
    self->data->markDirty(); // #289: text change invalidates own + parent cache
    return 0;
}

PyObject* UICaption::get_font(PyUICaptionObject* self, void* closure)
{
    // #320: read-only Font getter. self->font is populated at construction with
    // either the supplied Font or a wrapper around the engine default font.
    if (self->font) {
        Py_INCREF(self->font);
        return self->font;
    }
    Py_RETURN_NONE;
}

PyObject* UICaption::get_size(PyUICaptionObject* self, void* closure)
{
    auto bounds = self->data->text.getGlobalBounds();
    return PyVector(sf::Vector2f(bounds.width, bounds.height)).pyObject();
}

PyObject* UICaption::get_w(PyUICaptionObject* self, void* closure)
{
    auto bounds = self->data->text.getGlobalBounds();
    return PyFloat_FromDouble(bounds.width);
}

PyObject* UICaption::get_h(PyUICaptionObject* self, void* closure)
{
    auto bounds = self->data->text.getGlobalBounds();
    return PyFloat_FromDouble(bounds.height);
}

// #479: pen advance of the widest line (glyph advances + kerning), not ink extent.
// Outline does not change it; trailing spaces count.
static float text_advance(const sf::Text& t)
{
#if defined(MCRF_SDL2) || defined(MCRF_HEADLESS)
    return t.getAdvance();
#else
    const sf::String str = t.getString();
    float widest = 0.0f;
    for (std::size_t i = 0; i <= str.getSize(); i++) {
        if (i == str.getSize() || str[i] == U'\n')
            widest = std::max(widest, t.findCharacterPos(i).x);
    }
    return widest;
#endif
}

PyObject* UICaption::get_advance(PyUICaptionObject* self, void* closure)
{
    return PyFloat_FromDouble(text_advance(self->data->text));
}

PyGetSetDef UICaption::getsetters[] = {
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(x, "X coordinate of top-left corner (float)."),
     (void*)((intptr_t)PyObjectsEnum::UICAPTION << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(y, "Y coordinate of top-left corner (float)."),
     (void*)((intptr_t)PyObjectsEnum::UICAPTION << 8 | 1)},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position as (x, y) Vector."),
     (void*)PyObjectsEnum::UICAPTION},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos,
     MCRF_PROPERTY(grid_pos, "Position in grid tile coordinates (Vector). Only valid when parent is a Grid."),
     (void*)PyObjectsEnum::UICAPTION},
    {"grid_size", (getter)UIDrawable::get_grid_size, (setter)UIDrawable::set_grid_size,
     MCRF_PROPERTY(grid_size, "Size in grid tile coordinates (Vector). Only valid when parent is a Grid."),
     (void*)PyObjectsEnum::UICAPTION},
    {"size", (getter)UICaption::get_size, NULL,
     MCRF_PROPERTY(size, "Text dimensions as Vector (read-only)."),
     NULL},
    {"w", (getter)UICaption::get_w, NULL,
     MCRF_PROPERTY(w, "Text width in pixels (float, read-only)."),
     NULL},
    {"h", (getter)UICaption::get_h, NULL,
     MCRF_PROPERTY(h, "Text height in pixels (float, read-only)."),
     NULL},
    {"advance", (getter)UICaption::get_advance, NULL,
     MCRF_PROPERTY(advance,
         "Pen advance of the text in pixels (float, read-only): sum of glyph advances plus kerning "
         "for the widest line. Unlike w, it includes trailing spaces and side bearings, so it is where "
         "the next span starts. Unaffected by outline. 0 under MCRF_HEADLESS builds (no font metrics)."
     ), NULL},
    {"outline", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member,
     MCRF_PROPERTY(outline, "Thickness of the text outline border in pixels (float), 0 to 2048. Raises ValueError outside that range."),
     (void*)4},
    {"fill_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member,
     MCRF_PROPERTY(fill_color,
         "Fill color of the text (Color). Returns a copy; modifying components requires reassignment. "
         "For animation, use 'fill_color.r', 'fill_color.g', etc."
     ), (void*)0},
    {"outline_color", (getter)UICaption::get_color_member, (setter)UICaption::set_color_member,
     MCRF_PROPERTY(outline_color,
         "Outline color of the text (Color). Returns a copy; modifying components requires reassignment. "
         "For animation, use 'outline_color.r', 'outline_color.g', etc."
     ), (void*)1},
    //{"children", (getter)PyUIFrame_get_children, NULL, "UICollection of objects on top of this one", NULL},
    {"text", (getter)UICaption::get_text, (setter)UICaption::set_text,
     MCRF_PROPERTY(text, "The text string displayed by this Caption (str)."),
     NULL},
    {"font", (getter)UICaption::get_font, NULL,
     MCRF_PROPERTY(font,
         "Font used for text rendering (Font, read-only). Reflects the engine "
         "default font when none was provided at construction."
     ), NULL},
    {"font_size", (getter)UICaption::get_float_member, (setter)UICaption::set_float_member,
     MCRF_PROPERTY(font_size, "Font size in pixels (int), 0 to 2048. Raises ValueError outside that range."),
     (void*)5},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: MouseButton, action: InputState)."
     ), (void*)PyObjectsEnum::UICAPTION},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UICAPTION},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding elements (str)."),
     (void*)PyObjectsEnum::UICAPTION},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UICAPTION),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UICAPTION),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UICAPTION),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UICAPTION),
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
            "text='" << mcrf::to_utf8(text.getString()) << "', " <<
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
    
    // Define all parameters with defaults
    PyObject* pos_obj = nullptr;
    PyObject* font = nullptr;
    const char* text = "";
    PyObject* fill_color = nullptr;
    PyObject* outline_color = nullptr;
    float outline = 0.0f;
    float font_size = 16.0f;
    PyObject* click_handler = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f;
    PyObject* align_obj = nullptr;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;
    PyObject* parent_obj = nullptr;  // Auto-attach parent (Frame, Scene, or Grid)

    // Keywords list: pos, font, and text are positional-or-keyword (matching the
    // documented Caption(pos, font, text, ...) signature and the Sprite/Entity
    // convention). Everything after the '$' separator is keyword-only. (#320)
    static const char* kwlist[] = {
        "pos", "font", "text",
        // Keyword-only args follow:
        "fill_color", "outline_color", "outline", "font_size", "on_click",
        "visible", "opacity", "z_index", "name", "x", "y",
        "align", "margin", "horiz_margin", "vert_margin",
        "parent",
        nullptr
    };

    // '$' marker makes all following args keyword-only (Python 3.3+ format extension).
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOz$OOffOifizffOfffO", const_cast<char**>(kwlist),
                                     &pos_obj, &font, &text,  // pos+font+text are positional-or-keyword
                                     &fill_color, &outline_color, &outline, &font_size, &click_handler,
                                     &visible, &opacity, &z_index, &name, &x, &y,
                                     &align_obj, &margin, &horiz_margin, &vert_margin,
                                     &parent_obj)) {
        return -1;
    }
    
    // Handle position argument (can be tuple, Vector, or use x/y keywords)
    if (pos_obj) {
        PyVectorObject* vec = PyVector::from_arg(pos_obj);
        if (vec) {
            x = vec->data.x;
            y = vec->data.y;
            Py_DECREF(vec);
        } else {
            PyErr_Clear();
            if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                    (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                    x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                    y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                } else {
                    PyErr_SetString(PyExc_TypeError, "pos tuple must contain numbers");
                    return -1;
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                return -1;
            }
        }
    }
    
    // Handle font argument
    std::shared_ptr<PyFont> pyfont = nullptr;
    if (font && font != Py_None) {
        if (!PyObject_IsInstance(font, (PyObject*)&mcrfpydef::PyFontType)) {
            PyErr_SetString(PyExc_TypeError, "font must be a mcrfpy.Font instance");
            return -1;
        }
        auto obj = (PyFontObject*)font;
        pyfont = obj->data;
    }
    
    // Create the caption
    self->data = std::make_shared<UICaption>();
    self->data->position = sf::Vector2f(x, y);
    self->data->text.setPosition(self->data->position);
    if (!checkGlyphSize("outline", outline)) return -1;  // #463
    self->data->text.setOutlineThickness(outline);

    // Set the font, and remember the Python Font object for the read-only
    // `font` getter (#320). When no font was provided, expose the engine default
    // font rather than None so the getter reflects what is actually rendered.
    if (pyfont) {
        self->data->text.setFont(pyfont->font);
        Py_INCREF(font);
        Py_XSETREF(self->font, font);
    } else {
        // Use default font when None or not provided
        if (auto default_font = McRFPy_API::defaultFont()) {
            self->data->text.setFont(default_font->font);
            Py_XSETREF(self->font, default_font->pyObject());
        }
    }

    if (!checkGlyphSize("font_size", font_size)) return -1;  // #463
    self->data->text.setCharacterSize(static_cast<unsigned int>(font_size));
    
    // Set text
    if (text && strlen(text) > 0) {
        self->data->text.setString(mcrf::from_utf8(text));  // #477
    }
    
    // Handle fill_color
    if (fill_color && fill_color != Py_None) {
        sf::Color color;
        if (!PyColor::to_color(fill_color, color)) return -1;  // #450
        self->data->text.setFillColor(color);
    } else {
        self->data->text.setFillColor(sf::Color(255, 255, 255, 255));  // Default: white
    }
    
    // Handle outline_color
    if (outline_color && outline_color != Py_None) {
        sf::Color color;
        if (!PyColor::to_color(outline_color, color)) return -1;  // #450
        self->data->text.setOutlineColor(color);
    } else {
        self->data->text.setOutlineColor(sf::Color(0, 0, 0, 255));  // Default: black
    }
    
    // Set other properties
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    if (name) {
        self->data->name = std::string(name);
    }

    // Process alignment arguments
    UIDRAWABLE_PROCESS_ALIGNMENT(self->data, align_obj, margin, horiz_margin, vert_margin);

    // Handle click handler
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

    // Initialize weak reference list
    self->weakreflist = NULL;
    
    // Register in Python object cache
    if (mcrf::register_wrapper(self->data->serial_number, (PyObject*)self) < 0) return -1;

    // #184: Check if this is a Python subclass (for callback method support)
    self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUICaptionType;

    // Auto-attach to parent's children collection if parent= was supplied
    UIDRAWABLE_ATTACH_TO_PARENT(parent_obj, self);

    return 0;
}


// Property system implementation for animations. The shared names (x, y, pos,
// rotation, origin, opacity, z_index) are handled by UIDrawable (#426); Caption's
// w/h/size are read-only text bounds, so they are not animatable.
bool UICaption::checkGlyphSize(const char* what, float value) {
    if (std::isfinite(value) && value >= 0.0f && value <= MAX_GLYPH_PX) return true;
    PyErr_Format(PyExc_ValueError, "%s must be between 0 and %d pixels, got %R",
                 what, static_cast<int>(MAX_GLYPH_PX),
                 mcrf::PyRef(PyFloat_FromDouble(value)).get());
    return false;
}

bool UICaption::checkFloatTarget(const std::string& name, float final_value) const {
    if (name == "font_size" || name == "outline") return checkGlyphSize(name.c_str(), final_value);
    return true;
}

bool UICaption::setProperty(const std::string& name, float value) {
    // The ends are checked by checkFloatTarget; an easing that overshoots (back,
    // elastic) passes through values outside the range, so clamp those (#463).
    if (name == "font_size") {
        text.setCharacterSize(static_cast<unsigned int>(std::clamp(value, 0.0f, MAX_GLYPH_PX)));
        markDirty();  // #144 - Content change
        return true;
    }
    if (name == "outline") {
        text.setOutlineThickness(std::clamp(value, 0.0f, MAX_GLYPH_PX));
        markDirty();  // #144 - Content change
        return true;
    }
    int channel;
    if (colorChannelName(name, "fill_color", channel)) {
        auto color = text.getFillColor();
        colorChannel(color, channel) = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setFillColor(color);
        markDirty();  // #144 - Content change
        return true;
    }
    if (colorChannelName(name, "outline_color", channel)) {
        auto color = text.getOutlineColor();
        colorChannel(color, channel) = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        text.setOutlineColor(color);
        markDirty();  // #144 - Content change
        return true;
    }
    // #106: Check for shader uniform properties
    if (setShaderProperty(name, value)) {
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICaption::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        text.setFillColor(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "outline_color") {
        text.setOutlineColor(value);
        markDirty();  // #144 - Content change
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICaption::setProperty(const std::string& name, const std::string& value) {
    if (name == "text") {
        text.setString(mcrf::from_utf8(value));  // #477
        markDirty();  // #144 - Content change
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICaption::getProperty(const std::string& name, float& value) const {
    if (name == "font_size") {
        value = static_cast<float>(text.getCharacterSize());
        return true;
    }
    if (name == "outline") {
        value = text.getOutlineThickness();
        return true;
    }
    int channel;
    if (colorChannelName(name, "fill_color", channel)) {
        auto color = text.getFillColor();
        value = colorChannel(color, channel);
        return true;
    }
    if (colorChannelName(name, "outline_color", channel)) {
        auto color = text.getOutlineColor();
        value = colorChannel(color, channel);
        return true;
    }
    // #106: Check for shader uniform properties
    if (getShaderProperty(name, value)) {
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UICaption::setProperty(const std::string& name, const sf::Vector2f& value) {
    return UIDrawable::setProperty(name, value);
}

bool UICaption::getProperty(const std::string& name, sf::Vector2f& value) const {
    return UIDrawable::getProperty(name, value);
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
    return UIDrawable::getProperty(name, value);
}

bool UICaption::getProperty(const std::string& name, std::string& value) const {
    if (name == "text") {
        value = mcrf::to_utf8(text.getString());  // #477
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UICaption::hasProperty(const std::string& name) const {
    int channel;
    if (name == "font_size" || name == "outline" || name == "text" ||
        name == "fill_color" || name == "outline_color" ||
        colorChannelName(name, "fill_color", channel) ||
        colorChannelName(name, "outline_color", channel)) {
        return true;
    }
    // #106: Check for shader uniform properties
    if (hasShaderProperty(name)) {
        return true;
    }
    return UIDrawable::hasProperty(name);
}

