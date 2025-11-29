#include "UIGridPoint.h"
#include "UIGrid.h"
#include "GridLayers.h"  // #150 - for GridLayerType, ColorLayer, TileLayer
#include <cstring>       // #150 - for strcmp

UIGridPoint::UIGridPoint()
: color(1.0f, 1.0f, 1.0f), color_overlay(0.0f, 0.0f, 0.0f), walkable(false), transparent(false),
 tilesprite(-1), tile_overlay(-1), uisprite(-1), grid_x(-1), grid_y(-1), parent_grid(nullptr)
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

PyObject* UIGridPoint::get_color(PyUIGridPointObject* self, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) { // color
        return sfColor_to_PyObject(self->data->color);
    } else { // color_overlay
        return sfColor_to_PyObject(self->data->color_overlay);
    }
}

int UIGridPoint::set_color(PyUIGridPointObject* self, PyObject* value, void* closure) {
    sf::Color color = PyObject_to_sfColor(value);
    // Check if an error occurred during conversion
    if (PyErr_Occurred()) {
        return -1;
    }
    
    if (reinterpret_cast<long>(closure) == 0) { // color
        self->data->color = color;
    } else { // color_overlay
        self->data->color_overlay = color;
    }
    return 0;
}

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

PyObject* UIGridPoint::get_int_member(PyUIGridPointObject* self, void* closure) {
    switch(reinterpret_cast<long>(closure)) {
        case 0: return PyLong_FromLong(self->data->tilesprite);
        case 1: return PyLong_FromLong(self->data->tile_overlay);
        case 2: return PyLong_FromLong(self->data->uisprite);
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return nullptr;
    }
}

int UIGridPoint::set_int_member(PyUIGridPointObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;

    switch(reinterpret_cast<long>(closure)) {
        case 0: self->data->tilesprite = val; break;
        case 1: self->data->tile_overlay = val; break;
        case 2: self->data->uisprite = val; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid closure"); return -1;
    }
    return 0;
}

PyGetSetDef UIGridPoint::getsetters[] = {
    {"color", (getter)UIGridPoint::get_color, (setter)UIGridPoint::set_color, "GridPoint color", (void*)0},
    {"color_overlay", (getter)UIGridPoint::get_color, (setter)UIGridPoint::set_color, "GridPoint color overlay", (void*)1},
    {"walkable", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint walkable", (void*)0},
    {"transparent", (getter)UIGridPoint::get_bool_member, (setter)UIGridPoint::set_bool_member, "Is the GridPoint transparent", (void*)1},
    {"tilesprite", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "Tile sprite index", (void*)0},
    {"tile_overlay", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "Tile overlay sprite index", (void*)1},
    {"uisprite", (getter)UIGridPoint::get_int_member, (setter)UIGridPoint::set_int_member, "UI sprite index", (void*)2},
    {NULL}  /* Sentinel */
};

PyObject* UIGridPoint::repr(PyUIGridPointObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<GridPoint (invalid internal object)>";
    else {
        auto gp = self->data;
        ss << "<GridPoint (walkable=" << (gp->walkable ? "True" : "False") << ", transparent=" << (gp->transparent ? "True" : "False") << 
              ", tilesprite=" << gp->tilesprite << ", tile_overlay=" << gp->tile_overlay << ", uisprite=" << gp->uisprite <<
        ")>";
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

PyGetSetDef UIGridPointState::getsetters[] = {
    {"visible", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Is the GridPointState visible", (void*)0},
    {"discovered", (getter)UIGridPointState::get_bool_member, (setter)UIGridPointState::set_bool_member, "Has the GridPointState been discovered", (void*)1},
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
        color_layer->markDirty();
        return 0;
    } else if (layer->type == GridLayerType::Tile) {
        auto tile_layer = std::static_pointer_cast<TileLayer>(layer);
        if (!PyLong_Check(value)) {
            PyErr_SetString(PyExc_TypeError, "Tile layer values must be integers");
            return -1;
        }
        tile_layer->at(x, y) = PyLong_AsLong(value);
        tile_layer->markDirty();
        return 0;
    }

    PyErr_SetString(PyExc_RuntimeError, "Unknown layer type");
    return -1;
}
