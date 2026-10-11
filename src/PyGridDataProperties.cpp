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
#include "PyWrap.h"
#include "PyTexture.h"
#include <cmath>

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
    // #430: cache-aware, so this is the very Texture the user passed in.
    return PyTexture::pyobject_for(self->data->getTexture());
}

int PyGridData::assign_texture(const std::shared_ptr<GridData>& grid, PyObject* value)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete texture; assign None to remove it");
        return -1;
    }
    if (value == Py_None) {
        grid->setTexture(nullptr);   // the cell size keeps its value (#453)
        return 0;
    }
    int is_texture = PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyTextureType);
    if (is_texture < 0) return -1;
    if (!is_texture || !((PyTextureObject*)value)->data) {
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture or None");
        return -1;
    }
    grid->setTexture(((PyTextureObject*)value)->data);
    return 0;
}

int PyGridData::set_texture(PyGridDataObject* self, PyObject* value, void* closure) {
    return assign_texture(self->data, value);
}

// =========================================================================
// #453 - cell size
// =========================================================================

// A positive whole number of pixels, for `what`.
static bool cell_extent(double v, const char* what, int& out)
{
    if (!(v >= 1.0) || v != std::floor(v) || v > 65536.0) {
        char got[32];
        snprintf(got, sizeof got, "%g", v);
        PyErr_Format(PyExc_ValueError, "%s must be a whole number of pixels from 1 to 65536 (got %s)",
                     what, got);
        return false;
    }
    out = (int)v;
    return true;
}

PyObject* PyGridData::get_cell_size(PyGridDataObject* self, void* closure) {
    sf::Vector2i c = self->data->cellSize();
    return PyVector(sf::Vector2f((float)c.x, (float)c.y)).pyObject();
}

int PyGridData::set_cell_size(PyGridDataObject* self, PyObject* value, void* closure) {
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete cell_size; assign None to unset it");
        return -1;
    }
    if (value == Py_None) {
        self->data->setCellSize(std::nullopt);
        return 0;
    }
    sf::Vector2f v;
    if (!mcrf::to_vector2f(value, v, "cell_size")) return -1;
    int w = 0, h = 0;
    if (!cell_extent(v.x, "cell_size.x", w) || !cell_extent(v.y, "cell_size.y", h)) return -1;
    self->data->setCellSize(sf::Vector2i(w, h));
    return 0;
}

PyObject* PyGridData::get_cell_member(PyGridDataObject* self, void* closure) {
    sf::Vector2i c = self->data->cellSize();
    return PyLong_FromLong(closure ? c.y : c.x);
}

int PyGridData::set_cell_member(PyGridDataObject* self, PyObject* value, void* closure) {
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete a cell dimension; set cell_size = None");
        return -1;
    }
    double d = PyFloat_AsDouble(value);   // ints and floats; TypeError otherwise
    if (d == -1.0 && PyErr_Occurred()) return -1;
    int v = 0;
    if (!cell_extent(d, closure ? "cell_height" : "cell_width", v)) return -1;
    sf::Vector2i c = self->data->cellSize();   // the other dimension keeps what it reads
    if (closure) c.y = v; else c.x = v;
    self->data->setCellSize(c);
    return 0;
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

// #425: bytes of Dijkstra distance field the grid may keep cached (4 per cell per map).
PyObject* PyGridData::get_dijkstra_cache_budget(PyGridDataObject* self, void* closure)
{
    return PyLong_FromSize_t(self->data->dijkstra_cache.budget);
}

PyObject* PyGridData::get_dijkstra_cache_bytes(PyGridDataObject* self, void* closure)
{
    return PyLong_FromSize_t(self->data->dijkstra_cache.bytes);
}

int PyGridData::set_dijkstra_cache_budget(PyGridDataObject* self, PyObject* value, void* closure)
{
    if (!value || !PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "dijkstra_cache_budget must be an int (bytes)");
        return -1;
    }
    size_t budget = PyLong_AsSize_t(value);  // OverflowError for a negative value
    if (budget == (size_t)-1 && PyErr_Occurred()) return -1;
    self->data->dijkstra_cache.budget = budget;
    self->data->dijkstra_cache.trim();
    return 0;
}

// =========================================================================
// Collection getters
// =========================================================================

PyObject* PyGridData::get_entities(PyGridDataObject* self, void* closure)
{
    // #430: one wrapper per grid, keyed on GridData::entities_serial.
    return UIEntityCollection::pyobject_for(self->data);
}

// #364: get_children moved to UIGridView. GridData holds no drawables, so the
// internal _GridData no longer exposes a children collection at all.

PyObject* PyGridData::get_layers(PyGridDataObject* self, void* closure) {
    self->data->sortLayers();

    PyObject* tuple = PyTuple_New(self->data->layers.size());
    if (!tuple) return NULL;

    for (size_t i = 0; i < self->data->layers.size(); ++i) {
        // #430: each layer's one wrapper (the user's own object if they built it).
        PyObject* py_layer = PyGridLayerAPI::pyobject_for(self->data->layers[i], self->data);
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

    {"texture", (getter)PyGridData::get_texture, (setter)PyGridData::set_texture,
     MCRF_PROPERTY(texture,
         "Tile atlas for this map (Texture | None). Layers and entities with no texture of "
         "their own draw with it, so assigning it restyles them. Setting one fills an unset "
         "cell_size; removing it (None) leaves cell_size as it is."), NULL},
    {"cell_size", (getter)PyGridData::get_cell_size, (setter)PyGridData::set_cell_size,
     MCRF_PROPERTY(cell_size,
         "Pixels per cell, used by every tile<->pixel conversion: entity x/y/pos and a "
         "view's camera (Vector). Unset, it reads the texture's sprite size, or 1x1 with no "
         "texture. Assign whole pixels to set it, or None to unset it. Changing it keeps "
         "each view's camera on the same cells."), NULL},
    {"cell_width", (getter)PyGridData::get_cell_member, (setter)PyGridData::set_cell_member,
     MCRF_PROPERTY(cell_width, "cell_size.x (int)."), (void*)0},
    {"cell_height", (getter)PyGridData::get_cell_member, (setter)PyGridData::set_cell_member,
     MCRF_PROPERTY(cell_height, "cell_size.y (int)."), (void*)1},
    {"fov", (getter)PyGridData::get_fov, (setter)PyGridData::set_fov,
     MCRF_PROPERTY(fov,
         "FOV algorithm for this map (FOV enum). "
         "Used by entity.updateVisibility() and layer methods when fov=None."
     ), NULL},
    {"fov_radius", (getter)PyGridData::get_fov_radius, (setter)PyGridData::set_fov_radius,
     MCRF_PROPERTY(fov_radius, "Default FOV radius for this map (int). Used when radius is not specified."), NULL},
    {"dijkstra_cache_budget", (getter)PyGridData::get_dijkstra_cache_budget,
     (setter)PyGridData::set_dijkstra_cache_budget,
     MCRF_PROPERTY(dijkstra_cache_budget,
         "Bytes of Dijkstra distance field get_dijkstra_map() may keep cached (int, default "
         "256 MiB; each map costs 4 bytes per cell). Least recently used maps are evicted "
         "past it; the most recent one is always kept. Lowering it evicts at once."), NULL},
    {"dijkstra_cache_bytes", (getter)PyGridData::get_dijkstra_cache_bytes, NULL,
     MCRF_PROPERTY(dijkstra_cache_bytes,
         "Bytes of Dijkstra distance field currently cached (int, read-only). Compare "
         "with dijkstra_cache_budget."), NULL},
    {NULL}
};
