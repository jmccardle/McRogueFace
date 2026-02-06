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

// Greedy meshing (Milestone 13)
PyObject* PyVoxelGrid::get_greedy_meshing(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyBool_FromLong(self->data->isGreedyMeshingEnabled());
}

int PyVoxelGrid::set_greedy_meshing(PyVoxelGridObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "greedy_meshing must be a boolean");
        return -1;
    }

    bool enabled = (value == Py_True);
    self->data->setGreedyMeshing(enabled);
    return 0;
}

// Visible property
PyObject* PyVoxelGrid::get_visible(PyVoxelGridObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }
    return PyBool_FromLong(self->data->isVisible());
}

int PyVoxelGrid::set_visible(PyVoxelGridObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return -1;
    }

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "visible must be a boolean");
        return -1;
    }

    self->data->setVisible(value == Py_True);
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
// Bulk operations - Milestone 11
// =============================================================================

PyObject* PyVoxelGrid::fill_box_hollow(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    static const char* kwlist[] = {"min_coord", "max_coord", "material", "thickness", nullptr};

    PyObject* min_obj = nullptr;
    PyObject* max_obj = nullptr;
    int material;
    int thickness = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOi|i", const_cast<char**>(kwlist),
                                      &min_obj, &max_obj, &material, &thickness)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    if (thickness < 1) {
        PyErr_SetString(PyExc_ValueError, "thickness must be >= 1");
        return nullptr;
    }

    // Parse coordinates
    if (!PyTuple_Check(min_obj) && !PyList_Check(min_obj)) {
        PyErr_SetString(PyExc_TypeError, "min_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (!PyTuple_Check(max_obj) && !PyList_Check(max_obj)) {
        PyErr_SetString(PyExc_TypeError, "max_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(min_obj) != 3 || PySequence_Size(max_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "coordinates must have exactly 3 elements");
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

    self->data->fillBoxHollow(x0, y0, z0, x1, y1, z1, static_cast<uint8_t>(material), thickness);
    Py_RETURN_NONE;
}

PyObject* PyVoxelGrid::fill_sphere(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    PyObject* center_obj = nullptr;
    int radius;
    int material;

    if (!PyArg_ParseTuple(args, "Oii", &center_obj, &radius, &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    if (radius < 0) {
        PyErr_SetString(PyExc_ValueError, "radius must be >= 0");
        return nullptr;
    }

    if (!PyTuple_Check(center_obj) && !PyList_Check(center_obj)) {
        PyErr_SetString(PyExc_TypeError, "center must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(center_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "center must have exactly 3 elements");
        return nullptr;
    }

    int cx, cy, cz;
    PyObject* items[3];
    items[0] = PySequence_GetItem(center_obj, 0);
    items[1] = PySequence_GetItem(center_obj, 1);
    items[2] = PySequence_GetItem(center_obj, 2);

    bool valid = true;
    if (PyLong_Check(items[0])) cx = (int)PyLong_AsLong(items[0]); else valid = false;
    if (PyLong_Check(items[1])) cy = (int)PyLong_AsLong(items[1]); else valid = false;
    if (PyLong_Check(items[2])) cz = (int)PyLong_AsLong(items[2]); else valid = false;

    for (int i = 0; i < 3; i++) Py_DECREF(items[i]);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "center elements must be integers");
        return nullptr;
    }

    self->data->fillSphere(cx, cy, cz, radius, static_cast<uint8_t>(material));
    Py_RETURN_NONE;
}

PyObject* PyVoxelGrid::fill_cylinder(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    PyObject* base_obj = nullptr;
    int radius;
    int height;
    int material;

    if (!PyArg_ParseTuple(args, "Oiii", &base_obj, &radius, &height, &material)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    if (radius < 0) {
        PyErr_SetString(PyExc_ValueError, "radius must be >= 0");
        return nullptr;
    }

    if (height < 1) {
        PyErr_SetString(PyExc_ValueError, "height must be >= 1");
        return nullptr;
    }

    if (!PyTuple_Check(base_obj) && !PyList_Check(base_obj)) {
        PyErr_SetString(PyExc_TypeError, "base_pos must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(base_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "base_pos must have exactly 3 elements");
        return nullptr;
    }

    int cx, cy, cz;
    PyObject* items[3];
    items[0] = PySequence_GetItem(base_obj, 0);
    items[1] = PySequence_GetItem(base_obj, 1);
    items[2] = PySequence_GetItem(base_obj, 2);

    bool valid = true;
    if (PyLong_Check(items[0])) cx = (int)PyLong_AsLong(items[0]); else valid = false;
    if (PyLong_Check(items[1])) cy = (int)PyLong_AsLong(items[1]); else valid = false;
    if (PyLong_Check(items[2])) cz = (int)PyLong_AsLong(items[2]); else valid = false;

    for (int i = 0; i < 3; i++) Py_DECREF(items[i]);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "base_pos elements must be integers");
        return nullptr;
    }

    self->data->fillCylinder(cx, cy, cz, radius, height, static_cast<uint8_t>(material));
    Py_RETURN_NONE;
}

PyObject* PyVoxelGrid::fill_noise(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    static const char* kwlist[] = {"min_coord", "max_coord", "material", "threshold", "scale", "seed", nullptr};

    PyObject* min_obj = nullptr;
    PyObject* max_obj = nullptr;
    int material;
    float threshold = 0.5f;
    float scale = 0.1f;
    unsigned int seed = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OOi|ffI", const_cast<char**>(kwlist),
                                      &min_obj, &max_obj, &material, &threshold, &scale, &seed)) {
        return nullptr;
    }

    if (material < 0 || material > 255) {
        PyErr_SetString(PyExc_ValueError, "material must be 0-255");
        return nullptr;
    }

    // Parse coordinates
    if (!PyTuple_Check(min_obj) && !PyList_Check(min_obj)) {
        PyErr_SetString(PyExc_TypeError, "min_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (!PyTuple_Check(max_obj) && !PyList_Check(max_obj)) {
        PyErr_SetString(PyExc_TypeError, "max_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(min_obj) != 3 || PySequence_Size(max_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "coordinates must have exactly 3 elements");
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

    self->data->fillNoise(x0, y0, z0, x1, y1, z1, static_cast<uint8_t>(material), threshold, scale, seed);
    Py_RETURN_NONE;
}

// =============================================================================
// Copy/paste operations - Milestone 11
// =============================================================================

PyObject* PyVoxelGrid::copy_region(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    PyObject* min_obj = nullptr;
    PyObject* max_obj = nullptr;

    if (!PyArg_ParseTuple(args, "OO", &min_obj, &max_obj)) {
        return nullptr;
    }

    // Parse coordinates
    if (!PyTuple_Check(min_obj) && !PyList_Check(min_obj)) {
        PyErr_SetString(PyExc_TypeError, "min_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (!PyTuple_Check(max_obj) && !PyList_Check(max_obj)) {
        PyErr_SetString(PyExc_TypeError, "max_coord must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(min_obj) != 3 || PySequence_Size(max_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "coordinates must have exactly 3 elements");
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

    // Copy the region
    mcrf::VoxelRegion region = self->data->copyRegion(x0, y0, z0, x1, y1, z1);

    // Create Python object
    PyVoxelRegionObject* result = (PyVoxelRegionObject*)mcrfpydef::PyVoxelRegionType.tp_alloc(
        &mcrfpydef::PyVoxelRegionType, 0);
    if (!result) {
        return nullptr;
    }

    result->data = std::make_shared<mcrf::VoxelRegion>(std::move(region));
    return (PyObject*)result;
}

PyObject* PyVoxelGrid::paste_region(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    static const char* kwlist[] = {"region", "position", "skip_air", nullptr};

    PyObject* region_obj = nullptr;
    PyObject* pos_obj = nullptr;
    int skip_air = 1;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO|p", const_cast<char**>(kwlist),
                                      &region_obj, &pos_obj, &skip_air)) {
        return nullptr;
    }

    // Check region type
    if (!PyObject_TypeCheck(region_obj, &mcrfpydef::PyVoxelRegionType)) {
        PyErr_SetString(PyExc_TypeError, "region must be a VoxelRegion object");
        return nullptr;
    }

    PyVoxelRegionObject* py_region = (PyVoxelRegionObject*)region_obj;
    if (!py_region->data || !py_region->data->isValid()) {
        PyErr_SetString(PyExc_ValueError, "VoxelRegion is empty or invalid");
        return nullptr;
    }

    // Parse position
    if (!PyTuple_Check(pos_obj) && !PyList_Check(pos_obj)) {
        PyErr_SetString(PyExc_TypeError, "position must be a tuple or list of 3 integers");
        return nullptr;
    }
    if (PySequence_Size(pos_obj) != 3) {
        PyErr_SetString(PyExc_ValueError, "position must have exactly 3 elements");
        return nullptr;
    }

    int x, y, z;
    PyObject* items[3];
    items[0] = PySequence_GetItem(pos_obj, 0);
    items[1] = PySequence_GetItem(pos_obj, 1);
    items[2] = PySequence_GetItem(pos_obj, 2);

    bool valid = true;
    if (PyLong_Check(items[0])) x = (int)PyLong_AsLong(items[0]); else valid = false;
    if (PyLong_Check(items[1])) y = (int)PyLong_AsLong(items[1]); else valid = false;
    if (PyLong_Check(items[2])) z = (int)PyLong_AsLong(items[2]); else valid = false;

    for (int i = 0; i < 3; i++) Py_DECREF(items[i]);

    if (!valid) {
        PyErr_SetString(PyExc_TypeError, "position elements must be integers");
        return nullptr;
    }

    self->data->pasteRegion(*py_region->data, x, y, z, skip_air != 0);
    Py_RETURN_NONE;
}

// =============================================================================
// Serialization (Milestone 14)
// =============================================================================

PyObject* PyVoxelGrid::save(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    const char* path = nullptr;
    if (!PyArg_ParseTuple(args, "s", &path)) {
        return nullptr;
    }

    if (self->data->save(path)) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

PyObject* PyVoxelGrid::load(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    const char* path = nullptr;
    if (!PyArg_ParseTuple(args, "s", &path)) {
        return nullptr;
    }

    if (self->data->load(path)) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

PyObject* PyVoxelGrid::to_bytes(PyVoxelGridObject* self, PyObject* Py_UNUSED(args)) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    std::vector<uint8_t> buffer;
    if (!self->data->saveToBuffer(buffer)) {
        PyErr_SetString(PyExc_RuntimeError, "Failed to serialize VoxelGrid");
        return nullptr;
    }

    return PyBytes_FromStringAndSize(reinterpret_cast<const char*>(buffer.data()), buffer.size());
}

PyObject* PyVoxelGrid::from_bytes(PyVoxelGridObject* self, PyObject* args) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    Py_buffer buffer;
    if (!PyArg_ParseTuple(args, "y*", &buffer)) {
        return nullptr;
    }

    bool success = self->data->loadFromBuffer(
        static_cast<const uint8_t*>(buffer.buf), buffer.len);

    PyBuffer_Release(&buffer);

    if (success) {
        Py_RETURN_TRUE;
    } else {
        Py_RETURN_FALSE;
    }
}

// =============================================================================
// Navigation Projection (Milestone 12)
// =============================================================================

static PyObject* project_column(PyVoxelGridObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"x", "z", "headroom", nullptr};
    int x = 0, z = 0, headroom = 2;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii|i", const_cast<char**>(kwlist),
                                      &x, &z, &headroom)) {
        return nullptr;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "VoxelGrid not initialized");
        return nullptr;
    }

    if (headroom < 0) {
        PyErr_SetString(PyExc_ValueError, "headroom must be non-negative");
        return nullptr;
    }

    mcrf::VoxelGrid::NavInfo nav = self->data->projectColumn(x, z, headroom);

    // Return as dictionary with nav info
    return Py_BuildValue("{s:f,s:O,s:O,s:f}",
                         "height", nav.height,
                         "walkable", nav.walkable ? Py_True : Py_False,
                         "transparent", nav.transparent ? Py_True : Py_False,
                         "path_cost", nav.pathCost);
}

// =============================================================================
// PyVoxelRegion implementation
// =============================================================================

void PyVoxelRegion::dealloc(PyVoxelRegionObject* self) {
    self->data.reset();
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyVoxelRegion::repr(PyObject* obj) {
    PyVoxelRegionObject* self = (PyVoxelRegionObject*)obj;
    if (!self->data || !self->data->isValid()) {
        return PyUnicode_FromString("<VoxelRegion (empty)>");
    }

    std::ostringstream oss;
    oss << "<VoxelRegion " << self->data->width << "x"
        << self->data->height << "x" << self->data->depth
        << " voxels=" << self->data->totalVoxels() << ">";
    return PyUnicode_FromString(oss.str().c_str());
}

PyObject* PyVoxelRegion::get_size(PyVoxelRegionObject* self, void* closure) {
    if (!self->data || !self->data->isValid()) {
        return Py_BuildValue("(iii)", 0, 0, 0);
    }
    return Py_BuildValue("(iii)", self->data->width, self->data->height, self->data->depth);
}

PyObject* PyVoxelRegion::get_width(PyVoxelRegionObject* self, void* closure) {
    if (!self->data) return PyLong_FromLong(0);
    return PyLong_FromLong(self->data->width);
}

PyObject* PyVoxelRegion::get_height(PyVoxelRegionObject* self, void* closure) {
    if (!self->data) return PyLong_FromLong(0);
    return PyLong_FromLong(self->data->height);
}

PyObject* PyVoxelRegion::get_depth(PyVoxelRegionObject* self, void* closure) {
    if (!self->data) return PyLong_FromLong(0);
    return PyLong_FromLong(self->data->depth);
}

PyGetSetDef PyVoxelRegion::getsetters[] = {
    {"size", (getter)get_size, nullptr,
     "Dimensions (width, height, depth) of the region. Read-only.", nullptr},
    {"width", (getter)get_width, nullptr, "Region width. Read-only.", nullptr},
    {"height", (getter)get_height, nullptr, "Region height. Read-only.", nullptr},
    {"depth", (getter)get_depth, nullptr, "Region depth. Read-only.", nullptr},
    {nullptr}  // Sentinel
};

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
    {"fill_box_hollow", (PyCFunction)fill_box_hollow, METH_VARARGS | METH_KEYWORDS,
     "fill_box_hollow(min_coord, max_coord, material, thickness=1) -> None\n\n"
     "Create a hollow rectangular room (walls only, hollow inside).\n\n"
     "Args:\n"
     "    min_coord: (x0, y0, z0) - minimum corner (inclusive)\n"
     "    max_coord: (x1, y1, z1) - maximum corner (inclusive)\n"
     "    material: material ID for walls (0-255)\n"
     "    thickness: wall thickness in voxels (default 1)"},
    {"fill_sphere", (PyCFunction)fill_sphere, METH_VARARGS,
     "fill_sphere(center, radius, material) -> None\n\n"
     "Fill a spherical region.\n\n"
     "Args:\n"
     "    center: (cx, cy, cz) - sphere center coordinates\n"
     "    radius: sphere radius in voxels\n"
     "    material: material ID (0-255, use 0 to carve)"},
    {"fill_cylinder", (PyCFunction)fill_cylinder, METH_VARARGS,
     "fill_cylinder(base_pos, radius, height, material) -> None\n\n"
     "Fill a vertical cylinder (Y-axis aligned).\n\n"
     "Args:\n"
     "    base_pos: (cx, cy, cz) - base center position\n"
     "    radius: cylinder radius in voxels\n"
     "    height: cylinder height in voxels\n"
     "    material: material ID (0-255)"},
    {"fill_noise", (PyCFunction)fill_noise, METH_VARARGS | METH_KEYWORDS,
     "fill_noise(min_coord, max_coord, material, threshold=0.5, scale=0.1, seed=0) -> None\n\n"
     "Fill region with 3D noise-based pattern (caves, clouds).\n\n"
     "Args:\n"
     "    min_coord: (x0, y0, z0) - minimum corner\n"
     "    max_coord: (x1, y1, z1) - maximum corner\n"
     "    material: material ID for solid areas\n"
     "    threshold: noise threshold (0-1, higher = more solid)\n"
     "    scale: noise scale (smaller = larger features)\n"
     "    seed: random seed (0 for default)"},
    {"copy_region", (PyCFunction)copy_region, METH_VARARGS,
     "copy_region(min_coord, max_coord) -> VoxelRegion\n\n"
     "Copy a rectangular region to a VoxelRegion prefab.\n\n"
     "Args:\n"
     "    min_coord: (x0, y0, z0) - minimum corner (inclusive)\n"
     "    max_coord: (x1, y1, z1) - maximum corner (inclusive)\n\n"
     "Returns:\n"
     "    VoxelRegion object that can be pasted elsewhere."},
    {"paste_region", (PyCFunction)paste_region, METH_VARARGS | METH_KEYWORDS,
     "paste_region(region, position, skip_air=True) -> None\n\n"
     "Paste a VoxelRegion prefab at the specified position.\n\n"
     "Args:\n"
     "    region: VoxelRegion from copy_region()\n"
     "    position: (x, y, z) - paste destination\n"
     "    skip_air: if True, air voxels don't overwrite (default True)"},
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
    {"project_column", (PyCFunction)project_column, METH_VARARGS | METH_KEYWORDS,
     "project_column(x, z, headroom=2) -> dict\n\n"
     "Project a single column to navigation info.\n\n"
     "Scans the column from top to bottom, finding the topmost floor\n"
     "(solid voxel with air above) and checking for adequate headroom.\n\n"
     "Args:\n"
     "    x: X coordinate in voxel grid\n"
     "    z: Z coordinate in voxel grid\n"
     "    headroom: Required air voxels above floor (default 2)\n\n"
     "Returns:\n"
     "    dict with keys:\n"
     "        height (float): World Y of floor surface\n"
     "        walkable (bool): True if floor found with adequate headroom\n"
     "        transparent (bool): True if no opaque voxels in column\n"
     "        path_cost (float): Floor material's path cost"},
    {"save", (PyCFunction)PyVoxelGrid::save, METH_VARARGS,
     "save(path) -> bool\n\n"
     "Save the voxel grid to a binary file.\n\n"
     "Args:\n"
     "    path: File path to save to (.mcvg extension recommended)\n\n"
     "Returns:\n"
     "    True on success, False on failure.\n\n"
     "The file format includes grid dimensions, cell size, material palette,\n"
     "and RLE-compressed voxel data."},
    {"load", (PyCFunction)PyVoxelGrid::load, METH_VARARGS,
     "load(path) -> bool\n\n"
     "Load voxel data from a binary file.\n\n"
     "Args:\n"
     "    path: File path to load from\n\n"
     "Returns:\n"
     "    True on success, False on failure.\n\n"
     "Note: This replaces the current grid data entirely, including\n"
     "dimensions and material palette."},
    {"to_bytes", (PyCFunction)PyVoxelGrid::to_bytes, METH_NOARGS,
     "to_bytes() -> bytes\n\n"
     "Serialize the voxel grid to a bytes object.\n\n"
     "Returns:\n"
     "    bytes object containing the serialized grid data.\n\n"
     "Useful for network transmission or custom storage."},
    {"from_bytes", (PyCFunction)PyVoxelGrid::from_bytes, METH_VARARGS,
     "from_bytes(data) -> bool\n\n"
     "Load voxel data from a bytes object.\n\n"
     "Args:\n"
     "    data: bytes object containing serialized grid data\n\n"
     "Returns:\n"
     "    True on success, False on failure.\n\n"
     "Note: This replaces the current grid data entirely."},
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
    {"greedy_meshing", (getter)get_greedy_meshing, (setter)set_greedy_meshing,
     "Enable greedy meshing optimization (reduces vertex count for uniform regions).", nullptr},
    {"visible", (getter)get_visible, (setter)set_visible,
     "Show or hide this voxel grid in rendering.", nullptr},
    {nullptr}  // Sentinel
};
