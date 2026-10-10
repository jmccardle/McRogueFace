#include "PyMusic.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>
#include <iomanip>

PyMusic::PyMusic(const std::string& filename)
    : source(filename)
{
    if (!mcrf::audio::enabled()) {
        loaded = mcrf::audio::probe_file(filename, duration);
        return;
    }
    music = std::make_unique<sf::Music>();
    if (music->openFromFile(filename)) {
        duration = music->getDuration().asSeconds();
        loaded = true;
    }
}

bool PyMusic::active() const
{
    return music && music->getStatus() == sf::Music::Playing;
}

void PyMusic::releaseDevice()
{
    music.reset();
}

void PyMusic::play()
{
    if (!loaded || !music) return;
    music->play();
    mcrf::audio::retain(shared_from_this());
}

void PyMusic::pause()
{
    if (music) music->pause();
}

void PyMusic::stop()
{
    if (music) music->stop();
    position = 0.0f;
}

float PyMusic::getVolume() const
{
    return volume;
}

void PyMusic::setVolume(float vol)
{
    volume = std::max(0.0f, std::min(100.0f, vol));
    if (music) music->setVolume(volume);
}

bool PyMusic::getLoop() const
{
    return loop;
}

void PyMusic::setLoop(bool l)
{
    loop = l;
    if (music) music->setLoop(loop);
}

bool PyMusic::isPlaying() const
{
    return active();
}

float PyMusic::getDuration() const
{
    return loaded ? duration : 0.0f;
}

float PyMusic::getPosition() const
{
    return music ? music->getPlayingOffset().asSeconds() : position;
}

void PyMusic::setPosition(float pos)
{
    if (music) music->setPlayingOffset(sf::seconds(pos));
    else position = pos;
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
    auto* self = (PyMusicObject*)type->tp_alloc(type, 0);
    if (self) new (&self->data) std::shared_ptr<PyMusic>();
    return (PyObject*)self;
}

void PyMusic::dealloc(PyMusicObject* self)
{
    // #440: playing music is still retained by mcrf::audio and keeps playing.
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
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
         MCRF_DESC("Start or resume playing the music."),
         MCRF_NOTE("The engine keeps playing music alive, so it plays on without a held "
                   "reference. Does nothing when audio is off (--audio-off, or --headless "
                   "without --audio-on).")
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
