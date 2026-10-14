#include "PyEngineConfig.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "GameEngine.h"
#include "PyWrap.h"

static const McRogueFaceConfig* config_or_raise()
{
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return nullptr;
    }
    return &game->getConfig();
}

static PyObject* str_or_none(const std::string& s)
{
    if (s.empty()) Py_RETURN_NONE;
    return PyUnicode_DecodeFSDefault(s.c_str());
}

static PyObject* str_tuple(const std::vector<std::string>& v)
{
    mcrf::PyRef t(PyTuple_New((Py_ssize_t)v.size()));
    if (!t) return NULL;
    for (size_t i = 0; i < v.size(); i++) {
        PyObject* s = PyUnicode_DecodeFSDefault(v[i].c_str());
        if (!s) return NULL;
        PyTuple_SET_ITEM(t.get(), (Py_ssize_t)i, s);  // steals
    }
    return t.release();
}

#define CFG_BOOL_GETTER(getter_name, field) \
    static PyObject* getter_name(PyObject*, void*) { \
        const McRogueFaceConfig* c = config_or_raise(); \
        if (!c) return NULL; \
        return PyBool_FromLong(c->field); \
    }

CFG_BOOL_GETTER(get_headless, headless)
CFG_BOOL_GETTER(get_audio_enabled, audio_enabled)
CFG_BOOL_GETTER(get_run_forever, run_forever)
CFG_BOOL_GETTER(get_interactive, interactive_mode)
CFG_BOOL_GETTER(get_exit_on_exception, exit_on_exception)

static PyObject* get_exec_scripts(PyObject*, void*)
{
    const McRogueFaceConfig* c = config_or_raise();
    if (!c) return NULL;
    std::vector<std::string> v;
    for (const auto& p : c->exec_scripts) v.push_back(p.string());
    return str_tuple(v);
}

static PyObject* get_script_path(PyObject*, void*)
{
    const McRogueFaceConfig* c = config_or_raise();
    if (!c) return NULL;
    return str_or_none(c->script_path.string());
}

static PyObject* get_script_args(PyObject*, void*)
{
    const McRogueFaceConfig* c = config_or_raise();
    if (!c) return NULL;
    return str_tuple(c->script_args);
}

static PyObject* get_screenshot_path(PyObject*, void*)
{
    const McRogueFaceConfig* c = config_or_raise();
    if (!c) return NULL;
    if (!c->take_screenshot) Py_RETURN_NONE;
    return str_or_none(c->screenshot_path);
}

static int set_exit_on_exception(PyObject*, PyObject* value, void*)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "exit_on_exception cannot be deleted");
        return -1;
    }
    if (!PyBool_Check(value)) {
        PyErr_Format(PyExc_TypeError, "exit_on_exception must be a bool, not %.100s",
                     Py_TYPE(value)->tp_name);
        return -1;
    }
    GameEngine* game = McRFPy_API::game;
    if (!game) {
        PyErr_SetString(PyExc_RuntimeError, "No game engine initialized");
        return -1;
    }
    game->setExitOnException(value == Py_True);
    return 0;
}

PyObject* PyEngineConfig::repr(PyObject*)
{
    GameEngine* game = McRFPy_API::game;
    if (!game) return PyUnicode_FromString("<EngineConfig [no game engine]>");
    const auto& c = game->getConfig();
    return PyUnicode_FromFormat("<EngineConfig headless=%s exit_on_exception=%s run_forever=%s>",
        c.headless ? "True" : "False", c.exit_on_exception ? "True" : "False",
        c.run_forever ? "True" : "False");
}

PyGetSetDef PyEngineConfig::getsetters[] = {
    {"headless", (getter)get_headless, NULL,
     MCRF_PROPERTY(headless, "True when running without a window, --headless (bool, read-only)."), NULL},
    {"audio_enabled", (getter)get_audio_enabled, NULL,
     MCRF_PROPERTY(audio_enabled, "False after --audio-off, or --headless without --audio-on (bool, read-only)."), NULL},
    {"exec_scripts", (getter)get_exec_scripts, NULL,
     MCRF_PROPERTY(exec_scripts, "The --exec scripts in command-line order (tuple[str], read-only)."), NULL},
    {"script_path", (getter)get_script_path, NULL,
     MCRF_PROPERTY(script_path, "The script named on the command line, or None (str | None, read-only)."), NULL},
    {"script_args", (getter)get_script_args, NULL,
     MCRF_PROPERTY(script_args, "Arguments after the script, or after -- (tuple[str], read-only)."), NULL},
    {"run_forever", (getter)get_run_forever, NULL,
     MCRF_PROPERTY(run_forever, "True with --run-forever (bool, read-only)."), NULL},
    {"interactive", (getter)get_interactive, NULL,
     MCRF_PROPERTY(interactive, "True with -i (bool, read-only)."), NULL},
    {"screenshot_path", (getter)get_screenshot_path, NULL,
     MCRF_PROPERTY(screenshot_path, "The --screenshot path, or None (str | None, read-only)."), NULL},
    {"exit_on_exception", (getter)get_exit_on_exception, (setter)set_exit_on_exception,
     MCRF_PROPERTY(exit_on_exception,
         "Whether an uncaught exception in a Python callback ends the process (bool). "
         "False with --continue-after-exceptions. Assign a bool; anything else raises TypeError."), NULL},
    {NULL}
};
