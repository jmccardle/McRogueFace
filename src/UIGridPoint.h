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
class UIGridPointState;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> grid;
    int x, y;  // Grid coordinates - compute data pointer on access
} PyUIGridPointObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIGrid> grid;
    std::shared_ptr<UIEntity> entity;
    int x, y;  // Position in grid - compute state on access
} PyUIGridPointStateObject;

// UIGridPoint - grid cell data for pathfinding and layer access
// #150 - Layer-related properties (color, tilesprite, etc.) removed; now handled by layers
class UIGridPoint
{
public:
    bool walkable, transparent;  // Pathfinding/FOV properties
    int grid_x, grid_y;          // Position in parent grid
    GridData* parent_grid;       // Parent grid reference for TCOD sync (#252)
    UIGridPoint();

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

// UIGridPointState - entity-specific info for each cell
class UIGridPointState
{
public:
    bool visible, discovered;

    static PyObject* get_bool_member(PyUIGridPointStateObject* self, void* closure);
    static int set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure);
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIGridPointStateObject* self);

    // #16 - point property: access to GridPoint (None if not discovered)
    static PyObject* get_point(PyUIGridPointStateObject* self, void* closure);
};

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
            "GridPoint — a single cell in a Grid.\n\n"
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

    // #189 - Use inline instead of static to ensure single instance across translation units
    inline PyTypeObject PyUIGridPointStateType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.GridPointState",
        .tp_basicsize = sizeof(PyUIGridPointStateObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIGridPointState::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "GridPointState — per-entity visibility state for a grid cell.\n\n"
            "Obtained via entity.gridstate. Cannot be constructed directly.\n\n"
            "Properties:\n"
            "    visible (bool): Whether this cell is currently in the entity's FOV.\n"
            "    discovered (bool): Whether this cell has ever been seen.\n"
            "    point (GridPoint, read-only): The underlying GridPoint, or None.\n"
        ),
        .tp_getset = UIGridPointState::getsetters,
        .tp_new = NULL, // Prevent instantiation from Python - Issue #12
    };
}
