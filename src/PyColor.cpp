#include "PyColor.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "ColorNames.h"
#include <climits>
#include <cstdint>
#include <string>
#include <string_view>
#include <cstdio>

PyGetSetDef PyColor::getsetters[] = {
    {"r", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(r, "Red component, an int in 0-255; out of range raises ValueError."), (void*)0},
    {"g", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(g, "Green component, an int in 0-255; out of range raises ValueError."), (void*)1},
    {"b", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(b, "Blue component, an int in 0-255; out of range raises ValueError."), (void*)2},
    {"a", (getter)PyColor::get_member, (setter)PyColor::set_member,
     MCRF_PROPERTY(a, "Alpha component, an int in 0-255 (0=transparent, 255=opaque); out of range raises ValueError."), (void*)3},
    {NULL}
};

PyMethodDef PyColor::methods[] = {
    {"from_hex", (PyCFunction)PyColor::from_hex, METH_VARARGS | METH_CLASS,
     MCRF_METHOD(Color, from_hex,
         MCRF_SIG("(hex_string: str)", "Color"),
         MCRF_DESC("Create a Color from a hexadecimal string, '#' optional. Color('#FF0000') also works, and takes the short forms '#F00' / '#F008' too."),
         MCRF_ARGS_START
         MCRF_ARG("hex_string", "Hex color string (e.g., '#FF0000', 'FF0000', '#AABBCCDD' for RGBA)")
         MCRF_RETURNS("Color: New Color object with values from hex string")
         MCRF_RAISES("ValueError", "If the string is not 6 or 8 hex digits (RGB or RGBA)")
         MCRF_NOTE("This is a class method. Call as Color.from_hex('#FF0000')")
     )},
    {"names", (PyCFunction)(void(*)(void))PyColor::names, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(Color, names,
         MCRF_SIG("(source: str | None = None)", "list[str]"),
         MCRF_DESC("List the color names Color(name) accepts, one per lookup key, in each source's own spelling."),
         MCRF_ARGS_START
         MCRF_ARG("source", "None for the unprefixed names (each resolved by precedence css, xkcd, crayola, jenny), or one source: 'css', 'xkcd', 'crayola' or 'jenny', whose names work as Color('source:name')")
         MCRF_RETURNS("list[str]: names, ordered by lookup key")
         MCRF_RAISES("ValueError", "If source is not a known source")
         MCRF_NOTE("Lookup ignores case and every character but letters and digits: 'Dark Green', 'dark_green' and 'darkgreen' are one name.")
     )},
    {"to_hex", (PyCFunction)PyColor::to_hex, METH_NOARGS,
     MCRF_METHOD(Color, to_hex,
         MCRF_SIG("()", "str"),
         MCRF_DESC("Convert this Color to a hexadecimal string."),
         MCRF_RETURNS("str: Hex string in format '#RRGGBB' or '#RRGGBBAA' (if alpha < 255)")
         MCRF_NOTE("Alpha component is only included if not fully opaque (< 255)")
     )},
    {"lerp", (PyCFunction)PyColor::lerp, METH_VARARGS,
     MCRF_METHOD(Color, lerp,
         MCRF_SIG("(other: Color, t: float)", "Color"),
         MCRF_DESC("Linearly interpolate between this color and another."),
         MCRF_ARGS_START
         MCRF_ARG("other", "The target Color to interpolate towards")
         MCRF_ARG("t", "Interpolation factor (0.0 = this color, 1.0 = other color). Automatically clamped to [0.0, 1.0]")
         MCRF_RETURNS("Color: New Color representing the interpolated value")
         MCRF_NOTE("All components (r, g, b, a) are interpolated independently")
     )},
    {NULL}
};

PyColor::PyColor(sf::Color target)
:data(target) {}

PyObject* PyColor::pyObject()
{
    PyColorObject* obj = (PyColorObject*)mcrfpydef::PyColorType.tp_alloc(&mcrfpydef::PyColorType, 0);

    if (obj) {
        obj->data = data;
    }
    return (PyObject*)obj;
}

bool PyColor::to_color(PyObject* value, sf::Color& out)
{
    if (!value) {
        PyErr_SetString(PyExc_TypeError, "cannot delete a Color attribute");
        return false;
    }
    if (PyObject_TypeCheck(value, &mcrfpydef::PyColorType)) {
        out = ((PyColorObject*)value)->data;
        return true;
    }
    // Everything else is exactly Color(value): same accepted values, same exceptions.
    PyObject* color = PyObject_CallOneArg((PyObject*)&mcrfpydef::PyColorType, value);
    if (!color) return false;
    out = ((PyColorObject*)color)->data;
    Py_DECREF(color);
    return true;
}

void PyColor::set(sf::Color color)
{
    data = color;
}

sf::Color PyColor::get()
{
    return data;
}

Py_hash_t PyColor::hash(PyObject* obj)
{
    auto self = (PyColorObject*)obj;
    Py_hash_t value = 0;
    value += self->data.r;
    value <<= 8; value += self->data.g; 
    value <<= 8; value += self->data.b; 
    value <<= 8; value += self->data.a;

    return value;
}

PyObject* PyColor::repr(PyObject* obj)
{
    PyColorObject* self = (PyColorObject*)obj;
    std::ostringstream ss;
    sf::Color c = self->data;
    ss << "<Color (" << int(c.r) << ", " << int(c.g) << ", " << int(c.b) << ", " << int(c.a) << ")>";

    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}


namespace {

int hex_digit(char c)
{
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

// #458: strict hex digits (no '#'): 3 (rgb), 4 (rgba), 6 (rrggbb) or 8 (rrggbbaa).
// Every character must be a hex digit. has_alpha reports whether the string set alpha.
bool parse_hex_digits(std::string_view h, sf::Color& out, bool& has_alpha)
{
    std::size_t n = h.size();
    if (n != 3 && n != 4 && n != 6 && n != 8) return false;
    int v[8];
    for (std::size_t i = 0; i < n; ++i)
        if ((v[i] = hex_digit(h[i])) < 0) return false;
    std::uint8_t c[4] = {0, 0, 0, 255};
    std::size_t comps = (n == 3 || n == 6) ? 3 : 4;
    for (std::size_t i = 0; i < comps; ++i)
        c[i] = (n <= 4) ? (std::uint8_t)(v[i] * 17) : (std::uint8_t)(v[2 * i] * 16 + v[2 * i + 1]);
    out = sf::Color(c[0], c[1], c[2], c[3]);
    has_alpha = comps == 4;
    return true;
}

std::string_view trim_spaces(std::string_view s)
{
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t')) s.remove_prefix(1);
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t')) s.remove_suffix(1);
    return s;
}

std::string join(const std::vector<std::string>& items, const char* sep, const char* quote)
{
    std::string out;
    for (std::size_t i = 0; i < items.size(); ++i) {
        if (i) out += sep;
        out += quote; out += items[i]; out += quote;
    }
    return out;
}

// #458: a colour string -- "#rgb", "#rgba", "#rrggbb", "#rrggbbaa", a name ("red",
// "Dark Green"), or "source:name" ("xkcd:dust"). Sets ValueError and returns false
// otherwise. has_alpha is true only for 4/8-digit hex.
bool color_from_string(PyObject* str, sf::Color& out, bool& has_alpha)
{
    Py_ssize_t len = 0;
    const char* utf8 = PyUnicode_AsUTF8AndSize(str, &len);
    if (!utf8) return false;
    std::string_view text = trim_spaces(std::string_view(utf8, (std::size_t)len));
    has_alpha = false;

    if (!text.empty() && text.front() == '#') {
        if (parse_hex_digits(text.substr(1), out, has_alpha)) return true;
        PyErr_Format(PyExc_ValueError,
            "invalid hex color %R: expected '#rgb', '#rgba', '#rrggbb' or '#rrggbbaa'", str);
        return false;
    }

    namespace cn = mcrf::color_names;
    int source = -1;
    std::string_view name = text;
    if (auto colon = text.find(':'); colon != std::string_view::npos) {
        source = cn::source_index(text.substr(0, colon));
        if (source < 0) {
            std::vector<std::string> prefixes(cn::source_prefixes, cn::source_prefixes + cn::source_count);
            std::string known = join(prefixes, ", ", "");
            PyErr_Format(PyExc_ValueError, "unknown color source in %R: sources are %s",
                         str, known.c_str());
            return false;
        }
        name = text.substr(colon + 1);
    }
    std::string key = cn::normalize(name);
    if (key.empty()) {
        PyErr_Format(PyExc_ValueError,
            "%R is not a color: a color string is a name ('red'), 'source:name' "
            "('xkcd:dust') or hex ('#ff0000')", str);
        return false;
    }
    if (const cn::Entry* e = cn::find(key, source)) {
        out = sf::Color(e->r, e->g, e->b, 255);
        return true;
    }
    std::vector<std::string> close = cn::suggestions(key, source);
    std::string hint = close.empty() ? std::string()
                                     : " (did you mean " + join(close, ", ", "'") + "?)";
    PyErr_Format(PyExc_ValueError, "unknown color name %R%s; Color.names(%s) lists them",
                 str, hint.c_str(),
                 source < 0 ? "" : ("'" + std::string(cn::source_prefixes[source]) + "'").c_str());
    return false;
}

constexpr int UNSET = INT_MIN;

} // namespace

int PyColor::init(PyColorObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = { "r", "g", "b", "a", nullptr };
    static const char* usage = "mcrfpy.Color requires (r, g, b[, a]) ints in 0-255, a 3- or "
        "4-tuple of them, or a color string: a name ('red'), 'source:name' ('xkcd:dust') "
        "or hex ('#ff0000')";
    PyObject* leader;
    int r = -1, g = UNSET, b = UNSET, a = UNSET;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|iii", const_cast<char**>(keywords), &leader, &g, &b, &a)) {
        PyErr_SetString(PyExc_TypeError, usage);
        return -1;
    }

    // Tuple cases
    if (PyTuple_Check(leader)) {
        Py_ssize_t tupleSize = PyTuple_Size(leader);
        if (tupleSize < 3 || tupleSize > 4) {
            PyErr_Format(PyExc_TypeError, "Invalid tuple length: %s", usage);
            return -1;
        }
        // #450: read into long and range-check before narrowing (an int cast wrapped
        // 2**32 + 5 to 5); a non-int or overflowing component reports the whole tuple.
        long c[4] = {0, 0, 0, 255};
        bool ok = true;
        for (Py_ssize_t i = 0; i < tupleSize; i++) {
            c[i] = PyLong_AsLong(PyTuple_GetItem(leader, i));
            if ((c[i] == -1 && PyErr_Occurred()) || c[i] < 0 || c[i] > 255) ok = false;
        }
        if (!ok) {
            PyErr_Clear();
            PyErr_Format(PyExc_ValueError, "Color components must be ints in 0-255, got %R", leader);
            return -1;
        }
        r = (int)c[0]; g = (int)c[1]; b = (int)c[2]; a = (int)c[3];
    }
    // #458: a colour name, "source:name", or "#hex"; alpha only by keyword (a=).
    else if (PyUnicode_Check(leader)) {
        if (g != UNSET || b != UNSET) {
            PyErr_Format(PyExc_TypeError,
                "Color(%R) takes no g or b; pass alpha as a=, e.g. Color('red', a=128)", leader);
            return -1;
        }
        sf::Color c;
        bool has_alpha = false;
        if (!color_from_string(leader, c, has_alpha)) return -1;
        if (a != UNSET) {
            if (has_alpha) {
                PyErr_Format(PyExc_TypeError, "Color(%R, a=%d): alpha given twice", leader, a);
                return -1;
            }
            if (a < 0 || a > 255) {
                PyErr_Format(PyExc_ValueError, "Color components must be ints in 0-255, got a=%d", a);
                return -1;
            }
            c.a = (sf::Uint8)a;
        }
        self->data = c;
        return 0;
    }
    // Check if the leader is actually an integer for the r value
    else if (PyLong_Check(leader)) {
        long lr = PyLong_AsLong(leader);
        if (lr == -1 && PyErr_Occurred()) PyErr_Clear();
        r = (lr < 0 || lr > 255) ? -1 : (int)lr;  // #450: no narrowing wrap; -1 fails below
        if (a == UNSET) a = 255;
    } else {
        PyErr_SetString(PyExc_TypeError, usage);
        return -1;
    }

    // Validate color values
    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255) {
        PyErr_Format(PyExc_ValueError, "Color components must be ints in 0-255, got %R", args);
        return -1;
    }

    self->data = sf::Color(r, g, b, a);
    return 0;
}

PyObject* PyColor::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    auto obj = (PyObject*)type->tp_alloc(type, 0);
    //Py_INCREF(obj);
    return obj;
}

PyObject* PyColor::get_member(PyObject* obj, void* closure)
{
    PyColorObject* self = (PyColorObject*)obj;
    intptr_t member = (intptr_t)closure;
    
    switch (member) {
        case 0: // r
            return PyLong_FromLong(self->data.r);
        case 1: // g
            return PyLong_FromLong(self->data.g);
        case 2: // b
            return PyLong_FromLong(self->data.b);
        case 3: // a
            return PyLong_FromLong(self->data.a);
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid color member");
            return NULL;
    }
}

int PyColor::set_member(PyObject* obj, PyObject* value, void* closure)
{
    PyColorObject* self = (PyColorObject*)obj;
    intptr_t member = (intptr_t)closure;
    
    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "Color values must be integers");
        return -1;
    }
    
    long val = PyLong_AsLong(value);
    if (val < 0 || val > 255) {
        PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255");
        return -1;
    }
    
    switch (member) {
        case 0: // r
            self->data.r = static_cast<sf::Uint8>(val);
            break;
        case 1: // g
            self->data.g = static_cast<sf::Uint8>(val);
            break;
        case 2: // b
            self->data.b = static_cast<sf::Uint8>(val);
            break;
        case 3: // a
            self->data.a = static_cast<sf::Uint8>(val);
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid color member");
            return -1;
    }
    
    return 0;
}

// Color helper method implementations
PyObject* PyColor::from_hex(PyObject* cls, PyObject* args)
{
    const char* hex_str;
    if (!PyArg_ParseTuple(args, "s", &hex_str)) {
        return NULL;
    }
    
    // #458: the same strict digit parser as Color("#..."), which also takes the short
    // forms; here the '#' is optional, so only 6 or 8 digits are unambiguous ("FF00").
    std::string_view hex = trim_spaces(hex_str);
    if (!hex.empty() && hex.front() == '#') hex.remove_prefix(1);
    sf::Color c;
    bool has_alpha = false;
    if ((hex.size() != 6 && hex.size() != 8) || !parse_hex_digits(hex, c, has_alpha)) {
        PyErr_Format(PyExc_ValueError,
            "invalid hex color '%s': expected 6 or 8 hex digits (RRGGBB or RRGGBBAA)", hex_str);
        return NULL;
    }
    PyTypeObject* type = (PyTypeObject*)cls;
    PyColorObject* color = (PyColorObject*)type->tp_alloc(type, 0);
    if (color) color->data = c;
    return (PyObject*)color;
}

PyObject* PyColor::names(PyObject* cls, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = { "source", nullptr };
    const char* source_str = nullptr;
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|z", const_cast<char**>(keywords), &source_str))
        return NULL;
    namespace cn = mcrf::color_names;
    int source = -1;
    if (source_str) {
        source = cn::source_index(source_str);
        if (source < 0) {
            std::vector<std::string> prefixes(cn::source_prefixes, cn::source_prefixes + cn::source_count);
            PyErr_Format(PyExc_ValueError, "unknown color source '%s': sources are %s",
                         source_str, join(prefixes, ", ", "").c_str());
            return NULL;
        }
    }
    auto found = cn::names(source);
    PyObject* list = PyList_New((Py_ssize_t)found.size());
    if (!list) return NULL;
    for (std::size_t i = 0; i < found.size(); ++i) {
        PyObject* s = PyUnicode_FromString(found[i]->name);
        if (!s) { Py_DECREF(list); return NULL; }
        PyList_SET_ITEM(list, (Py_ssize_t)i, s);
    }
    return list;
}

PyObject* PyColor::to_hex(PyColorObject* self, PyObject* Py_UNUSED(ignored))
{
    char hex[10];  // #RRGGBBAA + null terminator
    
    // Include alpha only if not fully opaque
    if (self->data.a < 255) {
        snprintf(hex, sizeof(hex), "#%02X%02X%02X%02X", 
                 self->data.r, self->data.g, self->data.b, self->data.a);
    } else {
        snprintf(hex, sizeof(hex), "#%02X%02X%02X", 
                 self->data.r, self->data.g, self->data.b);
    }
    
    return PyUnicode_FromString(hex);
}

PyObject* PyColor::lerp(PyColorObject* self, PyObject* args)
{
    PyObject* other_obj;
    float t;

    if (!PyArg_ParseTuple(args, "Of", &other_obj, &t)) {
        return NULL;
    }

    // Validate other color
    if (!PyObject_IsInstance(other_obj, (PyObject*)&mcrfpydef::PyColorType)) {
        PyErr_SetString(PyExc_TypeError, "First argument must be a Color");
        return NULL;
    }

    PyColorObject* other = (PyColorObject*)other_obj;

    // Clamp t to [0, 1]
    if (t < 0.0f) t = 0.0f;
    if (t > 1.0f) t = 1.0f;

    // Perform linear interpolation
    sf::Uint8 r = static_cast<sf::Uint8>(self->data.r + (other->data.r - self->data.r) * t);
    sf::Uint8 g = static_cast<sf::Uint8>(self->data.g + (other->data.g - self->data.g) * t);
    sf::Uint8 b = static_cast<sf::Uint8>(self->data.b + (other->data.b - self->data.b) * t);
    sf::Uint8 a = static_cast<sf::Uint8>(self->data.a + (other->data.a - self->data.a) * t);

    // Create new Color object
    auto type = &mcrfpydef::PyColorType;
    PyColorObject* result = (PyColorObject*)type->tp_alloc(type, 0);

    if (result) {
        result->data = sf::Color(r, g, b, a);
    }

    return (PyObject*)result;
}

PyObject* PyColor::richcompare(PyObject* left, PyObject* right, int op)
{
    // Only support == and !=
    if (op != Py_EQ && op != Py_NE) {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Extract RGBA from left operand
    sf::Color left_c, right_c;

    if (PyObject_IsInstance(left, (PyObject*)&mcrfpydef::PyColorType)) {
        left_c = ((PyColorObject*)left)->data;
    } else {
        Py_RETURN_NOTIMPLEMENTED;
    }

    // Extract RGBA from right operand - accept Color, tuple, or list
    if (PyObject_IsInstance(right, (PyObject*)&mcrfpydef::PyColorType)) {
        right_c = ((PyColorObject*)right)->data;
    } else if (PyTuple_Check(right) || PyList_Check(right)) {
        Py_ssize_t size = PySequence_Size(right);
        if (size < 3 || size > 4) {
            Py_RETURN_NOTIMPLEMENTED;
        }
        PyObject* r = PySequence_GetItem(right, 0);
        PyObject* g = PySequence_GetItem(right, 1);
        PyObject* b = PySequence_GetItem(right, 2);
        if (!PyLong_Check(r) || !PyLong_Check(g) || !PyLong_Check(b)) {
            Py_DECREF(r); Py_DECREF(g); Py_DECREF(b);
            Py_RETURN_NOTIMPLEMENTED;
        }
        right_c.r = (sf::Uint8)PyLong_AsLong(r);
        right_c.g = (sf::Uint8)PyLong_AsLong(g);
        right_c.b = (sf::Uint8)PyLong_AsLong(b);
        Py_DECREF(r); Py_DECREF(g); Py_DECREF(b);
        if (size == 4) {
            PyObject* a = PySequence_GetItem(right, 3);
            if (PyLong_Check(a)) right_c.a = (sf::Uint8)PyLong_AsLong(a);
            Py_DECREF(a);
        } else {
            right_c.a = 255;
        }
    } else {
        Py_RETURN_NOTIMPLEMENTED;
    }

    bool equal = (left_c.r == right_c.r && left_c.g == right_c.g &&
                  left_c.b == right_c.b && left_c.a == right_c.a);

    if (op == Py_EQ) {
        return PyBool_FromLong(equal);
    } else {
        return PyBool_FromLong(!equal);
    }
}
