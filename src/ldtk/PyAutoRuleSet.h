#pragma once
#include "Python.h"
#include "LdtkTypes.h"
#include <memory>

// Python object structure
// Holds shared_ptr to parent project (keeps it alive) + index into rulesets
typedef struct PyAutoRuleSetObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::ldtk::LdtkProjectData> parent;
    int ruleset_index;
} PyAutoRuleSetObject;

// Python binding class
class PyAutoRuleSet {
public:
    // Factory: create from parent project + index
    static PyObject* create(std::shared_ptr<mcrf::ldtk::LdtkProjectData> parent, int index);

    static void dealloc(PyAutoRuleSetObject* self);
    static PyObject* repr(PyObject* obj);

    // Read-only properties
    static PyObject* get_name(PyAutoRuleSetObject* self, void* closure);
    static PyObject* get_grid_size(PyAutoRuleSetObject* self, void* closure);
    static PyObject* get_value_count(PyAutoRuleSetObject* self, void* closure);
    static PyObject* get_values(PyAutoRuleSetObject* self, void* closure);
    static PyObject* get_rule_count(PyAutoRuleSetObject* self, void* closure);
    static PyObject* get_group_count(PyAutoRuleSetObject* self, void* closure);

    // Methods
    static PyObject* terrain_enum(PyAutoRuleSetObject* self, PyObject* args);
    static PyObject* resolve(PyAutoRuleSetObject* self, PyObject* args, PyObject* kwds);
    static PyObject* apply(PyAutoRuleSetObject* self, PyObject* args, PyObject* kwds);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];

private:
    static const mcrf::ldtk::AutoRuleSet& getRuleSet(PyAutoRuleSetObject* self);
};

// Type definition in mcrfpydef namespace
namespace mcrfpydef {

inline PyTypeObject PyAutoRuleSetType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.AutoRuleSet",
    .tp_basicsize = sizeof(PyAutoRuleSetObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyAutoRuleSet::dealloc,
    .tp_repr = PyAutoRuleSet::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "AutoRuleSet - LDtk auto-tile rule set for pattern-based terrain rendering.\n\n"
        "AutoRuleSets are obtained from LdtkProject.ruleset().\n"
        "They map IntGrid terrain values to sprite tiles using LDtk's\n"
        "pattern-matching auto-rule system.\n\n"
        "Properties:\n"
        "    name (str, read-only): Rule set name (layer identifier).\n"
        "    grid_size (int, read-only): Cell size in pixels.\n"
        "    value_count (int, read-only): Number of IntGrid values.\n"
        "    values (list, read-only): List of value dicts.\n"
        "    rule_count (int, read-only): Total rules across all groups.\n"
        "    group_count (int, read-only): Number of rule groups.\n\n"
        "Example:\n"
        "    rs = project.ruleset('Walls')\n"
        "    Terrain = rs.terrain_enum()\n"
        "    rs.apply(discrete_map, tile_layer, seed=42)\n"
    ),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
};

} // namespace mcrfpydef
