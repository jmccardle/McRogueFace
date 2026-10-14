#pragma once
#include "Common.h"
#include "Python.h"

// #501: mcrfpy.config, the engine's run configuration as parsed from the command line.
// A stateless singleton view of the engine's McRogueFaceConfig: read-only, except
// exit_on_exception, which a long-lived host sets for itself.
typedef struct {
    PyObject_HEAD
} PyEngineConfigObject;

class PyEngineConfig
{
public:
    static PyObject* repr(PyObject* self);
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyEngineConfigType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.EngineConfig",
        .tp_basicsize = sizeof(PyEngineConfigObject),
        .tp_itemsize = 0,
        .tp_repr = PyEngineConfig::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "EngineConfig()\n\n"
            "The engine's run configuration, available as mcrfpy.config.\n\n"
            "Under --exec, sys.argv is the script's, so engine flags are visible only here.\n"
            "Every property is read-only except exit_on_exception. Reading raises\n"
            "RuntimeError when no engine is running.\n\n"
            "Properties:\n"
            "    headless (bool, read-only): True when running without a window (--headless).\n"
            "    audio_enabled (bool, read-only): False after --audio-off (or --headless).\n"
            "    exec_scripts (tuple[str], read-only): The --exec scripts, in order.\n"
            "    script_path (str | None, read-only): The script named on the command line, or None.\n"
            "    script_args (tuple[str], read-only): Arguments after the script (or after --).\n"
            "    run_forever (bool, read-only): True with --run-forever.\n"
            "    interactive (bool, read-only): True with -i.\n"
            "    screenshot_path (str | None, read-only): The --screenshot path, or None.\n"
            "    exit_on_exception (bool): Whether the first uncaught exception in a Python callback\n"
            "        ends the process. False with --continue-after-exceptions. Assign a bool.\n\n"
            "Example:\n"
            "    if mcrfpy.config.exit_on_exception:\n"
            "        raise RuntimeError('run me with --continue-after-exceptions')\n"
        ),
        .tp_getset = PyEngineConfig::getsetters,
        .tp_new = PyType_GenericNew,
    };
}
