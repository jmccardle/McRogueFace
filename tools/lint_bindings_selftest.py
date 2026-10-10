#!/usr/bin/env python3
"""Proves every lint_bindings.py rule still has teeth: each fixture below must
produce exactly the expected findings, and the corrected form must produce none.
Run with the .venv-audit interpreter; exits nonzero on any mismatch."""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_bindings as lb  # noqa: E402

CASES = [
    # (name, source, expected sorted list of (rule, detail-prefix))
    ("identity alloc outside converter", """
PyObject* Foo::find(PyObject* self) {
    PyTypeObject* entity_type = &mcrfpydef::PyUIEntityType;
    auto o = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
    return (PyObject*)o;
}""", [("identity-alloc", "tp_alloc PyUIEntityType")]),
    ("constructor allocates caller type: ok", """
PyObject* Foo::pynew(PyTypeObject* type, PyObject* a, PyObject* k) {
    return type->tp_alloc(type, 0);
}""", []),
    ("classmethod cast of cls: ok", """
PyObject* Foo::make(PyObject* cls, PyObject* a) {
    PyTypeObject* type = (PyTypeObject*)cls;
    return type->tp_alloc(type, 0);
}""", []),
    ("value type alloc: ok", """
PyObject* Foo::copy(PyObject* self) {
    auto type = &mcrfpydef::PyVectorType;
    return type->tp_alloc(type, 0);
}""", []),
    ("switch reassigns type: nearest assignment wins", """
static PyObject* conv(int k) {
    PyTypeObject* type = nullptr;
    switch (k) {
        case 0: { type = &mcrfpydef::PyVectorType; return type->tp_alloc(type, 0); }
        case 1: { type = &mcrfpydef::PyUIFrameType; return type->tp_alloc(type, 0); }
    }
    return nullptr;
}""", [("identity-alloc", "tp_alloc PyUIFrameType")]),
    ("identity wrapper built through pynew()", """
PyObject* PyFont::pyObject() {
    PyTypeObject* type = &mcrfpydef::PyFontType;
    PyObject* obj = PyFont::pynew(type, Py_None, Py_None);
    return obj;
}""", [("identity-alloc", "pynew PyFontType")]),
    ("C++ members without tp_dealloc", """
inline PyTypeObject PyFooType = {
    .tp_name = "mcrfpy.Foo",
    .tp_basicsize = sizeof(PyUIGridPointObject),
    .tp_itemsize = 0,
};""", [("missing-dealloc", "PyUIGridPointObject has C++ members")]),
    ("C++ members with tp_dealloc: ok", """
inline PyTypeObject PyFooType = {
    .tp_name = "mcrfpy.Foo",
    .tp_basicsize = sizeof(PyUIGridPointObject),
    .tp_itemsize = 0,
    .tp_dealloc = foo_dealloc,
};""", []),
    ("unclassified type", """
PyObject* f() { auto t = &mcrfpydef::PyBrandNewType; return t->tp_alloc(t, 0); }
""", [("unclassified", "tp_alloc PyBrandNewType")]),
    ("cached_wrapper converter: ok", """
PyObject* PyFoo::pyobject_for(const std::shared_ptr<Foo>& f) {
    return mcrf::cached_wrapper<PyUIFrameObject>(f->serial_number, &mcrfpydef::PyUIFrameType,
        [&](PyUIFrameObject* o) { o->data = f; });
}""", []),
    ("hand-rolled converter, even a pyobject_for", """
PyObject* UIDrawable::pyobject_for(std::shared_ptr<UIDrawable> d) {
    PyObject* c = PythonObjectCache::getInstance().lookup(d->serial_number);
    auto t = &mcrfpydef::PyUIFrameType; return t->tp_alloc(t, 0);
}""", [("cache-direct", "PythonObjectCache.lookup"), ("identity-alloc", "tp_alloc PyUIFrameType")]),
    ("direct cache use", """
int Foo::init(PyObject* self) {
    self->serial = PythonObjectCache::getInstance().assignSerial();
    return 0;
}""", [("cache-direct", "PythonObjectCache.assignSerial")]),
    ("borrowed sink with inline new ref", """
PyObject* m() { PyObject* d = PyDict_New();
    PyDict_SetItemString(d, "fps", PyLong_FromLong(60)); return d; }
""", [("borrowed-leak", "PyDict_SetItemString(..., PyLong_FromLong")]),
    ("borrowed sink with owned temp: ok", """
PyObject* m() { PyObject* d = PyDict_New(); PyObject* v = PyLong_FromLong(60);
    PyDict_SetItemString(d, "fps", v); Py_DECREF(v); return d; }
""", []),
    ("new ref inline to an arbitrary call", """
PyObject* f(PyObject* self, PyObject* kw) { return _click(self, PyTuple_New(0), kw); }
""", [("borrowed-leak", "_click(..., PyTuple_New")]),
    ("stealing sinks and N format: ok", """
void f(PyObject* t, double x) {
    PyTuple_SetItem(t, 0, PyFloat_FromDouble(x));
    Py_DECREF(PyObject_CallObject(t, NULL));
    PyObject* r = Py_BuildValue("(N)", PyLong_FromLong(1));
}""", []),
    ("from_arg never released", """
int Foo::set_pos(PyObject* self, PyObject* value, void*) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) return -1;
    use(vec->data); return 0;
}""", [("from-arg-owner", "vec = PyVector::from_arg")]),
    ("from_arg field returned is not ownership transfer", """
sf::Vector2f conv(PyObject* obj) {
    PyVectorObject* vec = PyVector::from_arg(obj);
    if (!vec) return sf::Vector2f(0, 0);
    return vec->data;
}""", [("from-arg-owner", "vec = PyVector::from_arg")]),
    ("from_arg returned to caller: ok", """
PyVectorObject* conv(PyObject* obj) {
    PyVectorObject* vec = PyVector::from_arg(obj);
    return vec;
}""", []),
    ("from_arg released: ok", """
int Foo::set_pos(PyObject* self, PyObject* value, void*) {
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) return -1;
    use(vec->data); Py_DECREF(vec); return 0;
}""", []),
    ("pin read as wrapper / release outside owner", """
void fire(std::shared_ptr<UIEntity>& e) {
    if (e->pyobject) call(e->pyobject);
    e->releasePyIdentity();
}""", [("pin-direct", "read pyobject"), ("pin-direct", "read pyobject"),
       ("pin-direct", "releasePyIdentity() call")]),
]


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory(dir=lb.ROOT / "tools") as d:
        for i, (name, src, expected) in enumerate(CASES):
            p = Path(d) / f"case{i}.cpp"
            p.write_text(src)
            got = sorted((f.rule, f.detail) for f in lb.lint_file(p))
            exp = sorted(expected)
            ok = len(got) == len(exp) and all(
                g[0] == e[0] and g[1].startswith(e[1]) for g, e in zip(got, exp))
            print(f"{'ok  ' if ok else 'FAIL'} {name}")
            if not ok:
                failures += 1
                print(f"     expected {exp}\n     got      {got}")
    print(f"lint_bindings self-test: {len(CASES) - failures}/{len(CASES)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
