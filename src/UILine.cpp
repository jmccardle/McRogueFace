#include "UILine.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PyVector.h"
#include "PyColor.h"
#include "PythonObjectCache.h"
#include "PyAlignment.h"
#include <cmath>

UILine::UILine()
    : start_pos(0.0f, 0.0f),
      end_pos(0.0f, 0.0f),
      color(sf::Color::White),
      thickness(1.0f),
      vertices(sf::TriangleStrip, 4),
      vertices_dirty(true)
{
    position = sf::Vector2f(0.0f, 0.0f);
}

UILine::UILine(sf::Vector2f start, sf::Vector2f end, float thickness, sf::Color color)
    : start_pos(start),
      end_pos(end),
      color(color),
      thickness(thickness),
      vertices(sf::TriangleStrip, 4),
      vertices_dirty(true)
{
    // Set position to the midpoint for consistency with other UIDrawables
    position = (start + end) / 2.0f;
}

UILine::UILine(const UILine& other)
    : UIDrawable(other),
      start_pos(other.start_pos),
      end_pos(other.end_pos),
      color(other.color),
      thickness(other.thickness),
      vertices(sf::TriangleStrip, 4),
      vertices_dirty(true)
{
}

UILine& UILine::operator=(const UILine& other) {
    if (this != &other) {
        UIDrawable::operator=(other);
        start_pos = other.start_pos;
        end_pos = other.end_pos;
        color = other.color;
        thickness = other.thickness;
        vertices_dirty = true;
    }
    return *this;
}

UILine::UILine(UILine&& other) noexcept
    : UIDrawable(std::move(other)),
      start_pos(other.start_pos),
      end_pos(other.end_pos),
      color(other.color),
      thickness(other.thickness),
      vertices(std::move(other.vertices)),
      vertices_dirty(other.vertices_dirty)
{
}

UILine& UILine::operator=(UILine&& other) noexcept {
    if (this != &other) {
        UIDrawable::operator=(std::move(other));
        start_pos = other.start_pos;
        end_pos = other.end_pos;
        color = other.color;
        thickness = other.thickness;
        vertices = std::move(other.vertices);
        vertices_dirty = other.vertices_dirty;
    }
    return *this;
}

void UILine::updateVertices() const {
    if (!vertices_dirty) return;

    // Calculate direction and perpendicular
    sf::Vector2f direction = end_pos - start_pos;
    float length = std::sqrt(direction.x * direction.x + direction.y * direction.y);

    if (length < 0.0001f) {
        // Zero-length line - make a small dot
        float half = thickness / 2.0f;
        vertices[0].position = start_pos + sf::Vector2f(-half, -half);
        vertices[1].position = start_pos + sf::Vector2f(half, -half);
        vertices[2].position = start_pos + sf::Vector2f(-half, half);
        vertices[3].position = start_pos + sf::Vector2f(half, half);
    } else {
        // Normalize direction
        direction /= length;

        // Perpendicular vector
        sf::Vector2f perpendicular(-direction.y, direction.x);
        perpendicular *= thickness / 2.0f;

        // Create a quad (triangle strip) for the thick line
        vertices[0].position = start_pos + perpendicular;
        vertices[1].position = start_pos - perpendicular;
        vertices[2].position = end_pos + perpendicular;
        vertices[3].position = end_pos - perpendicular;
    }

    // Set colors
    for (int i = 0; i < 4; ++i) {
        vertices[i].color = color;
    }

    vertices_dirty = false;
}

void UILine::render(sf::Vector2f offset, sf::RenderTarget& target) {
    if (!visible) return;

    updateVertices();

    // Apply opacity to color
    sf::Color render_color = color;
    render_color.a = static_cast<sf::Uint8>(color.a * opacity);

    // Use ConvexShape to draw the line as a quad
    sf::ConvexShape line_shape(4);
    // Vertices are: 0=start+perp, 1=start-perp, 2=end+perp, 3=end-perp
    // ConvexShape needs points in clockwise/counter-clockwise order
    line_shape.setPoint(0, vertices[0].position + offset);  // start + perp
    line_shape.setPoint(1, vertices[2].position + offset);  // end + perp
    line_shape.setPoint(2, vertices[3].position + offset);  // end - perp
    line_shape.setPoint(3, vertices[1].position + offset);  // start - perp
    line_shape.setFillColor(render_color);
    line_shape.setOutlineThickness(0);

    target.draw(line_shape);
}

UIDrawable* UILine::click_at(sf::Vector2f point) {
    // #184: Also check for Python subclass (might have on_click method)
    if (!click_callable && !is_python_subclass) return nullptr;

    // Check if point is close enough to the line
    // Using a simple bounding box check plus distance-to-line calculation
    sf::FloatRect bounds = get_bounds();
    bounds.left -= thickness;
    bounds.top -= thickness;
    bounds.width += thickness * 2;
    bounds.height += thickness * 2;

    if (!bounds.contains(point)) return nullptr;

    // Calculate distance from point to line segment
    sf::Vector2f line_vec = end_pos - start_pos;
    sf::Vector2f point_vec = point - start_pos;

    float line_len_sq = line_vec.x * line_vec.x + line_vec.y * line_vec.y;
    float t = 0.0f;

    if (line_len_sq > 0.0001f) {
        t = std::max(0.0f, std::min(1.0f,
            (point_vec.x * line_vec.x + point_vec.y * line_vec.y) / line_len_sq));
    }

    sf::Vector2f closest = start_pos + t * line_vec;
    sf::Vector2f diff = point - closest;
    float distance = std::sqrt(diff.x * diff.x + diff.y * diff.y);

    // Click is valid if within thickness + some margin
    if (distance <= thickness / 2.0f + 2.0f) {
        return this;
    }

    return nullptr;
}

PyObjectsEnum UILine::derived_type() {
    return PyObjectsEnum::UILINE;
}

sf::FloatRect UILine::get_bounds() const {
    float min_x = std::min(start_pos.x, end_pos.x);
    float min_y = std::min(start_pos.y, end_pos.y);
    float max_x = std::max(start_pos.x, end_pos.x);
    float max_y = std::max(start_pos.y, end_pos.y);

    return sf::FloatRect(min_x, min_y, max_x - min_x, max_y - min_y);
}

void UILine::move(float dx, float dy) {
    start_pos.x += dx;
    start_pos.y += dy;
    end_pos.x += dx;
    end_pos.y += dy;
    position.x += dx;
    position.y += dy;
    vertices_dirty = true;
}

void UILine::resize(float w, float h) {
    // For a line, resize adjusts the end point relative to start
    end_pos = start_pos + sf::Vector2f(w, h);
    vertices_dirty = true;
}

// Animation property system
bool UILine::setProperty(const std::string& name, float value) {
    if (name == "thickness") {
        thickness = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "x") {
        float dx = value - position.x;
        move(dx, 0);
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "y") {
        float dy = value - position.y;
        move(0, dy);
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "start_x") {
        start_pos.x = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "start_y") {
        start_pos.y = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "end_x") {
        end_pos.x = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "end_y") {
        end_pos.y = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    return false;
}

bool UILine::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "color") {
        color = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    return false;
}

bool UILine::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "start") {
        start_pos = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "end") {
        end_pos = value;
        vertices_dirty = true;
        markDirty();  // #144 - Content change
        return true;
    }
    return false;
}

bool UILine::getProperty(const std::string& name, float& value) const {
    if (name == "thickness") {
        value = thickness;
        return true;
    }
    else if (name == "x") {
        value = position.x;
        return true;
    }
    else if (name == "y") {
        value = position.y;
        return true;
    }
    else if (name == "start_x") {
        value = start_pos.x;
        return true;
    }
    else if (name == "start_y") {
        value = start_pos.y;
        return true;
    }
    else if (name == "end_x") {
        value = end_pos.x;
        return true;
    }
    else if (name == "end_y") {
        value = end_pos.y;
        return true;
    }
    return false;
}

bool UILine::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "color") {
        value = color;
        return true;
    }
    return false;
}

bool UILine::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "start") {
        value = start_pos;
        return true;
    }
    else if (name == "end") {
        value = end_pos;
        return true;
    }
    return false;
}

bool UILine::hasProperty(const std::string& name) const {
    // Float properties
    if (name == "thickness" || name == "x" || name == "y" ||
        name == "start_x" || name == "start_y" ||
        name == "end_x" || name == "end_y") {
        return true;
    }
    // Color properties
    if (name == "color") {
        return true;
    }
    // Vector2f properties
    if (name == "start" || name == "end") {
        return true;
    }
    return false;
}

// Python API implementation
PyObject* UILine::get_start(PyUILineObject* self, void* closure) {
    auto vec = self->data->getStart();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    if (obj) {
        obj->data = vec;
    }
    return (PyObject*)obj;
}

int UILine::set_start(PyUILineObject* self, PyObject* value, void* closure) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "start must be a Vector or tuple (x, y)");
        return -1;
    }
    self->data->setStart(vec->data);
    return 0;
}

PyObject* UILine::get_end(PyUILineObject* self, void* closure) {
    auto vec = self->data->getEnd();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    Py_DECREF(type);
    if (obj) {
        obj->data = vec;
    }
    return (PyObject*)obj;
}

int UILine::set_end(PyUILineObject* self, PyObject* value, void* closure) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "end must be a Vector or tuple (x, y)");
        return -1;
    }
    self->data->setEnd(vec->data);
    return 0;
}

PyObject* UILine::get_color(PyUILineObject* self, void* closure) {
    auto color = self->data->getColor();
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    PyObject* args = Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
    PyObject* obj = PyObject_CallObject((PyObject*)type, args);
    Py_DECREF(args);
    Py_DECREF(type);
    return obj;
}

int UILine::set_color(PyUILineObject* self, PyObject* value, void* closure) {
    auto color = PyColor::from_arg(value);
    if (!color) {
        PyErr_SetString(PyExc_TypeError, "color must be a Color or tuple (r, g, b) or (r, g, b, a)");
        return -1;
    }
    self->data->setColor(color->data);
    return 0;
}

PyObject* UILine::get_thickness(PyUILineObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->getThickness());
}

int UILine::set_thickness(PyUILineObject* self, PyObject* value, void* closure) {
    float thickness;
    if (PyFloat_Check(value)) {
        thickness = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        thickness = PyLong_AsLong(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "thickness must be a number");
        return -1;
    }

    if (thickness < 0.0f) {
        PyErr_SetString(PyExc_ValueError, "thickness must be non-negative");
        return -1;
    }

    self->data->setThickness(thickness);
    return 0;
}

// Define the Python type alias for macros
typedef PyUILineObject PyObjectType;

// Method definitions
PyMethodDef UILine_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}  // Sentinel
};

PyGetSetDef UILine::getsetters[] = {
    {"start", (getter)UILine::get_start, (setter)UILine::set_start,
     MCRF_PROPERTY(start, "Starting point of the line as a Vector."), NULL},
    {"end", (getter)UILine::get_end, (setter)UILine::set_end,
     MCRF_PROPERTY(end, "Ending point of the line as a Vector."), NULL},
    {"color", (getter)UILine::get_color, (setter)UILine::set_color,
     MCRF_PROPERTY(color, "Line color as a Color object."), NULL},
    {"thickness", (getter)UILine::get_thickness, (setter)UILine::set_thickness,
     MCRF_PROPERTY(thickness, "Line thickness in pixels."), NULL},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click, "Callable executed when line is clicked. Function receives (pos: Vector, button: str, action: str)."),
     (void*)PyObjectsEnum::UILINE},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index, "Z-order for rendering (lower values rendered first)."),
     (void*)PyObjectsEnum::UILINE},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding this element."),
     (void*)PyObjectsEnum::UILINE},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position as a Vector (midpoint of line)."),
     (void*)PyObjectsEnum::UILINE},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UILINE),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UILINE),
    {NULL}
};

PyObject* UILine::repr(PyUILineObject* self) {
    std::ostringstream ss;
    if (!self->data) {
        ss << "<Line (invalid internal object)>";
    } else {
        auto start = self->data->getStart();
        auto end = self->data->getEnd();
        auto color = self->data->getColor();
        ss << "<Line start=(" << start.x << ", " << start.y << ") "
           << "end=(" << end.x << ", " << end.y << ") "
           << "thickness=" << self->data->getThickness() << " "
           << "color=(" << (int)color.r << ", " << (int)color.g << ", "
           << (int)color.b << ", " << (int)color.a << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UILine::init(PyUILineObject* self, PyObject* args, PyObject* kwds) {
    // Arguments
    PyObject* start_obj = nullptr;
    PyObject* end_obj = nullptr;
    float thickness = 1.0f;
    PyObject* color_obj = nullptr;
    PyObject* click_handler = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    PyObject* align_obj = nullptr;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;

    static const char* kwlist[] = {
        "start", "end", "thickness", "color",
        "on_click", "visible", "opacity", "z_index", "name",
        "align", "margin", "horiz_margin", "vert_margin",
        nullptr
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOfOOifizOfff", const_cast<char**>(kwlist),
                                     &start_obj, &end_obj, &thickness, &color_obj,
                                     &click_handler, &visible, &opacity, &z_index, &name,
                                     &align_obj, &margin, &horiz_margin, &vert_margin)) {
        return -1;
    }

    // Parse start position
    sf::Vector2f start(0.0f, 0.0f);
    if (start_obj) {
        PyVectorObject* vec = PyVector::from_arg(start_obj);
        if (vec) {
            start = vec->data;
        } else {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "start must be a Vector or tuple (x, y)");
            return -1;
        }
    }

    // Parse end position
    sf::Vector2f end(0.0f, 0.0f);
    if (end_obj) {
        PyVectorObject* vec = PyVector::from_arg(end_obj);
        if (vec) {
            end = vec->data;
        } else {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "end must be a Vector or tuple (x, y)");
            return -1;
        }
    }

    // Parse color
    sf::Color color = sf::Color::White;
    if (color_obj && color_obj != Py_None) {
        auto pycolor = PyColor::from_arg(color_obj);
        if (pycolor) {
            color = pycolor->data;
        } else {
            PyErr_Clear();
            PyErr_SetString(PyExc_TypeError, "color must be a Color or tuple");
            return -1;
        }
    }

    // Validate thickness
    if (thickness < 0.0f) {
        PyErr_SetString(PyExc_ValueError, "thickness must be non-negative");
        return -1;
    }

    // Create the line
    self->data = std::make_shared<UILine>(start, end, thickness, color);
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
            PyErr_SetString(PyExc_TypeError, "on_click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

    // Initialize weak reference list
    self->weakreflist = NULL;

    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }

    // #184: Check if this is a Python subclass (for callback method support)
    PyObject* line_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Line");
    if (line_type) {
        self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != line_type;
        Py_DECREF(line_type);
    }

    return 0;
}
