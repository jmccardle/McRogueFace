#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>
#include <vector>
#include <cstdint>

// Forward declarations
class PyBSP;
class PyBSPNode;

// Maximum recursion depth to prevent memory exhaustion
// 2^16 = 65536 potential leaf nodes, which is already excessive
constexpr int BSP_MAX_DEPTH = 16;

// Python object structure for BSP tree (root owner)
typedef struct {
    PyObject_HEAD
    TCOD_bsp_t* root;           // libtcod BSP root (owned, will be deleted)
    int orig_x, orig_y;         // Original bounds for clear()
    int orig_w, orig_h;
    uint64_t generation;        // Incremented on structural changes (clear, split)
} PyBSPObject;

// Python object structure for BSPNode (lightweight reference)
typedef struct {
    PyObject_HEAD
    TCOD_bsp_t* node;           // libtcod BSP node (NOT owned)
    PyObject* bsp_owner;        // Reference to PyBSPObject to prevent dangling
    uint64_t generation;        // Generation at time of creation (for validity check)
} PyBSPNodeObject;

// BSP iterator for traverse()
typedef struct {
    PyObject_HEAD
    std::vector<TCOD_bsp_t*>* nodes;  // Pre-collected nodes
    size_t index;
    PyObject* bsp_owner;              // Reference to PyBSPObject
    uint64_t generation;              // Generation at iterator creation
} PyBSPIterObject;

class PyBSP
{
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyBSPObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyBSPObject* self);
    static PyObject* repr(PyObject* obj);

    // Properties
    static PyObject* get_bounds(PyBSPObject* self, void* closure);
    static PyObject* get_pos(PyBSPObject* self, void* closure);
    static PyObject* get_size(PyBSPObject* self, void* closure);
    static PyObject* get_root(PyBSPObject* self, void* closure);

    // Splitting methods (#202)
    static PyObject* split_once(PyBSPObject* self, PyObject* args, PyObject* kwds);
    static PyObject* split_recursive(PyBSPObject* self, PyObject* args, PyObject* kwds);
    static PyObject* clear(PyBSPObject* self, PyObject* Py_UNUSED(args));

    // Iteration methods (#204)
    static PyObject* leaves(PyBSPObject* self, PyObject* Py_UNUSED(args));
    static PyObject* traverse(PyBSPObject* self, PyObject* args, PyObject* kwds);

    // Query methods (#205)
    static PyObject* find(PyBSPObject* self, PyObject* args, PyObject* kwds);

    // HeightMap conversion (#206)
    static PyObject* to_heightmap(PyBSPObject* self, PyObject* args, PyObject* kwds);

    // Sequence protocol
    static Py_ssize_t len(PyBSPObject* self);
    static PyObject* iter(PyBSPObject* self);

    // Method and property definitions
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PySequenceMethods sequence_methods;
};

class PyBSPNode
{
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyBSPNodeObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyBSPNodeObject* self);
    static PyObject* repr(PyObject* obj);

    // Comparison
    static PyObject* richcompare(PyObject* self, PyObject* other, int op);

    // Properties (#203)
    static PyObject* get_bounds(PyBSPNodeObject* self, void* closure);
    static PyObject* get_pos(PyBSPNodeObject* self, void* closure);
    static PyObject* get_size(PyBSPNodeObject* self, void* closure);
    static PyObject* get_level(PyBSPNodeObject* self, void* closure);
    static PyObject* get_is_leaf(PyBSPNodeObject* self, void* closure);
    static PyObject* get_split_horizontal(PyBSPNodeObject* self, void* closure);
    static PyObject* get_split_position(PyBSPNodeObject* self, void* closure);

    // Navigation properties (#203)
    static PyObject* get_left(PyBSPNodeObject* self, void* closure);
    static PyObject* get_right(PyBSPNodeObject* self, void* closure);
    static PyObject* get_parent(PyBSPNodeObject* self, void* closure);
    static PyObject* get_sibling(PyBSPNodeObject* self, void* closure);

    // Methods (#203)
    static PyObject* contains(PyBSPNodeObject* self, PyObject* args, PyObject* kwds);
    static PyObject* center(PyBSPNodeObject* self, PyObject* Py_UNUSED(args));

    // Helper to create a BSPNode from a TCOD_bsp_t*
    static PyObject* create(TCOD_bsp_t* node, PyObject* bsp_owner);

    // Validity check - returns false and sets error if node is stale
    static bool checkValid(PyBSPNodeObject* self);

    // Method and property definitions
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// BSP Iterator class
class PyBSPIter
{
public:
    static void dealloc(PyBSPIterObject* self);
    static PyObject* iter(PyObject* self);
    static PyObject* next(PyBSPIterObject* self);
    static int init(PyBSPIterObject* self, PyObject* args, PyObject* kwds);
    static PyObject* repr(PyObject* obj);
};

// Traversal enum creation
class PyTraversal
{
public:
    static PyObject* traversal_enum_class;
    static PyObject* create_enum_class(PyObject* module);
    static int from_arg(PyObject* arg, int* out_order);
    // Cleanup for module finalization (optional)
    static void cleanup();
};

namespace mcrfpydef {
    // BSP - user-facing, exported
    inline PyTypeObject PyBSPType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.BSP",
        .tp_basicsize = sizeof(PyBSPObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyBSP::dealloc,
        .tp_repr = PyBSP::repr,
        .tp_as_sequence = &PyBSP::sequence_methods,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "BSP(pos: tuple[int, int], size: tuple[int, int])\n\n"
            "Binary Space Partitioning tree for procedural dungeon generation.\n\n"
            "BSP recursively divides a rectangular region into smaller sub-regions, "
            "creating a tree structure perfect for generating dungeon rooms and corridors.\n\n"
            "Args:\n"
            "    pos: (x, y) - Top-left position of the root region.\n"
            "    size: (w, h) - Width and height of the root region.\n\n"
            "Properties:\n"
            "    pos (tuple[int, int]): Read-only. Top-left position (x, y).\n"
            "    size (tuple[int, int]): Read-only. Dimensions (width, height).\n"
            "    bounds ((pos), (size)): Read-only. Combined position and size.\n"
            "    root (BSPNode): Read-only. Reference to the root node.\n\n"
            "Iteration:\n"
            "    for leaf in bsp:  # Iterates over leaf nodes (rooms)\n"
            "    len(bsp)          # Returns number of leaf nodes\n\n"
            "Example:\n"
            "    bsp = mcrfpy.BSP(pos=(0, 0), size=(80, 50))\n"
            "    bsp.split_recursive(depth=4, min_size=(8, 8))\n"
            "    for leaf in bsp:\n"
            "        print(f'Room at {leaf.pos}, size {leaf.size}')\n"
        ),
        .tp_iter = (getiterfunc)PyBSP::iter,
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp
        .tp_init = (initproc)PyBSP::init,
        .tp_new = PyBSP::pynew,
    };

    // BSPNode - internal type (returned by BSP methods)
    inline PyTypeObject PyBSPNodeType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.BSPNode",
        .tp_basicsize = sizeof(PyBSPNodeObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyBSPNode::dealloc,
        .tp_repr = PyBSPNode::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "BSPNode - Lightweight reference to a node in a BSP tree.\n\n"
            "BSPNode provides read-only access to node properties and navigation.\n"
            "Nodes are created by BSP methods, not directly instantiated.\n\n"
            "WARNING: BSPNode references become invalid after BSP.clear() or\n"
            "BSP.split_recursive(). Accessing properties of an invalid node\n"
            "raises RuntimeError.\n\n"
            "Properties:\n"
            "    pos (tuple[int, int]): Top-left position (x, y).\n"
            "    size (tuple[int, int]): Dimensions (width, height).\n"
            "    bounds ((pos), (size)): Combined position and size.\n"
            "    level (int): Depth in tree (0 for root).\n"
            "    is_leaf (bool): True if this node has no children.\n"
            "    split_horizontal (bool | None): Split orientation, None if leaf.\n"
            "    split_position (int | None): Split coordinate, None if leaf.\n"
            "    left (BSPNode | None): Left child, or None if leaf.\n"
            "    right (BSPNode | None): Right child, or None if leaf.\n"
            "    parent (BSPNode | None): Parent node, or None if root.\n"
            "    sibling (BSPNode | None): Other child of parent, or None.\n"
        ),
        .tp_richcompare = PyBSPNode::richcompare,
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp
        .tp_init = (initproc)PyBSPNode::init,
        .tp_new = PyBSPNode::pynew,
    };

    // BSP Iterator - internal type
    inline PyTypeObject PyBSPIterType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.BSPIter",
        .tp_basicsize = sizeof(PyBSPIterObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyBSPIter::dealloc,
        .tp_repr = PyBSPIter::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Iterator for BSP tree traversal."),
        .tp_iter = PyBSPIter::iter,
        .tp_iternext = (iternextfunc)PyBSPIter::next,
        .tp_init = (initproc)PyBSPIter::init,
        .tp_new = [](PyTypeObject* type, PyObject* args, PyObject* kwds) -> PyObject* {
            PyErr_SetString(PyExc_TypeError, "BSPIter cannot be instantiated directly");
            return NULL;
        },
    };
}
