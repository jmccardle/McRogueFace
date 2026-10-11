#include "PyAnimate.h"
#include "PyAnimation.h"
#include "PyColor.h"
#include "PyEasing.h"
#include "PyWrap.h"
#include <cstring>

namespace mcrf {

bool parse_animate_args(PyObject* args, PyObject* kwds, AnimateArgs& out)
{
    static const char* keywords[] = {"property", "target", "duration", "easing", "delta", "loop",
                                     "callback", "conflict_mode", nullptr};
    PyObject* easing_arg = Py_None;
    int delta = 0;
    int loop = 0;
    PyObject* callback = nullptr;
    const char* conflict_mode = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOf|OppOs", const_cast<char**>(keywords),
                                     &out.property, &out.target, &out.duration,
                                     &easing_arg, &delta, &loop, &callback, &conflict_mode)) {
        return false;
    }
    if (callback && callback != Py_None && !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return false;
    }
    out.callback = (callback == Py_None) ? nullptr : callback;
    out.delta = delta != 0;
    out.loop = loop != 0;

    if (!PyEasing::from_arg(easing_arg, &out.easing, nullptr)) return false;

    out.conflict = AnimationConflictMode::REPLACE;
    if (conflict_mode) {
        if (strcmp(conflict_mode, "replace") == 0) {
            out.conflict = AnimationConflictMode::REPLACE;
        } else if (strcmp(conflict_mode, "queue") == 0) {
            out.conflict = AnimationConflictMode::QUEUE;
        } else if (strcmp(conflict_mode, "error") == 0) {
            out.conflict = AnimationConflictMode::RAISE_ERROR;
        } else {
            PyErr_Format(PyExc_ValueError,
                "Invalid conflict_mode '%s'. Must be 'replace', 'queue', or 'error'.", conflict_mode);
            return false;
        }
    }
    return true;
}

static bool is_number(PyObject* v) { return PyFloat_Check(v) || PyLong_Check(v); }

bool animation_target(PyObject* value, AnimKind kind, const char* property, AnimationValue& out)
{
    switch (kind) {
        case AnimKind::Float:
            if (!is_number(value)) break;
            out = static_cast<float>(PyFloat_AsDouble(value));
            return !PyErr_Occurred();

        case AnimKind::Int:
            if (PyLong_Check(value)) {
                const long v = PyLong_AsLong(value);
                if (v == -1 && PyErr_Occurred()) return false;
                out = static_cast<int>(v);
                return true;
            }
            if (PyList_Check(value)) {
                // A list of ints steps through those values over the duration (sprite frames).
                std::vector<int> frames;
                for (Py_ssize_t i = 0; i < PyList_Size(value); i++) {
                    PyObject* item = PyList_GetItem(value, i);
                    if (!PyLong_Check(item)) {
                        PyErr_Format(PyExc_TypeError,
                            "'%s' frame list must contain only integers", property);
                        return false;
                    }
                    frames.push_back(static_cast<int>(PyLong_AsLong(item)));
                }
                if (frames.empty()) {
                    PyErr_Format(PyExc_ValueError, "'%s' frame list must not be empty", property);
                    return false;
                }
                out = frames;
                return true;
            }
            break;

        case AnimKind::Vector: {
            sf::Vector2f v;
            if (!to_vector2f(value, v, property)) return false;
            out = v;
            return true;
        }

        case AnimKind::Color: {
            // Color(value): a Color or an (r, g, b[, a]) tuple of ints in 0-255, strictly.
            // (PyColor::fromPy() clamps and reads a non-int component as 255.)
            if (!PyObject_TypeCheck(value, &mcrfpydef::PyColorType) && !PyTuple_Check(value)) break;
            PyRef color((PyObject*)PyColor::from_arg(value));
            if (!color) return false;
            out = ((PyColorObject*)color.get())->data;
            return true;
        }

        case AnimKind::String:
            if (!PyUnicode_Check(value)) break;
            {
                const char* s = PyUnicode_AsUTF8(value);
                if (!s) return false;
                out = std::string(s);
            }
            return true;

        case AnimKind::None:
            break;
    }

    static const char* const takes[] = {
        "", "a number", "an int, or a list of ints", "a Vector or (x, y)",
        "a Color or an (r, g, b[, a]) tuple", "a str"};
    PyErr_Format(PyExc_TypeError, "animation target for '%s' must be %s, not %s",
                 property, takes[static_cast<int>(kind)], Py_TYPE(value)->tp_name);
    return false;
}

void raise_not_animatable(const char* type_name, const char* property)
{
    // Names animate() accepted before #423/#426 that are not attributes.
    struct Hint { const char* type; const char* name; const char* hint; };
    static const Hint hints[] = {
        {nullptr,   "position",        "use 'pos'"},
        {nullptr,   "origin_x",        "use 'origin'"},
        {nullptr,   "origin_y",        "use 'origin'"},
        {"Caption", "size",            "use 'font_size' (Caption.size is the read-only text size)"},
        {"Caption", "w",               "Caption.w is read-only"},
        {"Caption", "h",               "Caption.h is read-only"},
        {"Line",    "start_x",         "use 'start'"},
        {"Line",    "start_y",         "use 'start'"},
        {"Line",    "end_x",           "use 'end'"},
        {"Line",    "end_y",           "use 'end'"},
        {"Entity",  "draw_x",          "use 'draw_pos' for tile coordinates, or 'x' for pixels"},
        {"Entity",  "draw_y",          "use 'draw_pos' for tile coordinates, or 'y' for pixels"},
        {"Entity",  "sprite_scale",    "an entity's sprite is scaled by its grid's zoom"},
    };
    // tp_name is "mcrfpy.Frame"; report the name users write.
    const char* dot = std::strrchr(type_name, '.');
    const char* short_name = dot ? dot + 1 : type_name;
    for (const auto& h : hints) {
        if (std::strcmp(h.name, property) == 0 && (!h.type || std::strcmp(h.type, short_name) == 0)) {
            PyErr_Format(PyExc_ValueError, "'%s' is not an animatable property of %s; %s",
                         property, short_name, h.hint);
            return;
        }
    }
    PyErr_Format(PyExc_ValueError, "'%s' is not an animatable property of %s",
                 property, short_name);
}

PyObject* launch_animation(const std::shared_ptr<Animation>& animation, AnimationConflictMode conflict)
{
    AnimationManager::getInstance().addAnimation(animation, conflict);
    if (PyErr_Occurred()) return nullptr;  // conflict_mode='error' found a running animation

    PyTypeObject* type = &mcrfpydef::PyAnimationType;
    auto* wrapper = (PyAnimationObject*)type->tp_alloc(type, 0);
    if (!wrapper) return nullptr;
    wrapper->data = animation;
    return (PyObject*)wrapper;
}

} // namespace mcrf
