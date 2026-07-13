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
class GridData;
class UIEntity;
class UIGridPoint;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<GridData> grid;
    int x, y;  // Grid coordinates - compute data pointer on access
} PyUIGridPointObject;

// UIGridPoint - namespaces the Python GridPoint type's accessors.
// #150 - Layer-related properties (color, tilesprite, etc.) removed; now handled by layers.
// #332 - per-cell data (walkable/transparent) moved to GridData's dense uint8
// planes (SoA); this class no longer stores cell state. The Python wrapper
// (PyUIGridPointObject) holds (grid, x, y) and reads/writes via GridData accessors.
class UIGridPoint
{
public:
    // Built-in property accessors (walkable, transparent only)
    static PyGetSetDef getsetters[];
    static int set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure);
    static PyObject* get_bool_member(PyUIGridPointObject* self, void* closure);
    static PyObject* repr(PyUIGridPointObject* self);

    // #114 - entities property: list of entities at this cell
    static PyObject* get_entities(PyUIGridPointObject* self, void* closure);

    // #177 - grid_pos property: grid coordinates as tuple
    static PyObject* get_grid_pos(PyUIGridPointObject* self, void* closure);

    // #150 - Dynamic property access for named layers
    static PyObject* getattro(PyUIGridPointObject* self, PyObject* name);
    static int setattro(PyUIGridPointObject* self, PyObject* name, PyObject* value);
};

// UIGridPointState / PyUIGridPointStateType removed in #294.
// Per-entity visibility memory now lives on UIEntity::perspective_map as a
// DiscreteMap (3-state: 0=unknown, 1=discovered, 2=visible). See mcrfpy.Perspective.

namespace mcrfpydef {
    // #189 - Use inline instead of static to ensure single instance across translation units
    inline PyTypeObject PyUIGridPointType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.GridPoint",
        .tp_basicsize = sizeof(PyUIGridPointObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIGridPoint::repr,
        // #150 - Dynamic attribute access for named layers
        .tp_getattro = (getattrofunc)UIGridPoint::getattro,
        .tp_setattro = (setattrofunc)UIGridPoint::setattro,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "GridPoint -- a single cell in a Grid.\n\n"
            "Obtained via grid.at(x, y). Cannot be constructed directly.\n\n"
            "Properties:\n"
            "    walkable (bool): Whether entities can traverse this cell.\n"
            "    transparent (bool): Whether this cell allows line-of-sight.\n"
            "    entities (list, read-only): Entities currently on this cell.\n"
            "    grid_pos (tuple, read-only): (x, y) position in the grid.\n\n"
            "Named layer data is accessible as dynamic attributes.\n"
        ),
        .tp_getset = UIGridPoint::getsetters,
        //.tp_init = (initproc)PyUIGridPoint_init, // TODO Define the init function
        .tp_new = NULL, // Prevent instantiation from Python - Issue #12
    };
}
