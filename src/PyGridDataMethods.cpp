// PyGridDataMethods.cpp - Python method implementations for GridData.
// #361: center_camera() moved to UIGridView (a map has no camera), and the
// UIDrawable method set is gone (a map is not a widget).
// Contains: FOV, layer management, spatial queries, camera, heightmap ops,
//           step/behavior system, py_at/subscript, and method table arrays.
#include "PyGridData.h"
#include <algorithm>
#include <vector>
#include "UIGridView.h"
#include "UIGridPathfinding.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "UIEntity.h"
#include "PyPositionHelper.h"
#include "PyVector.h"
#include "PyHeightMap.h"
#include "EntityBehavior.h"
#include "PyTrigger.h"
#include "UIBase.h"
#include "PyFOV.h"
#include "PyVisibilityMask.h"
#include "GameEngine.h"
#include "McRFPy_Doc.h"

// =========================================================================
// Cell access: py_at, subscript, mpmethods
// =========================================================================

PyObject* PyGridData::py_at(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    int x, y;

    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_w) {
        PyErr_Format(PyExc_IndexError, "x index %d is out of range [0, %d)", x, self->data->grid_w);
        return NULL;
    }
    if (y < 0 || y >= self->data->grid_h) {
        PyErr_Format(PyExc_IndexError, "y index %d is out of range [0, %d)", y, self->data->grid_h);
        return NULL;
    }

    auto type = &mcrfpydef::PyUIGridPointType;
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    obj->grid = self->data;
    obj->x = x;
    obj->y = y;
    return (PyObject*)obj;
}

PyObject* PyGridData::subscript(PyGridDataObject* self, PyObject* key)
{
    if (!PyTuple_Check(key) || PyTuple_Size(key) != 2) {
        PyErr_SetString(PyExc_TypeError, "Grid indices must be a tuple of (x, y)");
        return NULL;
    }

    PyObject* x_obj = PyTuple_GetItem(key, 0);
    PyObject* y_obj = PyTuple_GetItem(key, 1);

    if (!PyLong_Check(x_obj) || !PyLong_Check(y_obj)) {
        PyErr_SetString(PyExc_TypeError, "Grid indices must be integers");
        return NULL;
    }

    int x = PyLong_AsLong(x_obj);
    int y = PyLong_AsLong(y_obj);

    if (x < 0 || x >= self->data->grid_w) {
        PyErr_Format(PyExc_IndexError, "x index %d is out of range [0, %d)", x, self->data->grid_w);
        return NULL;
    }
    if (y < 0 || y >= self->data->grid_h) {
        PyErr_Format(PyExc_IndexError, "y index %d is out of range [0, %d)", y, self->data->grid_h);
        return NULL;
    }

    auto type = &mcrfpydef::PyUIGridPointType;
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    obj->grid = self->data;
    obj->x = x;
    obj->y = y;
    return (PyObject*)obj;
}

// Setitem on _GridData / Grid: GridPoints are views, not assignable.
static int UIGrid_subscript_assign(PyGridDataObject* self, PyObject* key, PyObject* value)
{
    (void)self; (void)key; (void)value;
    PyErr_SetString(PyExc_TypeError,
        "Grid points are not assignable; modify properties on the returned point");
    return -1;
}

PyMappingMethods PyGridData::mpmethods = {
    .mp_length = NULL,
    .mp_subscript = (binaryfunc)PyGridData::subscript,
    .mp_ass_subscript = (objobjargproc)UIGrid_subscript_assign,
};

// =========================================================================
// FOV methods
// =========================================================================

PyObject* PyGridData::py_compute_fov(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"pos", "radius", "light_walls", "algorithm", NULL};
    PyObject* pos_obj = NULL;
    int radius = 0;
    int light_walls = 1;
    PyObject* algorithm_obj = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|ipO", const_cast<char**>(kwlist),
                                     &pos_obj, &radius, &light_walls, &algorithm_obj)) {
        return NULL;
    }

    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        return NULL;
    }

    // #310: validate algorithm via PyFOV::from_arg so out-of-range ints become a
    // ValueError at the Python boundary instead of a UBSan-flagged invalid enum
    // load deep in GridData::computeFOV.
    TCOD_fov_algorithm_t algorithm = FOV_BASIC;
    if (algorithm_obj != NULL) {
        if (!PyFOV::from_arg(algorithm_obj, &algorithm)) {
            return NULL;
        }
    }

    self->data->computeFOV(x, y, radius, light_walls, algorithm);

    Py_RETURN_NONE;
}

PyObject* PyGridData::py_is_in_fov(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;
    }

    bool in_fov = self->data->isInFOV(x, y);
    return PyBool_FromLong(in_fov);
}

// =========================================================================
// observe() - masked snapshot of cell state + entities (fog-of-war, AI
// perception, replay). See PyVisibilityMask.h for the mask type itself.
// =========================================================================

PyObject* PyGridData::py_observe(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"origin", "fov_radius", "light_walls", "algorithm", NULL};
    PyObject* origin_obj = Py_None;
    PyObject* fov_radius_obj = Py_None;
    int light_walls = 1;
    PyObject* algorithm_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOpO", const_cast<char**>(kwlist),
                                     &origin_obj, &fov_radius_obj, &light_walls, &algorithm_obj)) {
        return NULL;
    }

    bool has_origin = (origin_obj != Py_None);
    bool has_radius = (fov_radius_obj != Py_None);

    // Fail Early: a radius with no origin isn't a mask at all.
    if (has_radius && !has_origin) {
        PyErr_SetString(PyExc_ValueError,
            "fov_radius requires an origin; a radius with no origin is not a mask");
        return NULL;
    }

    int ox = 0, oy = 0;
    if (has_origin) {
        if (!PyPosition_FromObjectInt(origin_obj, &ox, &oy)) {
            return NULL;
        }
        if (ox < 0 || ox >= self->data->grid_w || oy < 0 || oy >= self->data->grid_h) {
            PyErr_Format(PyExc_ValueError,
                "origin (%d, %d) is out of bounds for grid of size (%d, %d)",
                ox, oy, self->data->grid_w, self->data->grid_h);
            return NULL;
        }
    }

    // has_finite_radius distinguishes an explicit positive radius from
    // "unlimited" (fov_radius=None with an origin: FOV/occlusion still
    // applies, but nothing caps the distance). 0 is rejected -- libtcod's
    // "0 = unlimited" overload is deliberately NOT exposed here; None is the
    // unlimited spelling, so a caller-computed 0 is a real mistake.
    bool has_finite_radius = false;
    long radius_val = 0;
    if (has_radius) {
        if (!PyLong_Check(fov_radius_obj)) {
            PyErr_SetString(PyExc_TypeError, "fov_radius must be an int or None");
            return NULL;
        }
        radius_val = PyLong_AsLong(fov_radius_obj);
        if (radius_val == -1 && PyErr_Occurred()) {
            return NULL;
        }
        if (radius_val <= 0) {
            PyErr_Format(PyExc_ValueError,
                "fov_radius must be > 0 (got %ld); pass fov_radius=None for an unlimited radius",
                radius_val);
            return NULL;
        }
        has_finite_radius = true;
    }

    TCOD_fov_algorithm_t algorithm;
    if (!PyFOV::from_arg(algorithm_obj, &algorithm)) {
        return NULL;
    }

    if (!Resources::game) {
        PyErr_SetString(PyExc_RuntimeError,
            "observe() requires an initialized engine to read the current frame tick");
        return NULL;
    }
    int tick = Resources::game->getFrame();

    int w = self->data->grid_w;
    int h = self->data->grid_h;

    // ---- ONE code path builds the visibility plane, filled two different
    // ways. Nothing below this point may branch on `has_origin` again: the
    // cell projection, entity projection, and mask construction all just
    // read `visible`. ----
    std::vector<uint8_t> visible((size_t)w * h);
    if (has_origin) {
        int tcod_radius = has_finite_radius ? (int)radius_val : 0;  // 0 = unlimited, to TCOD
        // #402: computeFOVInto(), NOT computeFOV()+isInFOV(). The latter pair writes
        // and then reads the ONE shared per-grid TCOD FOV buffer, so an observe() run
        // between another caller's compute_fov() and its is_in_fov() reads silently
        // re-answered that caller's question from this origin. observe() promises a
        // result that "holds no live references"; it must also leave no live state.
        self->data->computeFOVInto(ox, oy, tcod_radius, light_walls != 0, algorithm, visible);
    } else {
        std::fill(visible.begin(), visible.end(), 1);
    }

    // Single pass over `visible`: builds the mask's ordered cell list plus
    // the walkable/transparent subsets together, so every masked cell's
    // (x, y) tuple is allocated exactly once and shared across whichever of
    // the three containers it ends up in.
    PyObject* cells_list = PyList_New(0);
    PyObject* walkable_list = PyList_New(0);
    PyObject* transparent_list = PyList_New(0);
    if (!cells_list || !walkable_list || !transparent_list) {
        Py_XDECREF(cells_list); Py_XDECREF(walkable_list); Py_XDECREF(transparent_list);
        return NULL;
    }

    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            if (!visible[(size_t)y * w + x]) continue;

            PyObject* pos = Py_BuildValue("(ii)", x, y);
            if (!pos) goto observe_alloc_fail;
            if (PyList_Append(cells_list, pos) < 0) { Py_DECREF(pos); goto observe_alloc_fail; }

            if (self->data->isWalkable(x, y)) {
                if (PyList_Append(walkable_list, pos) < 0) { Py_DECREF(pos); goto observe_alloc_fail; }
            }
            if (self->data->isTransparent(x, y)) {
                if (PyList_Append(transparent_list, pos) < 0) { Py_DECREF(pos); goto observe_alloc_fail; }
            }
            Py_DECREF(pos);
        }
    }

    {
        PyObject* cells_ordered = PyList_AsTuple(cells_list);
        Py_DECREF(cells_list);
        cells_list = NULL;
        if (!cells_ordered) { Py_DECREF(walkable_list); Py_DECREF(transparent_list); return NULL; }

        PyObject* cells_set = PyFrozenSet_New(cells_ordered);
        if (!cells_set) {
            Py_DECREF(cells_ordered); Py_DECREF(walkable_list); Py_DECREF(transparent_list);
            return NULL;
        }

        PyObject* walkable_set = PyFrozenSet_New(walkable_list);
        Py_DECREF(walkable_list);
        walkable_list = NULL;
        if (!walkable_set) {
            Py_DECREF(cells_ordered); Py_DECREF(cells_set); Py_DECREF(transparent_list);
            return NULL;
        }

        PyObject* transparent_set = PyFrozenSet_New(transparent_list);
        Py_DECREF(transparent_list);
        transparent_list = NULL;
        if (!transparent_set) {
            Py_DECREF(cells_ordered); Py_DECREF(cells_set); Py_DECREF(walkable_set);
            return NULL;
        }

        // Entity projection: only entities standing on a masked cell. A
        // second, independent pass over a different data source -- it does
        // not branch on has_origin either, only on `visible`.
        PyObject* entities_list = PyList_New(0);
        if (!entities_list) {
            Py_DECREF(cells_ordered); Py_DECREF(cells_set);
            Py_DECREF(walkable_set); Py_DECREF(transparent_set);
            return NULL;
        }

        if (self->data->entities) {
            for (const auto& entity : *self->data->entities) {
                if (!entity) continue;
                int ex = entity->cell_position.x;
                int ey = entity->cell_position.y;
                if (ex < 0 || ex >= w || ey < 0 || ey >= h) continue;
                if (!visible[(size_t)ey * w + ex]) continue;

                PyObject* labels = PyFrozenSet_New(NULL);
                if (!labels) { Py_DECREF(entities_list); Py_DECREF(cells_ordered); Py_DECREF(cells_set); Py_DECREF(walkable_set); Py_DECREF(transparent_set); return NULL; }
                for (const auto& label : entity->labels) {
                    PyObject* label_str = PyUnicode_FromString(label.c_str());
                    if (!label_str || PySet_Add(labels, label_str) < 0) {
                        Py_XDECREF(label_str); Py_DECREF(labels);
                        Py_DECREF(entities_list); Py_DECREF(cells_ordered); Py_DECREF(cells_set);
                        Py_DECREF(walkable_set); Py_DECREF(transparent_set);
                        return NULL;
                    }
                    Py_DECREF(label_str);
                }

                PyObject* entity_dict = Py_BuildValue(
                    "{s:s, s:(ii), s:N, s:i}",
                    "name", entity->sprite.name.c_str(),
                    "cell_pos", ex, ey,
                    "labels", labels,
                    "turn_order", entity->turn_order);
                if (!entity_dict) {
                    Py_DECREF(entities_list); Py_DECREF(cells_ordered); Py_DECREF(cells_set);
                    Py_DECREF(walkable_set); Py_DECREF(transparent_set);
                    return NULL;
                }
                if (PyList_Append(entities_list, entity_dict) < 0) {
                    Py_DECREF(entity_dict);
                    Py_DECREF(entities_list); Py_DECREF(cells_ordered); Py_DECREF(cells_set);
                    Py_DECREF(walkable_set); Py_DECREF(transparent_set);
                    return NULL;
                }
                Py_DECREF(entity_dict);
            }
        }

        PyObject* entities_tuple = PyList_AsTuple(entities_list);
        Py_DECREF(entities_list);
        if (!entities_tuple) {
            Py_DECREF(cells_ordered); Py_DECREF(cells_set);
            Py_DECREF(walkable_set); Py_DECREF(transparent_set);
            return NULL;
        }

        // Mask metadata: origin/fov_radius as the Python-visible None-means-
        // unbounded/unlimited spelling (independent of the internal tcod_radius
        // 0-means-unlimited encoding used to compute `visible` above).
        PyObject* mask_origin;
        if (has_origin) {
            mask_origin = Py_BuildValue("(ii)", ox, oy);
        } else {
            Py_INCREF(Py_None);
            mask_origin = Py_None;
        }
        PyObject* mask_radius;
        if (has_finite_radius) {
            mask_radius = PyLong_FromLong(radius_val);
        } else {
            Py_INCREF(Py_None);
            mask_radius = Py_None;
        }
        if (!mask_origin || !mask_radius) {
            Py_XDECREF(mask_origin); Py_XDECREF(mask_radius);
            Py_DECREF(cells_ordered); Py_DECREF(cells_set);
            Py_DECREF(walkable_set); Py_DECREF(transparent_set); Py_DECREF(entities_tuple);
            return NULL;
        }

        // create() steals cells_set, cells_ordered, mask_origin, mask_radius.
        // #404: has_origin is exactly "an FOV computation ran". Without an origin the
        // plane is std::fill(1) and light_walls/algorithm were never consulted, so the
        // mask reports them as None rather than as inert-but-plausible values.
        PyObject* mask = PyVisibilityMask::create(cells_set, cells_ordered, mask_origin, mask_radius,
                                                  tick, w, h, has_origin,
                                                  light_walls != 0, (int)algorithm);
        if (!mask) {
            Py_DECREF(walkable_set); Py_DECREF(transparent_set); Py_DECREF(entities_tuple);
            return NULL;
        }

        // "N" steals the reference for mask/walkable_set/transparent_set/
        // entities_tuple, which we already own; "i" copies the plain int tick.
        PyObject* result = Py_BuildValue("{s:i, s:N, s:N, s:N, s:N}",
            "tick", tick,
            "mask", mask,
            "walkable", walkable_set,
            "transparent", transparent_set,
            "entities", entities_tuple);
        return result;
    }

observe_alloc_fail:
    Py_XDECREF(cells_list);
    Py_XDECREF(walkable_list);
    Py_XDECREF(transparent_list);
    return NULL;
}

// =========================================================================
// Layer management
// =========================================================================

PyObject* PyGridData::py_add_layer(PyGridDataObject* self, PyObject* args) {
    PyObject* layer_obj;
    if (!PyArg_ParseTuple(args, "O", &layer_obj)) {
        return NULL;
    }

    auto* color_layer_type = (PyObject*)&mcrfpydef::PyColorLayerType;
    auto* tile_layer_type = (PyObject*)&mcrfpydef::PyTileLayerType;

    std::shared_ptr<GridLayer> layer;
    PyObject* py_layer_ref = nullptr;

    if (PyObject_IsInstance(layer_obj, color_layer_type)) {
        PyColorLayerObject* py_layer = (PyColorLayerObject*)layer_obj;
        if (!py_layer->data) {
            PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
            return NULL;
        }

        if (py_layer->grid && py_layer->grid.get() != self->data.get()) {
            PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
            return NULL;
        }

        layer = py_layer->data;
        py_layer_ref = layer_obj;

        if (!layer->name.empty() && GridData::isProtectedLayerName(layer->name)) {
            PyErr_Format(PyExc_ValueError, "Layer name '%s' is reserved", layer->name.c_str());
            return NULL;
        }

        if (!layer->name.empty()) {
            auto existing = self->data->getLayerByName(layer->name);
            if (existing && existing.get() != layer.get()) {
                existing->parent_grid = nullptr;
                self->data->removeLayer(existing);
            }
        }

        if (layer->grid_x == 0 && layer->grid_y == 0) {
            layer->resize(self->data->grid_w, self->data->grid_h);
        } else if (layer->grid_x != self->data->grid_w || layer->grid_y != self->data->grid_h) {
            PyErr_Format(PyExc_ValueError,
                "Layer size (%d, %d) does not match Grid size (%d, %d)",
                layer->grid_x, layer->grid_y, self->data->grid_w, self->data->grid_h);
            return NULL;
        }

        layer->parent_grid = self->data.get();
        self->data->layers.push_back(layer);
        self->data->layers_need_sort = true;
        py_layer->grid = self->data;

    } else if (PyObject_IsInstance(layer_obj, tile_layer_type)) {
        PyTileLayerObject* py_layer = (PyTileLayerObject*)layer_obj;
        if (!py_layer->data) {
            PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
            return NULL;
        }

        if (py_layer->grid && py_layer->grid.get() != self->data.get()) {
            PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
            return NULL;
        }

        layer = py_layer->data;
        py_layer_ref = layer_obj;

        if (!layer->name.empty() && GridData::isProtectedLayerName(layer->name)) {
            PyErr_Format(PyExc_ValueError, "Layer name '%s' is reserved", layer->name.c_str());
            return NULL;
        }

        if (!layer->name.empty()) {
            auto existing = self->data->getLayerByName(layer->name);
            if (existing && existing.get() != layer.get()) {
                existing->parent_grid = nullptr;
                self->data->removeLayer(existing);
            }
        }

        if (layer->grid_x == 0 && layer->grid_y == 0) {
            layer->resize(self->data->grid_w, self->data->grid_h);
        } else if (layer->grid_x != self->data->grid_w || layer->grid_y != self->data->grid_h) {
            PyErr_Format(PyExc_ValueError,
                "Layer size (%d, %d) does not match Grid size (%d, %d)",
                layer->grid_x, layer->grid_y, self->data->grid_w, self->data->grid_h);
            return NULL;
        }

        layer->parent_grid = self->data.get();
        self->data->layers.push_back(layer);
        self->data->layers_need_sort = true;
        py_layer->grid = self->data;

        auto tile_layer = std::static_pointer_cast<TileLayer>(layer);
        if (!tile_layer->texture) {
            tile_layer->texture = self->data->getTexture();
        }

    } else {
        PyErr_SetString(PyExc_TypeError, "layer must be a ColorLayer or TileLayer");
        return NULL;
    }

    Py_INCREF(py_layer_ref);
    return py_layer_ref;
}

PyObject* PyGridData::py_remove_layer(PyGridDataObject* self, PyObject* args) {
    PyObject* layer_obj;
    if (!PyArg_ParseTuple(args, "O", &layer_obj)) {
        return NULL;
    }

    if (PyUnicode_Check(layer_obj)) {
        const char* name_str = PyUnicode_AsUTF8(layer_obj);
        if (!name_str) return NULL;

        auto layer = self->data->getLayerByName(std::string(name_str));
        if (!layer) {
            PyErr_Format(PyExc_KeyError, "Layer '%s' not found", name_str);
            return NULL;
        }

        layer->parent_grid = nullptr;
        self->data->removeLayer(layer);
        Py_RETURN_NONE;
    }

    if (PyObject_IsInstance(layer_obj, (PyObject*)&mcrfpydef::PyColorLayerType)) {
        auto* py_layer = (PyColorLayerObject*)layer_obj;
        if (py_layer->data) {
            py_layer->data->parent_grid = nullptr;
            self->data->removeLayer(py_layer->data);
            py_layer->grid.reset();
        }
        Py_RETURN_NONE;
    }

    if (PyObject_IsInstance(layer_obj, (PyObject*)&mcrfpydef::PyTileLayerType)) {
        auto* py_layer = (PyTileLayerObject*)layer_obj;
        if (py_layer->data) {
            py_layer->data->parent_grid = nullptr;
            self->data->removeLayer(py_layer->data);
            py_layer->grid.reset();
        }
        Py_RETURN_NONE;
    }

    PyErr_SetString(PyExc_TypeError, "layer must be a string (layer name), ColorLayer, or TileLayer");
    return NULL;
}

PyObject* PyGridData::py_layer(PyGridDataObject* self, PyObject* args) {
    const char* name_str;
    if (!PyArg_ParseTuple(args, "s", &name_str)) {
        return NULL;
    }

    auto layer = self->data->getLayerByName(std::string(name_str));
    if (!layer) {
        Py_RETURN_NONE;
    }

    if (layer->type == GridLayerType::Color) {
        auto* type = &mcrfpydef::PyColorLayerType;
        PyColorLayerObject* obj = (PyColorLayerObject*)type->tp_alloc(type, 0);
        if (!obj) return NULL;

        obj->data = std::static_pointer_cast<ColorLayer>(layer);
        obj->grid = self->data;
        return (PyObject*)obj;
    } else {
        auto* type = &mcrfpydef::PyTileLayerType;
        PyTileLayerObject* obj = (PyTileLayerObject*)type->tp_alloc(type, 0);
        if (!obj) return NULL;

        obj->data = std::static_pointer_cast<TileLayer>(layer);
        obj->grid = self->data;
        return (PyObject*)obj;
    }
}

// =========================================================================
// Spatial queries
// =========================================================================

PyObject* PyGridData::py_entities_in_radius(PyGridDataObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"pos", "radius", NULL};
    PyObject* pos_obj;
    float radius;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "Of", const_cast<char**>(kwlist),
                                     &pos_obj, &radius)) {
        return NULL;
    }

    float x, y;
    if (!PyPosition_FromObject(pos_obj, &x, &y)) {
        return NULL;
    }

    if (radius < 0) {
        PyErr_SetString(PyExc_ValueError, "radius must be non-negative");
        return NULL;
    }

    auto entities = self->data->spatial_hash.queryRadius(x, y, radius);

    PyObject* result = PyList_New(entities.size());
    if (!result) return PyErr_NoMemory();

    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;

    for (size_t i = 0; i < entities.size(); i++) {
        auto& entity = entities[i];

        PyObject* py_entity = nullptr;
        if (entity->serial_number != 0) {
            py_entity = PythonObjectCache::getInstance().lookup(entity->serial_number);
        }
        if (!py_entity) {
            auto pyEntity = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
            if (!pyEntity) {
                Py_DECREF(result);
                return PyErr_NoMemory();
            }
            pyEntity->data = entity;
            pyEntity->weakreflist = NULL;
            py_entity = (PyObject*)pyEntity;
        }
        PyList_SET_ITEM(result, i, py_entity);
    }

    return result;
}

// =========================================================================
// HeightMap application methods
// =========================================================================

PyObject* PyGridData::py_apply_threshold(PyGridDataObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"source", "range", "walkable", "transparent", nullptr};
    PyObject* source_obj = nullptr;
    PyObject* range_obj = nullptr;
    PyObject* walkable_obj = Py_None;
    PyObject* transparent_obj = Py_None;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|OO", const_cast<char**>(keywords),
                                     &source_obj, &range_obj, &walkable_obj, &transparent_obj)) {
        return nullptr;
    }

    if (!PyObject_IsInstance(source_obj, (PyObject*)&mcrfpydef::PyHeightMapType)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return nullptr;
    }
    PyHeightMapObject* hmap = (PyHeightMapObject*)source_obj;

    if (!hmap->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (!PyTuple_Check(range_obj) || PyTuple_Size(range_obj) != 2) {
        PyErr_SetString(PyExc_TypeError, "range must be a tuple of (min, max)");
        return nullptr;
    }

    float range_min = (float)PyFloat_AsDouble(PyTuple_GetItem(range_obj, 0));
    float range_max = (float)PyFloat_AsDouble(PyTuple_GetItem(range_obj, 1));

    if (PyErr_Occurred()) {
        return nullptr;
    }

    if (hmap->heightmap->w != self->data->grid_w || hmap->heightmap->h != self->data->grid_h) {
        PyErr_Format(PyExc_ValueError,
            "HeightMap size (%d, %d) does not match Grid size (%d, %d)",
            hmap->heightmap->w, hmap->heightmap->h, self->data->grid_w, self->data->grid_h);
        return nullptr;
    }

    bool set_walkable = (walkable_obj != Py_None);
    bool set_transparent = (transparent_obj != Py_None);
    bool walkable_value = false;
    bool transparent_value = false;

    if (set_walkable) {
        walkable_value = PyObject_IsTrue(walkable_obj);
    }
    if (set_transparent) {
        transparent_value = PyObject_IsTrue(transparent_obj);
    }

    for (int y = 0; y < self->data->grid_h; y++) {
        for (int x = 0; x < self->data->grid_w; x++) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);
            if (value >= range_min && value <= range_max) {
                if (set_walkable) {
                    self->data->setWalkable(x, y, walkable_value);
                }
                if (set_transparent) {
                    self->data->setTransparent(x, y, transparent_value);
                }
            }
        }
    }

    if (self->data->getTCODMap()) {
        self->data->syncTCODMap();
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

PyObject* PyGridData::py_apply_ranges(PyGridDataObject* self, PyObject* args) {
    PyObject* source_obj = nullptr;
    PyObject* ranges_obj = nullptr;

    if (!PyArg_ParseTuple(args, "OO", &source_obj, &ranges_obj)) {
        return nullptr;
    }

    if (!PyObject_IsInstance(source_obj, (PyObject*)&mcrfpydef::PyHeightMapType)) {
        PyErr_SetString(PyExc_TypeError, "source must be a HeightMap");
        return nullptr;
    }
    PyHeightMapObject* hmap = (PyHeightMapObject*)source_obj;

    if (!hmap->heightmap) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap not initialized");
        return nullptr;
    }

    if (!PyList_Check(ranges_obj)) {
        PyErr_SetString(PyExc_TypeError, "ranges must be a list");
        return nullptr;
    }

    if (hmap->heightmap->w != self->data->grid_w || hmap->heightmap->h != self->data->grid_h) {
        PyErr_Format(PyExc_ValueError,
            "HeightMap size (%d, %d) does not match Grid size (%d, %d)",
            hmap->heightmap->w, hmap->heightmap->h, self->data->grid_w, self->data->grid_h);
        return nullptr;
    }

    struct RangeEntry {
        float min, max;
        bool set_walkable, set_transparent;
        bool walkable_value, transparent_value;
    };
    std::vector<RangeEntry> entries;

    Py_ssize_t num_ranges = PyList_Size(ranges_obj);
    for (Py_ssize_t i = 0; i < num_ranges; i++) {
        PyObject* entry = PyList_GetItem(ranges_obj, i);

        if (!PyTuple_Check(entry) || PyTuple_Size(entry) != 2) {
            PyErr_Format(PyExc_TypeError,
                "ranges[%zd] must be a tuple of (range, properties_dict)", i);
            return nullptr;
        }

        PyObject* range_tuple = PyTuple_GetItem(entry, 0);
        PyObject* props_dict = PyTuple_GetItem(entry, 1);

        if (!PyTuple_Check(range_tuple) || PyTuple_Size(range_tuple) != 2) {
            PyErr_Format(PyExc_TypeError,
                "ranges[%zd] range must be a tuple of (min, max)", i);
            return nullptr;
        }

        if (!PyDict_Check(props_dict)) {
            PyErr_Format(PyExc_TypeError,
                "ranges[%zd] properties must be a dict", i);
            return nullptr;
        }

        RangeEntry re;
        re.min = (float)PyFloat_AsDouble(PyTuple_GetItem(range_tuple, 0));
        re.max = (float)PyFloat_AsDouble(PyTuple_GetItem(range_tuple, 1));

        if (PyErr_Occurred()) {
            return nullptr;
        }

        PyObject* walkable_val = PyDict_GetItemString(props_dict, "walkable");
        re.set_walkable = (walkable_val != nullptr);
        if (re.set_walkable) {
            re.walkable_value = PyObject_IsTrue(walkable_val);
        }

        PyObject* transparent_val = PyDict_GetItemString(props_dict, "transparent");
        re.set_transparent = (transparent_val != nullptr);
        if (re.set_transparent) {
            re.transparent_value = PyObject_IsTrue(transparent_val);
        }

        entries.push_back(re);
    }

    for (int y = 0; y < self->data->grid_h; y++) {
        for (int x = 0; x < self->data->grid_w; x++) {
            float value = TCOD_heightmap_get_value(hmap->heightmap, x, y);

            for (const auto& re : entries) {
                if (value >= re.min && value <= re.max) {
                    if (re.set_walkable) {
                        self->data->setWalkable(x, y, re.walkable_value);
                    }
                    if (re.set_transparent) {
                        self->data->setTransparent(x, y, re.transparent_value);
                    }
                    break;
                }
            }
        }
    }

    if (self->data->getTCODMap()) {
        self->data->syncTCODMap();
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// =========================================================================
// Step / turn-based behavior system
// =========================================================================

static void fireStepCallback(std::shared_ptr<UIEntity>& entity, int trigger_int, PyObject* data) {
    PyObject* callback = entity->step_callback;

    if (!callback && entity->pyobject) {
        PyObject* step_attr = PyObject_GetAttrString(entity->pyobject, "on_step");
        if (step_attr && PyCallable_Check(step_attr)) {
            callback = step_attr;
        } else {
            PyErr_Clear();
            Py_XDECREF(step_attr);
            return;
        }
        PyObject* trigger_obj = nullptr;
        if (PyTrigger::trigger_enum_class) {
            trigger_obj = PyObject_CallFunction(PyTrigger::trigger_enum_class, "i", trigger_int);
        }
        if (!trigger_obj) {
            PyErr_Clear();
            trigger_obj = PyLong_FromLong(trigger_int);
        }
        if (!data) data = Py_None;
        PyObject* result = PyObject_CallFunction(callback, "OO", trigger_obj, data);
        Py_XDECREF(result);
        if (PyErr_Occurred()) PyErr_Print();
        Py_DECREF(trigger_obj);
        Py_DECREF(step_attr);
        return;
    }

    if (!callback) return;

    PyObject* trigger_obj = nullptr;
    if (PyTrigger::trigger_enum_class) {
        trigger_obj = PyObject_CallFunction(PyTrigger::trigger_enum_class, "i", trigger_int);
    }
    if (!trigger_obj) {
        PyErr_Clear();
        trigger_obj = PyLong_FromLong(trigger_int);
    }

    if (!data) data = Py_None;
    PyObject* result = PyObject_CallFunction(callback, "OO", trigger_obj, data);
    Py_XDECREF(result);
    if (PyErr_Occurred()) PyErr_Print();
    Py_DECREF(trigger_obj);
}

PyObject* PyGridData::py_step(PyGridDataObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"n", "turn_order", nullptr};
    int n = 1;
    PyObject* turn_order_filter = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iO", const_cast<char**>(kwlist),
                                     &n, &turn_order_filter)) {
        return NULL;
    }

    int filter_turn_order = -1;
    if (turn_order_filter && turn_order_filter != Py_None) {
        filter_turn_order = PyLong_AsLong(turn_order_filter);
        if (filter_turn_order == -1 && PyErr_Occurred()) return NULL;
    }

    auto& grid = self->data;
    if (!grid->entities) Py_RETURN_NONE;

    // #351 - the turn manager mutates entity positions directly (bypassing the
    // Python setters that invalidate the view). Track whether any entity moved
    // so we can invalidate the view's render cache once after all rounds.
    bool content_changed = false;

    for (int round = 0; round < n; round++) {
        std::vector<std::shared_ptr<UIEntity>> snapshot;
        for (auto& entity : *grid->entities) {
            if (entity->turn_order == 0) continue;
            if (filter_turn_order >= 0 && entity->turn_order != filter_turn_order) continue;
            snapshot.push_back(entity);
        }

        std::sort(snapshot.begin(), snapshot.end(),
            [](const auto& a, const auto& b) { return a->turn_order < b->turn_order; });

        for (auto& entity : snapshot) {
            if (!entity->grid) continue;
            if (entity->behavior.type == BehaviorType::IDLE) continue;

            if (!entity->target_label.empty()) {
                auto nearby = grid->spatial_hash.queryRadius(
                    static_cast<float>(entity->cell_position.x),
                    static_cast<float>(entity->cell_position.y),
                    static_cast<float>(entity->sight_radius));

                std::vector<std::shared_ptr<UIEntity>> matching_targets;
                for (auto& candidate : nearby) {
                    if (candidate.get() != entity.get() &&
                        candidate->labels.count(entity->target_label)) {
                        matching_targets.push_back(candidate);
                    }
                }

                if (!matching_targets.empty()) {
                    auto& cache = entity->target_fov_cache;

                    if (!cache.isValid(entity->cell_position, entity->sight_radius,
                                       grid->transparency_generation)) {
                        grid->computeFOV(entity->cell_position.x, entity->cell_position.y,
                                        entity->sight_radius, true, grid->fov_algorithm);

                        int r = entity->sight_radius;
                        int side = 2 * r + 1;
                        cache.origin = entity->cell_position;
                        cache.radius = r;
                        cache.transparency_gen = grid->transparency_generation;
                        cache.vis_side = side;
                        cache.visibility.resize(side * side);
                        for (int dy = -r; dy <= r; dy++) {
                            for (int dx = -r; dx <= r; dx++) {
                                cache.visibility[(dy + r) * side + (dx + r)] =
                                    grid->isInFOV(entity->cell_position.x + dx,
                                                  entity->cell_position.y + dy);
                            }
                        }
                    }

                    for (auto& target : matching_targets) {
                        if (cache.isVisible(target->cell_position.x,
                                           target->cell_position.y)) {
                            PyObject* target_pyobj = Py_None;
                            if (target->pyobject) {
                                target_pyobj = target->pyobject;
                            }
                            fireStepCallback(entity, 2 /* TARGET */, target_pyobj);
                            goto next_entity;
                        }
                    }
                }
            }

            {
                BehaviorOutput output = executeBehavior(*entity, *grid);

                switch (output.result) {
                    case BehaviorResult::MOVED: {
                        int old_x = entity->cell_position.x;
                        int old_y = entity->cell_position.y;
                        entity->cell_position = output.target_cell;
                        grid->spatial_hash.updateCell(entity, old_x, old_y);

                        entity->position = sf::Vector2f(
                            static_cast<float>(output.target_cell.x),
                            static_cast<float>(output.target_cell.y));
                        content_changed = true;  // #351 - view render cache is now stale
                        break;
                    }
                    case BehaviorResult::DONE: {
                        fireStepCallback(entity, 0 /* DONE */, Py_None);
                        entity->behavior.type = static_cast<BehaviorType>(entity->default_behavior);
                        break;
                    }
                    case BehaviorResult::BLOCKED: {
                        PyObject* blocker = Py_None;
                        auto blockers = grid->spatial_hash.queryCell(
                            output.target_cell.x, output.target_cell.y);
                        if (!blockers.empty() && blockers[0]->pyobject) {
                            blocker = blockers[0]->pyobject;
                        }
                        fireStepCallback(entity, 1 /* BLOCKED */, blocker);
                        break;
                    }
                    case BehaviorResult::NO_ACTION:
                        break;
                }
            }
            next_entity:;
        }
    }

    // #351 - invalidate the view's render early-out once if anything moved.
    if (content_changed) grid->markCompositeDirty();

    Py_RETURN_NONE;
}

// =========================================================================
// Method tables
// =========================================================================

typedef PyGridDataObject PyObjectType;

PyMethodDef PyGridData_all_methods[] = {
    {"at", (PyCFunction)PyGridData::py_at, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, at,
         MCRF_SIG("(x: int, y: int)", "GridPoint"),
         MCRF_DESC("Return the GridPoint cell at grid coordinates (x, y)."),
         MCRF_ARGS_START
         MCRF_ARG("x", "Column index (0-based)")
         MCRF_ARG("y", "Row index (0-based)")
         MCRF_RETURNS("GridPoint: the cell at the given position")
         MCRF_RAISES("IndexError", "If x or y is out of range")
         MCRF_NOTE("Also accepts a single positional tuple/list/Vector: at((x, y)) or at(vec), or keyword form: at(pos=(x, y)).")
     )},
    {"compute_fov", (PyCFunction)PyGridData::py_compute_fov, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, compute_fov,
         MCRF_SIG("(pos, radius: int = 0, light_walls: bool = True, algorithm: FOV | int = FOV.BASIC)", "None"),
         MCRF_DESC("Compute field of view from a position. Updates the internal FOV state; use is_in_fov() to query visibility."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, list, or Vector")
         MCRF_ARG("radius", "Maximum view distance (0 = unlimited)")
         MCRF_ARG("light_walls", "Whether walls are lit when visible")
         MCRF_ARG("algorithm", "FOV algorithm to use (FOV.BASIC, FOV.DIAMOND, FOV.SHADOW, FOV.PERMISSIVE_0-8)")
         MCRF_RETURNS("None")
     )},
    {"is_in_fov", (PyCFunction)PyGridData::py_is_in_fov, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, is_in_fov,
         MCRF_SIG("(x: int, y: int)", "bool"),
         MCRF_DESC("Check if a cell is in the field of view. Must call compute_fov() first to calculate visibility."),
         MCRF_ARGS_START
         MCRF_ARG("x", "Column index (0-based)")
         MCRF_ARG("y", "Row index (0-based)")
         MCRF_RETURNS("True if the cell is visible, False otherwise")
         MCRF_NOTE("Also accepts a single positional tuple/list/Vector: is_in_fov((x, y)) or is_in_fov(vec), or keyword form: is_in_fov(pos=(x, y)).")
     )},
    {"observe", (PyCFunction)PyGridData::py_observe, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, observe,
         MCRF_SIG("(origin=None, fov_radius: int = None, light_walls: bool = True, algorithm: FOV | int = FOV.BASIC)", "dict"),
         MCRF_DESC("Take an immutable snapshot of this map as seen through a field of view: which cells "
             "are visible, which of those are walkable or transparent, and which entities stand on a "
             "visible cell. Use this for fog-of-war persistence, AI perception queries, or replaying what "
             "an observer could see at a point in time -- the returned dict holds no live references and "
             "is unaffected by later grid or entity changes.")
         MCRF_ARGS_START
         MCRF_ARG("origin", "Observing position as (x, y) tuple, list, or Vector. None (the default) "
             "means an unbounded mask: every in-bounds cell is visible and no FOV state is touched at all.")
         MCRF_ARG("fov_radius", "Maximum view distance from origin. None (the default) means an "
             "unlimited radius -- occlusion from walls still applies if origin is given. Must be > 0 "
             "when given: 0 is a ValueError, not 'unlimited', because a caller-computed radius of 0 "
             "means 'see nothing', not 'see everything'.")
         MCRF_ARG("light_walls", "Whether walls are themselves visible when lit, passed through to the "
             "FOV computation exactly as compute_fov() would use it. Ignored when origin is None.")
         MCRF_ARG("algorithm", "FOV algorithm to use (FOV.BASIC, FOV.DIAMOND, FOV.SHADOW, "
             "FOV.PERMISSIVE_0-8, FOV.RESTRICTIVE, FOV.SYMMETRIC_SHADOWCAST). Ignored when origin is None.")
         MCRF_RETURNS("dict with keys: 'tick' (int, engine current_frame read once at the projection "
             "instant), 'mask' (VisibilityMask, the cells this projection could see), 'walkable' "
             "(frozenset of (x,y) tuples, the subset of mask.cells that are walkable), 'transparent' "
             "(frozenset of (x,y) tuples, the subset of mask.cells that are transparent), and 'entities' "
             "(tuple of dict, one per entity standing on a masked cell -- each with keys 'name' (str), "
             "'cell_pos' ((x,y) tuple), 'labels' (frozenset of str), and 'turn_order' (int)).")
         MCRF_RAISES("ValueError", "fov_radius is given without an origin, origin is out of bounds for "
             "this grid, or fov_radius <= 0")
         MCRF_RAISES("TypeError", "origin is not a valid position, or fov_radius/algorithm is the wrong type")
         MCRF_RAISES("RuntimeError", "The engine is not initialized, so there is no current_frame tick to record")
         MCRF_NOTE("An entity's 'cell_pos' is a plain (x, y) int tuple, NOT the live entity.cell_pos "
             "Vector -- the snapshot is inert: hashable, serialisable, and unaffected by later entity movement.")
         MCRF_NOTE("'labels' is a frozenset, so membership is a real predicate: "
             "label in snap['entities'][i]['labels'].")
         MCRF_NOTE("'entities' is a tuple, not a dict keyed by name: entity names are not unique and may "
             "be empty, so keying by name here would silently discard entities. The caller chooses the "
             "collision policy.")
         MCRF_NOTE("Terrain is given as two cell sets rather than a per-cell record: (x, y) in "
             "snap['walkable']. A cell absent from 'walkable' is either not walkable OR not observed -- "
             "check snap['mask'] to tell those apart. That distinction is deliberate: it is the entire "
             "point of a masked projection.")
         MCRF_NOTE("Grid layers are NOT projected. They are appearance, not world state.")
         MCRF_NOTE("The tick is read once, at the projection instant, and is the same value carried by "
             "mask.tick. Calling observe() inside mcrfpy.lock() is what makes that instant a frame barrier.")
         MCRF_NOTE("observe() is side-effect-free with or without an origin (#402): it computes its FOV "
             "in a scratch buffer private to the call and never writes the shared per-grid FOV state that "
             "compute_fov()/is_in_fov() use. A background observer projecting from an NPC's position "
             "therefore cannot disturb a field of view the player or the renderer just computed, and two "
             "observers on one grid do not interfere.")
         MCRF_NOTE("observe() never advances a frame and never releases the GIL: the snapshot is atomic "
             "with respect to other Python threads. It does NOT take the lock for you -- wrap the call "
             "in mcrfpy.lock() yourself when you need it to be atomic with respect to the frame.")
     )},
    {"find_path", (PyCFunction)UIGridPathfinding::Grid_find_path, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, find_path,
         MCRF_SIG("(start, end, diagonal_cost: float = 1.41, collide: str = None, heuristic = None, weight: float = 1.0)", "AStarPath | None"),
         MCRF_DESC("Compute A* path between two points. The returned AStarPath can be iterated or walked step-by-step."),
         MCRF_ARGS_START
         MCRF_ARG("start", "Starting position as Vector, Entity, or (x, y) tuple")
         MCRF_ARG("end", "Target position as Vector, Entity, or (x, y) tuple")
         MCRF_ARG("diagonal_cost", "Cost of diagonal movement (default: 1.41)")
         MCRF_ARG("collide", "Label string. Entities with this label block pathfinding.")
         MCRF_ARG("heuristic", "Heuristic enum member, string name, or int (EUCLIDEAN=0, MANHATTAN=1, CHEBYSHEV=2). None uses default (Euclidean).")
         MCRF_ARG("weight", "Heuristic weight multiplier. Values > 1.0 trade optimality for speed (weighted A*).")
         MCRF_RETURNS("AStarPath object if path exists, None otherwise")
     )},
    {"get_dijkstra_map", (PyCFunction)UIGridPathfinding::Grid_get_dijkstra_map, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, get_dijkstra_map,
         MCRF_SIG("(root=None, diagonal_cost: float = 1.41, collide: str = None, roots=None)", "DijkstraMap"),
         MCRF_DESC("Get or create a cached Dijkstra distance map for a root position. Call clear_dijkstra_maps() after changing grid walkability to invalidate."),
         MCRF_ARGS_START
         MCRF_ARG("root", "Root position as Vector, Entity, or (x, y) tuple. Use 'root' for single-source maps (cached by position).")
         MCRF_ARG("diagonal_cost", "Cost of diagonal movement (default: 1.41)")
         MCRF_ARG("collide", "Label string. Entities with this label block pathfinding.")
         MCRF_ARG("roots", "Sequence of root positions or a DiscreteMap mask for multi-source Dijkstra. Pass 'roots' instead of 'root' for multi-source maps (not cached).")
         MCRF_RETURNS("DijkstraMap object for querying distances and paths")
     )},
    {"clear_dijkstra_maps", (PyCFunction)UIGridPathfinding::Grid_clear_dijkstra_maps, METH_NOARGS,
     MCRF_METHOD(GridData, clear_dijkstra_maps,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Clear all cached Dijkstra maps. Call this after modifying grid cell walkability to ensure pathfinding uses updated walkability data.")
     )},
    {"add_layer", (PyCFunction)PyGridData::py_add_layer, METH_VARARGS,
     MCRF_METHOD(GridData, add_layer,
         MCRF_SIG("(layer: ColorLayer | TileLayer)", "ColorLayer | TileLayer"),
         MCRF_DESC("Add a layer to the grid. Layers with size (0, 0) are automatically resized to match the grid."),
         MCRF_ARGS_START
         MCRF_ARG("layer", "A ColorLayer or TileLayer object. Named layers replace any existing layer with the same name.")
         MCRF_RETURNS("The added layer object")
         MCRF_RAISES("ValueError", "If layer is already attached to another grid, or if layer size doesn't match grid (and isn't (0,0))")
         MCRF_RAISES("TypeError", "If argument is not a ColorLayer or TileLayer")
     )},
    {"remove_layer", (PyCFunction)PyGridData::py_remove_layer, METH_VARARGS,
     MCRF_METHOD(GridData, remove_layer,
         MCRF_SIG("(name_or_layer: str | ColorLayer | TileLayer)", "None"),
         MCRF_DESC("Remove a layer from the grid by name or by object reference."),
         MCRF_ARGS_START
         MCRF_ARG("name_or_layer", "Either a layer name (str) or the layer object itself")
         MCRF_RAISES("KeyError", "If name is provided but no layer with that name exists")
         MCRF_RAISES("TypeError", "If argument is not a string, ColorLayer, or TileLayer")
     )},
    {"layer", (PyCFunction)PyGridData::py_layer, METH_VARARGS,
     MCRF_METHOD(GridData, layer,
         MCRF_SIG("(name: str)", "ColorLayer | TileLayer | None"),
         MCRF_DESC("Get a layer by its name."),
         MCRF_ARGS_START
         MCRF_ARG("name", "The name of the layer to find")
         MCRF_RETURNS("The layer with the specified name, or None if not found")
     )},
    {"entities_in_radius", (PyCFunction)PyGridData::py_entities_in_radius, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, entities_in_radius,
         MCRF_SIG("(pos: tuple | Vector, radius: float)", "list"),
         MCRF_DESC("Query entities within radius using spatial hash (O(k) where k = nearby entities)."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Center position as (x, y) tuple, Vector, or other 2-element sequence")
         MCRF_ARG("radius", "Search radius")
         MCRF_RETURNS("List of Entity objects within the radius")
     )},
    {"apply_threshold", (PyCFunction)PyGridData::py_apply_threshold, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, apply_threshold,
         MCRF_SIG("(source: HeightMap, range: tuple, walkable: bool = None, transparent: bool = None)", "GridData"),
         MCRF_DESC("Apply walkable/transparent properties to cells where heightmap values fall within range."),
         MCRF_ARGS_START
         MCRF_ARG("source", "HeightMap with values to check. Must match grid size.")
         MCRF_ARG("range", "Tuple of (min, max) - cells with values in this range are affected")
         MCRF_ARG("walkable", "If not None, set walkable to this value for cells in range")
         MCRF_ARG("transparent", "If not None, set transparent to this value for cells in range")
         MCRF_RETURNS("GridData: self, for method chaining")
         MCRF_RAISES("ValueError", "If HeightMap size doesn't match grid size")
     )},
    {"apply_ranges", (PyCFunction)PyGridData::py_apply_ranges, METH_VARARGS,
     MCRF_METHOD(GridData, apply_ranges,
         MCRF_SIG("(source: HeightMap, ranges: list)", "GridData"),
         MCRF_DESC("Apply multiple walkability thresholds to the grid in a single pass."),
         MCRF_ARGS_START
         MCRF_ARG("source", "HeightMap with values to check. Must match grid size.")
         MCRF_ARG("ranges", "List of (range_tuple, properties_dict) tuples where range_tuple=(min,max) and properties_dict has 'walkable'/'transparent' keys")
         MCRF_RETURNS("GridData: self, for method chaining")
     )},
    {"step", (PyCFunction)PyGridData::py_step, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(GridData, step,
         MCRF_SIG("(n: int = 1, turn_order: int = None)", "None"),
         MCRF_DESC("Execute n rounds of turn-based entity behavior. Each round: entities grouped by turn_order (ascending), behaviors executed, triggers fired (TARGET, DONE, BLOCKED), movement animated."),
         MCRF_ARGS_START
         MCRF_ARG("n", "Number of rounds to execute (default: 1)")
         MCRF_ARG("turn_order", "If provided, only process entities with this turn_order value")
     )},
    {NULL}
};
