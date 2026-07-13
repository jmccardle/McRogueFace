// PyGridDataProperties.cpp - Python getter/setter implementations for GridData.
// #361: the widget properties (pos/size/center/zoom/camera_rotation/fill_color/
// x/y/w/h/on_click/z_index/name/visible/opacity/align/rotation/shader) are gone --
// a map has no position and is never drawn. They live on UIGridView, which is the
// only widget. What is left is what a MAP actually has.
#include "PyGridData.h"
#include "UIGridView.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFOV.h"
#include "UIBase.h"
#include "UICollection.h"
#include "McRFPy_Doc.h"

// =========================================================================
// Grid dimension properties
// =========================================================================

PyObject* PyGridData::get_grid_size(PyGridDataObject* self, void* closure) {
    return PyVector(sf::Vector2f(static_cast<float>(self->data->grid_w),
                                  static_cast<float>(self->data->grid_h))).pyObject();
}

PyObject* PyGridData::get_grid_w(PyGridDataObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_w);
}

PyObject* PyGridData::get_grid_h(PyGridDataObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_h);
}

// =========================================================================
// Texture property
// =========================================================================

PyObject* PyGridData::get_texture(PyGridDataObject* self, void* closure) {
    auto texture = self->data->getTexture();
    if (!texture) {
        Py_RETURN_NONE;
    }

    auto type = &mcrfpydef::PyTextureType;
    auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
    obj->data = texture;
    return (PyObject*)obj;
}

PyObject* PyGridData::get_fov(PyGridDataObject* self, void* closure)
{
    if (PyFOV::fov_enum_class) {
        PyObject* value = PyLong_FromLong(self->data->fov_algorithm);
        if (!value) return NULL;

        PyObject* args = PyTuple_Pack(1, value);
        Py_DECREF(value);
        if (!args) return NULL;

        PyObject* result = PyObject_Call(PyFOV::fov_enum_class, args, NULL);
        Py_DECREF(args);
        return result;
    }
    return PyLong_FromLong(self->data->fov_algorithm);
}

int PyGridData::set_fov(PyGridDataObject* self, PyObject* value, void* closure)
{
    TCOD_fov_algorithm_t algo;
    if (!PyFOV::from_arg(value, &algo, nullptr)) {
        return -1;
    }
    self->data->fov_algorithm = algo;
    self->data->markDirty();
    return 0;
}

PyObject* PyGridData::get_fov_radius(PyGridDataObject* self, void* closure)
{
    return PyLong_FromLong(self->data->fov_radius);
}

int PyGridData::set_fov_radius(PyGridDataObject* self, PyObject* value, void* closure)
{
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "fov_radius must be an integer");
        return -1;
    }
    long radius = PyLong_AsLong(value);
    if (radius == -1 && PyErr_Occurred()) {
        return -1;
    }
    if (radius < 0) {
        PyErr_SetString(PyExc_ValueError, "fov_radius must be non-negative");
        return -1;
    }
    self->data->fov_radius = (int)radius;
    self->data->markDirty();
    return 0;
}

// =========================================================================
// Collection getters
// =========================================================================

PyObject* PyGridData::get_entities(PyGridDataObject* self, void* closure)
{
    PyTypeObject* type = &mcrfpydef::PyUIEntityCollectionType;
    auto o = (PyUIEntityCollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->entities;
        o->grid = self->data;
    }
    return (PyObject*)o;
}

// #364: get_children moved to UIGridView. GridData holds no drawables, so the
// internal _GridData no longer exposes a children collection at all.

PyObject* PyGridData::get_layers(PyGridDataObject* self, void* closure) {
    self->data->sortLayers();

    PyObject* tuple = PyTuple_New(self->data->layers.size());
    if (!tuple) return NULL;

    auto* color_layer_type = &mcrfpydef::PyColorLayerType;
    auto* tile_layer_type = &mcrfpydef::PyTileLayerType;

    for (size_t i = 0; i < self->data->layers.size(); ++i) {
        auto& layer = self->data->layers[i];
        PyObject* py_layer = nullptr;

        if (layer->type == GridLayerType::Color) {
            PyColorLayerObject* obj = (PyColorLayerObject*)color_layer_type->tp_alloc(color_layer_type, 0);
            if (obj) {
                obj->data = std::static_pointer_cast<ColorLayer>(layer);
                obj->grid = self->data;
                py_layer = (PyObject*)obj;
            }
        } else {
            PyTileLayerObject* obj = (PyTileLayerObject*)tile_layer_type->tp_alloc(tile_layer_type, 0);
            if (obj) {
                obj->data = std::static_pointer_cast<TileLayer>(layer);
                obj->grid = self->data;
                py_layer = (PyObject*)obj;
            }
        }

        if (!py_layer) {
            Py_DECREF(tuple);
            return NULL;
        }

        PyTuple_SET_ITEM(tuple, i, py_layer);
    }

    return tuple;
}

// =========================================================================
// repr
// =========================================================================

PyObject* PyGridData::repr(PyGridDataObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<GridData (invalid internal object)>";
    else {
        auto grid = self->data;
        ss << "<GridData (" << grid->grid_w << "x" << grid->grid_h << ", "
           << grid->entities->size() << " entities, "
           << grid->layers.size() << " layers)>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// #355 - cell callback properties moved to UIGridView (src/UIGridView.cpp)

// =========================================================================
// getsetters[] table
//
// #361: a map has no pos/size/center/zoom/camera_rotation/fill_color/x/y/w/h/
// on_click/z_index/name/visible/opacity/align/rotation/shader. Every one of those
// was a widget property that happened to hang off the data because UIGrid was
// both. They are on UIGridView now. What a GridData exposes is its shape, its
// contents, and its FOV defaults.
// =========================================================================

PyGetSetDef PyGridData::getsetters[] = {

    {"grid_size", (getter)PyGridData::get_grid_size, NULL,
     MCRF_PROPERTY(grid_size, "Grid dimensions as (grid_w, grid_h) (Vector, read-only)."), NULL},
    {"grid_w", (getter)PyGridData::get_grid_w, NULL,
     MCRF_PROPERTY(grid_w, "Grid width in cells (int, read-only)."), NULL},
    {"grid_h", (getter)PyGridData::get_grid_h, NULL,
     MCRF_PROPERTY(grid_h, "Grid height in cells (int, read-only)."), NULL},

    {"entities", (getter)PyGridData::get_entities, NULL,
     MCRF_PROPERTY(entities, "EntityCollection of entities on this map (EntityCollection, read-only). Shared by every view of this data."), NULL},
    {"layers", (getter)PyGridData::get_layers, NULL,
     MCRF_PROPERTY(layers, "Tuple of grid layers sorted by z_index (tuple, read-only). Contains ColorLayer and TileLayer objects."), NULL},

    {"texture", (getter)PyGridData::get_texture, NULL,
     MCRF_PROPERTY(texture, "Tile atlas for this map (Texture | None, read-only). Defines the cell size in pixels."), NULL},
    {"fov", (getter)PyGridData::get_fov, (setter)PyGridData::set_fov,
     MCRF_PROPERTY(fov,
         "FOV algorithm for this map (FOV enum). "
         "Used by entity.updateVisibility() and layer methods when fov=None."
     ), NULL},
    {"fov_radius", (getter)PyGridData::get_fov_radius, (setter)PyGridData::set_fov_radius,
     MCRF_PROPERTY(fov_radius, "Default FOV radius for this map (int). Used when radius is not specified."), NULL},
    {NULL}
};
