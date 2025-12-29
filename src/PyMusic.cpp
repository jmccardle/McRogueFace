#include "PyMusic.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>
#include <iomanip>

PyMusic::PyMusic(const std::string& filename)
    : source(filename), loaded(false)
{
    if (music.openFromFile(filename)) {
        loaded = true;
    }
}

void PyMusic::play()
{
    if (loaded) {
        music.play();
    }
}

void PyMusic::pause()
{
    if (loaded) {
        music.pause();
    }
}

void PyMusic::stop()
{
    if (loaded) {
        music.stop();
    }
}

float PyMusic::getVolume() const
{
    return music.getVolume();
}

void PyMusic::setVolume(float vol)
{
    music.setVolume(std::max(0.0f, std::min(100.0f, vol)));
}

bool PyMusic::getLoop() const
{
    return music.getLoop();
}

void PyMusic::setLoop(bool loop)
{
    music.setLoop(loop);
}

bool PyMusic::isPlaying() const
{
    return music.getStatus() == sf::Music::Playing;
}

float PyMusic::getDuration() const
{
    if (!loaded) return 0.0f;
    return music.getDuration().asSeconds();
}

float PyMusic::getPosition() const
{
    return music.getPlayingOffset().asSeconds();
}

void PyMusic::setPosition(float pos)
{
    music.setPlayingOffset(sf::seconds(pos));
}

PyObject* PyMusic::pyObject()
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Music");
    PyObject* obj = PyMusic::pynew(type, Py_None, Py_None);
    Py_DECREF(type);
    try {
        ((PyMusicObject*)obj)->data = shared_from_this();
    }
    catch (std::bad_weak_ptr& e) {
        std::cerr << "PyMusic::pyObject() - shared_from_this() failed" << std::endl;
    }
    return obj;
}

PyObject* PyMusic::repr(PyObject* obj)
{
    PyMusicObject* self = (PyMusicObject*)obj;
    std::ostringstream ss;
    if (!self->data) {
        ss << "<Music [invalid]>";
    } else if (!self->data->loaded) {
        ss << "<Music [failed to load: " << self->data->source << "]>";
    } else {
        ss << "<Music source='" << self->data->source << "' duration="
           << std::fixed << std::setprecision(2) << self->data->getDuration() << "s>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_hash_t PyMusic::hash(PyObject* obj)
{
    auto self = (PyMusicObject*)obj;
    return reinterpret_cast<Py_hash_t>(self->data.get());
}

int PyMusic::init(PyMusicObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"filename", nullptr};
    const char* filename = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &filename)) {
        return -1;
    }

    self->data = std::make_shared<PyMusic>(filename);

    if (!self->data->loaded) {
        PyErr_Format(PyExc_RuntimeError, "Failed to load music file: %s", filename);
        return -1;
    }

    return 0;
}

PyObject* PyMusic::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    return (PyObject*)type->tp_alloc(type, 0);
}

// Python methods
PyObject* PyMusic::py_play(PyMusicObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    self->data->play();
    Py_RETURN_NONE;
}

PyObject* PyMusic::py_pause(PyMusicObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    self->data->pause();
    Py_RETURN_NONE;
}

PyObject* PyMusic::py_stop(PyMusicObject* self, PyObject* args)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    self->data->stop();
    Py_RETURN_NONE;
}

// Property getters/setters
PyObject* PyMusic::get_volume(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getVolume());
}

int PyMusic::set_volume(PyMusicObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return -1;
    }
    float vol = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setVolume(vol);
    return 0;
}

PyObject* PyMusic::get_loop(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyBool_FromLong(self->data->getLoop());
}

int PyMusic::set_loop(PyMusicObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return -1;
    }
    self->data->setLoop(PyObject_IsTrue(value));
    return 0;
}

PyObject* PyMusic::get_playing(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyBool_FromLong(self->data->isPlaying());
}

PyObject* PyMusic::get_duration(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getDuration());
}

PyObject* PyMusic::get_position(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getPosition());
}

int PyMusic::set_position(PyMusicObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return -1;
    }
    float pos = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setPosition(pos);
    return 0;
}

PyObject* PyMusic::get_source(PyMusicObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Music object is invalid");
        return NULL;
    }
    return PyUnicode_FromString(self->data->source.c_str());
}

PyMethodDef PyMusic::methods[] = {
    {"play", (PyCFunction)PyMusic::py_play, METH_NOARGS,
     MCRF_METHOD(Music, play,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start or resume playing the music.")
     )},
    {"pause", (PyCFunction)PyMusic::py_pause, METH_NOARGS,
     MCRF_METHOD(Music, pause,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Pause the music. Use play() to resume from the paused position.")
     )},
    {"stop", (PyCFunction)PyMusic::py_stop, METH_NOARGS,
     MCRF_METHOD(Music, stop,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Stop playing and reset to the beginning.")
     )},
    {NULL}
};

PyGetSetDef PyMusic::getsetters[] = {
    {"volume", (getter)PyMusic::get_volume, (setter)PyMusic::set_volume,
     MCRF_PROPERTY(volume, "Volume level from 0 (silent) to 100 (full volume)."), NULL},
    {"loop", (getter)PyMusic::get_loop, (setter)PyMusic::set_loop,
     MCRF_PROPERTY(loop, "Whether the music loops when it reaches the end."), NULL},
    {"playing", (getter)PyMusic::get_playing, NULL,
     MCRF_PROPERTY(playing, "True if the music is currently playing (read-only)."), NULL},
    {"duration", (getter)PyMusic::get_duration, NULL,
     MCRF_PROPERTY(duration, "Total duration of the music in seconds (read-only)."), NULL},
    {"position", (getter)PyMusic::get_position, (setter)PyMusic::set_position,
     MCRF_PROPERTY(position, "Current playback position in seconds. Can be set to seek."), NULL},
    {"source", (getter)PyMusic::get_source, NULL,
     MCRF_PROPERTY(source, "Filename path used to load this music (read-only)."), NULL},
    {NULL}
};
