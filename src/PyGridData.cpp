// PyGridData.cpp - Python bindings for GridData (mcrfpy.GridData).
//
// #361: this file used to define `class UIGrid : public UIDrawable, public
// GridData` -- a map that was also a widget, carrying a second camera and
// RenderTexture that no user ever saw. GridData is now pure data (GridData.cpp)
// and UIGridView is the only widget. What remains here is the binding layer:
// construction, properties, and the shared helpers the Grid() factory path in
// UIGridView needs.
#include "PyGridData.h"
#include "UIGridView.h"
#include "UIGridPathfinding.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "UIEntity.h"
#include "PyFOV.h"
#include "PyVector.h"
#include <algorithm>
#include <cmath>
#include <cstring>
#include <limits>

// =========================================================================
// Shared construction helpers (used by GridData() and by Grid()/GridView)
// =========================================================================

int PyGridData::parse_grid_shape(PyObject* grid_size_obj, PyObject* texture_obj,
                                 int& grid_w, int& grid_h,
                                 std::shared_ptr<PyTexture>& texture_out)
{
    if (grid_size_obj) {
        if (!PyTuple_Check(grid_size_obj) || PyTuple_Size(grid_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a tuple (grid_w, grid_h)");
            return -1;
        }
        PyObject* gx_val = PyTuple_GetItem(grid_size_obj, 0);
        PyObject* gy_val = PyTuple_GetItem(grid_size_obj, 1);
        if (!PyLong_Check(gx_val) || !PyLong_Check(gy_val)) {
            PyErr_SetString(PyExc_TypeError, "grid_size tuple must contain integers");
            return -1;
        }
        grid_w = PyLong_AsLong(gx_val);
        grid_h = PyLong_AsLong(gy_val);
    }

    if (grid_w <= 0 || grid_h <= 0) {
        PyErr_SetString(PyExc_ValueError, "Grid dimensions must be positive integers");
        return -1;
    }
    if (grid_w > GRID_MAX || grid_h > GRID_MAX) {  // #212
        PyErr_Format(PyExc_ValueError,
            "Grid dimensions cannot exceed %d (got %dx%d)", GRID_MAX, grid_w, grid_h);
        return -1;
    }

    if (texture_obj && texture_obj != Py_None) {
        if (!PyObject_IsInstance(texture_obj, (PyObject*)&mcrfpydef::PyTextureType)) {
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
            return -1;
        }
        texture_out = reinterpret_cast<PyTextureObject*>(texture_obj)->data;
    } else {
        texture_out = McRFPy_API::default_texture;
    }
    return 0;
}

// Attach one layer object (already type-checked) to `grid`. Returns -1 with an
// exception set on failure.
static int attach_layer(const std::shared_ptr<GridData>& grid,
                        const std::shared_ptr<GridLayer>& layer)
{
    if (!layer->name.empty() && GridData::isProtectedLayerName(layer->name)) {
        PyErr_Format(PyExc_ValueError, "Layer name '%s' is reserved", layer->name.c_str());
        return -1;
    }
    if (!layer->name.empty()) {
        auto existing = grid->getLayerByName(layer->name);
        if (existing) {
            existing->parent_grid = nullptr;
            grid->removeLayer(existing);
        }
    }
    // Lazy allocation: a layer left at (0,0) adopts the grid's dimensions.
    if (layer->grid_x == 0 && layer->grid_y == 0) {
        layer->resize(grid->grid_w, grid->grid_h);
    } else if (layer->grid_x != grid->grid_w || layer->grid_y != grid->grid_h) {
        PyErr_Format(PyExc_ValueError,
            "Layer size (%d, %d) does not match Grid size (%d, %d)",
            layer->grid_x, layer->grid_y, grid->grid_w, grid->grid_h);
        return -1;
    }
    layer->parent_grid = grid.get();
    grid->layers.push_back(layer);
    return 0;
}

int PyGridData::apply_layers_arg(const std::shared_ptr<GridData>& grid,
                                 PyObject* layers_obj,
                                 std::shared_ptr<PyTexture> default_texture)
{
    // Omitted -> one default TileLayer named "tilesprite" (z_index -1, below entities).
    if (layers_obj == nullptr) {
        grid->addTileLayer(-1, default_texture, "tilesprite");
        return 0;
    }
    // Explicit None -> no rendering layers (entity storage + pathfinding only).
    if (layers_obj == Py_None) return 0;

    PyObject* iterator = PyObject_GetIter(layers_obj);
    if (!iterator) {
        PyErr_SetString(PyExc_TypeError,
            "layers must be an iterable of ColorLayer or TileLayer objects");
        return -1;
    }

    auto* color_layer_type = (PyObject*)&mcrfpydef::PyColorLayerType;
    auto* tile_layer_type  = (PyObject*)&mcrfpydef::PyTileLayerType;

    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        bool is_color = PyObject_IsInstance(item, color_layer_type);
        bool is_tile  = PyObject_IsInstance(item, tile_layer_type);
        if (!is_color && !is_tile) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError,
                "layers must contain only ColorLayer or TileLayer objects");
            return -1;
        }

        // Both wrapper types share the same {data, grid} prefix layout, but read
        // them through their own types rather than punning.
        std::shared_ptr<GridLayer> layer;
        bool already_attached = false;
        if (is_color) {
            auto* py_layer = (PyColorLayerObject*)item;
            if (!py_layer->data) {
                Py_DECREF(item); Py_DECREF(iterator);
                PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
                return -1;
            }
            already_attached = (bool)py_layer->grid;
            layer = py_layer->data;
        } else {
            auto* py_layer = (PyTileLayerObject*)item;
            if (!py_layer->data) {
                Py_DECREF(item); Py_DECREF(iterator);
                PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
                return -1;
            }
            already_attached = (bool)py_layer->grid;
            layer = py_layer->data;
        }

        if (already_attached) {
            Py_DECREF(item); Py_DECREF(iterator);
            PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
            return -1;
        }

        if (attach_layer(grid, layer) < 0) {
            Py_DECREF(item); Py_DECREF(iterator);
            return -1;
        }

        if (is_color) {
            ((PyColorLayerObject*)item)->grid = grid;
        } else {
            auto* py_layer = (PyTileLayerObject*)item;
            py_layer->grid = grid;
            // #254 - a TileLayer with no texture of its own inherits the grid's.
            auto tile_layer_ptr = std::static_pointer_cast<TileLayer>(layer);
            if (!tile_layer_ptr->texture) {
                tile_layer_ptr->texture = grid->getTexture();
            }
        }

        Py_DECREF(item);
    }

    Py_DECREF(iterator);
    if (PyErr_Occurred()) return -1;

    grid->layers_need_sort = true;
    return 0;
}

// #348/#361 - One Python wrapper per GridData. `entity.grid`, `view.grid_data`
// and the layer/GridPoint back-references must all hand back the SAME object,
// so identity (`a.grid is b.grid`) holds and repeated attribute access does not
// churn allocations.
PyObject* PyGridData::pyobject_for(const std::shared_ptr<GridData>& grid)
{
    if (!grid) Py_RETURN_NONE;

    if (grid->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(grid->serial_number);
        if (cached) return cached;  // new strong ref
    }

    auto* type = &mcrfpydef::PyGridDataType;
    auto* obj = (PyGridDataObject*)type->tp_alloc(type, 0);
    if (!obj) return nullptr;
    obj->data = grid;
    obj->weakreflist = NULL;

    if (grid->serial_number == 0) {
        grid->serial_number = PythonObjectCache::getInstance().assignSerial();
    }
    PyObject* weakref = PyWeakref_NewRef((PyObject*)obj, NULL);
    if (weakref) {
        PythonObjectCache::getInstance().registerObject(grid->serial_number, weakref);
        Py_DECREF(weakref);
    }
    return (PyObject*)obj;
}

// =========================================================================
// GridData(grid_size=..., texture=..., layers=...)
// =========================================================================

int PyGridData::init(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    PyObject* grid_size_obj = nullptr;
    PyObject* texture_obj = nullptr;
    PyObject* layers_obj = nullptr;
    int grid_w = 2, grid_h = 2;

    static const char* kwlist[] = {
        "grid_size", "texture", "layers", "grid_w", "grid_h", nullptr
    };

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOii", const_cast<char**>(kwlist),
                                     &grid_size_obj, &texture_obj, &layers_obj,
                                     &grid_w, &grid_h)) {
        return -1;
    }

    std::shared_ptr<PyTexture> texture;
    if (parse_grid_shape(grid_size_obj, texture_obj, grid_w, grid_h, texture) < 0) {
        return -1;
    }

    self->data = std::make_shared<GridData>(grid_w, grid_h, texture);

    if (apply_layers_arg(self->data, layers_obj, texture) < 0) {
        return -1;
    }

    self->weakreflist = NULL;

    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }

    return 0;
}
