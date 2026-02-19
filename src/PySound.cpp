#include "PySound.h"
#include "PySoundBuffer.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>
#include <random>

PySound::PySound(const std::string& filename)
    : source(filename), loaded(false)
{
    if (buffer.loadFromFile(filename)) {
        sound.setBuffer(buffer);
        loaded = true;
    }
}

PySound::PySound(std::shared_ptr<SoundBufferData> bufData)
    : source("<SoundBuffer>"), loaded(false), bufferData(bufData)
{
    if (bufData && !bufData->samples.empty()) {
        buffer = bufData->getSfBuffer();
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

float PySound::getPitch() const
{
    return sound.getPitch();
}

void PySound::setPitch(float pitch)
{
    sound.setPitch(std::max(0.01f, pitch));
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
    // Accept either a string filename or a SoundBuffer object
    PyObject* source_obj = nullptr;

    if (!PyArg_ParseTuple(args, "O", &source_obj)) {
        return -1;
    }

    if (PyUnicode_Check(source_obj)) {
        // String filename path
        const char* filename = PyUnicode_AsUTF8(source_obj);
        if (!filename) return -1;

        self->data = std::make_shared<PySound>(filename);

        if (!self->data->loaded) {
            PyErr_Format(PyExc_RuntimeError, "Failed to load sound file: %s", filename);
            return -1;
        }
    } else if (PyObject_IsInstance(source_obj, (PyObject*)&mcrfpydef::PySoundBufferType)) {
        // SoundBuffer object
        auto* sbObj = (PySoundBufferObject*)source_obj;
        if (!sbObj->data || sbObj->data->samples.empty()) {
            PyErr_SetString(PyExc_RuntimeError, "SoundBuffer is empty or invalid");
            return -1;
        }

        self->data = std::make_shared<PySound>(sbObj->data);

        if (!self->data->loaded) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to create sound from SoundBuffer");
            return -1;
        }
    } else {
        PyErr_SetString(PyExc_TypeError, "Sound() argument must be a filename string or SoundBuffer");
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

PyObject* PySound::py_play_varied(PySoundObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"pitch_range", "volume_range", nullptr};
    double pitch_range = 0.1;
    double volume_range = 3.0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|dd", const_cast<char**>(keywords),
                                     &pitch_range, &volume_range)) {
        return NULL;
    }
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }

    // Save original values
    float origPitch = self->data->getPitch();
    float origVolume = self->data->getVolume();

    // Randomize
    static std::mt19937 rng(std::random_device{}());
    std::uniform_real_distribution<double> pitchDist(-pitch_range, pitch_range);
    std::uniform_real_distribution<double> volDist(-volume_range, volume_range);

    self->data->setPitch(std::max(0.01f, origPitch + static_cast<float>(pitchDist(rng))));
    self->data->setVolume(std::max(0.0f, std::min(100.0f, origVolume + static_cast<float>(volDist(rng)))));

    self->data->play();

    // Restore originals (SFML will use the values set at play time)
    // Note: we restore after play() so the variation applies only to this instance
    self->data->setPitch(origPitch);
    self->data->setVolume(origVolume);

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

PyObject* PySound::get_pitch(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    return PyFloat_FromDouble(self->data->getPitch());
}

int PySound::set_pitch(PySoundObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return -1;
    }
    float pitch = PyFloat_AsDouble(value);
    if (PyErr_Occurred()) {
        return -1;
    }
    self->data->setPitch(pitch);
    return 0;
}

PyObject* PySound::get_buffer(PySoundObject* self, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Sound object is invalid");
        return NULL;
    }
    auto bufData = self->data->getBufferData();
    if (!bufData) {
        Py_RETURN_NONE;
    }
    return PySoundBuffer_from_data(bufData);
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
    {"play_varied", (PyCFunction)PySound::py_play_varied, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Sound, play_varied,
         MCRF_SIG("(pitch_range: float = 0.1, volume_range: float = 3.0)", "None"),
         MCRF_DESC("Play with randomized pitch and volume for natural variation."),
         MCRF_ARGS_START
         MCRF_ARG("pitch_range", "Random pitch offset range (default 0.1)")
         MCRF_ARG("volume_range", "Random volume offset range (default 3.0)")
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
    {"pitch", (getter)PySound::get_pitch, (setter)PySound::set_pitch,
     MCRF_PROPERTY(pitch, "Playback pitch multiplier (1.0 = normal, >1 = higher, <1 = lower)."), NULL},
    {"buffer", (getter)PySound::get_buffer, NULL,
     MCRF_PROPERTY(buffer, "The SoundBuffer if created from one, else None (read-only)."), NULL},
    {NULL}
};
