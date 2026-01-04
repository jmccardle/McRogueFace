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
class UICircle;

// Python object structure
typedef struct {
    PyObject_HEAD
    std::shared_ptr<UICircle> data;
    PyObject* weakreflist;
} PyUICircleObject;

class UICircle : public UIDrawable
{
private:
    sf::CircleShape shape;
    float radius;
    sf::Color fill_color;
    sf::Color outline_color;
    float outline_thickness;

public:
    UICircle();
    UICircle(float radius, sf::Vector2f center = sf::Vector2f(0, 0),
             sf::Color fillColor = sf::Color::White,
             sf::Color outlineColor = sf::Color::Transparent,
             float outlineThickness = 0.0f);

    // Copy constructor and assignment
    UICircle(const UICircle& other);
    UICircle& operator=(const UICircle& other);

    // Move constructor and assignment
    UICircle(UICircle&& other) noexcept;
    UICircle& operator=(UICircle&& other) noexcept;

    // UIDrawable interface
    void render(sf::Vector2f offset, sf::RenderTarget& target) override;
    UIDrawable* click_at(sf::Vector2f point) override;
    PyObjectsEnum derived_type() override;

    // Getters and setters
    float getRadius() const { return radius; }
    void setRadius(float r);

    sf::Vector2f getCenter() const { return position; }
    void setCenter(sf::Vector2f c) { position = c; }

    sf::Color getFillColor() const { return fill_color; }
    void setFillColor(sf::Color c);

    sf::Color getOutlineColor() const { return outline_color; }
    void setOutlineColor(sf::Color c);

    float getOutline() const { return outline_thickness; }
    void setOutline(float t);

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
    static PyObject* get_radius(PyUICircleObject* self, void* closure);
    static int set_radius(PyUICircleObject* self, PyObject* value, void* closure);
    static PyObject* get_center(PyUICircleObject* self, void* closure);
    static int set_center(PyUICircleObject* self, PyObject* value, void* closure);
    static PyObject* get_fill_color(PyUICircleObject* self, void* closure);
    static int set_fill_color(PyUICircleObject* self, PyObject* value, void* closure);
    static PyObject* get_outline_color(PyUICircleObject* self, void* closure);
    static int set_outline_color(PyUICircleObject* self, PyObject* value, void* closure);
    static PyObject* get_outline(PyUICircleObject* self, void* closure);
    static int set_outline(PyUICircleObject* self, PyObject* value, void* closure);

    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUICircleObject* self);
    static int init(PyUICircleObject* self, PyObject* args, PyObject* kwds);
};

// Method definitions
extern PyMethodDef UICircle_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUICircleType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Circle",
        .tp_basicsize = sizeof(PyUICircleObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self) {
            PyUICircleObject* obj = (PyUICircleObject*)self;
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)UICircle::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR(
            "Circle(radius=0, center=None, fill_color=None, outline_color=None, outline=0, **kwargs)\n\n"
            "A circle UI element for drawing filled or outlined circles.\n\n"
            "Args:\n"
            "    radius (float, optional): Circle radius in pixels. Default: 0\n"
            "    center (tuple, optional): Center position as (x, y). Default: (0, 0)\n"
            "    fill_color (Color, optional): Fill color. Default: White\n"
            "    outline_color (Color, optional): Outline color. Default: Transparent\n"
            "    outline (float, optional): Outline thickness. Default: 0 (no outline)\n\n"
            "Keyword Args:\n"
            "    on_click (callable): Click handler. Default: None\n"
            "    visible (bool): Visibility state. Default: True\n"
            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
            "    z_index (int): Rendering order. Default: 0\n"
            "    name (str): Element name for finding. Default: None\n\n"
            "Attributes:\n"
            "    radius (float): Circle radius\n"
            "    center (Vector): Center position\n"
            "    fill_color (Color): Fill color\n"
            "    outline_color (Color): Outline color\n"
            "    outline (float): Outline thickness\n"
            "    visible (bool): Visibility state\n"
            "    opacity (float): Opacity value\n"
            "    z_index (int): Rendering order\n"
            "    name (str): Element name\n"
        ),
        .tp_methods = UICircle_methods,
        .tp_getset = UICircle::getsetters,
        .tp_base = &mcrfpydef::PyDrawableType,
        .tp_init = (initproc)UICircle::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyUICircleObject* self = (PyUICircleObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<UICircle>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
