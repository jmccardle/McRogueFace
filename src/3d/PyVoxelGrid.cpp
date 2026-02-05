// PyVoxelGrid.cpp - Python bindings for VoxelGrid implementation
// Part of McRogueFace 3D Extension - Milestone 9

#include "PyVoxelGrid.h"
#include "../McRFPy_API.h"
#include "../PyColor.h"
#include <sstream>

// =============================================================================
// Python type interface
// =============================================================================

PyObject* PyVoxelGrid::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    PyVoxelGridObject* self = (PyVoxelGridObject*)type->tp_alloc(type, 0);
    if (self) {
        self->data = nullptr;  // Will be initialized in init
        self->weakreflist = nullptr;
    }
    return (PyObject*)self;
}

int PyVoxelGrid::init(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"size", "cell_size", nullptr};

    PyObject* size_obj = nullptr;
    float cell_size = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|f", const_cast<char**>(kwlist),
                                      &size_obj, &cell_size)) {
        return -1;
    }

    // Parse size tuple
    if (!PyTuple_Check(size_obj) && !PyList_Check(size_obj)) {
        PyErr_SetString(PyExc_TypeError, "size must be a tuple or list of 3 integers");
        return -1;
    }

    if (PySequence_Size(size_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "size must have exactly 3 elements (width, height, depth)");
        return -1;
    }

    int width = 0, height = 0, depth = 0;

    PyObject* w_obj = PySequence_GetItem(size_obj, 0);
    PyObject* h_obj = PySequence_GetItem(size_obj, 1);
    PyObject* d_obj = PySequence_GetItem(size_obj, 2);

    bool valid = true;
    if (PyLong_Check(w_obj)) width = (int)PyLong_AsLong(w_obj); else valid = false;
    if (PyLong_Check(h_obj)) height = (int)PyLong_AsLong(h_obj); else valid = false;
    if (PyLong_Check(d_obj)) depth = (int)PyLong_AsLong(d_obj); else valid = false;

    Py_DECREF(w_obj);
    Py_DECREF(h_obj);
    Py_DECREF(d_obj);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "size elements must be integers");
        return -1;
    }

    if (width <= 0 || height <= 0 || depth <= 0) {
        PyErr_SetString(PyExc_ValueError, "size dimensions must be positive");
        return -1;
    }

    if (cell_size <= 0.0f) {
        PyErr_SetString(PyExc_ValueError, "cell_size must be positive");
        return -1;
    }

    // Create the VoxelGrid
    try {
        self->data = std::make_shared<mcrf::VoxelGrid>(width, height, depth, cell_size);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return -1;
    }

    return 0;
}

void PyVoxelGrid::dealloc(PyVoxelGridObject* self) {
    PyObject_GC_UnTrack(self);
    if (self->weakreflist != nullptr) {
        PyObject_ClearWeakRefs((PyObject*)self);
    }
    self->data.reset();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyVoxelGrid::repr(PyObject* obj) {
    PyVoxelGridObject* self = (PyVoxelGridObject*)obj;
    if (!self->data) {
        return PyUnicode_FromString("<VoxelGrid (uninitialized)>");
    }

    std::ostringstream oss;
    oss << "<VoxelGrid " << self->data->width() << "x"
        << self->data->height() << "x" << self->data->depth()
        << " cells=" << self->data->totalVoxels()
        << " materials=" << self->data->materialCount()
        << " non_air=" << self->data->countNonAir() << ">";
    return PyUnicode_FromString(oss.str().c_str());
}

// =============================================================================
// Properties - dimensions (read-only)
// =============================================================================

PyObject* PyVoxelGrid::get_size(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return Py_BuildValue("(iii)", self->data->width(), self->data->height(), self->data->depth());
}

PyObject* PyVoxelGrid::get_width(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyLong_FromLong(self->data->width());
}

PyObject* PyVoxelGrid::get_height(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyLong_FromLong(self->data->height());
}

PyObject* PyVoxelGrid::get_depth(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyLong_FromLong(self->data->depth());
}

PyObject* PyVoxelGrid::get_cell_size(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyFloat_FromDouble(self->data->cellSize());
}

PyObject* PyVoxelGrid::get_material_count(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyLong_FromSize_t(self->data->materialCount());
}

// =============================================================================
// Properties - transform (read-write)
// =============================================================================

PyObject* PyVoxelGrid::get_offset(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    mcrf::vec3 offset = self->data->getOffset();
    return Py_BuildValue("(fff)", offset.x, offset.y, offset.z);
}

int PyVoxelGrid::set_offset(PyVoxelGridObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return -1;
    }

    if (!PyTuple_Check(value) && !PyList_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "offset must be a tuple or list of 3 floats");
        return -1;
    }

    if (PySequence_Size(value) != 3) {
        PyErr_SetString(PyExc_ValueError, "offset must have exactly 3 elements (x, y, z)");
        return -1;
    }

    float x = 0, y = 0, z = 0;
    PyObject* x_obj = PySequence_GetItem(value, 0);
    PyObject* y_obj = PySequence_GetItem(value, 1);
    PyObject* z_obj = PySequence_GetItem(value, 2);

    bool valid = true;
    if (PyNumber_Check(x_obj)) x = (float)PyFloat_AsDouble(PyNumber_Float(x_obj)); else valid = false;
    if (PyNumber_Check(y_obj)) y = (float)PyFloat_AsDouble(PyNumber_Float(y_obj)); else valid = false;
    if (PyNumber_Check(z_obj)) z = (float)PyFloat_AsDouble(PyNumber_Float(z_obj)); else valid = false;

    Py_DECREF(x_obj);
    Py_DECREF(y_obj);
    Py_DECREF(z_obj);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "offset elements must be numbers");
        return -1;
    }

    self->data->setOffset(x, y, z);
    return 0;
}

PyObject* PyVoxelGrid::get_rotation(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyFloat_FromDouble(self->data->getRotation());
}

int PyVoxelGrid::set_rotation(PyVoxelGridObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return -1;
    }

    if (!PyNumber_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "rotation must be a number");
        return -1;
    }

    float rotation = (float)PyFloat_AsDouble(PyNumber_Float(value));
    self->data->setRotation(rotation);
    return 0;
}

// =============================================================================
// Voxel access methods
// =============================================================================

PyObject* PyVoxelGrid::get(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    int x, y, z;
    if (!PyArg_ParseTuple(args, "iii", &x, &y, &z)) {
        return nullptr;
    }

    // Bounds check with warning (returns 0 for out-of-bounds, like C++ API)
    if (!self->data->isValid(x, y, z)) {
        // Return 0 (air) for out-of-bounds, matching C++ behavior
        return PyLong_FromLong(0);
    }

    return PyLong_FromLong(self->data->get(x, y, z));
}

PyObject* PyVoxelGrid::set(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    int x, y, z, material;
    if (!PyArg_ParseTuple(args, "iiii", &x, &y, &z, &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    // Bounds check - silently ignore out-of-bounds, like C++ API
    self->data->set(x, y, z, static_cast<uint8_t>(material));
    Py_RETURN_NONE;
}

// =============================================================================
// Material methods
// =============================================================================

PyObject* PyVoxelGrid::add_material(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    static const char* kwlist[] = {"name", "color", "sprite_index", "transparent", "path_cost", nullptr};

    const char* name = nullptr;
    PyObject* color_obj = nullptr;
    int sprite_index = -1;
    int transparent = 0;  // Python bool maps to int
    float path_cost = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s|Oipf", const_cast<char**>(kwlist),
                                      &name, &color_obj, &sprite_index, &transparent, &path_cost)) {
        return nullptr;
    }

    // Default color is white
    sf::Color color = sf::Color::White;

    // Parse color if provided
    if (color_obj && color_obj != Py_None) {
        color = PyColor::fromPy(color_obj);
        if (PyErr_Occurred()) {
            return nullptr;
        }
    }

    try {
        uint8_t id = self->data->addMaterial(name, color, sprite_index, transparent != 0, path_cost);
        return PyLong_FromLong(id);
    } catch (const std::exception& e) {
        PyErr_SetString(PyExc_RuntimeError, e.what());
        return nullptr;
    }
}

PyObject* PyVoxelGrid::get_material(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    int id;
    if (!PyArg_ParseTuple(args, "i", &id)) {
        return nullptr;
    }

    if (id < 0 || id > 255) {
        PyErr_SetString(PyExc_ValueError, "material id must be 0-255");
        return nullptr;
    }

    const mcrf::VoxelMaterial& mat = self->data->getMaterial(static_cast<uint8_t>(id));

    // Create color object
    PyObject* color_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    if (!color_type) {
        return nullptr;
    }

    PyObject* color_obj = PyObject_Call(color_type,
        Py_BuildValue("(iiii)", mat.color.r, mat.color.g, mat.color.b, mat.color.a),
        nullptr);
    Py_DECREF(color_type);

    if (!color_obj) {
        return nullptr;
    }

    // Build result dict
    PyObject* result = Py_BuildValue("{s:s, s:N, s:i, s:O, s:f}",
        "name", mat.name.c_str(),
        "color", color_obj,
        "sprite_index", mat.spriteIndex,
        "transparent", mat.transparent ? Py_True : Py_False,
        "path_cost", mat.pathCost);

    return result;
}

// =============================================================================
// Bulk operations
// =============================================================================

PyObject* PyVoxelGrid::fill(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    int material;
    if (!PyArg_ParseTuple(args, "i", &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    self->data->fill(static_cast<uint8_t>(material));
    Py_RETURN_NONE;
}

PyObject* PyVoxelGrid::clear(PyVoxelGridObject* self, PyObject* Py_UNUSED(args)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    self->data->clear();
    Py_RETURN_NONE;
}

PyObject* PyVoxelGrid::fill_box(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    PyObject* min_obj = nullptr;
    PyObject* max_obj = nullptr;
    int material;

    if (!PyArg_ParseTuple(args, "OOi", &min_obj, &max_obj, &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    // Parse min tuple (x0, y0, z0)
    if (!PyTuple_Check(min_obj) && !PyList_Check(min_obj)) {
        PyErr_SetString(PyExc_TypeError, "min_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(min_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "min_coord must have exactly 3 elements");
        return nullptr;
    }

    // Parse max tuple (x1, y1, z1)
    if (!PyTuple_Check(max_obj) && !PyList_Check(max_obj)) {
        PyErr_SetString(PyExc_TypeError, "max_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(max_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "max_coord must have exactly 3 elements");
        return nullptr;
    }

    int x0, y0, z0, x1, y1, z1;
    PyObject* items[6];

    items[0] = PySequence_GetItem(min_obj, 0);
    items[1] = PySequence_GetItem(min_obj, 1);
    items[2] = PySequence_GetItem(min_obj, 2);
    items[3] = PySequence_GetItem(max_obj, 0);
    items[4] = PySequence_GetItem(max_obj, 1);
    items[5] = PySequence_GetItem(max_obj, 2);

    bool valid = true;
    if (PyLong_Check(items[0])) x0 = (int)PyLong_AsLong(items[0]); else valid = false;
    if (PyLong_Check(items[1])) y0 = (int)PyLong_AsLong(items[1]); else valid = false;
    if (PyLong_Check(items[2])) z0 = (int)PyLong_AsLong(items[2]); else valid = false;
    if (PyLong_Check(items[3])) x1 = (int)PyLong_AsLong(items[3]); else valid = false;
    if (PyLong_Check(items[4])) y1 = (int)PyLong_AsLong(items[4]); else valid = false;
    if (PyLong_Check(items[5])) z1 = (int)PyLong_AsLong(items[5]); else valid = false;

    for (int i = 0; i < 6; i++) Py_DECREF(items[i]);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "coordinate elements must be integers");
        return nullptr;
    }

    self->data->fillBox(x0, y0, z0, x1, y1, z1, static_cast<uint8_t>(material));
    Py_RETURN_NONE;
}

// =============================================================================
// Mesh caching methods (Milestone 10)
// =============================================================================

PyObject* PyVoxelGrid::get_vertex_count(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyLong_FromSize_t(self->data->vertexCount());
}

PyObject* PyVoxelGrid::rebuild_mesh(PyVoxelGridObject* self, PyObject* Py_UNUSED(args)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    self->data->rebuildMesh();
    Py_RETURN_NONE;
}

// =============================================================================
// Statistics
// =============================================================================

PyObject* PyVoxelGrid::count_non_air(PyVoxelGridObject* self, PyObject* Py_UNUSED(args)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    return PyLong_FromSize_t(self->data->countNonAir());
}

PyObject* PyVoxelGrid::count_material(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    int material;
    if (!PyArg_ParseTuple(args, "i", &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    return PyLong_FromSize_t(self->data->countMaterial(static_cast<uint8_t>(material)));
}

// =============================================================================
// Method definitions
// =============================================================================

PyMethodDef PyVoxelGrid::methods[] = {
    {"get", (PyCFunction)get, METH_VARARGS,
     "get(x, y, z) -> int\n\n"
     "Get the material ID at integer coordinates.\n\n"
     "Returns 0 (air) for out-of-bounds coordinates."},
    {"set", (PyCFunction)set, METH_VARARGS,
     "set(x, y, z, material) -> None\n\n"
     "Set the material ID at integer coordinates.\n\n"
     "Out-of-bounds coordinates are silently ignored."},
    {"add_material", (PyCFunction)add_material, METH_VARARGS | METH_KEYWORDS,
     "add_material(name, color=Color(255,255,255), sprite_index=-1, transparent=False, path_cost=1.0) -> int\n\n"
     "Add a new material to the palette. Returns the material ID (1-indexed).\n\n"
     "Material 0 is always air (implicit, never stored in palette).\n"
     "Maximum 255 materials can be added."},
    {"get_material", (PyCFunction)get_material, METH_VARARGS,
     "get_material(id) -> dict\n\n"
     "Get material properties by ID.\n\n"
     "Returns dict with keys: name, color, sprite_index, transparent, path_cost.\n"
     "ID 0 returns the implicit air material."},
    {"fill", (PyCFunction)fill, METH_VARARGS,
     "fill(material) -> None\n\n"
     "Fill the entire grid with the specified material ID."},
    {"fill_box", (PyCFunction)fill_box, METH_VARARGS,
     "fill_box(min_coord, max_coord, material) -> None\n\n"
     "Fill a rectangular region with the specified material.\n\n"
     "Args:\n"
     "    min_coord: (x0, y0, z0) - minimum corner (inclusive)\n"
     "    max_coord: (x1, y1, z1) - maximum corner (inclusive)\n"
     "    material: material ID (0-255)\n\n"
     "Coordinates are clamped to grid bounds."},
    {"clear", (PyCFunction)clear, METH_NOARGS,
     "clear() -> None\n\n"
     "Clear the grid (fill with air, material 0)."},
    {"rebuild_mesh", (PyCFunction)rebuild_mesh, METH_NOARGS,
     "rebuild_mesh() -> None\n\n"
     "Force immediate mesh rebuild for rendering."},
    {"count_non_air", (PyCFunction)count_non_air, METH_NOARGS,
     "count_non_air() -> int\n\n"
     "Count the number of non-air voxels in the grid."},
    {"count_material", (PyCFunction)count_material, METH_VARARGS,
     "count_material(material) -> int\n\n"
     "Count the number of voxels with the specified material ID."},
    {nullptr}  // Sentinel
};

// =============================================================================
// Property definitions
// =============================================================================

PyGetSetDef PyVoxelGrid::getsetters[] = {
    {"size", (getter)get_size, nullptr,
     "Dimensions (width, height, depth) of the grid. Read-only.", nullptr},
    {"width", (getter)get_width, nullptr,
     "Grid width (X dimension). Read-only.", nullptr},
    {"height", (getter)get_height, nullptr,
     "Grid height (Y dimension). Read-only.", nullptr},
    {"depth", (getter)get_depth, nullptr,
     "Grid depth (Z dimension). Read-only.", nullptr},
    {"cell_size", (getter)get_cell_size, nullptr,
     "World units per voxel. Read-only.", nullptr},
    {"material_count", (getter)get_material_count, nullptr,
     "Number of materials in the palette. Read-only.", nullptr},
    {"vertex_count", (getter)get_vertex_count, nullptr,
     "Number of vertices after mesh generation. Read-only.", nullptr},
    {"offset", (getter)get_offset, (setter)set_offset,
     "World-space position (x, y, z) of the grid origin.", nullptr},
    {"rotation", (getter)get_rotation, (setter)set_rotation,
     "Y-axis rotation in degrees.", nullptr},
    {nullptr}  // Sentinel
};
