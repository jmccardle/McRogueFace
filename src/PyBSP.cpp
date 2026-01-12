#include "PyBSP.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "PyPositionHelper.h"
#include "PyHeightMap.h"
#include <sstream>
#include <cstdlib>
#include <ctime>

// Static storage for Traversal enum
PyObject* PyTraversal::traversal_enum_class = nullptr;

// Traversal order constants
enum TraversalOrder {
    TRAVERSAL_PRE_ORDER = 0,
    TRAVERSAL_IN_ORDER = 1,
    TRAVERSAL_POST_ORDER = 2,
    TRAVERSAL_LEVEL_ORDER = 3,
    TRAVERSAL_INVERTED_LEVEL_ORDER = 4,
};

// ==================== Traversal Enum ====================

PyObject* PyTraversal::create_enum_class(PyObject* module) {
    // Import IntEnum from enum module
    PyObject* enum_module = PyImport_ImportModule("enum");
    if (!enum_module) {
        return NULL;
    }

    PyObject* int_enum = PyObject_GetAttrString(enum_module, "IntEnum");
    Py_DECREF(enum_module);
    if (!int_enum) {
        return NULL;
    }

    // Create dict of enum members
    PyObject* members = PyDict_New();
    if (!members) {
        Py_DECREF(int_enum);
        return NULL;
    }

    // Add traversal order members
    struct { const char* name; int value; } entries[] = {
        {"PRE_ORDER", TRAVERSAL_PRE_ORDER},
        {"IN_ORDER", TRAVERSAL_IN_ORDER},
        {"POST_ORDER", TRAVERSAL_POST_ORDER},
        {"LEVEL_ORDER", TRAVERSAL_LEVEL_ORDER},
        {"INVERTED_LEVEL_ORDER", TRAVERSAL_INVERTED_LEVEL_ORDER},
    };

    for (const auto& entry : entries) {
        PyObject* value = PyLong_FromLong(entry.value);
        if (!value || PyDict_SetItemString(members, entry.name, value) < 0) {
            Py_XDECREF(value);
            Py_DECREF(members);
            Py_DECREF(int_enum);
            return NULL;
        }
        Py_DECREF(value);
    }

    // Call IntEnum("Traversal", members)
    PyObject* name = PyUnicode_FromString("Traversal");
    if (!name) {
        Py_DECREF(members);
        Py_DECREF(int_enum);
        return NULL;
    }

    PyObject* args = PyTuple_Pack(2, name, members);
    Py_DECREF(name);
    Py_DECREF(members);
    if (!args) {
        Py_DECREF(int_enum);
        return NULL;
    }

    PyObject* traversal_class = PyObject_Call(int_enum, args, NULL);
    Py_DECREF(args);
    Py_DECREF(int_enum);

    if (!traversal_class) {
        return NULL;
    }

    // Cache reference (borrowed by module after AddObject)
    traversal_enum_class = traversal_class;

    // Add to module (steals reference)
    if (PyModule_AddObject(module, "Traversal", traversal_class) < 0) {
        Py_DECREF(traversal_class);
        traversal_enum_class = nullptr;
        return NULL;
    }

    return traversal_class;
}

void PyTraversal::cleanup() {
    // The enum class is owned by the module after PyModule_AddObject
    // We just clear our pointer; the module handles cleanup
    traversal_enum_class = nullptr;
}

int PyTraversal::from_arg(PyObject* arg, int* out_order) {
    // Accept None -> default to LEVEL_ORDER
    if (arg == NULL || arg == Py_None) {
        *out_order = TRAVERSAL_LEVEL_ORDER;
        return 1;
    }

    // Accept Traversal enum member
    if (traversal_enum_class && PyObject_IsInstance(arg, traversal_enum_class)) {
        PyObject* value = PyObject_GetAttrString(arg, "value");
        if (!value) {
            return 0;
        }
        long val = PyLong_AsLong(value);
        Py_DECREF(value);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val >= 0 && val <= TRAVERSAL_INVERTED_LEVEL_ORDER) {
            *out_order = (int)val;
            return 1;
        }
        PyErr_Format(PyExc_ValueError, "Invalid Traversal value: %ld", val);
        return 0;
    }

    // Accept int
    if (PyLong_Check(arg)) {
        long val = PyLong_AsLong(arg);
        if (val == -1 && PyErr_Occurred()) {
            return 0;
        }
        if (val >= 0 && val <= TRAVERSAL_INVERTED_LEVEL_ORDER) {
            *out_order = (int)val;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Invalid traversal value: %ld. Must be 0-4 or use mcrfpy.Traversal enum.", val);
        return 0;
    }

    // Accept string
    if (PyUnicode_Check(arg)) {
        const char* name = PyUnicode_AsUTF8(arg);
        if (!name) {
            return 0;
        }
        if (strcmp(name, "pre") == 0 || strcmp(name, "PRE_ORDER") == 0) {
            *out_order = TRAVERSAL_PRE_ORDER;
            return 1;
        }
        if (strcmp(name, "in") == 0 || strcmp(name, "IN_ORDER") == 0) {
            *out_order = TRAVERSAL_IN_ORDER;
            return 1;
        }
        if (strcmp(name, "post") == 0 || strcmp(name, "POST_ORDER") == 0) {
            *out_order = TRAVERSAL_POST_ORDER;
            return 1;
        }
        if (strcmp(name, "level") == 0 || strcmp(name, "LEVEL_ORDER") == 0) {
            *out_order = TRAVERSAL_LEVEL_ORDER;
            return 1;
        }
        if (strcmp(name, "level_inverted") == 0 || strcmp(name, "INVERTED_LEVEL_ORDER") == 0) {
            *out_order = TRAVERSAL_INVERTED_LEVEL_ORDER;
            return 1;
        }
        PyErr_Format(PyExc_ValueError,
            "Unknown traversal order: '%s'. Use mcrfpy.Traversal enum or: "
            "'pre', 'in', 'post', 'level', 'level_inverted'", name);
        return 0;
    }

    PyErr_SetString(PyExc_TypeError,
        "Traversal order must be mcrfpy.Traversal enum, string, int, or None");
    return 0;
}

// ==================== BSP Property Definitions ====================

PyGetSetDef PyBSP::getsetters[] = {
    {"bounds", (getter)PyBSP::get_bounds, NULL,
     MCRF_PROPERTY(bounds, "Root node bounds as ((x, y), (w, h)). Read-only."), NULL},
    {"pos", (getter)PyBSP::get_pos, NULL,
     MCRF_PROPERTY(pos, "Top-left position (x, y). Read-only."), NULL},
    {"size", (getter)PyBSP::get_size, NULL,
     MCRF_PROPERTY(size, "Dimensions (width, height). Read-only."), NULL},
    {"root", (getter)PyBSP::get_root, NULL,
     MCRF_PROPERTY(root, "Reference to the root BSPNode. Read-only."), NULL},
    {NULL}
};

// Sequence methods for len() and iteration
PySequenceMethods PyBSP::sequence_methods = {
    .sq_length = (lenfunc)PyBSP::len,
};

// ==================== BSP Method Definitions ====================

PyMethodDef PyBSP::methods[] = {
    {"split_once", (PyCFunction)PyBSP::split_once, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSP, split_once,
         MCRF_SIG("(horizontal: bool, position: int)", "BSP"),
         MCRF_DESC("Split the root node once at the specified position. "
                   "horizontal=True creates a horizontal divider, producing top/bottom rooms. "
                   "horizontal=False creates a vertical divider, producing left/right rooms."),
         MCRF_ARGS_START
         MCRF_ARG("horizontal", "True for horizontal divider (top/bottom), False for vertical (left/right)")
         MCRF_ARG("position", "Split coordinate (y for horizontal, x for vertical)")
         MCRF_RETURNS("BSP: self, for method chaining")
     )},
    {"split_recursive", (PyCFunction)PyBSP::split_recursive, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSP, split_recursive,
         MCRF_SIG("(depth: int, min_size: tuple[int, int], max_ratio: float = 1.5, seed: int = None)", "BSP"),
         MCRF_DESC("Recursively split to the specified depth. "
                   "WARNING: Invalidates all existing BSPNode references from this tree."),
         MCRF_ARGS_START
         MCRF_ARG("depth", "Maximum recursion depth (1-16). Creates up to 2^depth leaves.")
         MCRF_ARG("min_size", "Minimum (width, height) for a node to be split.")
         MCRF_ARG("max_ratio", "Maximum aspect ratio before forcing split direction. Default: 1.5.")
         MCRF_ARG("seed", "Random seed. None for random.")
         MCRF_RETURNS("BSP: self, for method chaining")
     )},
    {"clear", (PyCFunction)PyBSP::clear, METH_NOARGS,
     MCRF_METHOD(BSP, clear,
         MCRF_SIG("()", "BSP"),
         MCRF_DESC("Remove all children, keeping only the root node with original bounds. "
                   "WARNING: Invalidates all existing BSPNode references from this tree."),
         MCRF_RETURNS("BSP: self, for method chaining")
     )},
    {"leaves", (PyCFunction)PyBSP::leaves, METH_NOARGS,
     MCRF_METHOD(BSP, leaves,
         MCRF_SIG("()", "Iterator[BSPNode]"),
         MCRF_DESC("Iterate all leaf nodes (the actual rooms). Same as iterating the BSP directly."),
         MCRF_RETURNS("Iterator yielding BSPNode objects")
     )},
    {"traverse", (PyCFunction)PyBSP::traverse, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSP, traverse,
         MCRF_SIG("(order: Traversal = Traversal.LEVEL_ORDER)", "Iterator[BSPNode]"),
         MCRF_DESC("Iterate all nodes in the specified order."),
         MCRF_ARGS_START
         MCRF_ARG("order", "Traversal order from Traversal enum. Default: LEVEL_ORDER.")
         MCRF_RETURNS("Iterator yielding BSPNode objects")
         MCRF_NOTE("Orders: PRE_ORDER, IN_ORDER, POST_ORDER, LEVEL_ORDER, INVERTED_LEVEL_ORDER")
     )},
    {"find", (PyCFunction)PyBSP::find, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSP, find,
         MCRF_SIG("(pos: tuple[int, int])", "BSPNode | None"),
         MCRF_DESC("Find the smallest (deepest) node containing the position."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, list, or Vector")
         MCRF_RETURNS("BSPNode if found, None if position is outside bounds")
     )},
    {"to_heightmap", (PyCFunction)PyBSP::to_heightmap, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSP, to_heightmap,
         MCRF_SIG("(size: tuple[int, int] = None, select: str = 'leaves', shrink: int = 0, value: float = 1.0)", "HeightMap"),
         MCRF_DESC("Convert BSP node selection to a HeightMap."),
         MCRF_ARGS_START
         MCRF_ARG("size", "Output size (width, height). Default: bounds size.")
         MCRF_ARG("select", "'leaves', 'all', or 'internal'. Default: 'leaves'.")
         MCRF_ARG("shrink", "Pixels to shrink from each node's bounds. Default: 0.")
         MCRF_ARG("value", "Value inside selected regions. Default: 1.0.")
         MCRF_RETURNS("HeightMap with selected regions filled")
     )},
    {NULL}
};

// ==================== BSP Implementation ====================

PyObject* PyBSP::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyBSPObject* self = (PyBSPObject*)type->tp_alloc(type, 0);
    if (self) {
        self->root = nullptr;
        self->orig_x = 0;
        self->orig_y = 0;
        self->orig_w = 0;
        self->orig_h = 0;
        self->generation = 0;
    }
    return (PyObject*)self;
}

int PyBSP::init(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"pos", "size", nullptr};
    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "OO", const_cast<char**>(keywords),
                                     &pos_obj, &size_obj)) {
        return -1;
    }

    // Parse position using PyPositionHelper pattern
    int x, y;
    if (!PyPosition_FromObjectInt(pos_obj, &x, &y)) {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y), list, or Vector");
        return -1;
    }

    // Parse size using PyPositionHelper pattern
    int w, h;
    if (!PyPosition_FromObjectInt(size_obj, &w, &h)) {
        PyErr_SetString(PyExc_TypeError, "size must be a tuple (w, h), list, or Vector");
        return -1;
    }

    if (w <= 0 || h <= 0) {
        PyErr_SetString(PyExc_ValueError, "width and height must be positive");
        return -1;
    }

    // Validate against GRID_MAX like HeightMap does
    if (w > GRID_MAX || h > GRID_MAX) {
        PyErr_Format(PyExc_ValueError,
            "BSP dimensions cannot exceed %d (got %dx%d)",
            GRID_MAX, w, h);
        return -1;
    }

    // Clean up any existing BSP
    if (self->root) {
        TCOD_bsp_delete(self->root);
    }

    // Create new BSP with size
    self->root = TCOD_bsp_new_with_size(x, y, w, h);
    if (!self->root) {
        PyErr_SetString(PyExc_MemoryError, "Failed to allocate BSP");
        return -1;
    }

    // Store original bounds for clear()
    self->orig_x = x;
    self->orig_y = y;
    self->orig_w = w;
    self->orig_h = h;
    self->generation = 0;

    return 0;
}

void PyBSP::dealloc(PyBSPObject* self)
{
    if (self->root) {
        TCOD_bsp_delete(self->root);
        self->root = nullptr;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyBSP::repr(PyObject* obj)
{
    PyBSPObject* self = (PyBSPObject*)obj;
    std::ostringstream ss;

    if (self->root) {
        // Count leaves
        int leaf_count = 0;
        TCOD_bsp_traverse_pre_order(self->root, [](TCOD_bsp_t* node, void* data) -> bool {
            if (TCOD_bsp_is_leaf(node)) {
                (*(int*)data)++;
            }
            return true;
        }, &leaf_count);

        ss << "<BSP (" << self->root->w << " x " << self->root->h << "), "
           << leaf_count << " leaves>";
    } else {
        ss << "<BSP (uninitialized)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}

// Property: bounds
PyObject* PyBSP::get_bounds(PyBSPObject* self, void* closure)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }
    return Py_BuildValue("((ii)(ii))",
                         self->root->x, self->root->y,
                         self->root->w, self->root->h);
}

// Property: pos
PyObject* PyBSP::get_pos(PyBSPObject* self, void* closure)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }
    return Py_BuildValue("(ii)", self->root->x, self->root->y);
}

// Property: size
PyObject* PyBSP::get_size(PyBSPObject* self, void* closure)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }
    return Py_BuildValue("(ii)", self->root->w, self->root->h);
}

// Property: root
PyObject* PyBSP::get_root(PyBSPObject* self, void* closure)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }
    return PyBSPNode::create(self->root, (PyObject*)self);
}

// Method: split_once(horizontal, position) -> BSP
PyObject* PyBSP::split_once(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"horizontal", "position", nullptr};
    int horizontal;
    int position;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "pi", const_cast<char**>(keywords),
                                     &horizontal, &position)) {
        return nullptr;
    }

    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Note: split_once only adds children, doesn't remove any nodes
    // Root node pointer remains valid, so we don't increment generation
    TCOD_bsp_split_once(self->root, horizontal ? true : false, position);

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: split_recursive(depth, min_size, max_ratio=1.5, seed=None) -> BSP
PyObject* PyBSP::split_recursive(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"depth", "min_size", "max_ratio", "seed", nullptr};
    int depth;
    PyObject* min_size_obj = nullptr;
    float max_ratio = 1.5f;
    PyObject* seed_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "iO|fO", const_cast<char**>(keywords),
                                     &depth, &min_size_obj, &max_ratio, &seed_obj)) {
        return nullptr;
    }

    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Parse min_size using PyPositionHelper pattern
    int min_w, min_h;
    if (!PyPosition_FromObjectInt(min_size_obj, &min_w, &min_h)) {
        PyErr_SetString(PyExc_TypeError, "min_size must be (width, height) tuple, list, or Vector");
        return nullptr;
    }

    if (depth < 1) {
        PyErr_SetString(PyExc_ValueError, "depth must be at least 1");
        return nullptr;
    }

    if (depth > BSP_MAX_DEPTH) {
        PyErr_Format(PyExc_ValueError,
            "depth cannot exceed %d (got %d) to prevent memory exhaustion",
            BSP_MAX_DEPTH, depth);
        return nullptr;
    }

    if (min_w <= 0 || min_h <= 0) {
        PyErr_SetString(PyExc_ValueError, "min_size values must be positive");
        return nullptr;
    }

    // Create random generator if seed provided
    TCOD_Random* rnd = nullptr;
    if (seed_obj != nullptr && seed_obj != Py_None) {
        if (!PyLong_Check(seed_obj)) {
            PyErr_SetString(PyExc_TypeError, "seed must be an integer or None");
            return nullptr;
        }
        uint32_t seed = (uint32_t)PyLong_AsUnsignedLong(seed_obj);
        if (PyErr_Occurred()) {
            return nullptr;
        }
        rnd = TCOD_random_new_from_seed(TCOD_RNG_MT, seed);
    }

    // Increment generation BEFORE splitting - invalidates existing nodes
    self->generation++;

    TCOD_bsp_split_recursive(self->root, rnd, depth, min_w, min_h, max_ratio, max_ratio);

    if (rnd) {
        TCOD_random_delete(rnd);
    }

    Py_INCREF(self);
    return (PyObject*)self;
}

// Method: clear() -> BSP
PyObject* PyBSP::clear(PyBSPObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Increment generation BEFORE clearing - invalidates existing nodes
    self->generation++;

    TCOD_bsp_remove_sons(self->root);

    // Restore original bounds
    TCOD_bsp_resize(self->root, self->orig_x, self->orig_y, self->orig_w, self->orig_h);

    Py_INCREF(self);
    return (PyObject*)self;
}

// Sequence protocol: len(bsp) returns leaf count
Py_ssize_t PyBSP::len(PyBSPObject* self)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return -1;
    }

    int leaf_count = 0;
    TCOD_bsp_traverse_pre_order(self->root, [](TCOD_bsp_t* node, void* data) -> bool {
        if (TCOD_bsp_is_leaf(node)) {
            (*(int*)data)++;
        }
        return true;
    }, &leaf_count);

    return (Py_ssize_t)leaf_count;
}

// __iter__ is shorthand for leaves()
PyObject* PyBSP::iter(PyBSPObject* self)
{
    return PyBSP::leaves(self, nullptr);
}

// ==================== BSP Iteration ====================

// Traversal callback to collect nodes
struct TraversalData {
    std::vector<TCOD_bsp_t*>* nodes;
    bool leaves_only;
};

static bool collect_callback(TCOD_bsp_t* node, void* userData) {
    TraversalData* data = (TraversalData*)userData;
    if (!data->leaves_only || TCOD_bsp_is_leaf(node)) {
        data->nodes->push_back(node);
    }
    return true;  // Continue traversal
}

// Method: leaves() -> Iterator[BSPNode]
PyObject* PyBSP::leaves(PyBSPObject* self, PyObject* Py_UNUSED(args))
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Create iterator object
    PyBSPIterObject* iter = (PyBSPIterObject*)mcrfpydef::PyBSPIterType.tp_alloc(
        &mcrfpydef::PyBSPIterType, 0);
    if (!iter) {
        return nullptr;
    }

    // Collect all leaf nodes
    iter->nodes = new std::vector<TCOD_bsp_t*>();
    TraversalData data = {iter->nodes, true};  // leaves_only = true
    TCOD_bsp_traverse_level_order(self->root, collect_callback, &data);

    iter->index = 0;
    iter->bsp_owner = (PyObject*)self;
    iter->generation = self->generation;  // Capture generation for validity check
    Py_INCREF(self);

    return (PyObject*)iter;
}

// Method: traverse(order) -> Iterator[BSPNode]
PyObject* PyBSP::traverse(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"order", nullptr};
    PyObject* order_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|O", const_cast<char**>(keywords),
                                     &order_obj)) {
        return nullptr;
    }

    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    int order;
    if (!PyTraversal::from_arg(order_obj, &order)) {
        return nullptr;
    }

    // Create iterator object
    PyBSPIterObject* iter = (PyBSPIterObject*)mcrfpydef::PyBSPIterType.tp_alloc(
        &mcrfpydef::PyBSPIterType, 0);
    if (!iter) {
        return nullptr;
    }

    // Collect all nodes in the specified order
    iter->nodes = new std::vector<TCOD_bsp_t*>();
    TraversalData data = {iter->nodes, false};  // leaves_only = false

    switch (order) {
        case TRAVERSAL_PRE_ORDER:
            TCOD_bsp_traverse_pre_order(self->root, collect_callback, &data);
            break;
        case TRAVERSAL_IN_ORDER:
            TCOD_bsp_traverse_in_order(self->root, collect_callback, &data);
            break;
        case TRAVERSAL_POST_ORDER:
            TCOD_bsp_traverse_post_order(self->root, collect_callback, &data);
            break;
        case TRAVERSAL_LEVEL_ORDER:
            TCOD_bsp_traverse_level_order(self->root, collect_callback, &data);
            break;
        case TRAVERSAL_INVERTED_LEVEL_ORDER:
            TCOD_bsp_traverse_inverted_level_order(self->root, collect_callback, &data);
            break;
    }

    iter->index = 0;
    iter->bsp_owner = (PyObject*)self;
    iter->generation = self->generation;  // Capture generation for validity check
    Py_INCREF(self);

    return (PyObject*)iter;
}

// Method: find(pos) -> BSPNode | None
PyObject* PyBSP::find(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return nullptr;
    }

    TCOD_bsp_t* found = TCOD_bsp_find_node(self->root, x, y);
    if (!found) {
        Py_RETURN_NONE;
    }

    return PyBSPNode::create(found, (PyObject*)self);
}

// Method: to_heightmap(...) -> HeightMap
PyObject* PyBSP::to_heightmap(PyBSPObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"size", "select", "shrink", "value", nullptr};
    PyObject* size_obj = nullptr;
    const char* select = "leaves";
    int shrink = 0;
    float value = 1.0f;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Osif", const_cast<char**>(keywords),
                                     &size_obj, &select, &shrink, &value)) {
        return nullptr;
    }

    if (!self->root) {
        PyErr_SetString(PyExc_RuntimeError, "BSP not initialized");
        return nullptr;
    }

    // Determine output size
    int width = self->root->w;
    int height = self->root->h;
    if (size_obj != nullptr && size_obj != Py_None) {
        if (!PyPosition_FromObjectInt(size_obj, &width, &height)) {
            PyErr_SetString(PyExc_TypeError, "size must be (width, height) tuple, list, or Vector");
            return nullptr;
        }
    }

    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "size values must be positive");
        return nullptr;
    }

    if (shrink < 0) {
        PyErr_SetString(PyExc_ValueError, "shrink must be non-negative");
        return nullptr;
    }

    // Determine which nodes to select
    bool select_leaves = false;
    bool select_internal = false;
    if (strcmp(select, "leaves") == 0) {
        select_leaves = true;
    } else if (strcmp(select, "all") == 0) {
        select_leaves = true;
        select_internal = true;
    } else if (strcmp(select, "internal") == 0) {
        select_internal = true;
    } else {
        PyErr_Format(PyExc_ValueError,
            "select must be 'leaves', 'all', or 'internal', got '%s'", select);
        return nullptr;
    }

    // Create HeightMap
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found");
        return nullptr;
    }

    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    PyObject* hmap_args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);

    PyHeightMapObject* hmap = (PyHeightMapObject*)PyObject_Call(heightmap_type, hmap_args, nullptr);
    Py_DECREF(hmap_args);
    Py_DECREF(heightmap_type);

    if (!hmap) {
        return nullptr;
    }

    // Fill selected nodes
    struct FillData {
        TCOD_heightmap_t* heightmap;
        int shrink;
        float value;
        bool select_leaves;
        bool select_internal;
        int bsp_x, bsp_y;  // BSP origin for offset calculation
        int hmap_w, hmap_h;
    };

    FillData fill_data = {
        hmap->heightmap,
        shrink,
        value,
        select_leaves,
        select_internal,
        self->root->x,
        self->root->y,
        width,
        height
    };

    TCOD_bsp_traverse_level_order(self->root, [](TCOD_bsp_t* node, void* userData) -> bool {
        FillData* data = (FillData*)userData;
        bool is_leaf = TCOD_bsp_is_leaf(node);

        // Check if this node should be selected
        if ((is_leaf && !data->select_leaves) || (!is_leaf && !data->select_internal)) {
            return true;  // Continue but don't fill
        }

        // Calculate bounds with shrink
        int x1 = node->x - data->bsp_x + data->shrink;
        int y1 = node->y - data->bsp_y + data->shrink;
        int x2 = node->x - data->bsp_x + node->w - data->shrink;
        int y2 = node->y - data->bsp_y + node->h - data->shrink;

        // Clamp to heightmap bounds
        if (x1 < 0) x1 = 0;
        if (y1 < 0) y1 = 0;
        if (x2 > data->hmap_w) x2 = data->hmap_w;
        if (y2 > data->hmap_h) y2 = data->hmap_h;

        // Fill the region
        for (int y = y1; y < y2; y++) {
            for (int x = x1; x < x2; x++) {
                TCOD_heightmap_set_value(data->heightmap, x, y, data->value);
            }
        }

        return true;
    }, &fill_data);

    return (PyObject*)hmap;
}

// ==================== BSPNode Property Definitions ====================

PyGetSetDef PyBSPNode::getsetters[] = {
    {"bounds", (getter)PyBSPNode::get_bounds, NULL,
     MCRF_PROPERTY(bounds, "Node bounds as ((x, y), (w, h)). Read-only."), NULL},
    {"pos", (getter)PyBSPNode::get_pos, NULL,
     MCRF_PROPERTY(pos, "Top-left position (x, y). Read-only."), NULL},
    {"size", (getter)PyBSPNode::get_size, NULL,
     MCRF_PROPERTY(size, "Dimensions (width, height). Read-only."), NULL},
    {"level", (getter)PyBSPNode::get_level, NULL,
     MCRF_PROPERTY(level, "Depth in tree (0 for root). Read-only."), NULL},
    {"is_leaf", (getter)PyBSPNode::get_is_leaf, NULL,
     MCRF_PROPERTY(is_leaf, "True if this node has no children. Read-only."), NULL},
    {"split_horizontal", (getter)PyBSPNode::get_split_horizontal, NULL,
     MCRF_PROPERTY(split_horizontal, "Split orientation, None if leaf. Read-only."), NULL},
    {"split_position", (getter)PyBSPNode::get_split_position, NULL,
     MCRF_PROPERTY(split_position, "Split coordinate, None if leaf. Read-only."), NULL},
    {"left", (getter)PyBSPNode::get_left, NULL,
     MCRF_PROPERTY(left, "Left child, or None if leaf. Read-only."), NULL},
    {"right", (getter)PyBSPNode::get_right, NULL,
     MCRF_PROPERTY(right, "Right child, or None if leaf. Read-only."), NULL},
    {"parent", (getter)PyBSPNode::get_parent, NULL,
     MCRF_PROPERTY(parent, "Parent node, or None if root. Read-only."), NULL},
    {"sibling", (getter)PyBSPNode::get_sibling, NULL,
     MCRF_PROPERTY(sibling, "Other child of parent, or None. Read-only."), NULL},
    {NULL}
};

// ==================== BSPNode Method Definitions ====================

PyMethodDef PyBSPNode::methods[] = {
    {"contains", (PyCFunction)PyBSPNode::contains, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(BSPNode, contains,
         MCRF_SIG("(pos: tuple[int, int])", "bool"),
         MCRF_DESC("Check if position is inside this node's bounds."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position as (x, y) tuple, list, or Vector")
         MCRF_RETURNS("bool: True if position is inside bounds")
     )},
    {"center", (PyCFunction)PyBSPNode::center, METH_NOARGS,
     MCRF_METHOD(BSPNode, center,
         MCRF_SIG("()", "tuple[int, int]"),
         MCRF_DESC("Return the center point of this node's bounds."),
         MCRF_RETURNS("tuple[int, int]: Center position (x + w//2, y + h//2)")
     )},
    {NULL}
};

// ==================== BSPNode Implementation ====================

// Validity check - returns false and sets error if node is stale
bool PyBSPNode::checkValid(PyBSPNodeObject* self)
{
    if (!self->node) {
        PyErr_SetString(PyExc_RuntimeError, "BSPNode is invalid (null pointer)");
        return false;
    }

    if (!self->bsp_owner) {
        PyErr_SetString(PyExc_RuntimeError, "BSPNode has no parent BSP");
        return false;
    }

    PyBSPObject* bsp = (PyBSPObject*)self->bsp_owner;
    if (self->generation != bsp->generation) {
        PyErr_SetString(PyExc_RuntimeError,
            "BSPNode is stale: parent BSP was modified (clear() or split_recursive() called). "
            "Re-fetch nodes from the BSP object.");
        return false;
    }

    return true;
}

PyObject* PyBSPNode::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    // BSPNode cannot be directly instantiated
    PyErr_SetString(PyExc_TypeError,
        "BSPNode cannot be instantiated directly. Use BSP methods to get nodes.");
    return NULL;
}

int PyBSPNode::init(PyBSPNodeObject* self, PyObject* args, PyObject* kwds)
{
    // This should never be called since pynew returns NULL
    PyErr_SetString(PyExc_TypeError, "BSPNode cannot be instantiated directly");
    return -1;
}

void PyBSPNode::dealloc(PyBSPNodeObject* self)
{
    // Don't delete the node - it's owned by the BSP tree
    Py_XDECREF(self->bsp_owner);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyBSPNode::repr(PyObject* obj)
{
    PyBSPNodeObject* self = (PyBSPNodeObject*)obj;

    // Check validity without raising error for repr
    PyBSPObject* bsp = self->bsp_owner ? (PyBSPObject*)self->bsp_owner : nullptr;
    bool is_valid = self->node && bsp && self->generation == bsp->generation;

    std::ostringstream ss;

    if (is_valid) {
        const char* type = TCOD_bsp_is_leaf(self->node) ? "leaf" : "split";
        ss << "<BSPNode " << type << " at (" << self->node->x << ", " << self->node->y
           << ") size (" << self->node->w << " x " << self->node->h << ") level "
           << (int)self->node->level << ">";
    } else {
        ss << "<BSPNode (invalid/stale)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}

// Rich comparison for BSPNode - compares underlying pointers
PyObject* PyBSPNode::richcompare(PyObject* self, PyObject* other, int op)
{
    // Only support == and !=
    if (op != Py_EQ && op != Py_NE) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Check if other is also a BSPNode
    if (!PyObject_TypeCheck(other, &mcrfpydef::PyBSPNodeType)) {
        if (op == Py_EQ) Py_RETURN_FALSE;
        else Py_RETURN_TRUE;
    }

    PyBSPNodeObject* self_node = (PyBSPNodeObject*)self;
    PyBSPNodeObject* other_node = (PyBSPNodeObject*)other;

    // Compare wrapped pointers
    bool equal = (self_node->node == other_node->node);

    if (op == Py_EQ) {
        return PyBool_FromLong(equal);
    } else {
        return PyBool_FromLong(!equal);
    }
}

// Helper to create a BSPNode wrapper
PyObject* PyBSPNode::create(TCOD_bsp_t* node, PyObject* bsp_owner)
{
    if (!node) {
        Py_RETURN_NONE;
    }

    PyBSPNodeObject* py_node = (PyBSPNodeObject*)mcrfpydef::PyBSPNodeType.tp_alloc(
        &mcrfpydef::PyBSPNodeType, 0);
    if (!py_node) {
        return nullptr;
    }

    py_node->node = node;
    py_node->bsp_owner = bsp_owner;
    py_node->generation = ((PyBSPObject*)bsp_owner)->generation;
    Py_INCREF(bsp_owner);

    return (PyObject*)py_node;
}

// Property: bounds
PyObject* PyBSPNode::get_bounds(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return Py_BuildValue("((ii)(ii))",
                         self->node->x, self->node->y,
                         self->node->w, self->node->h);
}

// Property: pos
PyObject* PyBSPNode::get_pos(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return Py_BuildValue("(ii)", self->node->x, self->node->y);
}

// Property: size
PyObject* PyBSPNode::get_size(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return Py_BuildValue("(ii)", self->node->w, self->node->h);
}

// Property: level
PyObject* PyBSPNode::get_level(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return PyLong_FromLong(self->node->level);
}

// Property: is_leaf
PyObject* PyBSPNode::get_is_leaf(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return PyBool_FromLong(TCOD_bsp_is_leaf(self->node));
}

// Property: split_horizontal
PyObject* PyBSPNode::get_split_horizontal(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    if (TCOD_bsp_is_leaf(self->node)) {
        Py_RETURN_NONE;
    }
    return PyBool_FromLong(self->node->horizontal);
}

// Property: split_position
PyObject* PyBSPNode::get_split_position(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    if (TCOD_bsp_is_leaf(self->node)) {
        Py_RETURN_NONE;
    }
    return PyLong_FromLong(self->node->position);
}

// Property: left
PyObject* PyBSPNode::get_left(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return PyBSPNode::create(TCOD_bsp_left(self->node), self->bsp_owner);
}

// Property: right
PyObject* PyBSPNode::get_right(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return PyBSPNode::create(TCOD_bsp_right(self->node), self->bsp_owner);
}

// Property: parent
PyObject* PyBSPNode::get_parent(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;
    return PyBSPNode::create(TCOD_bsp_father(self->node), self->bsp_owner);
}

// Property: sibling
PyObject* PyBSPNode::get_sibling(PyBSPNodeObject* self, void* closure)
{
    if (!checkValid(self)) return nullptr;

    TCOD_bsp_t* parent = TCOD_bsp_father(self->node);
    if (!parent) {
        Py_RETURN_NONE;
    }

    TCOD_bsp_t* left = TCOD_bsp_left(parent);
    TCOD_bsp_t* right = TCOD_bsp_right(parent);

    if (left == self->node) {
        return PyBSPNode::create(right, self->bsp_owner);
    } else {
        return PyBSPNode::create(left, self->bsp_owner);
    }
}

// Method: contains(pos) -> bool
PyObject* PyBSPNode::contains(PyBSPNodeObject* self, PyObject* args, PyObject* kwds)
{
    if (!checkValid(self)) return nullptr;

    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return nullptr;
    }

    return PyBool_FromLong(TCOD_bsp_contains(self->node, x, y));
}

// Method: center() -> (x, y)
PyObject* PyBSPNode::center(PyBSPNodeObject* self, PyObject* Py_UNUSED(args))
{
    if (!checkValid(self)) return nullptr;

    int cx = self->node->x + self->node->w / 2;
    int cy = self->node->y + self->node->h / 2;

    return Py_BuildValue("(ii)", cx, cy);
}

// ==================== BSP Iterator Implementation ====================

void PyBSPIter::dealloc(PyBSPIterObject* self)
{
    if (self->nodes) {
        delete self->nodes;
        self->nodes = nullptr;
    }
    Py_XDECREF(self->bsp_owner);
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyBSPIter::iter(PyObject* self)
{
    Py_INCREF(self);
    return self;
}

PyObject* PyBSPIter::next(PyBSPIterObject* self)
{
    if (!self || !self->nodes) {
        PyErr_SetString(PyExc_RuntimeError, "Iterator is invalid");
        return NULL;
    }

    // Check for tree modification during iteration
    if (self->bsp_owner) {
        PyBSPObject* bsp = (PyBSPObject*)self->bsp_owner;
        if (self->generation != bsp->generation) {
            PyErr_SetString(PyExc_RuntimeError,
                "BSP tree was modified during iteration (clear() or split_recursive() called)");
            return NULL;
        }
    }

    if (self->index >= self->nodes->size()) {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }

    TCOD_bsp_t* node = (*self->nodes)[self->index++];
    return PyBSPNode::create(node, self->bsp_owner);
}

int PyBSPIter::init(PyBSPIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "BSPIter cannot be instantiated directly");
    return -1;
}

PyObject* PyBSPIter::repr(PyObject* obj)
{
    PyBSPIterObject* self = (PyBSPIterObject*)obj;
    std::ostringstream ss;

    if (self->nodes) {
        ss << "<BSPIter at " << self->index << "/" << self->nodes->size() << ">";
    } else {
        ss << "<BSPIter (exhausted)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}
