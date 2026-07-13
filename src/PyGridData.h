#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>
#include <libtcod.h>
#include <mutex>
#include <optional>
#include <map>
#include <memory>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyDrawable.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

#include "UIGridPoint.h"
#include "UIEntity.h"
#include "UIDrawable.h"
#include "UIBase.h"
#include "GridLayers.h"
#include "SpatialHash.h"
#include "UIEntityCollection.h"  // EntityCollection types (extracted from UIGrid)
#include "GridData.h"  // #252 - Data layer base class
#include "UIGridView.h"  // #252 - GridView shim

// Forward declaration for pathfinding
class DijkstraMap;

// PyGridData - the Python binding layer for GridData (mcrfpy.GridData).
//
// #361: there is no longer a C++ `UIGrid` class. It used to inherit BOTH
// UIDrawable and GridData, which meant every map dragged a second, redundant
// camera and RenderTexture around, and appending one to a scene drew the map a
// second time through that frozen camera. GridData is a MAP -- no position, no
// size, no render() -- and UIGridView is the only widget. This struct holds
// nothing but the static binding functions; it is never instantiated.
struct PyGridData
{
    // Shared by GridData::init and UIGridView::init (the Grid() factory path):
    // attaches an iterable of ColorLayer/TileLayer objects to a fresh GridData,
    // lazily sizing any layer left at (0,0). Returns -1 with a Python exception
    // set on failure. layers_obj == nullptr means "default tilesprite layer";
    // Py_None means "no layers at all" (entity storage + pathfinding only).
    static int apply_layers_arg(const std::shared_ptr<GridData>& grid,
                                PyObject* layers_obj,
                                std::shared_ptr<PyTexture> default_texture);

    // Parses grid_size/grid_w/grid_h/texture into a validated (w, h, texture)
    // triple. Returns -1 with an exception set on failure.
    static int parse_grid_shape(PyObject* grid_size_obj, PyObject* texture_obj,
                                int& grid_w, int& grid_h,
                                std::shared_ptr<PyTexture>& texture_out);

    // Builds (or reuses) the one Python wrapper for a GridData (#348 identity).
    static PyObject* pyobject_for(const std::shared_ptr<GridData>& grid);

    static int init(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* get_grid_size(PyGridDataObject* self, void* closure);
    static PyObject* get_grid_w(PyGridDataObject* self, void* closure);
    static PyObject* get_grid_h(PyGridDataObject* self, void* closure);
    static PyObject* get_texture(PyGridDataObject* self, void* closure);
    static PyObject* get_fov(PyGridDataObject* self, void* closure);
    static int set_fov(PyGridDataObject* self, PyObject* value, void* closure);
    static PyObject* get_fov_radius(PyGridDataObject* self, void* closure);
    static int set_fov_radius(PyGridDataObject* self, PyObject* value, void* closure);
    static PyObject* py_at(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_compute_fov(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_is_in_fov(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_entities_in_radius(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_apply_threshold(PyGridDataObject* self, PyObject* args, PyObject* kwds);
    static PyObject* py_apply_ranges(PyGridDataObject* self, PyObject* args);
    static PyObject* py_step(PyGridDataObject* self, PyObject* args, PyObject* kwds);

    static PyGetSetDef getsetters[];
    static PyMappingMethods mpmethods;
    static PyObject* subscript(PyGridDataObject* self, PyObject* key);
    static PyObject* get_entities(PyGridDataObject* self, void* closure);
    // #364: get_children lives on UIGridView -- overlay children belong to the view.
    static PyObject* repr(PyGridDataObject* self);

    static PyObject* py_add_layer(PyGridDataObject* self, PyObject* args);
    static PyObject* py_remove_layer(PyGridDataObject* self, PyObject* args);
    static PyObject* get_layers(PyGridDataObject* self, void* closure);
    static PyObject* py_layer(PyGridDataObject* self, PyObject* args);
};

// UIEntityCollection types are now in UIEntityCollection.h

// Forward declaration of methods array
extern PyMethodDef PyGridData_all_methods[];

namespace mcrfpydef {
    inline PyTypeObject PyGridDataType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        // #361: public, and NOT a Drawable subclass -- tp_base is left null
        // (i.e. `object`). Appending one to scene.children raises TypeError.
        .tp_name = "mcrfpy.GridData",
        .tp_basicsize = sizeof(PyGridDataObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)[](PyObject* self)
        {
            PyGridDataObject* obj = (PyGridDataObject*)self;
            PyObject_GC_UnTrack(self);
            if (obj->weakreflist != NULL) {
                PyObject_ClearWeakRefs(self);
            }
            // #361: no click/hover callbacks to unregister -- a map is not a
            // widget and receives no input. Cell callbacks live on UIGridView
            // (#355), overlay children on UIGridView (#364).
            obj->data.reset();
            Py_TYPE(self)->tp_free(self);
        },
        .tp_repr = (reprfunc)PyGridData::repr,
        .tp_as_mapping = &PyGridData::mpmethods,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
        .tp_doc = PyDoc_STR("GridData(grid_size=None, texture=None, layers=None)\n\n"
                            "A tile map: cells, entities, layers, FOV and pathfinding state.\n\n"
                            "GridData is DATA, not a widget -- it has no position, no size, no\n"
                            "camera, and is never drawn. Appending one to a scene raises TypeError.\n"
                            "To display it, point one or more Grid (GridView) cameras at it:\n\n"
                            "    data = mcrfpy.GridData(grid_size=(80, 40))\n"
                            "    main = mcrfpy.Grid(grid=data, pos=(0, 0), size=(800, 400))\n"
                            "    mini = mcrfpy.Grid(grid=data, pos=(820, 0), size=(160, 80))\n\n"
                            "Both views show the same map and the same entities, each through its\n"
                            "own camera. A map with no view at all is perfectly valid (an offscreen\n"
                            "level, still steppable and queryable).\n\n"
                            "mcrfpy.Grid(grid_size=...) is sugar for a GridView that creates its own\n"
                            "GridData; reach it with `grid.grid_data`.\n\n"
                            "Args:\n"
                            "    grid_size (tuple): Grid dimensions as (grid_w, grid_h). Default: (2, 2)\n"
                            "    texture (Texture): Tile atlas; defines the cell size in pixels.\n"
                            "    layers (list): ColorLayer/TileLayer objects. Omit for a default\n"
                            "        'tilesprite' TileLayer; pass None for no layers at all.\n\n"
                            "Attributes:\n"
                            "    grid_size (Vector, read-only): Dimensions in tiles\n"
                            "    grid_w, grid_h (int, read-only): Dimensions in tiles\n"
                            "    texture (Texture, read-only): Tile atlas\n"
                            "    entities (EntityCollection): Entities on this map\n"
                            "    layers (tuple, read-only): Layers sorted by z_index\n"
                            "    fov (FOV): Default field-of-view algorithm\n"
                            "    fov_radius (int): Default field-of-view radius"),
        .tp_traverse = [](PyObject* self, visitproc visit, void* arg) -> int {
            // #361: a GridData holds no Python callbacks -- nothing to visit.
            (void)self; (void)visit; (void)arg;
            return 0;
        },
        .tp_clear = [](PyObject* self) -> int {
            (void)self;
            return 0;
        },
        .tp_methods = PyGridData_all_methods,
        .tp_getset = PyGridData::getsetters,
        .tp_init = (initproc)PyGridData::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject*
        {
            PyGridDataObject* self = (PyGridDataObject*)type->tp_alloc(type, 0);
            if (self) {
                self->data = std::make_shared<GridData>();
                self->weakreflist = nullptr;
            }
            return (PyObject*)self;
        }
    };
}
