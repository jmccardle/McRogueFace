#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

static PyObject* sfColor_to_PyObject(sf::Color color);
static sf::Color PyObject_to_sfColor(PyObject* obj);

class UIGrid;
class UIEntity;
class UIGridPoint;
class UIGridPointState;

typedef struct {
    PyObject_HEAD
    UIGridPoint* data;
    std::shared_ptr<UIGrid> grid;
} PyUIGridPointObject;

typedef struct {
    PyObject_HEAD
    UIGridPointState* data;
    std::shared_ptr<UIGrid> grid;
    std::shared_ptr<UIEntity> entity;
} PyUIGridPointStateObject;

// UIGridPoint - revised grid data for each point
class UIGridPoint
{
public:
    sf::Color color, color_overlay;
    bool walkable, transparent;
    int tilesprite, tile_overlay, uisprite;
    UIGridPoint();

    static int set_int_member(PyUIGridPointObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* get_color(PyUIGridPointObject* self, void* closure);
    static PyObject* get_int_member(PyUIGridPointObject* self, void* closure);
    static int set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure);
    static PyObject* get_bool_member(PyUIGridPointObject* self, void* closure);
    static int set_color(PyUIGridPointObject* self, PyObject* value, void* closure);
    static PyObject* repr(PyUIGridPointObject* self);
};

// UIGridPointState - entity-specific info for each cell
class UIGridPointState
{
public:
    bool visible, discovered;

    static PyObject* get_bool_member(PyUIGridPointStateObject* self, void* closure);
    static int set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIGridPointStateObject* self);
};

namespace mcrfpydef {
    static PyTypeObject PyUIGridPointType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.GridPoint",
        .tp_basicsize = sizeof(PyUIGridPointObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIGridPoint::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = "UIGridPoint object",
        .tp_getset = UIGridPoint::getsetters,
        //.tp_init = (initproc)PyUIGridPoint_init, // TODO Define the init function
        .tp_new = NULL, // Prevent instantiation from Python - Issue #12
    };

    static PyTypeObject PyUIGridPointStateType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.GridPointState",
        .tp_basicsize = sizeof(PyUIGridPointStateObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIGridPointState::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = "UIGridPointState object", // TODO: Add PyUIGridPointState tp_init
        .tp_getset = UIGridPointState::getsetters,
        .tp_new = NULL, // Prevent instantiation from Python - Issue #12
    };
}
