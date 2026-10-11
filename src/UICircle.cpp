#include "UICircle.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyVector.h"
#include "PyWrap.h"
#include "PyColor.h"
#include "PythonObjectCache.h"
#include "PyAlignment.h"
#include "UIFrame.h"          // parent= kwarg: Frame parent type
#include "UICaption.h"        // parent= kwarg: needed for ATTACH macro instantiation
#include "PyGridData.h"           // parent= kwarg: Grid/GridView parent type
#include "PySceneObject.h"    // parent= kwarg: Scene parent type
#include <cmath>

UICircle::UICircle()
    : radius(10.0f),
      fill_color(sf::Color::White),
      outline_color(sf::Color::Transparent),
      outline_thickness(0.0f)
{
    position = sf::Vector2f(0.0f, 0.0f);
    shape.setRadius(radius);
    shape.setFillColor(fill_color);
    shape.setOutlineColor(outline_color);
    shape.setOutlineThickness(outline_thickness);
    shape.setOrigin(radius, radius);  // Center the origin
}

UICircle::UICircle(float radius, sf::Vector2f center, sf::Color fillColor,
                   sf::Color outlineColor, float outlineThickness)
    : radius(radius),
      fill_color(fillColor),
      outline_color(outlineColor),
      outline_thickness(outlineThickness)
{
    position = center;
    shape.setRadius(radius);
    shape.setFillColor(fill_color);
    shape.setOutlineColor(outline_color);
    shape.setOutlineThickness(outline_thickness);
    shape.setOrigin(radius, radius);  // Center the origin
}

UICircle::UICircle(const UICircle& other)
    : UIDrawable(other),
      radius(other.radius),
      fill_color(other.fill_color),
      outline_color(other.outline_color),
      outline_thickness(other.outline_thickness)
{
    shape.setRadius(radius);
    shape.setFillColor(fill_color);
    shape.setOutlineColor(outline_color);
    shape.setOutlineThickness(outline_thickness);
    shape.setOrigin(radius, radius);
}

UICircle& UICircle::operator=(const UICircle& other) {
    if (this != &other) {
        UIDrawable::operator=(other);
        radius = other.radius;
        fill_color = other.fill_color;
        outline_color = other.outline_color;
        outline_thickness = other.outline_thickness;
        shape.setRadius(radius);
        shape.setFillColor(fill_color);
        shape.setOutlineColor(outline_color);
        shape.setOutlineThickness(outline_thickness);
        shape.setOrigin(radius, radius);
    }
    return *this;
}

UICircle::UICircle(UICircle&& other) noexcept
    : UIDrawable(std::move(other)),
      shape(std::move(other.shape)),
      radius(other.radius),
      fill_color(other.fill_color),
      outline_color(other.outline_color),
      outline_thickness(other.outline_thickness)
{
}

UICircle& UICircle::operator=(UICircle&& other) noexcept {
    if (this != &other) {
        UIDrawable::operator=(std::move(other));
        shape = std::move(other.shape);
        radius = other.radius;
        fill_color = other.fill_color;
        outline_color = other.outline_color;
        outline_thickness = other.outline_thickness;
    }
    return *this;
}

void UICircle::setRadius(float r) {
    radius = r;
    shape.setRadius(r);
    shape.setOrigin(r, r);  // Keep origin at center
}

void UICircle::setFillColor(sf::Color c) {
    fill_color = c;
    shape.setFillColor(c);
}

void UICircle::setOutlineColor(sf::Color c) {
    outline_color = c;
    shape.setOutlineColor(c);
}

void UICircle::setOutline(float t) {
    outline_thickness = t;
    shape.setOutlineThickness(t);
}

void UICircle::render(sf::Vector2f offset, sf::RenderTarget& target) {
    if (!visible) return;

    // Apply position and offset
    shape.setPosition(position + offset);

    // Apply rotation (using UIDrawable::origin as offset from circle center)
    // The shape already has its origin at center (radius, radius)
    // UIDrawable::origin provides additional offset from that center
    shape.setOrigin(radius + origin.x, radius + origin.y);
    shape.setRotation(rotation);

    // Apply opacity to colors
    sf::Color render_fill = fill_color;
    render_fill.a = static_cast<sf::Uint8>(fill_color.a * opacity);
    shape.setFillColor(render_fill);

    sf::Color render_outline = outline_color;
    render_outline.a = static_cast<sf::Uint8>(outline_color.a * opacity);
    shape.setOutlineColor(render_outline);

    target.draw(shape);
}

UIDrawable* UICircle::click_at(sf::Vector2f point) {
    // #184: Also check for Python subclass (might have on_click method)
    if (!click_callable && !is_python_subclass) return nullptr;

    // Calculate the actual circle center accounting for rotation around origin
    // In render(), the circle is drawn at position with origin offset (radius + origin.x/y)
    // So the visual center moves when rotated around a non-default origin
    sf::Vector2f circleCenter = position;

    if (rotation != 0.0f && (origin.x != 0.0f || origin.y != 0.0f)) {
        // The circle center in local space (relative to position) is at (0, 0)
        // With rotation around (origin.x, origin.y), the center moves
        float rad = rotation * 3.14159265f / 180.0f;
        float cos_r = std::cos(rad);
        float sin_r = std::sin(rad);

        // Rotate (0,0) around origin
        float dx = -origin.x;
        float dy = -origin.y;
        float rotatedX = dx * cos_r - dy * sin_r + origin.x;
        float rotatedY = dx * sin_r + dy * cos_r + origin.y;

        circleCenter = position + sf::Vector2f(rotatedX, rotatedY);
    }

    // Check if point is within the circle (including outline)
    float dx = point.x - circleCenter.x;
    float dy = point.y - circleCenter.y;
    float distance = std::sqrt(dx * dx + dy * dy);

    float effective_radius = radius + outline_thickness;
    if (distance <= effective_radius) {
        return this;
    }

    return nullptr;
}

PyObjectsEnum UICircle::derived_type() {
    return PyObjectsEnum::UICIRCLE;
}

sf::FloatRect UICircle::get_bounds() const {
    float effective_radius = radius + outline_thickness;
    return sf::FloatRect(
        position.x - effective_radius,
        position.y - effective_radius,
        effective_radius * 2,
        effective_radius * 2
    );
}

void UICircle::move(float dx, float dy) {
    position.x += dx;
    position.y += dy;
}

void UICircle::resize(float w, float h) {
    // For circles, use the average of w and h as diameter
    radius = (w + h) / 4.0f;  // Average of w and h, then divide by 2 for radius
    shape.setRadius(radius);
    shape.setOrigin(radius, radius);
}

// Property system for animations. The shared names (x, y, pos, rotation, origin,
// opacity, z_index) are handled by UIDrawable (#426); a circle's pos is its center.
bool UICircle::setProperty(const std::string& name, float value) {
    if (name == "radius") {
        setRadius(value);
        markDirty();  // #144 - Content change
        return true;
    } else if (name == "outline") {
        setOutline(value);
        markDirty();  // #144 - Content change
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICircle::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        setFillColor(value);
        markDirty();  // #144 - Content change
        return true;
    } else if (name == "outline_color") {
        setOutlineColor(value);
        markDirty();  // #144 - Content change
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICircle::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "center") {
        assignPosition(value);
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UICircle::getProperty(const std::string& name, float& value) const {
    if (name == "radius") {
        value = radius;
        return true;
    } else if (name == "outline") {
        value = outline_thickness;
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UICircle::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = fill_color;
        return true;
    } else if (name == "outline_color") {
        value = outline_color;
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UICircle::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "center") {
        value = position;
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UICircle::hasProperty(const std::string& name) const {
    if (name == "radius" || name == "outline" || name == "fill_color" ||
        name == "outline_color" || name == "center") {
        return true;
    }
    return UIDrawable::hasProperty(name);
}

// Python API implementations
PyObject* UICircle::get_radius(PyUICircleObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getRadius());
}

int UICircle::set_radius(PyUICircleObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "radius must be a number");
        return -1;
    }
    self->data->setRadius(static_cast<float>(PyFloat_AsDouble(value)));
    self->data->markDirty(); // #291: visual change
    return 0;
}

PyObject* UICircle::get_center(PyUICircleObject* self, void* closure) {
    sf::Vector2f center = self->data->getCenter();
    auto type = &mcrfpydef::PyVectorType;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "ff", center.x, center.y);
    return result;
}

int UICircle::set_center(PyUICircleObject* self, PyObject* value, void* closure) {
    sf::Vector2f center;
    if (!mcrf::to_vector2f(value, center, "center")) return -1;
    self->data->setCenter(center);
    self->data->markCompositeDirty(); // #291: position change
    return 0;
}

PyObject* UICircle::get_fill_color(PyUICircleObject* self, void* closure) {
    sf::Color c = self->data->getFillColor();
    auto type = &mcrfpydef::PyColorType;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "iiii", c.r, c.g, c.b, c.a);
    return result;
}

int UICircle::set_fill_color(PyUICircleObject* self, PyObject* value, void* closure) {
    sf::Color color;
    if (!PyColor::to_color(value, color)) return -1;  // #450: was a silent uint8 wrap
    self->data->setFillColor(color);
    self->data->markDirty(); // #291: color change
    return 0;
}

PyObject* UICircle::get_outline_color(PyUICircleObject* self, void* closure) {
    sf::Color c = self->data->getOutlineColor();
    auto type = &mcrfpydef::PyColorType;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "iiii", c.r, c.g, c.b, c.a);
    return result;
}

int UICircle::set_outline_color(PyUICircleObject* self, PyObject* value, void* closure) {
    sf::Color color;
    if (!PyColor::to_color(value, color)) return -1;  // #450: was a silent uint8 wrap
    self->data->setOutlineColor(color);
    self->data->markDirty(); // #291: color change
    return 0;
}

PyObject* UICircle::get_outline(PyUICircleObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getOutline());
}

int UICircle::set_outline(PyUICircleObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "outline must be a number");
        return -1;
    }
    self->data->setOutline(static_cast<float>(PyFloat_AsDouble(value)));
    self->data->markDirty(); // #291: visual change
    return 0;
}

// Required typedef for UIDRAWABLE_GETSETTERS and UIDRAWABLE_METHODS macro templates
typedef PyUICircleObject PyObjectType;

PyGetSetDef UICircle::getsetters[] = {
    {"radius", (getter)UICircle::get_radius, (setter)UICircle::set_radius,
     MCRF_PROPERTY(radius, "Circle radius in pixels (float)."), NULL},
    {"center", (getter)UICircle::get_center, (setter)UICircle::set_center,
     MCRF_PROPERTY(center, "Center position of the circle (Vector)."), NULL},
    {"fill_color", (getter)UICircle::get_fill_color, (setter)UICircle::set_fill_color,
     MCRF_PROPERTY(fill_color, "Fill color of the circle (Color)."), NULL},
    {"outline_color", (getter)UICircle::get_outline_color, (setter)UICircle::set_outline_color,
     MCRF_PROPERTY(outline_color, "Outline color of the circle (Color)."), NULL},
    {"outline", (getter)UICircle::get_outline, (setter)UICircle::set_outline,
     MCRF_PROPERTY(outline, "Outline thickness in pixels (float). Use 0 for no outline."), NULL},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click, "Callable executed when circle is clicked (Callable | None). Function receives (pos: Vector, button: MouseButton, action: InputState)."), (void*)PyObjectsEnum::UICIRCLE},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index, "Z-order for rendering (int). Lower values are rendered first."), (void*)PyObjectsEnum::UICIRCLE},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding this element (str)."), (void*)PyObjectsEnum::UICIRCLE},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position as a Vector (same as center) (Vector)."), (void*)PyObjectsEnum::UICIRCLE},
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(x, "X coordinate of the center (float)."),
     (void*)((intptr_t)PyObjectsEnum::UICIRCLE << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(y, "Y coordinate of the center (float)."),
     (void*)((intptr_t)PyObjectsEnum::UICIRCLE << 8 | 1)},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos,
     MCRF_PROPERTY(grid_pos, "Position in grid tile coordinates (Vector). Only meaningful when parent is a Grid."), (void*)PyObjectsEnum::UICIRCLE},
    {"grid_size", (getter)UIDrawable::get_grid_size, (setter)UIDrawable::set_grid_size,
     MCRF_PROPERTY(grid_size, "Size in grid tile coordinates (Vector). Only meaningful when parent is a Grid."), (void*)PyObjectsEnum::UICIRCLE},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UICIRCLE),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UICIRCLE),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UICIRCLE),
    {NULL}
};

PyMethodDef UICircle_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}
};

PyObject* UICircle::repr(PyUICircleObject* self) {
    std::ostringstream oss;
    auto& circle = self->data;
    sf::Vector2f center = circle->getCenter();
    sf::Color fc = circle->getFillColor();
    oss << "<Circle center=(" << center.x << ", " << center.y << ") "
        << "radius=" << circle->getRadius() << " "
        << "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", "
        << (int)fc.b << ", " << (int)fc.a << ")>";
    return PyUnicode_FromString(oss.str().c_str());
}

int UICircle::init(PyUICircleObject* self, PyObject* args, PyObject* kwds) {
    // 1.0 API freeze: positional order is now (center, radius, ...). The old
    // (radius, center) ordering is no longer supported.
    static const char* kwlist[] = {
        "center", "radius", "fill_color", "outline_color", "outline",
        "on_click", "visible", "opacity", "z_index", "name",
        "align", "margin", "horiz_margin", "vert_margin",
        "parent", NULL
    };

    float radius = 10.0f;
    PyObject* center_obj = NULL;
    PyObject* fill_color_obj = NULL;
    PyObject* outline_color_obj = NULL;
    float outline = 0.0f;

    // Common UIDrawable kwargs
    PyObject* click_obj = NULL;
    int visible = 1;
    float opacity_val = 1.0f;
    int z_index = 0;
    const char* name = NULL;
    PyObject* align_obj = NULL;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;
    PyObject* parent_obj = NULL;  // Auto-attach parent (Frame, Scene, or Grid)

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OfOOfOpfisOfffO", (char**)kwlist,
            &center_obj, &radius, &fill_color_obj, &outline_color_obj, &outline,
            &click_obj, &visible, &opacity_val, &z_index, &name,
            &align_obj, &margin, &horiz_margin, &vert_margin,
            &parent_obj)) {
        return -1;
    }

    // Set radius
    self->data->setRadius(radius);

    // Set center if provided
    if (center_obj && center_obj != Py_None) {
        sf::Vector2f center;
        if (!mcrf::to_vector2f(center_obj, center, "center")) return -1;
        self->data->setCenter(center);
    }

    // Set fill color if provided
    if (fill_color_obj && fill_color_obj != Py_None) {
        sf::Color color;
        if (!PyColor::to_color(fill_color_obj, color)) return -1;  // #450
        self->data->setFillColor(color);
    }

    // Set outline color if provided
    if (outline_color_obj && outline_color_obj != Py_None) {
        sf::Color color;
        if (!PyColor::to_color(outline_color_obj, color)) return -1;  // #450
        self->data->setOutlineColor(color);
    }

    // Set outline thickness
    self->data->setOutline(outline);

    // Handle common UIDrawable properties
    if (click_obj && click_obj != Py_None) {
        if (!PyCallable_Check(click_obj)) {
            PyErr_SetString(PyExc_TypeError, "on_click must be callable");
            return -1;
        }
        self->data->click_register(click_obj);
    }

    self->data->visible = (visible != 0);
    self->data->opacity = opacity_val;
    self->data->z_index = z_index;

    if (name) {
        self->data->name = name;
    }

    // Process alignment arguments
    UIDRAWABLE_PROCESS_ALIGNMENT(self->data, align_obj, margin, horiz_margin, vert_margin);

    // Register in Python object cache
    if (mcrf::register_wrapper(self->data->serial_number, (PyObject*)self) < 0) return -1;

    // #184: Check if this is a Python subclass (for callback method support)
    self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUICircleType;

    // Auto-attach to parent's children collection if parent= was supplied
    UIDRAWABLE_ATTACH_TO_PARENT(parent_obj, self);

    return 0;
}
