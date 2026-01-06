#include "UIGridPoint.h"
#include "UIGrid.h"
#include "UIEntity.h"    // #114 - for GridPoint.entities
#include "GridLayers.h"  // #150 - for GridLayerType, ColorLayer, TileLayer
#include "McRFPy_Doc.h"  // #177 - for MCRF_PROPERTY macro
#include <cstring>       // #150 - for strcmp

UIGridPoint::UIGridPoint()
: walkable(false), transparent(false), grid_x(-1), grid_y(-1), parent_grid(nullptr)
{}

// Utility function to convert sf::Color to PyObject*
PyObject* sfColor_to_PyObject(sf::Color color) {
    // For now, keep returning tuples to avoid breaking existing code
    return Py_BuildValue("(iiii)", color.r, color.g, color.b, color.a);
}

// Utility function to convert PyObject* to sf::Color
sf::Color PyObject_to_sfColor(PyObject* obj) {
    // Get the mcrfpy module and Color type
    PyObject* module = PyImport_ImportModule("mcrfpy");
    if (!module) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to import mcrfpy module");
        return sf::Color();
    }

    PyObject* color_type = PyObject_GetAttrString(module, "Color");
    Py_DECREF(module);

    if (!color_type) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to get Color type from mcrfpy module");
        return sf::Color();
    }

    // Check if it's a mcrfpy.Color object
    int is_color = PyObject_IsInstance(obj, color_type);
    Py_DECREF(color_type);

    if (is_color == 1) {
        PyColorObject* color_obj = (PyColorObject*)obj;
        return color_obj->data;
    } else if (is_color == -1) {
        // Error occurred in PyObject_IsInstance
        return sf::Color();
    }

    // Otherwise try to parse as tuple
    int r, g, b, a = 255; // Default alpha to fully opaque if not specified
    if (!PyArg_ParseTuple(obj, "iii|i", &r, &g, &b, &a)) {
        PyErr_Clear(); // Clear the error from failed tuple parsing
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or a tuple of (r, g, b[, a])");
        return sf::Color(); // Return default color on parse error
    }
    return sf::Color(r, g, b, a);
}

// #150 - Removed get_color/set_color - now handled by layers

PyObject* UIGridPoint::get_bool_member(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // walkable
        return PyBool_FromLong(self->data->walkable);
    } else { // transparent
        return PyBool_FromLong(self->data->transparent);
    }
}

int UIGridPoint::set_bool_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    if (value == Py_True) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = true;
        } else { // transparent
            self->data->transparent = true;
        }
    } else if (value == Py_False) {
        if (reinterpret_cast<long>(closure) == 0) { // walkable
            self->data->walkable = false;
        } else { // transparent
            self->data->transparent = false;
        }
    } else {
        PyErr_SetString(PyExc_ValueError, "Expected a boolean value");
        return -1;
    }

    // Sync with TCOD map if parent grid exists
    if (self->data->parent_grid && self->data->grid_x >= 0 && self->data->grid_y >= 0) {
        self->data->parent_grid->syncTCODMapCell(self->data->grid_x, self->data->grid_y);
    }

    return 0;
}

// #150 - Removed get_int_member/set_int_member - now handled by layers

// #114 - Get list of entities at this grid cell
PyObject* UIGridPoint::get_entities(PyUIGridPointObject* self, void* closure) {
    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "GridPoint has no parent grid");
        return NULL;
    }

    int target_x = self->data->grid_x;
    int target_y = self->data->grid_y;

    PyObject* list = PyList_New(0);
    if (!list) return NULL;

    // Iterate through grid's entities and find those at this position
    for (auto& entity : *(self->grid->entities)) {
        if (static_cast<int>(entity->position.x) == target_x &&
            static_cast<int>(entity->position.y) == target_y) {
            // Create Python Entity object for this entity
            auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
            if (!type) {
                Py_DECREF(list);
                return NULL;
            }
            auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
            Py_DECREF(type);
            if (!obj) {
                Py_DECREF(list);
                return NULL;
            }
            obj->data = entity;
            if (PyList_Append(list, (PyObject*)obj) < 0) {
                Py_DECREF(obj);
                Py_DECREF(list);
                return NULL;
            }
            Py_DECREF(obj);  // List now owns the reference
        }
    }

    return list;
}

// #177 - Get grid position as tuple
PyObject* UIGridPoint::get_grid_pos(PyUIGridPointObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyGetSetDef UIGridPoint::getsetters[] = {
    {"walkable", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint walkable", (void*)0},
    {"transparent", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint transparent", (void*)1},
    {"entities", (getter)UIGridPoint::get_entities, NULL, "List of entities at this grid cell (read-only)", NULL},
    {"grid_pos", (getter)UIGridPoint::get_grid_pos, NULL,
     MCRF_PROPERTY(grid_pos, "Grid coordinates as (x, y) tuple (read-only)."), NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIGridPoint::repr(PyUIGridPointObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<GridPoint (invalid internal object)>";
    else {
        auto gp = self->data;
        ss << "<GridPoint (walkable=" << (gp->walkable ? "True" : "False")
           << ", transparent=" << (gp->transparent ? "True" : "False")
           << ") at (" << gp->grid_x << ", " << gp->grid_y << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

PyObject* UIGridPointState::get_bool_member(PyUIGridPointStateObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // visible
        return PyBool_FromLong(self->data->visible);
    } else { // discovered
        return PyBool_FromLong(self->data->discovered);
    }
}

int UIGridPointState::set_bool_member(PyUIGridPointStateObject* self, PyObject* value, void* closure) {
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Value must be a boolean");
        return -1;
    }

    int truthValue = PyObject_IsTrue(value);
    if (truthValue < 0) {
        return -1; // PyObject_IsTrue returns -1 on error
    }

    if (reinterpret_cast<long>(closure) == 0) { // visible
        self->data->visible = truthValue;
    } else { // discovered
        self->data->discovered = truthValue;
    }

    return 0;
}

// #16 - Get GridPoint at this position (None if not discovered)
PyObject* UIGridPointState::get_point(PyUIGridPointStateObject* self, void* closure) {
    // Return None if entity hasn't discovered this cell
    if (!self->data->discovered) {
        Py_RETURN_NONE;
    }

    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "GridPointState has no parent grid");
        return NULL;
    }

    // Return the GridPoint at this position (use type directly since it's internal-only)
    auto type = &mcrfpydef::PyUIGridPointType;
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    if (!obj) return NULL;

    // Get the GridPoint from the grid
    int idx = self->y * self->grid->grid_w + self->x;
    if (idx < 0 || idx >= static_cast<int>(self->grid->points.size())) {
        Py_DECREF(obj);
        PyErr_SetString(PyExc_IndexError, "GridPointState position out of bounds");
        return NULL;
    }

    obj->data = &(self->grid->points[idx]);
    obj->grid = self->grid;
    return (PyObject*)obj;
}

PyGetSetDef UIGridPointState::getsetters[] = {
    {"visible", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Is the GridPointState visible", (void*)0},
    {"discovered", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Has the GridPointState been discovered", (void*)1},
    {"point", (getter)UIGridPointState::get_point, NULL, "GridPoint at this position (None if not discovered)", NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIGridPointState::repr(PyUIGridPointStateObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<GridPointState (invalid internal object)>";
    else {
        auto gps = self->data;
        ss << "<GridPointState (visible=" << (gps->visible ? "True" : "False") << ", discovered=" << (gps->discovered ? "True" : "False") <<
        ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// #150 - Dynamic attribute access for named layers
PyObject* UIGridPoint::getattro(PyUIGridPointObject* self, PyObject* name) {
    // First try standard attribute lookup (built-in properties)
    PyObject* result = PyObject_GenericGetAttr((PyObject*)self, name);
    if (result != nullptr || !PyErr_ExceptionMatches(PyExc_AttributeError)) {
        return result;
    }

    // Clear the AttributeError and check for layer name
    PyErr_Clear();

    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "GridPoint has no parent grid");
        return nullptr;
    }

    const char* attr_name = PyUnicode_AsUTF8(name);
    if (!attr_name) return nullptr;

    // Look up layer by name
    auto layer = self->grid->getLayerByName(attr_name);
    if (!layer) {
        PyErr_Format(PyExc_AttributeError, "'GridPoint' object has no attribute '%s'", attr_name);
        return nullptr;
    }

    int x = self->data->grid_x;
    int y = self->data->grid_y;

    // Get value based on layer type
    if (layer->type == GridLayerType::Color) {
        auto color_layer = std::static_pointer_cast<ColorLayer>(layer);
        return sfColor_to_PyObject(color_layer->at(x, y));
    } else if (layer->type == GridLayerType::Tile) {
        auto tile_layer = std::static_pointer_cast<TileLayer>(layer);
        return PyLong_FromLong(tile_layer->at(x, y));
    }

    PyErr_SetString(PyExc_RuntimeError, "Unknown layer type");
    return nullptr;
}

int UIGridPoint::setattro(PyUIGridPointObject* self, PyObject* name, PyObject* value) {
    // First try standard attribute setting (built-in properties)
    // We need to check if this is a known attribute first
    const char* attr_name = PyUnicode_AsUTF8(name);
    if (!attr_name) return -1;

    // Check if it's a built-in property (defined in getsetters)
    for (PyGetSetDef* gsd = UIGridPoint::getsetters; gsd->name != nullptr; gsd++) {
        if (strcmp(gsd->name, attr_name) == 0) {
            // It's a built-in property, use standard setter
            return PyObject_GenericSetAttr((PyObject*)self, name, value);
        }
    }

    // Not a built-in property - try layer lookup
    if (!self->grid) {
        PyErr_SetString(PyExc_RuntimeError, "GridPoint has no parent grid");
        return -1;
    }

    auto layer = self->grid->getLayerByName(attr_name);
    if (!layer) {
        PyErr_Format(PyExc_AttributeError, "'GridPoint' object has no attribute '%s'", attr_name);
        return -1;
    }

    int x = self->data->grid_x;
    int y = self->data->grid_y;

    // Set value based on layer type
    if (layer->type == GridLayerType::Color) {
        auto color_layer = std::static_pointer_cast<ColorLayer>(layer);
        sf::Color color = PyObject_to_sfColor(value);
        if (PyErr_Occurred()) return -1;
        color_layer->at(x, y) = color;
        color_layer->markDirty(x, y);  // Mark only the affected chunk
        return 0;
    } else if (layer->type == GridLayerType::Tile) {
        auto tile_layer = std::static_pointer_cast<TileLayer>(layer);
        if (!PyLong_Check(value)) {
            PyErr_SetString(PyExc_TypeError, "Tile layer values must be integers");
            return -1;
        }
        tile_layer->at(x, y) = PyLong_AsLong(value);
        tile_layer->markDirty(x, y);  // Mark only the affected chunk
        return 0;
    }

    PyErr_SetString(PyExc_RuntimeError, "Unknown layer type");
    return -1;
}
