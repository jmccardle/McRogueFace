#pragma once
#include "Common.h"
#include "Python.h"
#include "McRFPy_Doc.h"
#include <vector>
#include <memory>
#include <string>
#include <cstdint>

// Forward declarations
struct SfxrParams;

// Core audio data container - holds authoritative sample data
class SoundBufferData : public std::enable_shared_from_this<SoundBufferData>
{
public:
    std::vector<int16_t> samples;
    unsigned int sampleRate = 44100;
    unsigned int channels = 1;

    // Optional sfxr params (set when created via sfxr synthesis)
    std::shared_ptr<SfxrParams> sfxrParams;

    // Lazy sf::SoundBuffer rebuild
    sf::SoundBuffer sfBuffer;
    bool sfBufferDirty = true;

    // #430: PythonObjectCache key for this buffer's SoundBuffer wrapper (0 = none yet).
    uint64_t serial_number = 0;

    SoundBufferData() = default;
    SoundBufferData(std::vector<int16_t>&& s, unsigned int rate, unsigned int ch)
        : samples(std::move(s)), sampleRate(rate), channels(ch), sfBufferDirty(true) {}
    ~SoundBufferData();  // unregisters serial_number; defined in PySoundBuffer.cpp
    // A copy would share serial_number, and destroying either would evict the other's wrapper.
    SoundBufferData(const SoundBufferData&) = delete;
    SoundBufferData& operator=(const SoundBufferData&) = delete;

    // Rebuild sf::SoundBuffer from samples if dirty
    sf::SoundBuffer& getSfBuffer() {
        if (sfBufferDirty && !samples.empty()) {
            sfBuffer.loadFromSamples(samples.data(), samples.size(), channels, sampleRate);
            sfBufferDirty = false;
        }
        return sfBuffer;
    }

    float duration() const {
        if (sampleRate == 0 || channels == 0 || samples.empty()) return 0.0f;
        return static_cast<float>(samples.size()) / static_cast<float>(channels) / static_cast<float>(sampleRate);
    }
};

// Python object wrapper
typedef struct {
    PyObject_HEAD
    std::shared_ptr<SoundBufferData> data;
    PyObject* weakreflist;  // #430: required by the PythonObjectCache
} PySoundBufferObject;

// Python type methods/getset declarations
namespace PySoundBuffer {
    // tp_init, tp_new, tp_repr
    int init(PySoundBufferObject* self, PyObject* args, PyObject* kwds);
    PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    PyObject* repr(PyObject* obj);
    void dealloc(PySoundBufferObject* self);

    // #430: the SoundBuffer wrapper for `data` -- the live one if any (identity
    // preserved), else a newly registered one. A freshly made buffer (every factory
    // and effect) has serial 0, so it allocates. nullptr -> None.
    PyObject* pyobject_for(const std::shared_ptr<SoundBufferData>& data);

    // Class methods (factories)
    PyObject* from_samples(PyObject* cls, PyObject* args, PyObject* kwds);
    PyObject* tone(PyObject* cls, PyObject* args, PyObject* kwds);
    PyObject* sfxr(PyObject* cls, PyObject* args, PyObject* kwds);
    PyObject* concat(PyObject* cls, PyObject* args, PyObject* kwds);
    PyObject* mix(PyObject* cls, PyObject* args, PyObject* kwds);

    // Instance methods (DSP - each returns new SoundBuffer)
    PyObject* pitch_shift(PySoundBufferObject* self, PyObject* args);
    PyObject* low_pass(PySoundBufferObject* self, PyObject* args);
    PyObject* high_pass(PySoundBufferObject* self, PyObject* args);
    PyObject* echo(PySoundBufferObject* self, PyObject* args);
    PyObject* reverb(PySoundBufferObject* self, PyObject* args);
    PyObject* distortion(PySoundBufferObject* self, PyObject* args);
    PyObject* bit_crush(PySoundBufferObject* self, PyObject* args);
    PyObject* gain(PySoundBufferObject* self, PyObject* args);
    PyObject* normalize(PySoundBufferObject* self, PyObject* args);
    PyObject* reverse(PySoundBufferObject* self, PyObject* args);
    PyObject* slice(PySoundBufferObject* self, PyObject* args);
    PyObject* sfxr_mutate(PySoundBufferObject* self, PyObject* args);

    // Properties
    PyObject* get_duration(PySoundBufferObject* self, void* closure);
    PyObject* get_sample_count(PySoundBufferObject* self, void* closure);
    PyObject* get_sample_rate(PySoundBufferObject* self, void* closure);
    PyObject* get_channels(PySoundBufferObject* self, void* closure);
    PyObject* get_sfxr_params(PySoundBufferObject* self, void* closure);

    extern PyMethodDef methods[];
    extern PyGetSetDef getsetters[];
}


namespace mcrfpydef {
    inline PyTypeObject PySoundBufferType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.SoundBuffer",
        .tp_basicsize = sizeof(PySoundBufferObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PySoundBuffer::dealloc,
        .tp_repr = PySoundBuffer::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "SoundBuffer(filename: str)\n"
            "SoundBuffer.from_samples(data: bytes, channels: int, sample_rate: int)\n"
            "SoundBuffer.tone(frequency: float, duration: float, waveform: str = 'sine', ...)\n"
            "SoundBuffer.sfxr(preset: str, seed: int = None)\n\n"
            "Audio sample buffer for procedural audio generation and effects.\n\n"
            "Holds PCM sample data that can be created from files, raw samples,\n"
            "tone synthesis, or sfxr presets. Effect methods return new SoundBuffer\n"
            "instances (copy-modify pattern).\n\n"
            "Properties:\n"
            "    duration (float, read-only): Duration in seconds.\n"
            "    sample_count (int, read-only): Total number of samples.\n"
            "    sample_rate (int, read-only): Samples per second (e.g. 44100).\n"
            "    channels (int, read-only): Number of audio channels.\n"
            "    sfxr_params (dict or None, read-only): sfxr parameters if sfxr-generated.\n"
        ),
        .tp_weaklistoffset = offsetof(PySoundBufferObject, weakreflist),
        .tp_methods = PySoundBuffer::methods,
        .tp_getset = PySoundBuffer::getsetters,
        .tp_init = (initproc)PySoundBuffer::init,
        .tp_new = PySoundBuffer::pynew,
    };
}
