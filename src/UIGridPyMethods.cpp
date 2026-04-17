// UIGridPyMethods.cpp — Python method implementations for UIGrid
// Extracted from UIGrid.cpp (#149) for maintainability.
// Contains: FOV, layer management, spatial queries, camera, heightmap ops,
//           step/behavior system, py_at/subscript, and method table arrays.
#include "UIGrid.h"
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

// =========================================================================
// Cell access: py_at, subscript, mpmethods
// =========================================================================

PyObject* UIGrid::py_at(PyUIGridObject* self, PyObject* args, PyObject* kwds)
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

PyObject* UIGrid::subscript(PyUIGridObject* self, PyObject* key)
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

PyMappingMethods UIGrid::mpmethods = {
    .mp_length = NULL,
    .mp_subscript = (binaryfunc)UIGrid::subscript,
    .mp_ass_subscript = NULL
};

// =========================================================================
// FOV methods
// =========================================================================

PyObject* UIGrid::py_compute_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds)
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

PyObject* UIGrid::py_is_in_fov(PyUIGridObject* self, PyObject* args, PyObject* kwds)
{
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;
    }

    bool in_fov = self->data->isInFOV(x, y);
    return PyBool_FromLong(in_fov);
}

// =========================================================================
// Layer management
// =========================================================================

PyObject* UIGrid::py_add_layer(PyUIGridObject* self, PyObject* args) {
    PyObject* layer_obj;
    if (!PyArg_ParseTuple(args, "O", &layer_obj)) {
        return NULL;
    }

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_layer_type = PyObject_GetAttrString(mcrfpy_module, "ColorLayer");
    auto* tile_layer_type = PyObject_GetAttrString(mcrfpy_module, "TileLayer");
    Py_DECREF(mcrfpy_module);

    if (!color_layer_type || !tile_layer_type) {
        if (color_layer_type) Py_DECREF(color_layer_type);
        if (tile_layer_type) Py_DECREF(tile_layer_type);
        return NULL;
    }

    std::shared_ptr<GridLayer> layer;
    PyObject* py_layer_ref = nullptr;

    if (PyObject_IsInstance(layer_obj, color_layer_type)) {
        PyColorLayerObject* py_layer = (PyColorLayerObject*)layer_obj;
        if (!py_layer->data) {
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
            PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
            return NULL;
        }

        if (py_layer->grid && py_layer->grid.get() != self->data.get()) {
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
            PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
            return NULL;
        }

        layer = py_layer->data;
        py_layer_ref = layer_obj;

        if (!layer->name.empty() && UIGrid::isProtectedLayerName(layer->name)) {
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
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
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
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
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
            PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
            return NULL;
        }

        if (py_layer->grid && py_layer->grid.get() != self->data.get()) {
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
            PyErr_SetString(PyExc_ValueError, "Layer is already attached to another Grid");
            return NULL;
        }

        layer = py_layer->data;
        py_layer_ref = layer_obj;

        if (!layer->name.empty() && UIGrid::isProtectedLayerName(layer->name)) {
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
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
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
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
        Py_DECREF(color_layer_type);
        Py_DECREF(tile_layer_type);
        PyErr_SetString(PyExc_TypeError, "layer must be a ColorLayer or TileLayer");
        return NULL;
    }

    Py_DECREF(color_layer_type);
    Py_DECREF(tile_layer_type);

    Py_INCREF(py_layer_ref);
    return py_layer_ref;
}

PyObject* UIGrid::py_remove_layer(PyUIGridObject* self, PyObject* args) {
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

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_layer_type = PyObject_GetAttrString(mcrfpy_module, "ColorLayer");
    if (color_layer_type && PyObject_IsInstance(layer_obj, color_layer_type)) {
        Py_DECREF(color_layer_type);
        Py_DECREF(mcrfpy_module);
        auto* py_layer = (PyColorLayerObject*)layer_obj;
        if (py_layer->data) {
            py_layer->data->parent_grid = nullptr;
            self->data->removeLayer(py_layer->data);
            py_layer->grid.reset();
        }
        Py_RETURN_NONE;
    }
    if (color_layer_type) Py_DECREF(color_layer_type);

    auto* tile_layer_type = PyObject_GetAttrString(mcrfpy_module, "TileLayer");
    if (tile_layer_type && PyObject_IsInstance(layer_obj, tile_layer_type)) {
        Py_DECREF(tile_layer_type);
        Py_DECREF(mcrfpy_module);
        auto* py_layer = (PyTileLayerObject*)layer_obj;
        if (py_layer->data) {
            py_layer->data->parent_grid = nullptr;
            self->data->removeLayer(py_layer->data);
            py_layer->grid.reset();
        }
        Py_RETURN_NONE;
    }
    if (tile_layer_type) Py_DECREF(tile_layer_type);

    Py_DECREF(mcrfpy_module);
    PyErr_SetString(PyExc_TypeError, "layer must be a string (layer name), ColorLayer, or TileLayer");
    return NULL;
}

PyObject* UIGrid::py_layer(PyUIGridObject* self, PyObject* args) {
    const char* name_str;
    if (!PyArg_ParseTuple(args, "s", &name_str)) {
        return NULL;
    }

    auto layer = self->data->getLayerByName(std::string(name_str));
    if (!layer) {
        Py_RETURN_NONE;
    }

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    if (layer->type == GridLayerType::Color) {
        auto* type = (PyTypeObject*)PyObject_GetAttrString(mcrfpy_module, "ColorLayer");
        Py_DECREF(mcrfpy_module);
        if (!type) return NULL;

        PyColorLayerObject* obj = (PyColorLayerObject*)type->tp_alloc(type, 0);
        Py_DECREF(type);
        if (!obj) return NULL;

        obj->data = std::static_pointer_cast<ColorLayer>(layer);
        obj->grid = self->data;
        return (PyObject*)obj;
    } else {
        auto* type = (PyTypeObject*)PyObject_GetAttrString(mcrfpy_module, "TileLayer");
        Py_DECREF(mcrfpy_module);
        if (!type) return NULL;

        PyTileLayerObject* obj = (PyTileLayerObject*)type->tp_alloc(type, 0);
        Py_DECREF(type);
        if (!obj) return NULL;

        obj->data = std::static_pointer_cast<TileLayer>(layer);
        obj->grid = self->data;
        return (PyObject*)obj;
    }
}

// =========================================================================
// Spatial queries
// =========================================================================

PyObject* UIGrid::py_entities_in_radius(PyUIGridObject* self, PyObject* args, PyObject* kwds)
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
// Camera positioning
// =========================================================================

void UIGrid::center_camera() {
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    center_x = (grid_w / 2.0f) * cell_width;
    center_y = (grid_h / 2.0f) * cell_height;
    markDirty();
}

void UIGrid::center_camera(float tile_x, float tile_y) {
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    float half_viewport_x = box.getSize().x / zoom / 2.0f;
    float half_viewport_y = box.getSize().y / zoom / 2.0f;
    center_x = tile_x * cell_width + half_viewport_x;
    center_y = tile_y * cell_height + half_viewport_y;
    markDirty();
}

PyObject* UIGrid::py_center_camera(PyUIGridObject* self, PyObject* args) {
    PyObject* pos_arg = nullptr;

    if (!PyArg_ParseTuple(args, "|O", &pos_arg)) {
        return nullptr;
    }

    if (pos_arg == nullptr || pos_arg == Py_None) {
        self->data->center_camera();
    } else if (PyTuple_Check(pos_arg) && PyTuple_Size(pos_arg) == 2) {
        PyObject* x_obj = PyTuple_GetItem(pos_arg, 0);
        PyObject* y_obj = PyTuple_GetItem(pos_arg, 1);

        float tile_x, tile_y;
        if (PyFloat_Check(x_obj)) {
            tile_x = PyFloat_AsDouble(x_obj);
        } else if (PyLong_Check(x_obj)) {
            tile_x = (float)PyLong_AsLong(x_obj);
        } else {
            PyErr_SetString(PyExc_TypeError, "tile coordinates must be numeric");
            return nullptr;
        }

        if (PyFloat_Check(y_obj)) {
            tile_y = PyFloat_AsDouble(y_obj);
        } else if (PyLong_Check(y_obj)) {
            tile_y = (float)PyLong_AsLong(y_obj);
        } else {
            PyErr_SetString(PyExc_TypeError, "tile coordinates must be numeric");
            return nullptr;
        }

        self->data->center_camera(tile_x, tile_y);
    } else {
        PyErr_SetString(PyExc_TypeError, "center_camera() takes an optional tuple (tile_x, tile_y)");
        return nullptr;
    }

    Py_RETURN_NONE;
}

// =========================================================================
// HeightMap application methods
// =========================================================================

PyObject* UIGrid::py_apply_threshold(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
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
                UIGridPoint& point = self->data->at(x, y);
                if (set_walkable) {
                    point.walkable = walkable_value;
                }
                if (set_transparent) {
                    point.transparent = transparent_value;
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

PyObject* UIGrid::py_apply_ranges(PyUIGridObject* self, PyObject* args) {
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
            UIGridPoint& point = self->data->at(x, y);

            for (const auto& re : entries) {
                if (value >= re.min && value <= re.max) {
                    if (re.set_walkable) {
                        point.walkable = re.walkable_value;
                    }
                    if (re.set_transparent) {
                        point.transparent = re.transparent_value;
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

PyObject* UIGrid::py_step(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
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

                        if (entity->move_speed > 0) {
                            entity->position = sf::Vector2f(
                                static_cast<float>(output.target_cell.x),
                                static_cast<float>(output.target_cell.y));
                        } else {
                            entity->position = sf::Vector2f(
                                static_cast<float>(output.target_cell.x),
                                static_cast<float>(output.target_cell.y));
                        }
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

    Py_RETURN_NONE;
}

// =========================================================================
// Method tables
// =========================================================================

PyMethodDef UIGrid::methods[] = {
    {"at", (PyCFunction)UIGrid::py_at, METH_VARARGS | METH_KEYWORDS},
    {"compute_fov", (PyCFunction)UIGrid::py_compute_fov, METH_VARARGS | METH_KEYWORDS,
     "compute_fov(pos, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> None\n\n"
     "Compute field of view from a position.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    radius: Maximum view distance (0 = unlimited)\n"
     "    light_walls: Whether walls are lit when visible\n"
     "    algorithm: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)\n\n"
     "Updates the internal FOV state. Use is_in_fov(pos) to query visibility."},
    {"is_in_fov", (PyCFunction)UIGrid::py_is_in_fov, METH_VARARGS | METH_KEYWORDS,
     "is_in_fov(pos) -> bool\n\n"
     "Check if a cell is in the field of view.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n\n"
     "Returns:\n"
     "    True if the cell is visible, False otherwise\n\n"
     "Must call compute_fov() first to calculate visibility."},
    {"find_path", (PyCFunction)UIGridPathfinding::Grid_find_path, METH_VARARGS | METH_KEYWORDS,
     "find_path(start, end, diagonal_cost=1.41, collide=None) -> AStarPath | None\n\n"
     "Compute A* path between two points.\n\n"
     "Args:\n"
     "    start: Starting position as Vector, Entity, or (x, y) tuple\n"
     "    end: Target position as Vector, Entity, or (x, y) tuple\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n"
     "    collide: Label string. Entities with this label block pathfinding.\n\n"
     "Returns:\n"
     "    AStarPath object if path exists, None otherwise.\n\n"
     "The returned AStarPath can be iterated or walked step-by-step."},
    {"get_dijkstra_map", (PyCFunction)UIGridPathfinding::Grid_get_dijkstra_map, METH_VARARGS | METH_KEYWORDS,
     "get_dijkstra_map(root, diagonal_cost=1.41, collide=None) -> DijkstraMap\n\n"
     "Get or create a Dijkstra distance map for a root position.\n\n"
     "Args:\n"
     "    root: Root position as Vector, Entity, or (x, y) tuple\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n"
     "    collide: Label string. Entities with this label block pathfinding.\n\n"
     "Returns:\n"
     "    DijkstraMap object for querying distances and paths.\n\n"
     "Grid caches DijkstraMaps by (root, collide) key. Multiple requests for\n"
     "the same root and collide label return the same cached map. Call\n"
     "clear_dijkstra_maps() after changing grid walkability to invalidate."},
    {"clear_dijkstra_maps", (PyCFunction)UIGridPathfinding::Grid_clear_dijkstra_maps, METH_NOARGS,
     "clear_dijkstra_maps() -> None\n\n"
     "Clear all cached Dijkstra maps.\n\n"
     "Call this after modifying grid cell walkability to ensure pathfinding\n"
     "uses updated walkability data."},
    {"add_layer", (PyCFunction)UIGrid::py_add_layer, METH_VARARGS,
     "add_layer(layer: ColorLayer | TileLayer) -> ColorLayer | TileLayer"},
    {"remove_layer", (PyCFunction)UIGrid::py_remove_layer, METH_VARARGS,
     "remove_layer(name_or_layer: str | ColorLayer | TileLayer) -> None"},
    {"layer", (PyCFunction)UIGrid::py_layer, METH_VARARGS,
     "layer(name: str) -> ColorLayer | TileLayer | None"},
    {"entities_in_radius", (PyCFunction)UIGrid::py_entities_in_radius, METH_VARARGS | METH_KEYWORDS,
     "entities_in_radius(pos: tuple|Vector, radius: float) -> list[Entity]\n\n"
     "Query entities within radius using spatial hash (O(k) where k = nearby entities).\n\n"
     "Args:\n"
     "    pos: Center position as (x, y) tuple, Vector, or other 2-element sequence\n"
     "    radius: Search radius\n\n"
     "Returns:\n"
     "    List of Entity objects within the radius."},
    {"center_camera", (PyCFunction)UIGrid::py_center_camera, METH_VARARGS,
     "center_camera(pos: tuple = None) -> None\n\n"
     "Center the camera on a tile coordinate.\n\n"
     "Args:\n"
     "    pos: Optional (tile_x, tile_y) tuple. If None, centers on grid's middle tile.\n\n"
     "Example:\n"
     "    grid.center_camera()        # Center on middle of grid\n"
     "    grid.center_camera((5, 10)) # Center on tile (5, 10)\n"
     "    grid.center_camera((0, 0))  # Center on tile (0, 0)"},
    {"apply_threshold", (PyCFunction)UIGrid::py_apply_threshold, METH_VARARGS | METH_KEYWORDS,
     "apply_threshold(source: HeightMap, range: tuple, walkable: bool = None, transparent: bool = None) -> Grid\n\n"
     "Apply walkable/transparent properties where heightmap values are in range.\n\n"
     "Args:\n"
     "    source: HeightMap with values to check. Must match grid size.\n"
     "    range: Tuple of (min, max) - cells with values in this range are affected.\n"
     "    walkable: If not None, set walkable to this value for cells in range.\n"
     "    transparent: If not None, set transparent to this value for cells in range.\n\n"
     "Returns:\n"
     "    Grid: self, for method chaining.\n\n"
     "Raises:\n"
     "    ValueError: If HeightMap size doesn't match grid size."},
    {"apply_ranges", (PyCFunction)UIGrid::py_apply_ranges, METH_VARARGS,
     "apply_ranges(source: HeightMap, ranges: list) -> Grid\n\n"
     "Apply multiple thresholds in a single pass.\n\n"
     "Args:\n"
     "    source: HeightMap with values to check. Must match grid size.\n"
     "    ranges: List of (range_tuple, properties_dict) tuples.\n"
     "            range_tuple: (min, max) value range\n"
     "            properties_dict: {'walkable': bool, 'transparent': bool}\n\n"
     "Returns:\n"
     "    Grid: self, for method chaining.\n\n"
     "Example:\n"
     "    grid.apply_ranges(terrain, [\n"
     "        ((0.0, 0.3), {'walkable': False, 'transparent': True}),   # Water\n"
     "        ((0.3, 0.8), {'walkable': True, 'transparent': True}),    # Land\n"
     "        ((0.8, 1.0), {'walkable': False, 'transparent': False}),  # Mountains\n"
     "    ])"},
    {NULL, NULL, 0, NULL}
};

typedef PyUIGridObject PyObjectType;

PyMethodDef UIGrid_all_methods[] = {
    UIDRAWABLE_METHODS,
    {"at", (PyCFunction)UIGrid::py_at, METH_VARARGS | METH_KEYWORDS},
    {"compute_fov", (PyCFunction)UIGrid::py_compute_fov, METH_VARARGS | METH_KEYWORDS,
     "compute_fov(pos, radius: int = 0, light_walls: bool = True, algorithm: int = FOV_BASIC) -> None\n\n"
     "Compute field of view from a position.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n"
     "    radius: Maximum view distance (0 = unlimited)\n"
     "    light_walls: Whether walls are lit when visible\n"
     "    algorithm: FOV algorithm to use (FOV_BASIC, FOV_DIAMOND, FOV_SHADOW, FOV_PERMISSIVE_0-8)\n\n"
     "Updates the internal FOV state. Use is_in_fov(pos) to query visibility."},
    {"is_in_fov", (PyCFunction)UIGrid::py_is_in_fov, METH_VARARGS | METH_KEYWORDS,
     "is_in_fov(pos) -> bool\n\n"
     "Check if a cell is in the field of view.\n\n"
     "Args:\n"
     "    pos: Position as (x, y) tuple, list, or Vector\n\n"
     "Returns:\n"
     "    True if the cell is visible, False otherwise\n\n"
     "Must call compute_fov() first to calculate visibility."},
    {"find_path", (PyCFunction)UIGridPathfinding::Grid_find_path, METH_VARARGS | METH_KEYWORDS,
     "find_path(start, end, diagonal_cost=1.41, collide=None) -> AStarPath | None\n\n"
     "Compute A* path between two points.\n\n"
     "Args:\n"
     "    start: Starting position as Vector, Entity, or (x, y) tuple\n"
     "    end: Target position as Vector, Entity, or (x, y) tuple\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n"
     "    collide: Label string. Entities with this label block pathfinding.\n\n"
     "Returns:\n"
     "    AStarPath object if path exists, None otherwise.\n\n"
     "The returned AStarPath can be iterated or walked step-by-step."},
    {"get_dijkstra_map", (PyCFunction)UIGridPathfinding::Grid_get_dijkstra_map, METH_VARARGS | METH_KEYWORDS,
     "get_dijkstra_map(root, diagonal_cost=1.41, collide=None) -> DijkstraMap\n\n"
     "Get or create a Dijkstra distance map for a root position.\n\n"
     "Args:\n"
     "    root: Root position as Vector, Entity, or (x, y) tuple\n"
     "    diagonal_cost: Cost of diagonal movement (default: 1.41)\n"
     "    collide: Label string. Entities with this label block pathfinding.\n\n"
     "Returns:\n"
     "    DijkstraMap object for querying distances and paths.\n\n"
     "Grid caches DijkstraMaps by (root, collide) key. Multiple requests for\n"
     "the same root and collide label return the same cached map. Call\n"
     "clear_dijkstra_maps() after changing grid walkability to invalidate."},
    {"clear_dijkstra_maps", (PyCFunction)UIGridPathfinding::Grid_clear_dijkstra_maps, METH_NOARGS,
     "clear_dijkstra_maps() -> None\n\n"
     "Clear all cached Dijkstra maps.\n\n"
     "Call this after modifying grid cell walkability to ensure pathfinding\n"
     "uses updated walkability data."},
    {"add_layer", (PyCFunction)UIGrid::py_add_layer, METH_VARARGS,
     "add_layer(layer: ColorLayer | TileLayer) -> ColorLayer | TileLayer\n\n"
     "Add a layer to the grid.\n\n"
     "Args:\n"
     "    layer: A ColorLayer or TileLayer object. Layers with size (0, 0) are\n"
     "           automatically resized to match the grid. Named layers replace\n"
     "           any existing layer with the same name.\n\n"
     "Returns:\n"
     "    The added layer object.\n\n"
     "Raises:\n"
     "    ValueError: If layer is already attached to another grid, or if\n"
     "                layer size doesn't match grid (and isn't (0,0)).\n"
     "    TypeError: If argument is not a ColorLayer or TileLayer."},
    {"remove_layer", (PyCFunction)UIGrid::py_remove_layer, METH_VARARGS,
     "remove_layer(name_or_layer: str | ColorLayer | TileLayer) -> None\n\n"
     "Remove a layer from the grid.\n\n"
     "Args:\n"
     "    name_or_layer: Either a layer name (str) or the layer object itself.\n\n"
     "Raises:\n"
     "    KeyError: If name is provided but no layer with that name exists.\n"
     "    TypeError: If argument is not a string, ColorLayer, or TileLayer."},
    {"layer", (PyCFunction)UIGrid::py_layer, METH_VARARGS,
     "layer(name: str) -> ColorLayer | TileLayer | None\n\n"
     "Get a layer by its name.\n\n"
     "Args:\n"
     "    name: The name of the layer to find.\n\n"
     "Returns:\n"
     "    The layer with the specified name, or None if not found."},
    {"entities_in_radius", (PyCFunction)UIGrid::py_entities_in_radius, METH_VARARGS | METH_KEYWORDS,
     "entities_in_radius(pos: tuple|Vector, radius: float) -> list[Entity]\n\n"
     "Query entities within radius using spatial hash (O(k) where k = nearby entities).\n\n"
     "Args:\n"
     "    pos: Center position as (x, y) tuple, Vector, or other 2-element sequence\n"
     "    radius: Search radius\n\n"
     "Returns:\n"
     "    List of Entity objects within the radius."},
    {"center_camera", (PyCFunction)UIGrid::py_center_camera, METH_VARARGS,
     "center_camera(pos: tuple = None) -> None\n\n"
     "Center the camera on a tile coordinate.\n\n"
     "Args:\n"
     "    pos: Optional (tile_x, tile_y) tuple. If None, centers on grid's middle tile.\n\n"
     "Example:\n"
     "    grid.center_camera()        # Center on middle of grid\n"
     "    grid.center_camera((5, 10)) # Center on tile (5, 10)\n"
     "    grid.center_camera((0, 0))  # Center on tile (0, 0)"},
    {"apply_threshold", (PyCFunction)UIGrid::py_apply_threshold, METH_VARARGS | METH_KEYWORDS,
     "apply_threshold(source: HeightMap, range: tuple, walkable: bool = None, transparent: bool = None) -> Grid\n\n"
     "Apply walkable/transparent properties where heightmap values are in range.\n\n"
     "Args:\n"
     "    source: HeightMap with values to check. Must match grid size.\n"
     "    range: Tuple of (min, max) - cells with values in this range are affected.\n"
     "    walkable: If not None, set walkable to this value for cells in range.\n"
     "    transparent: If not None, set transparent to this value for cells in range.\n\n"
     "Returns:\n"
     "    Grid: self, for method chaining.\n\n"
     "Raises:\n"
     "    ValueError: If HeightMap size doesn't match grid size."},
    {"apply_ranges", (PyCFunction)UIGrid::py_apply_ranges, METH_VARARGS,
     "apply_ranges(source: HeightMap, ranges: list) -> Grid\n\n"
     "Apply multiple thresholds in a single pass.\n\n"
     "Args:\n"
     "    source: HeightMap with values to check. Must match grid size.\n"
     "    ranges: List of (range_tuple, properties_dict) tuples.\n"
     "            range_tuple: (min, max) value range\n"
     "            properties_dict: {'walkable': bool, 'transparent': bool}\n\n"
     "Returns:\n"
     "    Grid: self, for method chaining.\n\n"
     "Example:\n"
     "    grid.apply_ranges(terrain, [\n"
     "        ((0.0, 0.3), {'walkable': False, 'transparent': True}),   # Water\n"
     "        ((0.3, 0.8), {'walkable': True, 'transparent': True}),    # Land\n"
     "        ((0.8, 1.0), {'walkable': False, 'transparent': False}),  # Mountains\n"
     "    ])"},
    {"step", (PyCFunction)UIGrid::py_step, METH_VARARGS | METH_KEYWORDS,
     "step(n=1, turn_order=None) -> None\n\n"
     "Execute n rounds of turn-based entity behavior.\n\n"
     "Args:\n"
     "    n (int): Number of rounds to execute. Default: 1\n"
     "    turn_order (int, optional): Only process entities with this turn_order value\n\n"
     "Each round: entities grouped by turn_order (ascending), behaviors executed,\n"
     "triggers fired (TARGET, DONE, BLOCKED), movement animated."},
    {NULL}
};
