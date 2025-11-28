#include "UIArc.h"
#include "McRFPy_API.h"
#include <cmath>
#include <sstream>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

UIArc::UIArc()
    : center(0.0f, 0.0f), radius(0.0f), start_angle(0.0f), end_angle(90.0f),
      color(sf::Color::White), thickness(1.0f), vertices_dirty(true)
{
    position = center;
}

UIArc::UIArc(sf::Vector2f center, float radius, float startAngle, float endAngle,
             sf::Color color, float thickness)
    : center(center), radius(radius), start_angle(startAngle), end_angle(endAngle),
      color(color), thickness(thickness), vertices_dirty(true)
{
    position = center;
}

UIArc::UIArc(const UIArc& other)
    : UIDrawable(other),
      center(other.center),
      radius(other.radius),
      start_angle(other.start_angle),
      end_angle(other.end_angle),
      color(other.color),
      thickness(other.thickness),
      vertices_dirty(true)
{
}

UIArc& UIArc::operator=(const UIArc& other) {
    if (this != &other) {
        UIDrawable::operator=(other);
        center = other.center;
        radius = other.radius;
        start_angle = other.start_angle;
        end_angle = other.end_angle;
        color = other.color;
        thickness = other.thickness;
        vertices_dirty = true;
    }
    return *this;
}

UIArc::UIArc(UIArc&& other) noexcept
    : UIDrawable(std::move(other)),
      center(other.center),
      radius(other.radius),
      start_angle(other.start_angle),
      end_angle(other.end_angle),
      color(other.color),
      thickness(other.thickness),
      vertices(std::move(other.vertices)),
      vertices_dirty(other.vertices_dirty)
{
}

UIArc& UIArc::operator=(UIArc&& other) noexcept {
    if (this != &other) {
        UIDrawable::operator=(std::move(other));
        center = other.center;
        radius = other.radius;
        start_angle = other.start_angle;
        end_angle = other.end_angle;
        color = other.color;
        thickness = other.thickness;
        vertices = std::move(other.vertices);
        vertices_dirty = other.vertices_dirty;
    }
    return *this;
}

void UIArc::rebuildVertices() {
    vertices.clear();
    vertices.setPrimitiveType(sf::TriangleStrip);

    // Calculate the arc parameters
    float inner_radius = radius - thickness / 2.0f;
    float outer_radius = radius + thickness / 2.0f;

    if (inner_radius < 0) inner_radius = 0;

    // Normalize angles
    float start_rad = start_angle * M_PI / 180.0f;
    float end_rad = end_angle * M_PI / 180.0f;

    // Calculate number of segments based on arc length
    float angle_span = end_rad - start_rad;
    int num_segments = std::max(3, static_cast<int>(std::abs(angle_span * radius) / 5.0f));
    num_segments = std::min(num_segments, 100);  // Cap at 100 segments

    float angle_step = angle_span / num_segments;

    // Apply opacity to color
    sf::Color render_color = color;
    render_color.a = static_cast<sf::Uint8>(render_color.a * opacity);

    // Build the triangle strip
    for (int i = 0; i <= num_segments; ++i) {
        float angle = start_rad + i * angle_step;
        float cos_a = std::cos(angle);
        float sin_a = std::sin(angle);

        // Inner vertex
        sf::Vector2f inner_pos(
            center.x + inner_radius * cos_a,
            center.y + inner_radius * sin_a
        );
        vertices.append(sf::Vertex(inner_pos, render_color));

        // Outer vertex
        sf::Vector2f outer_pos(
            center.x + outer_radius * cos_a,
            center.y + outer_radius * sin_a
        );
        vertices.append(sf::Vertex(outer_pos, render_color));
    }

    vertices_dirty = false;
}

void UIArc::render(sf::Vector2f offset, sf::RenderTarget& target) {
    if (!visible) return;

    if (vertices_dirty) {
        rebuildVertices();
    }

    // Apply offset by creating a transformed copy
    sf::Transform transform;
    transform.translate(offset);
    target.draw(vertices, transform);
}

UIDrawable* UIArc::click_at(sf::Vector2f point) {
    if (!visible) return nullptr;

    // Calculate distance from center
    float dx = point.x - center.x;
    float dy = point.y - center.y;
    float dist = std::sqrt(dx * dx + dy * dy);

    // Check if within the arc's radial range
    float inner_radius = radius - thickness / 2.0f;
    float outer_radius = radius + thickness / 2.0f;
    if (inner_radius < 0) inner_radius = 0;

    if (dist < inner_radius || dist > outer_radius) {
        return nullptr;
    }

    // Check if within the angle range
    float angle = std::atan2(dy, dx) * 180.0f / M_PI;

    // Normalize angle to match start/end angle range
    float start = start_angle;
    float end = end_angle;

    // Handle angle wrapping
    while (angle < start - 180.0f) angle += 360.0f;
    while (angle > start + 180.0f) angle -= 360.0f;

    if ((start <= end && angle >= start && angle <= end) ||
        (start > end && (angle >= start || angle <= end))) {
        return this;
    }

    return nullptr;
}

PyObjectsEnum UIArc::derived_type() {
    return PyObjectsEnum::UIARC;
}

sf::FloatRect UIArc::get_bounds() const {
    float outer_radius = radius + thickness / 2.0f;
    return sf::FloatRect(
        center.x - outer_radius,
        center.y - outer_radius,
        outer_radius * 2,
        outer_radius * 2
    );
}

void UIArc::move(float dx, float dy) {
    center.x += dx;
    center.y += dy;
    position = center;
    vertices_dirty = true;
}

void UIArc::resize(float w, float h) {
    // Resize by adjusting radius to fit in the given dimensions
    radius = std::min(w, h) / 2.0f - thickness / 2.0f;
    if (radius < 0) radius = 0;
    vertices_dirty = true;
}

// Property setters
bool UIArc::setProperty(const std::string& name, float value) {
    if (name == "radius") {
        setRadius(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "start_angle") {
        setStartAngle(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "end_angle") {
        setEndAngle(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "thickness") {
        setThickness(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "x") {
        center.x = value;
        position = center;
        vertices_dirty = true;
        markDirty();  // #144 - Propagate to parent for texture caching
        return true;
    }
    else if (name == "y") {
        center.y = value;
        position = center;
        vertices_dirty = true;
        markDirty();  // #144 - Propagate to parent for texture caching
        return true;
    }
    return false;
}

bool UIArc::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "color") {
        setColor(value);
        markDirty();  // #144 - Content change
        return true;
    }
    return false;
}

bool UIArc::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "center") {
        setCenter(value);
        markDirty();  // #144 - Propagate to parent for texture caching
        return true;
    }
    return false;
}

bool UIArc::getProperty(const std::string& name, float& value) const {
    if (name == "radius") {
        value = radius;
        return true;
    }
    else if (name == "start_angle") {
        value = start_angle;
        return true;
    }
    else if (name == "end_angle") {
        value = end_angle;
        return true;
    }
    else if (name == "thickness") {
        value = thickness;
        return true;
    }
    else if (name == "x") {
        value = center.x;
        return true;
    }
    else if (name == "y") {
        value = center.y;
        return true;
    }
    return false;
}

bool UIArc::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "color") {
        value = color;
        return true;
    }
    return false;
}

bool UIArc::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "center") {
        value = center;
        return true;
    }
    return false;
}

// Python API implementation
PyObject* UIArc::get_center(PyUIArcObject* self, void* closure) {
    auto center = self->data->getCenter();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!type) return NULL;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "ff", center.x, center.y);
    Py_DECREF(type);
    return result;
}

int UIArc::set_center(PyUIArcObject* self, PyObject* value, void* closure) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_Clear();
        PyErr_SetString(PyExc_TypeError, "center must be a Vector or tuple (x, y)");
        return -1;
    }
    self->data->setCenter(vec->data);
    return 0;
}

PyObject* UIArc::get_radius(PyUIArcObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getRadius());
}

int UIArc::set_radius(PyUIArcObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "radius must be a number");
        return -1;
    }
    self->data->setRadius(static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

PyObject* UIArc::get_start_angle(PyUIArcObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getStartAngle());
}

int UIArc::set_start_angle(PyUIArcObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "start_angle must be a number");
        return -1;
    }
    self->data->setStartAngle(static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

PyObject* UIArc::get_end_angle(PyUIArcObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getEndAngle());
}

int UIArc::set_end_angle(PyUIArcObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "end_angle must be a number");
        return -1;
    }
    self->data->setEndAngle(static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

PyObject* UIArc::get_color(PyUIArcObject* self, void* closure) {
    auto color = self->data->getColor();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    PyObject* args = Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
    PyObject* obj = PyObject_CallObject((PyObject*)type, args);
    Py_DECREF(args);
    Py_DECREF(type);
    return obj;
}

int UIArc::set_color(PyUIArcObject* self, PyObject* value, void* closure) {
    auto color = PyColor::from_arg(value);
    if (!color) {
        PyErr_SetString(PyExc_TypeError, "color must be a Color or tuple (r, g, b) or (r, g, b, a)");
        return -1;
    }
    self->data->setColor(color->data);
    return 0;
}

PyObject* UIArc::get_thickness(PyUIArcObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getThickness());
}

int UIArc::set_thickness(PyUIArcObject* self, PyObject* value, void* closure) {
    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "thickness must be a number");
        return -1;
    }
    self->data->setThickness(static_cast<float>(PyFloat_AsDouble(value)));
    return 0;
}

// Required typedef for UIDRAWABLE_GETSETTERS and UIDRAWABLE_METHODS macro templates
typedef PyUIArcObject PyObjectType;

PyGetSetDef UIArc::getsetters[] = {
    {"center", (getter)UIArc::get_center, (setter)UIArc::set_center,
     "Center position of the arc", NULL},
    {"radius", (getter)UIArc::get_radius, (setter)UIArc::set_radius,
     "Arc radius in pixels", NULL},
    {"start_angle", (getter)UIArc::get_start_angle, (setter)UIArc::set_start_angle,
     "Starting angle in degrees", NULL},
    {"end_angle", (getter)UIArc::get_end_angle, (setter)UIArc::set_end_angle,
     "Ending angle in degrees", NULL},
    {"color", (getter)UIArc::get_color, (setter)UIArc::set_color,
     "Arc color", NULL},
    {"thickness", (getter)UIArc::get_thickness, (setter)UIArc::set_thickness,
     "Line thickness", NULL},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     "Callable executed when arc is clicked.", (void*)PyObjectsEnum::UIARC},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     "Z-order for rendering (lower values rendered first).", (void*)PyObjectsEnum::UIARC},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     "Name for finding this element.", (void*)PyObjectsEnum::UIARC},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     "Position as a Vector (same as center).", (void*)PyObjectsEnum::UIARC},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIARC),
    {NULL}
};

PyMethodDef UIArc_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}
};

PyObject* UIArc::repr(PyUIArcObject* self) {
    std::ostringstream oss;
    if (!self->data) {
        oss << "<Arc (invalid internal object)>";
    } else {
        auto center = self->data->getCenter();
        auto color = self->data->getColor();
        oss << "<Arc center=(" << center.x << ", " << center.y << ") "
            << "radius=" << self->data->getRadius() << " "
            << "angles=(" << self->data->getStartAngle() << ", " << self->data->getEndAngle() << ") "
            << "color=(" << (int)color.r << ", " << (int)color.g << ", "
            << (int)color.b << ", " << (int)color.a << ")>";
    }
    std::string repr_str = oss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIArc::init(PyUIArcObject* self, PyObject* args, PyObject* kwds) {
    // Arguments
    PyObject* center_obj = nullptr;
    float radius = 0.0f;
    float start_angle = 0.0f;
    float end_angle = 90.0f;
    PyObject* color_obj = nullptr;
    float thickness = 1.0f;
    PyObject* click_handler = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;

    static const char* kwlist[] = {
        "center", "radius", "start_angle", "end_angle", "color", "thickness",
        "click", "visible", "opacity", "z_index", "name",
        nullptr
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OfffOfOifiz", const_cast<char**>(kwlist),
                                     &center_obj, &radius, &start_angle, &end_angle,
                                     &color_obj, &thickness,
                                     &click_handler, &visible, &opacity, &z_index, &name)) {
        return -1;
    }

    // Parse center position
    sf::Vector2f center(0.0f, 0.0f);
    if (center_obj) {
        PyVectorObject* vec = PyVector::from_arg(center_obj);
        if (vec) {
            center = vec->data;
        } else {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "center must be a Vector or tuple (x, y)");
            return -1;
        }
    }

    // Parse color
    sf::Color color = sf::Color::White;
    if (color_obj) {
        auto pycolor = PyColor::from_arg(color_obj);
        if (pycolor) {
            color = pycolor->data;
        } else {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "color must be a Color or tuple (r, g, b) or (r, g, b, a)");
            return -1;
        }
    }

    // Set values
    self->data->setCenter(center);
    self->data->setRadius(radius);
    self->data->setStartAngle(start_angle);
    self->data->setEndAngle(end_angle);
    self->data->setColor(color);
    self->data->setThickness(thickness);

    // Handle common UIDrawable properties
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

    self->data->visible = (visible != 0);
    self->data->opacity = opacity;
    self->data->z_index = z_index;

    if (name) {
        self->data->name = name;
    }

    return 0;
}
