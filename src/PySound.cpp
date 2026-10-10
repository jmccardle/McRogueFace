#include "PySound.h"
#include "PySoundBuffer.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include "EngineRandom.h"
#include <algorithm>
#include <sstream>
#include <random>

PySound::PySound(const std::string& filename)
    : source(filename)
{
    if (!mcrf::audio::enabled()) {
        loaded = mcrf::audio::probe_file(filename, duration);
        return;
    }
    device = std::make_unique<Device>();
    if (device->buffer.loadFromFile(filename)) {
        device->sound.setBuffer(device->buffer);
        duration = device->buffer.getDuration().asSeconds();
        loaded = true;
    }
}

PySound::PySound(std::shared_ptr<SoundBufferData> bufData)
    : source("<SoundBuffer>"), bufferData(bufData)
{
    if (!bufData || bufData->samples.empty()) return;
    loaded = true;
    duration = bufData->duration();
    if (!mcrf::audio::enabled()) return;
    device = std::make_unique<Device>();
    // Rebuild the sf::SoundBuffer from sample data directly
    // (avoids copy-assign which is deleted on SDL2 backend)
    device->buffer.loadFromSamples(bufData->samples.data(), bufData->samples.size(),
                                   bufData->channels, bufData->sampleRate);
    device->sound.setBuffer(device->buffer);
}

bool PySound::active() const
{
    if (!device) return false;
    if (device->sound.getStatus() == sf::Sound::Playing) return true;
    for (const auto& v : device->varied)
        if (v->getStatus() == sf::Sound::Playing) return true;
    return false;
}

void PySound::releaseDevice()
{
    device.reset();
}

void PySound::play()
{
    if (!loaded || !device) return;
    device->sound.play();
    mcrf::audio::retain(shared_from_this());
}

void PySound::pause()
{
    if (device) device->sound.pause();
}

void PySound::stop()
{
    if (!device) return;
    device->sound.stop();
    device->varied.clear();
}

bool PySound::playVoice(float voicePitch, float voiceVolume)
{
    if (!loaded || !device) return false;
    auto& voices = device->varied;
    voices.erase(std::remove_if(voices.begin(), voices.end(),
                                [](const std::unique_ptr<sf::Sound>& v) {
                                    return v->getStatus() == sf::Sound::Stopped;
                                }),
                 voices.end());
    auto voice = std::make_unique<sf::Sound>(device->buffer);
    voice->setPitch(voicePitch);
    voice->setVolume(voiceVolume);
    voice->setLoop(loop);
    voice->play();
    voices.push_back(std::move(voice));
    mcrf::audio::retain(shared_from_this());
    return true;
}

float PySound::getVolume() const
{
    return volume;
}

void PySound::setVolume(float vol)
{
    volume = std::max(0.0f, std::min(100.0f, vol));
    if (device) device->sound.setVolume(volume);
}

bool PySound::getLoop() const
{
    return loop;
}

void PySound::setLoop(bool l)
{
    loop = l;
    if (device) device->sound.setLoop(loop);
}

bool PySound::isPlaying() const
{
    return device && device->sound.getStatus() == sf::Sound::Playing;
}

float PySound::getDuration() const
{
    return loaded ? duration : 0.0f;
}

float PySound::getPitch() const
{
    return pitch;
}

void PySound::setPitch(float p)
{
    pitch = std::max(0.01f, p);
    if (device) device->sound.setPitch(pitch);
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
    auto* self = (PySoundObject*)type->tp_alloc(type, 0);
    if (self) new (&self->data) std::shared_ptr<PySound>();
    return (PyObject*)self;
}

void PySound::dealloc(PySoundObject* self)
{
    // #440: a playing sound is still retained by mcrf::audio and keeps playing.
    self->data.~shared_ptr();
    Py_TYPE(self)->tp_free((PyObject*)self);
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

    float origPitch = self->data->getPitch();
    float origVolume = self->data->getVolume();

    // Randomize. #394: draws from the engine's AUDIO stream rather than a private
    // std::random_device-seeded static, so the variation is reproducible at a fixed
    // mcrfpy.set_random_seed(). The AUDIO stream is INDEPENDENT of the BEHAVIOR
    // stream, so playing sounds does not shift entity behaviour -- an audio-on and
    // an audio-off run at the same seed produce the same world.
    std::mt19937& rng = mcrf::EngineRandom::stream(mcrf::RandomStream::AUDIO);
    std::uniform_real_distribution<double> pitchDist(-pitch_range, pitch_range);
    std::uniform_real_distribution<double> volDist(-volume_range, volume_range);

    float variedPitch = std::max(0.01f, origPitch + static_cast<float>(pitchDist(rng)));
    float variedVolume = std::max(0.0f, std::min(100.0f, origVolume + static_cast<float>(volDist(rng))));

    // #407: the variation plays on its own voice. It used to be applied to the
    // object's voice and restored right after play(), but OpenAL applies pitch and
    // gain live, so the restore cancelled it. The draw happens even with audio off,
    // so an audio-on and an audio-off run consume the AUDIO stream identically.
    self->data->playVoice(variedPitch, variedVolume);

    // The object's own pitch/volume never change, so this is the only record of
    // the draw -- and an unobservable random draw cannot be checked against the
    // seed that produced it.
    return Py_BuildValue("(dd)", static_cast<double>(variedPitch),
                                 static_cast<double>(variedVolume));
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
    return PySoundBuffer::pyobject_for(bufData);
}

PyMethodDef PySound::methods[] = {
    {"play", (PyCFunction)PySound::py_play, METH_NOARGS,
     MCRF_METHOD(Sound, play,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Start or resume playing the sound."),
         MCRF_NOTE("The engine keeps a playing sound alive, so Sound(...).play() plays to "
                   "the end without holding a reference. Does nothing when audio is off "
                   "(--audio-off, or --headless without --audio-on).")
     )},
    {"pause", (PyCFunction)PySound::py_pause, METH_NOARGS,
     MCRF_METHOD(Sound, pause,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Pause the sound. Use play() to resume from the paused position.")
     )},
    {"stop", (PyCFunction)PySound::py_stop, METH_NOARGS,
     MCRF_METHOD(Sound, stop,
         MCRF_SIG("()", "None"),
         MCRF_DESC("Stop playing and reset to the beginning. Also stops play_varied() voices.")
     )},
    {"play_varied", (PyCFunction)PySound::py_play_varied, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Sound, play_varied,
         MCRF_SIG("(pitch_range: float = 0.1, volume_range: float = 3.0)", "tuple[float, float]"),
         MCRF_DESC("Play an extra voice with randomized pitch and volume for natural variation. "
                   "Voices overlap, so rapid calls (footsteps, hits) layer instead of restarting."),
         MCRF_ARGS_START
         MCRF_ARG("pitch_range", "Random pitch offset range (default 0.1)")
         MCRF_ARG("volume_range", "Random volume offset range (default 3.0)")
         MCRF_RETURNS("tuple[float, float]: the (pitch, volume) drawn for this voice. The "
                      "sound's own pitch/volume properties are not changed, and .playing "
                      "reports only play(), so this return value is the only record of the draw.")
         MCRF_NOTE("The randomness comes from the engine's AUDIO random stream. Set "
                   "mcrfpy.set_random_seed() to make the variation reproducible; read "
                   "mcrfpy.get_random_seed() to learn the seed a run used. The AUDIO stream "
                   "is independent of the entity-behaviour stream, so playing sounds never "
                   "changes how entities move.")
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
