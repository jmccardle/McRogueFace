#pragma once
#include "Python.h"
#include "LdtkTypes.h"
#include <memory>

// Python object structure
typedef struct PyLdtkProjectObject {
    PyObject_HEAD
    std::shared_ptr<mcrf::ldtk::LdtkProjectData> data;
} PyLdtkProjectObject;

// Python binding class
class PyLdtkProject {
public:
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyLdtkProjectObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyLdtkProjectObject* self);
    static PyObject* repr(PyObject* obj);

    // Read-only properties
    static PyObject* get_version(PyLdtkProjectObject* self, void* closure);
    static PyObject* get_tileset_names(PyLdtkProjectObject* self, void* closure);
    static PyObject* get_ruleset_names(PyLdtkProjectObject* self, void* closure);
    static PyObject* get_level_names(PyLdtkProjectObject* self, void* closure);
    static PyObject* get_enums(PyLdtkProjectObject* self, void* closure);

    // Methods
    static PyObject* tileset(PyLdtkProjectObject* self, PyObject* args);
    static PyObject* ruleset(PyLdtkProjectObject* self, PyObject* args);
    static PyObject* level(PyLdtkProjectObject* self, PyObject* args);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

// Type definition in mcrfpydef namespace
namespace mcrfpydef {

inline PyTypeObject PyLdtkProjectType = {
    .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
    .tp_name = "mcrfpy.LdtkProject",
    .tp_basicsize = sizeof(PyLdtkProjectObject),
    .tp_itemsize = 0,
    .tp_dealloc = (destructor)PyLdtkProject::dealloc,
    .tp_repr = PyLdtkProject::repr,
    .tp_flags = Py_TPFLAGS_DEFAULT,
    .tp_doc = PyDoc_STR(
        "LdtkProject(path: str)\n\n"
        "Load an LDtk project file (.ldtk).\n\n"
        "Parses the project and provides access to tilesets, auto-rule sets,\n"
        "levels, and enum definitions.\n\n"
        "Args:\n"
        "    path: Path to the .ldtk project file.\n\n"
        "Properties:\n"
        "    version (str, read-only): LDtk JSON format version.\n"
        "    tileset_names (list[str], read-only): Names of all tilesets.\n"
        "    ruleset_names (list[str], read-only): Names of all rule sets.\n"
        "    level_names (list[str], read-only): Names of all levels.\n"
        "    enums (dict, read-only): Enum definitions from the project.\n\n"
        "Example:\n"
        "    proj = mcrfpy.LdtkProject('dungeon.ldtk')\n"
        "    ts = proj.tileset('Dungeon_Tiles')\n"
        "    rs = proj.ruleset('Walls')\n"
        "    level = proj.level('Level_0')\n"
    ),
    .tp_methods = nullptr,  // Set before PyType_Ready
    .tp_getset = nullptr,   // Set before PyType_Ready
    .tp_init = (initproc)PyLdtkProject::init,
    .tp_new = PyLdtkProject::pynew,
};

} // namespace mcrfpydef
