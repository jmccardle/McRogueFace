#include "UICircle.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PyVector.h"
#include "PyColor.h"
#include "PythonObjectCache.h"
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
    if (!click_callable) return nullptr;

    // Check if point is within the circle (including outline)
    float dx = point.x - position.x;
    float dy = point.y - position.y;
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

// Property system for animations
bool UICircle::setProperty(const std::string& name, float value) {
    if (name == "radius") {
        setRadius(value);
        return true;
    } else if (name == "outline") {
        setOutline(value);
        return true;
    } else if (name == "x") {
        position.x = value;
        return true;
    } else if (name == "y") {
        position.y = value;
        return true;
    }
    return false;
}

bool UICircle::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        setFillColor(value);
        return true;
    } else if (name == "outline_color") {
        setOutlineColor(value);
        return true;
    }
    return false;
}

bool UICircle::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "center" || name == "position") {
        position = value;
        return true;
    }
    return false;
}

bool UICircle::getProperty(const std::string& name, float& value) const {
    if (name == "radius") {
        value = radius;
        return true;
    } else if (name == "outline") {
        value = outline_thickness;
        return true;
    } else if (name == "x") {
        value = position.x;
        return true;
    } else if (name == "y") {
        value = position.y;
        return true;
    }
    return false;
}

bool UICircle::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = fill_color;
        return true;
    } else if (name == "outline_color") {
        value = outline_color;
        return true;
    }
    return false;
}

bool UICircle::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "center" || name == "position") {
        value = position;
        return true;
    }
    return false;
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
    return 0;
}

PyObject* UICircle::get_center(PyUICircleObject* self, void* closure) {
    sf::Vector2f center = self->data->getCenter();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!type) return NULL;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "ff", center.x, center.y);
    Py_DECREF(type);
    return result;
}

int UICircle::set_center(PyUICircleObject* self, PyObject* value, void* closure) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_Clear();
        PyErr_SetString(PyExc_TypeError, "center must be a Vector or tuple (x, y)");
        return -1;
    }
    self->data->setCenter(vec->data);
    return 0;
}

PyObject* UICircle::get_fill_color(PyUICircleObject* self, void* closure) {
    sf::Color c = self->data->getFillColor();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (!type) return NULL;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "iiii", c.r, c.g, c.b, c.a);
    Py_DECREF(type);
    return result;
}

int UICircle::set_fill_color(PyUICircleObject* self, PyObject* value, void* closure) {
    sf::Color color;
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color"))) {
        auto pyColor = (PyColorObject*)value;
        color = pyColor->data;
    } else if (PyTuple_Check(value)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(value, "iii|i", &r, &g, &b, &a)) {
            PyErr_SetString(PyExc_TypeError, "color tuple must be (r, g, b) or (r, g, b, a)");
            return -1;
        }
        color = sf::Color(r, g, b, a);
    } else {
        PyErr_SetString(PyExc_TypeError, "fill_color must be a Color or tuple");
        return -1;
    }
    self->data->setFillColor(color);
    return 0;
}

PyObject* UICircle::get_outline_color(PyUICircleObject* self, void* closure) {
    sf::Color c = self->data->getOutlineColor();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (!type) return NULL;
    PyObject* result = PyObject_CallFunction((PyObject*)type, "iiii", c.r, c.g, c.b, c.a);
    Py_DECREF(type);
    return result;
}

int UICircle::set_outline_color(PyUICircleObject* self, PyObject* value, void* closure) {
    sf::Color color;
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color"))) {
        auto pyColor = (PyColorObject*)value;
        color = pyColor->data;
    } else if (PyTuple_Check(value)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(value, "iii|i", &r, &g, &b, &a)) {
            PyErr_SetString(PyExc_TypeError, "color tuple must be (r, g, b) or (r, g, b, a)");
            return -1;
        }
        color = sf::Color(r, g, b, a);
    } else {
        PyErr_SetString(PyExc_TypeError, "outline_color must be a Color or tuple");
        return -1;
    }
    self->data->setOutlineColor(color);
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
    return 0;
}

// Required typedef for UIDRAWABLE_GETSETTERS and UIDRAWABLE_METHODS macro templates
typedef PyUICircleObject PyObjectType;

PyGetSetDef UICircle::getsetters[] = {
    {"radius", (getter)UICircle::get_radius, (setter)UICircle::set_radius,
     "Circle radius in pixels", NULL},
    {"center", (getter)UICircle::get_center, (setter)UICircle::set_center,
     "Center position of the circle", NULL},
    {"fill_color", (getter)UICircle::get_fill_color, (setter)UICircle::set_fill_color,
     "Fill color of the circle", NULL},
    {"outline_color", (getter)UICircle::get_outline_color, (setter)UICircle::set_outline_color,
     "Outline color of the circle", NULL},
    {"outline", (getter)UICircle::get_outline, (setter)UICircle::set_outline,
     "Outline thickness (0 for no outline)", NULL},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     "Callable executed when circle is clicked.", (void*)PyObjectsEnum::UICIRCLE},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     "Z-order for rendering (lower values rendered first).", (void*)PyObjectsEnum::UICIRCLE},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     "Name for finding this element.", (void*)PyObjectsEnum::UICIRCLE},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     "Position as a Vector (same as center).", (void*)PyObjectsEnum::UICIRCLE},
    UIDRAWABLE_GETSETTERS,
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
    static const char* kwlist[] = {
        "radius", "center", "fill_color", "outline_color", "outline",
        "click", "visible", "opacity", "z_index", "name", NULL
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

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|fOOOfOpfis", (char**)kwlist,
            &radius, &center_obj, &fill_color_obj, &outline_color_obj, &outline,
            &click_obj, &visible, &opacity_val, &z_index, &name)) {
        return -1;
    }

    // Set radius
    self->data->setRadius(radius);

    // Set center if provided
    if (center_obj && center_obj != Py_None) {
        PyVectorObject* vec = PyVector::from_arg(center_obj);
        if (!vec) {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "center must be a Vector or tuple (x, y)");
            return -1;
        }
        self->data->setCenter(vec->data);
    }

    // Set fill color if provided
    if (fill_color_obj && fill_color_obj != Py_None) {
        sf::Color color;
        if (PyObject_IsInstance(fill_color_obj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color"))) {
            color = ((PyColorObject*)fill_color_obj)->data;
        } else if (PyTuple_Check(fill_color_obj)) {
            int r, g, b, a = 255;
            if (!PyArg_ParseTuple(fill_color_obj, "iii|i", &r, &g, &b, &a)) {
                PyErr_SetString(PyExc_TypeError, "fill_color tuple must be (r, g, b) or (r, g, b, a)");
                return -1;
            }
            color = sf::Color(r, g, b, a);
        } else {
            PyErr_SetString(PyExc_TypeError, "fill_color must be a Color or tuple");
            return -1;
        }
        self->data->setFillColor(color);
    }

    // Set outline color if provided
    if (outline_color_obj && outline_color_obj != Py_None) {
        sf::Color color;
        if (PyObject_IsInstance(outline_color_obj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color"))) {
            color = ((PyColorObject*)outline_color_obj)->data;
        } else if (PyTuple_Check(outline_color_obj)) {
            int r, g, b, a = 255;
            if (!PyArg_ParseTuple(outline_color_obj, "iii|i", &r, &g, &b, &a)) {
                PyErr_SetString(PyExc_TypeError, "outline_color tuple must be (r, g, b) or (r, g, b, a)");
                return -1;
            }
            color = sf::Color(r, g, b, a);
        } else {
            PyErr_SetString(PyExc_TypeError, "outline_color must be a Color or tuple");
            return -1;
        }
        self->data->setOutlineColor(color);
    }

    // Set outline thickness
    self->data->setOutline(outline);

    // Handle common UIDrawable properties
    if (click_obj && click_obj != Py_None) {
        if (!PyCallable_Check(click_obj)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
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

    return 0;
}
