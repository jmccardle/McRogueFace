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

    if (self->view) {
        if (member_ptr == 0)
            self->view->box.setPosition(val, self->view->box.getPosition().y);
        else if (member_ptr == 1)
            self->view->box.setPosition(self->view->box.getPosition().x, val);
        else if (member_ptr == 2)
            self->view->box.setSize(sf::Vector2f(val, self->view->box.getSize().y));
        else if (member_ptr == 3)
            self->view->box.setSize(sf::Vector2f(self->view->box.getSize().x, val));
        else if (member_ptr == 4) self->view->center_x = val;
        else if (member_ptr == 5) self->view->center_y = val;
        else if (member_ptr == 6) self->view->zoom = val;
        else if (member_ptr == 7) self->view->camera_rotation = val;
        self->view->position = self->view->box.getPosition();
    }

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

// =========================================================================
// Perspective properties
// =========================================================================

PyObject* UIGrid::get_perspective(PyUIGridObject* self, void* closure)
{
    auto locked = self->data->perspective_entity.lock();
    if (locked) {
        if (locked->serial_number != 0) {
            PyObject* cached = PythonObjectCache::getInstance().lookup(locked->serial_number);
            if (cached) {
                return cached;
            }
        }

        auto type = &mcrfpydef::PyUIEntityType;
        auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
        if (o) {
            o->data = locked;
            o->weakreflist = NULL;
            return (PyObject*)o;
        }
    }
    Py_RETURN_NONE;
}

int UIGrid::set_perspective(PyUIGridObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        self->data->perspective_entity.reset();
        self->data->markDirty();
        return 0;
    }

    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIEntityType)) {
        PyErr_SetString(PyExc_TypeError, "perspective must be a UIEntity or None");
        return -1;
    }

    PyUIEntityObject* entity_obj = (PyUIEntityObject*)value;
    self->data->perspective_entity = entity_obj->data;
    self->data->perspective_enabled = true;
    self->data->markDirty();
    return 0;
}

PyObject* UIGrid::get_perspective_enabled(PyUIGridObject* self, void* closure)
{
    return PyBool_FromLong(self->data->perspective_enabled);
}

int UIGrid::set_perspective_enabled(PyUIGridObject* self, PyObject* value, void* closure)
{
    int enabled = PyObject_IsTrue(value);
    if (enabled == -1) {
        return -1;
    }
    self->data->perspective_enabled = enabled;
    self->data->markDirty();
    return 0;
}

// =========================================================================
// FOV properties
// =========================================================================

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

PyObject* UIGrid::get_view(PyUIGridObject* self, void* closure)
{
    if (!self->view) Py_RETURN_NONE;
    auto type = &mcrfpydef::PyUIGridViewType;
    auto obj = (PyUIGridViewObject*)type->tp_alloc(type, 0);
    if (!obj) return PyErr_NoMemory();
    obj->data = self->view;
    obj->weakreflist = NULL;
    return (PyObject*)obj;
}

PyObject* UIGrid::get_layers(PyUIGridObject* self, void* closure) {
    self->data->sortLayers();

    PyObject* tuple = PyTuple_New(self->data->layers.size());
    if (!tuple) return NULL;

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) {
        Py_DECREF(tuple);
        return NULL;
    }

    auto* color_layer_type = (PyTypeObject*)PyObject_GetAttrString(mcrfpy_module, "ColorLayer");
    auto* tile_layer_type = (PyTypeObject*)PyObject_GetAttrString(mcrfpy_module, "TileLayer");
    Py_DECREF(mcrfpy_module);

    if (!color_layer_type || !tile_layer_type) {
        if (color_layer_type) Py_DECREF(color_layer_type);
        if (tile_layer_type) Py_DECREF(tile_layer_type);
        Py_DECREF(tuple);
        return NULL;
    }

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
            Py_DECREF(color_layer_type);
            Py_DECREF(tile_layer_type);
            Py_DECREF(tuple);
            return NULL;
        }

        PyTuple_SET_ITEM(tuple, i, py_layer);
    }

    Py_DECREF(color_layer_type);
    Py_DECREF(tile_layer_type);
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

// =========================================================================
// Cell callback properties
// =========================================================================

PyObject* UIGrid::get_on_cell_enter(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_enter_callable) {
        PyObject* cb = self->data->on_cell_enter_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_enter(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_enter_callable.reset();
    } else {
        self->data->on_cell_enter_callable = std::make_unique<PyCellHoverCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_on_cell_exit(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_exit_callable) {
        PyObject* cb = self->data->on_cell_exit_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_exit(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_exit_callable.reset();
    } else {
        self->data->on_cell_exit_callable = std::make_unique<PyCellHoverCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_on_cell_click(PyUIGridObject* self, void* closure) {
    if (self->data->on_cell_click_callable) {
        PyObject* cb = self->data->on_cell_click_callable->borrow();
        Py_INCREF(cb);
        return cb;
    }
    Py_RETURN_NONE;
}

int UIGrid::set_on_cell_click(PyUIGridObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->on_cell_click_callable.reset();
    } else {
        self->data->on_cell_click_callable = std::make_unique<PyClickCallable>(value);
    }
    return 0;
}

PyObject* UIGrid::get_hovered_cell(PyUIGridObject* self, void* closure) {
    if (self->data->hovered_cell.has_value()) {
        return Py_BuildValue("(ii)", self->data->hovered_cell->x, self->data->hovered_cell->y);
    }
    Py_RETURN_NONE;
}

// =========================================================================
// getsetters[] table
// =========================================================================

typedef PyUIGridObject PyObjectType;

PyGetSetDef UIGrid::getsetters[] = {

    {"grid_size", (getter)UIGrid::get_grid_size, NULL, "Grid dimensions (grid_w, grid_h)", NULL},
    {"grid_w", (getter)UIGrid::get_grid_w, NULL, "Grid width in cells", NULL},
    {"grid_h", (getter)UIGrid::get_grid_h, NULL, "Grid height in cells", NULL},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos, "Position of the grid as Vector", (void*)PyObjectsEnum::UIGRID},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos, "Position in parent grid's tile coordinates (only when parent is Grid)", (void*)PyObjectsEnum::UIGRID},
    {"size", (getter)UIGrid::get_size, (setter)UIGrid::set_size, "Size of the grid as Vector (width, height)", NULL},
    {"center", (getter)UIGrid::get_center, (setter)UIGrid::set_center, "Grid coordinate at the center of the Grid's view (pan)", NULL},

    {"entities", (getter)UIGrid::get_entities, NULL, "EntityCollection of entities on this grid", NULL},
    {"children", (getter)UIGrid::get_children, NULL, "UICollection of UIDrawable children (speech bubbles, effects, overlays)", NULL},
    {"layers", (getter)UIGrid::get_layers, NULL, "List of grid layers (ColorLayer, TileLayer) sorted by z_index", NULL},

    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "top-left corner X-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "top-left corner Y-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "visible widget width", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "visible widget height", (void*)((intptr_t)PyObjectsEnum::UIGRID << 8 | 3)},
    {"center_x", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view X-coordinate", (void*)4},
    {"center_y", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view Y-coordinate", (void*)5},
    {"zoom", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "zoom factor for displaying the Grid", (void*)6},
    {"camera_rotation", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "Rotation of grid contents around camera center (degrees). The grid widget stays axis-aligned; only the view into the world rotates.", (void*)7},

    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: str, action: str)."
     ), (void*)PyObjectsEnum::UIGRID},

    {"texture", (getter)UIGrid::get_texture, NULL, "Texture of the grid", NULL},
    {"fill_color", (getter)UIGrid::get_fill_color, (setter)UIGrid::set_fill_color,
     "Background fill color of the grid. Returns a copy; modifying components requires reassignment. "
     "For animation, use 'fill_color.r', 'fill_color.g', etc.", NULL},
    {"perspective", (getter)UIGrid::get_perspective, (setter)UIGrid::set_perspective,
     "Entity whose perspective to use for FOV rendering (None for omniscient view). "
     "Setting an entity automatically enables perspective mode.", NULL},
    {"perspective_enabled", (getter)UIGrid::get_perspective_enabled, (setter)UIGrid::set_perspective_enabled,
     "Whether to use perspective-based FOV rendering. When True with no valid entity, "
     "all cells appear undiscovered.", NULL},
    {"fov", (getter)UIGrid::get_fov, (setter)UIGrid::set_fov,
     "FOV algorithm for this grid (mcrfpy.FOV enum). "
     "Used by entity.updateVisibility() and layer methods when fov=None.", NULL},
    {"fov_radius", (getter)UIGrid::get_fov_radius, (setter)UIGrid::set_fov_radius,
     "Default FOV radius for this grid. Used when radius not specified.", NULL},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UIGRID},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name, "Name for finding elements", (void*)PyObjectsEnum::UIGRID},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIGRID),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UIGRID),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UIGRID),
    {"on_cell_enter", (getter)UIGrid::get_on_cell_enter, (setter)UIGrid::set_on_cell_enter,
     "Callback when mouse enters a grid cell. Called with (cell_pos: Vector).", NULL},
    {"on_cell_exit", (getter)UIGrid::get_on_cell_exit, (setter)UIGrid::set_on_cell_exit,
     "Callback when mouse exits a grid cell. Called with (cell_pos: Vector).", NULL},
    {"on_cell_click", (getter)UIGrid::get_on_cell_click, (setter)UIGrid::set_on_cell_click,
     "Callback when a grid cell is clicked. Called with (cell_pos: Vector).", NULL},
    {"hovered_cell", (getter)UIGrid::get_hovered_cell, NULL,
     "Currently hovered cell as (x, y) tuple, or None if not hovering.", NULL},
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UIGRID),
    {"view", (getter)UIGrid::get_view, NULL,
     "Auto-created GridView for rendering (read-only). "
     "When Grid is appended to a scene, this view is what actually renders.", NULL},
    {NULL}
};
