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
CFG_BOOL_GETTER(get_use_virtual_env, use_virtual_env)

// #510: what became of VIRTUAL_ENV, decided before Python started (McRFPy_API statics)
static PyObject* get_virtual_env(PyObject*, void*)
{
    return str_or_none(McRFPy_API::virtual_env);
}

static PyObject* get_virtual_env_ignored(PyObject*, void*)
{
    if (McRFPy_API::virtual_env_ignored.empty()) Py_RETURN_NONE;
    mcrf::PyRef path(PyUnicode_DecodeFSDefault(McRFPy_API::virtual_env_ignored.c_str()));
    if (!path) return NULL;
    return Py_BuildValue("(Os)", path.get(), McRFPy_API::virtual_env_ignored_reason.c_str());
}

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
    {"use_virtual_env", (getter)get_use_virtual_env, NULL,
     MCRF_PROPERTY(use_virtual_env, "True with --use-virtual-env: a packaged game honours VIRTUAL_ENV (bool, read-only)."), NULL},
    {"virtual_env", (getter)get_virtual_env, NULL,
     MCRF_PROPERTY(virtual_env, "The VIRTUAL_ENV whose site-packages is on sys.path, or None (str | None, read-only). "
         "See docs/sys-path-order.md."), NULL},
    {"virtual_env_ignored", (getter)get_virtual_env_ignored, NULL,
     MCRF_PROPERTY(virtual_env_ignored, "When VIRTUAL_ENV was set but not used, a (path, reason) pair of str: it "
         "is for another Python, or this is a packaged game without --use-virtual-env. Otherwise None "
         "(tuple | None, read-only)."), NULL},
    {"exit_on_exception", (getter)get_exit_on_exception, (setter)set_exit_on_exception,
     MCRF_PROPERTY(exit_on_exception,
         "Whether an uncaught exception in a Python callback ends the process (bool). "
         "False with --continue-after-exceptions. Assign a bool; anything else raises TypeError."), NULL},
    {NULL}
};
