#include "PySound.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>

PySound::PySound(const std::string& filename)
    : source(filename), loaded(false)
{
    if (buffer.loadFromFile(filename)) {
        sound.setBuffer(buffer);
        loaded = true;
    }
}

void PySound::play()
{
    if (loaded) {
        sound.play();
    }
}

void PySound::pause()
{
    if (loaded) {
        sound.pause();
    }
}

void PySound::stop()
{
    if (loaded) {
        sound.stop();
    }
}

float PySound::getVolume() const
{
    return sound.getVolume();
}

void PySound::setVolume(float vol)
{
    sound.setVolume(std::max(0.0f, std::min(100.0f, vol)));
}

bool PySound::getLoop() const
{
    return sound.getLoop();
}

void PySound::setLoop(bool loop)
{
    sound.setLoop(loop);
}

bool PySound::isPlaying() const
{
    return sound.getStatus() == sf::Sound::Playing;
}

float PySound::getDuration() const
{
    if (!loaded) return 0.0f;
    return buffer.getDuration().asSeconds();
}

PyObject* PySound::pyObject()
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sound");
    PyObject* obj = PySound::pynew(type, Py_None, Py_None);
    Py_DECREF(type);
    try {
        ((PySoundObject*)obj)->data = shared_from_this();
    }
    catch (std::bad_weak_ptr& e) {
        std::cerr << "PySound::pyObject() - shared_from_this() failed" << std::endl;
    }
    return obj;
}

PyObject* PySound::repr(PyObject* obj)
{
    PySoundObject* self = (PySoundObject*)obj;
    std::ostringstream ss;
    if (!self->data) {
        ss << "<Sound [invalid]>";
    } else if (!self->data->loaded) {
        ss << "<Sound [failed to load: " << self->data->source << "]>";
    } else {
        ss << "<Sound source='" << self->data->source << "' duration="
           << std::fixed << std::setprecision(2) << self->data->getDuration() << "s>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_hash_t PySound::hash(PyObject* obj)
{
    auto self = (PySoundObject*)obj;
    return reinterpret_cast<Py_hash_t>(self->data.get());
}

int PySound::init(PySoundObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"filename", nullptr};
    const char* filename = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &filename)) {
        return -1;
    }

    self->data = std::make_shared<PySound>(filename);

    if (!self->data->loaded) {
        PyErr_Format(PyExc_RuntimeError, "Failed to load sound file: %s", filename);
        return -1;
    }

    return 0;
}

PyObject* PySound::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}

// Python methods
PyObject* PySound::py_play(PySoundObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    self->data->play();
    Py_RETURN_NONE;
}

PyObject* PySound::py_pause(PySoundObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    self->data->pause();
    Py_RETURN_NONE;
}

PyObject* PySound::py_stop(PySoundObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    self->data->stop();
    Py_RETURN_NONE;
}

// Property getters/setters
PyObject* PySound::get_volume(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getVolume());
}

int PySound::set_volume(PySoundObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return -1;
    }
    float vol = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setVolume(vol);
    return 0;
}

PyObject* PySound::get_loop(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyBool_FromLong(self->data->getLoop());
}

int PySound::set_loop(PySoundObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return -1;
    }
    self->data->setLoop(PyObject_IsTrue(value));
    return 0;
}

PyObject* PySound::get_playing(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyBool_FromLong(self->data->isPlaying());
}

PyObject* PySound::get_duration(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getDuration());
}

PyObject* PySound::get_source(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyUnicode_FromString(self->data->source.c_str());
}

PyMethodDef PySound::methods[] = {
    {"play", (PyCFunction)PySound::py_play, METH_NOARGS,
     MCRF_METHOD(Sound, play,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start or resume playing the sound.")
     )},
    {"pause", (PyCFunction)PySound::py_pause, METH_NOARGS,
     MCRF_METHOD(Sound, pause,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Pause the sound. Use play() to resume from the paused position.")
     )},
    {"stop", (PyCFunction)PySound::py_stop, METH_NOARGS,
     MCRF_METHOD(Sound, stop,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Stop playing and reset to the beginning.")
     )},
    {NULL}
};

PyGetSetDef PySound::getsetters[] = {
    {"volume", (getter)PySound::get_volume, (setter)PySound::set_volume,
     MCRF_PROPERTY(volume, "Volume level from 0 (silent) to 100 (full volume)."), NULL},
    {"loop", (getter)PySound::get_loop, (setter)PySound::set_loop,
     MCRF_PROPERTY(loop, "Whether the sound loops when it reaches the end."), NULL},
    {"playing", (getter)PySound::get_playing, NULL,
     MCRF_PROPERTY(playing, "True if the sound is currently playing (read-only)."), NULL},
    {"duration", (getter)PySound::get_duration, NULL,
     MCRF_PROPERTY(duration, "Total duration of the sound in seconds (read-only)."), NULL},
    {"source", (getter)PySound::get_source, NULL,
     MCRF_PROPERTY(source, "Filename path used to load this sound (read-only)."), NULL},
    {NULL}
};
