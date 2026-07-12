// UIGridPyProperties.cpp — Python getter/setter implementations for UIGrid
// Extracted from UIGrid.cpp (#149) for maintainability.
// Contains: all PyGetSetDef getters/setters and the getsetters[] array.
#include "UIGrid.h"
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

PyObject* UIGrid::get_grid_size(PyUIGridObject* self, void* closure) {
    return PyVector(sf::Vector2f(static_cast<float>(self->data->grid_w),
                                  static_cast<float>(self->data->grid_h))).pyObject();
}

PyObject* UIGrid::get_grid_w(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_w);
}

PyObject* UIGrid::get_grid_h(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_h);
}

PyObject* UIGrid::get_size(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return PyVector(box.getSize()).pyObject();
}

int UIGrid::set_size(PyUIGridObject* self, PyObject* value, void* closure) {
    float w, h;
    PyVectorObject* vec = PyVector::from_arg(value);
    if (vec) {
        w = vec->data.x;
        h = vec->data.y;
        Py_DECREF(vec);
    } else {
        PyErr_Clear();
        if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
            PyErr_SetString(PyExc_TypeError, "size must be a Vector or tuple (w, h)");
            return -1;
        }
    }
    self->data->box.setSize(sf::Vector2f(w, h));

    unsigned int tex_width = static_cast<unsigned int>(w * 1.5f);
    unsigned int tex_height = static_cast<unsigned int>(h * 1.5f);

    tex_width = std::min(tex_width, 4096u);
    tex_height = std::min(tex_height, 4096u);

    self->data->renderTexture.create(tex_width, tex_height);
    self->data->markDirty();

    return 0;
}

// =========================================================================
// Camera/view properties
// =========================================================================

PyObject* UIGrid::get_center(PyUIGridObject* self, void* closure) {
    return PyVector(sf::Vector2f(self->data->center_x, self->data->center_y)).pyObject();
}

int UIGrid::set_center(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->center_x = x;
    self->data->center_y = y;
    self->data->markDirty();
    return 0;
}

PyObject* UIGrid::get_float_member(PyUIGridObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1)
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2)
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3)
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4)
        return PyFloat_FromDouble(self->data->center_x);
    else if (member_ptr == 5)
        return PyFloat_FromDouble(self->data->center_y);
    else if (member_ptr == 6)
        return PyFloat_FromDouble(self->data->zoom);
    else if (member_ptr == 7)
        return PyFloat_FromDouble(self->data->camera_rotation);
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIGrid::set_float_member(PyUIGridObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    if (member_ptr == 0)
        self->data->box.setPosition(val, self->data->box.getPosition().y);
    else if (member_ptr == 1)
        self->data->box.setPosition(self->data->box.getPosition().x, val);
    else if (member_ptr == 2)
    {
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
        unsigned int tex_width = static_cast<unsigned int>(val * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(self->data->box.getSize().y * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 3)
    {
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
        unsigned int tex_width = static_cast<unsigned int>(self->data->box.getSize().x * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(val * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 4)
        self->data->center_x = val;
    else if (member_ptr == 5)
        self->data->center_y = val;
    else if (member_ptr == 6)
        self->data->zoom = val;
    else if (member_ptr == 7)
        self->data->camera_rotation = val;

    if (member_ptr == 0 || member_ptr == 1) {
        self->data->markCompositeDirty();
    } else {
        self->data->markDirty();
    }

    return 0;
}

// =========================================================================
// Texture property
// =========================================================================

PyObject* UIGrid::get_texture(PyUIGridObject* self, void* closure) {
    auto texture = self->data->getTexture();
    if (!texture) {
        Py_RETURN_NONE;
    }

    auto type = &mcrfpydef::PyTextureType;
    auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
    obj->data = texture;
    return (PyObject*)obj;
}

// =========================================================================
// Fill color
// =========================================================================

PyObject* UIGrid::get_fill_color(PyUIGridObject* self, void* closure)
{
    auto& color = self->data->fill_color;
    auto type = &mcrfpydef::PyColorType;
    PyObject* args = Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
    PyObject* obj = PyObject_CallObject((PyObject*)type, args);
    Py_DECREF(args);
    return obj;
}

int UIGrid::set_fill_color(PyUIGridObject* self, PyObject* value, void* closure)
{
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyColorType)) {
        PyErr_SetString(PyExc_TypeError, "fill_color must be a Color object");
        return -1;
    }

    PyColorObject* color = (PyColorObject*)value;
    self->data->fill_color = color->data;
    self->data->markDirty();
    return 0;
}

PyObject* UIGrid::get_fov(PyUIGridObject* self, void* closure)
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

int UIGrid::set_fov(PyUIGridObject* self, PyObject* value, void* closure)
{
    TCOD_fov_algorithm_t algo;
    if (!PyFOV::from_arg(value, &algo, nullptr)) {
        return -1;
    }
    self->data->fov_algorithm = algo;
    self->data->markDirty();
    return 0;
}

PyObject* UIGrid::get_fov_radius(PyUIGridObject* self, void* closure)
{
    return PyLong_FromLong(self->data->fov_radius);
}

int UIGrid::set_fov_radius(PyUIGridObject* self, PyObject* value, void* closure)
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

PyObject* UIGrid::get_entities(PyUIGridObject* self, void* closure)
{
    PyTypeObject* type = &mcrfpydef::PyUIEntityCollectionType;
    auto o = (PyUIEntityCollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->entities;
        o->grid = self->data;
    }
    return (PyObject*)o;
}

PyObject* UIGrid::get_children(PyUIGridObject* self, void* closure)
{
    PyTypeObject* type = &mcrfpydef::PyUICollectionType;
    auto o = (PyUICollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->children;
        o->owner = self->data;
    }
    return (PyObject*)o;
}

PyObject* UIGrid::get_layers(PyUIGridObject* self, void* closure) {
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

PyObject* UIGrid::repr(PyUIGridObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Grid (invalid internal object)>";
    else {
        auto grid = self->data;
        auto box = grid->box;
        ss << "<Grid (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", w=" << box.getSize().x << ", h=" << box.getSize().y << ", " <<
            "center=(" << grid->center_x << ", " << grid->center_y << "), zoom=" << grid->zoom <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// #355 - cell callback properties moved to UIGridView (src/UIGridView.cpp)

// =========================================================================
// getsetters[] table
// =========================================================================

typedef PyUIGridObject PyObjectType;

PyGetSetDef UIGrid::getsetters[] = {

    {"grid_size", (getter)UIGrid::get_grid_size, NULL,
     MCRF_PROPERTY(grid_size, "Grid dimensions as (grid_w, grid_h) (Vector, read-only)."), NULL},
    {"grid_w", (getter)UIGrid::get_grid_w, NULL,
     MCRF_PROPERTY(grid_w, "Grid width in cells (int, read-only)."), NULL},
    {"grid_h", (getter)UIGrid::get_grid_h, NULL,
     MCRF_PROPERTY(grid_h, "Grid height in cells (int, read-only)."), NULL},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position of the grid as Vector (Vector)."), (void*)PyObjectsEnum::UIGRID},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos,
     MCRF_PROPERTY(grid_pos, "Position in parent grid's tile coordinates (Vector). Only valid when parent is a Grid."), (void*)PyObjectsEnum::UIGRID},
    {"size", (getter)UIGrid::get_size, (setter)UIGrid::set_size,
     MCRF_PROPERTY(size, "Size of the grid widget as Vector (Vector, width x height in pixels)."), NULL},
    {"center", (getter)UIGrid::get_center, (setter)UIGrid::set_center,
     MCRF_PROPERTY(center, "Camera center point in pixel coordinates (Vector). Controls which part of the grid world is visible (pan)."), NULL},

    {"entities", (getter)UIGrid::get_entities, NULL,
     MCRF_PROPERTY(entities, "EntityCollection of entities on this grid (EntityCollection, read-only)."), NULL},
    {"children", (getter)UIGrid::get_children, NULL,
     MCRF_PROPERTY(children,
         "UICollection of UIDrawable children such as speech bubbles, effects, and range "
         "indicators anchored to grid content (UICollection, read-only)."
         MCRF_NOTE(
             "Grid children are positioned in the grid's pixel-world coordinates -- the same "
             "origin as Entity positions -- NOT in the grid widget's screen-space pixels. They "
             "pan and zoom with the grid camera (center, zoom), so a child placed near an "
             "entity stays near that entity as the camera moves. This differs from "
             "Frame.children, which are frame-local: since a Frame cannot pan its content, "
             "Frame children are effectively already in screen coordinates. If you want UI "
             "that floats over the grid regardless of camera position (e.g. a HUD), do not use "
             "Grid.children -- add a sibling Frame with the same pos/size as the Grid instead."
         )
         MCRF_LINK("docs/grid-coordinate-spaces.md", "Grid Coordinate Spaces & Overlay Pattern")
     ), NULL},
    {"layers", (getter)UIGrid::get_layers, NULL,
     MCRF_PROPERTY(layers, "Tuple of grid layers sorted by z_index (tuple, read-only). Contains ColorLayer and TileLayer objects."), NULL},

    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(x, "Top-left corner X-coordinate in pixels (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(y, "Top-left corner Y-coordinate in pixels (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(w, "Visible widget width in pixels (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(h, "Visible widget height in pixels (float)."), (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 3)},
    {"center_x", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member,
     MCRF_PROPERTY(center_x, "Camera center X-coordinate in pixels (float)."), (void*)4},
    {"center_y", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member,
     MCRF_PROPERTY(center_y, "Camera center Y-coordinate in pixels (float)."), (void*)5},
    {"zoom", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member,
     MCRF_PROPERTY(zoom, "Zoom factor for rendering the grid (float). Values > 1 zoom in; values < 1 zoom out."), (void*)6},
    {"camera_rotation", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member,
     MCRF_PROPERTY(camera_rotation, "Rotation of grid contents around camera center in degrees (float). The grid widget stays axis-aligned; only the view into the world rotates."), (void*)7},

    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: MouseButton, action: InputState)."
     ), (void*)PyObjectsEnum::UIGRID},

    {"texture", (getter)UIGrid::get_texture, NULL,
     MCRF_PROPERTY(texture, "Texture used for tile rendering (Texture | None, read-only)."), NULL},
    {"fill_color", (getter)UIGrid::get_fill_color, (setter)UIGrid::set_fill_color,
     MCRF_PROPERTY(fill_color,
         "Background fill color of the grid (Color). "
         "Returns a copy; modifying components requires reassignment. "
         "For animation, use 'fill_color.r', 'fill_color.g', etc."
     ), NULL},
    {"fov", (getter)UIGrid::get_fov, (setter)UIGrid::set_fov,
     MCRF_PROPERTY(fov,
         "FOV algorithm for this grid (FOV enum). "
         "Used by entity.updateVisibility() and layer methods when fov=None."
     ), NULL},
    {"fov_radius", (getter)UIGrid::get_fov_radius, (setter)UIGrid::set_fov_radius,
     MCRF_PROPERTY(fov_radius, "Default FOV radius for this grid (int). Used when radius is not specified."), NULL},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UIGRID},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding elements (str)."), (void*)PyObjectsEnum::UIGRID},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIGRID),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UIGRID),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UIGRID),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UIGRID),
    {NULL}
};
