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
class UIArc;

// Python object structure
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIArc> data;
    PyObject* weakreflist;
} PyUIArcObject;

class UIArc : public UIDrawable
{
private:
    sf::Vector2f center;
    float radius;
    float start_angle;  // in degrees
    float end_angle;    // in degrees
    sf::Color color;
    float thickness;

    // Cached vertex array for rendering
    sf::VertexArray vertices;
    bool vertices_dirty;

    void rebuildVertices();

public:
    UIArc();
    UIArc(sf::Vector2f center, float radius, float startAngle, float endAngle,
          sf::Color color = sf::Color::White, float thickness = 1.0f);

    // Copy constructor and assignment
    UIArc(const UIArc& other);
    UIArc& operator=(const UIArc& other);

    // Move constructor and assignment
    UIArc(UIArc&& other) noexcept;
    UIArc& operator=(UIArc&& other) noexcept;

    // UIDrawable interface
    void render(sf::Vector2f offset, sf::RenderTarget& target) override;
    UIDrawable* click_at(sf::Vector2f point) override;
    PyObjectsEnum derived_type() override;

    // Getters and setters
    sf::Vector2f getCenter() const { return center; }
    void setCenter(sf::Vector2f c) { center = c; position = c; vertices_dirty = true; }

    float getRadius() const { return radius; }
    void setRadius(float r) { radius = r; vertices_dirty = true; }

    float getStartAngle() const { return start_angle; }
    void setStartAngle(float a) { start_angle = a; vertices_dirty = true; }

    float getEndAngle() const { return end_angle; }
    void setEndAngle(float a) { end_angle = a; vertices_dirty = true; }

    sf::Color getColor() const { return color; }
    void setColor(sf::Color c) { color = c; vertices_dirty = true; }

    float getThickness() const { return thickness; }
    void setThickness(float t) { thickness = t; vertices_dirty = true; }

    // Phase 1 virtual method implementations
    sf::FloatRect get_bounds() const override;
    void move(float dx, float dy) override;
    void resize(float w, float h) override;
    void onPositionChanged() override;

    // Property system for animations
    bool setProperty(const std::string& name, float value) override;
    bool setProperty(const std::string& name, const sf::Color& value) override;
    bool setProperty(const std::string& name, const sf::Vector2f& value) override;
    bool getProperty(const std::string& name, float& value) const override;
    bool getProperty(const std::string& name, sf::Color& value) const override;
    bool getProperty(const std::string& name, sf::Vector2f& value) const override;

    bool hasProperty(const std::string& name) const override;

    // Python API
    static PyObject* get_center(PyUIArcObject* self, void* closure);
    static int set_center(PyUIArcObject* self, PyObject* value, void* closure);
    static PyObject* get_radius(PyUIArcObject* self, void* closure);
    static int set_radius(PyUIArcObject* self, PyObject* value, void* closure);
    static PyObject* get_start_angle(PyUIArcObject* self, void* closure);
    static int set_start_angle(PyUIArcObject* self, PyObject* value, void* closure);
    static PyObject* get_end_angle(PyUIArcObject* self, void* closure);
    static int set_end_angle(PyUIArcObject* self, PyObject* value, void* closure);
    static PyObject* get_color(PyUIArcObject* self, void* closure);
    static int set_color(PyUIArcObject* self, PyObject* value, void* closure);
    static PyObject* get_thickness(PyUIArcObject* self, void* closure);
    static int set_thickness(PyUIArcObject* self, PyObject* value, void* closure);

    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIArcObject* self);
    static int init(PyUIArcObject* self, PyObject* args, PyObject* kwds);
};

// Method definitions
extern PyMethodDef UIArc_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIArcType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Arc",
        .tp_basicsize = sizeof(PyUIArcObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyUIArcObject* obj = (PyUIArcObject*)self;
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UIArc::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR(
            "Arc(center=None, radius=0, start_angle=0, end_angle=90, color=None, thickness=1, **kwargs)\n\n"
            "An arc UI element for drawing curved line segments.\n\n"
            "Args:\n"
            "    center (tuple, optional): Center position as (x, y). Default: (0, 0)\n"
            "    radius (float, optional): Arc radius in pixels. Default: 0\n"
            "    start_angle (float, optional): Starting angle in degrees. Default: 0\n"
            "    end_angle (float, optional): Ending angle in degrees. Default: 90\n"
            "    color (Color, optional): Arc color. Default: White\n"
            "    thickness (float, optional): Line thickness. Default: 1.0\n\n"
            "Keyword Args:\n"
            "    on_click (callable): Click handler. Default: None\n"
            "    visible (bool): Visibility state. Default: True\n"
            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
            "    z_index (int): Rendering order. Default: 0\n"
            "    name (str): Element name for finding. Default: None\n"
            "    align (Alignment): Alignment relative to parent. Default: None\n"
            "    margin (float): Margin from parent edge when aligned. Default: 0\n"
            "    horiz_margin (float): Horizontal margin override. Default: 0 (use margin)\n"
            "    vert_margin (float): Vertical margin override. Default: 0 (use margin)\n\n"
            "Attributes:\n"
            "    center (Vector): Center position\n"
            "    radius (float): Arc radius\n"
            "    start_angle (float): Starting angle in degrees\n"
            "    end_angle (float): Ending angle in degrees\n"
            "    color (Color): Arc color\n"
            "    thickness (float): Line thickness\n"
            "    visible (bool): Visibility state\n"
            "    opacity (float): Opacity value\n"
            "    z_index (int): Rendering order\n"
            "    name (str): Element name\n"
            "    align (Alignment): Alignment relative to parent (or None)\n"
            "    margin (float): General margin for alignment\n"
            "    horiz_margin (float): Horizontal margin override\n"
            "    vert_margin (float): Vertical margin override\n"
        ),
        .tp_methods = UIArc_methods,
        .tp_getset = UIArc::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UIArc::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyUIArcObject* self = (PyUIArcObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UIArc>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
