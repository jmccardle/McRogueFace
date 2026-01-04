#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "UIDrawable.h"
#include "UIBase.h"
#include "PyDrawable.h"
#include "PyColor.h"
#include "PyVector.h"
#include "McRFPy_Doc.h"

// Forward declaration
class UILine;

// Python object structure
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UILine> data;
    PyObject* weakreflist;
} PyUILineObject;

class UILine : public UIDrawable
{
private:
    sf::Vector2f start_pos;      // Starting point
    sf::Vector2f end_pos;        // Ending point
    sf::Color color;             // Line color
    float thickness;             // Line thickness in pixels

    // Cached vertex array for rendering
    mutable sf::VertexArray vertices;
    mutable bool vertices_dirty;

    void updateVertices() const;

public:
    UILine();
    UILine(sf::Vector2f start, sf::Vector2f end, float thickness = 1.0f, sf::Color color = sf::Color::White);

    // Copy constructor and assignment
    UILine(const UILine& other);
    UILine& operator=(const UILine& other);

    // Move constructor and assignment
    UILine(UILine&& other) noexcept;
    UILine& operator=(UILine&& other) noexcept;

    // UIDrawable interface
    void render(sf::Vector2f offset, sf::RenderTarget& target) override;
    UIDrawable* click_at(sf::Vector2f point) override;
    PyObjectsEnum derived_type() override;

    // Getters and setters
    sf::Vector2f getStart() const { return start_pos; }
    void setStart(sf::Vector2f pos) { start_pos = pos; vertices_dirty = true; }

    sf::Vector2f getEnd() const { return end_pos; }
    void setEnd(sf::Vector2f pos) { end_pos = pos; vertices_dirty = true; }

    sf::Color getColor() const { return color; }
    void setColor(sf::Color c) { color = c; vertices_dirty = true; }

    float getThickness() const { return thickness; }
    void setThickness(float t) { thickness = t; vertices_dirty = true; }

    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;

    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Color& value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Color& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    bool hasProperty(const std::string& name) const override;

    // Python API
    static PyObject* get_start(PyUILineObject* self, void* closure);
    static int set_start(PyUILineObject* self, PyObject* value, void* closure);
    static PyObject* get_end(PyUILineObject* self, void* closure);
    static int set_end(PyUILineObject* self, PyObject* value, void* closure);
    static PyObject* get_color(PyUILineObject* self, void* closure);
    static int set_color(PyUILineObject* self, PyObject* value, void* closure);
    static PyObject* get_thickness(PyUILineObject* self, void* closure);
    static int set_thickness(PyUILineObject* self, PyObject* value, void* closure);

    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUILineObject* self);
    static int init(PyUILineObject* self, PyObject* args, PyObject* kwds);
};

// Method definitions (extern to be defined in .cpp)
extern PyMethodDef UILine_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUILineType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Line",
        .tp_basicsize = sizeof(PyUILineObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyUILineObject* obj = (PyUILineObject*)self;
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UILine::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR(
            "Line(start=None, end=None, thickness=1.0, color=None, **kwargs)\n\n"
            "A line UI element for drawing straight lines between two points.\n\n"
            "Args:\n"
            "    start (tuple, optional): Starting point as (x, y). Default: (0, 0)\n"
            "    end (tuple, optional): Ending point as (x, y). Default: (0, 0)\n"
            "    thickness (float, optional): Line thickness in pixels. Default: 1.0\n"
            "    color (Color, optional): Line color. Default: White\n\n"
            "Keyword Args:\n"
            "    on_click (callable): Click handler. Default: None\n"
            "    visible (bool): Visibility state. Default: True\n"
            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
            "    z_index (int): Rendering order. Default: 0\n"
            "    name (str): Element name for finding. Default: None\n\n"
            "Attributes:\n"
            "    start (Vector): Starting point\n"
            "    end (Vector): Ending point\n"
            "    thickness (float): Line thickness\n"
            "    color (Color): Line color\n"
            "    visible (bool): Visibility state\n"
            "    opacity (float): Opacity value\n"
            "    z_index (int): Rendering order\n"
            "    name (str): Element name\n"
        ),
        .tp_methods = UILine_methods,
        .tp_getset = UILine::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UILine::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyUILineObject* self = (PyUILineObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UILine>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
