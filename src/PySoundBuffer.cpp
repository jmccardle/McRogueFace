#include "PySoundBuffer.h"
#include "audio/SfxrSynth.h"
#include "audio/AudioEffects.h"
#include <sstream>
#include <cmath>
#include <random>
#include <algorithm>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// Helper: create a Python SoundBuffer wrapping given data
PyObject* PySoundBuffer_from_data(std::shared_ptr<SoundBufferData> data) {
    auto* obj = (PySoundBufferObject*)mcrfpydef::PySoundBufferType.tp_alloc(&mcrfpydef::PySoundBufferType, 0);
    if (obj) {
        new (&obj->data) std::shared_ptr<SoundBufferData>(std::move(data));
    }
    return (PyObject*)obj;
}

// ============================================================================
// Type infrastructure
// ============================================================================

PyObject* PySoundBuffer::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds) {
    auto* self = (PySoundBufferObject*)type->tp_alloc(type, 0);
    if (self) {
        new (&self->data) std::shared_ptr<SoundBufferData>();
    }
    return (PyObject*)self;
}

int PySoundBuffer::init(PySoundBufferObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"filename", nullptr};
    const char* filename = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "s", const_cast<char**>(keywords), &filename)) {
        return -1;
    }

    // Load from file via sf::SoundBuffer
    sf::SoundBuffer tmpBuf;
    if (!tmpBuf.loadFromFile(filename)) {
        PyErr_Format(PyExc_RuntimeError, "Failed to load sound file: %s", filename);
        return -1;
    }

    // Extract samples from the loaded buffer
    auto data = std::make_shared<SoundBufferData>();
    data->sampleRate = tmpBuf.getSampleRate();
    data->channels = tmpBuf.getChannelCount();

    // Copy sample data from sf::SoundBuffer
    auto count = tmpBuf.getSampleCount();
    if (count > 0) {
        // SFML provides getSamples() on desktop; for headless/SDL2 we have no samples to copy
        // On SFML desktop builds, sf::SoundBuffer has getSamples()
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
        const sf::Int16* src = tmpBuf.getSamples();
        data->samples.assign(src, src + count);
#else
        // Headless/SDL2: samples not directly accessible from sf::SoundBuffer
        // Create silence of the appropriate duration
        float dur = tmpBuf.getDuration().asSeconds();
        size_t numSamples = static_cast<size_t>(dur * data->sampleRate * data->channels);
        data->samples.resize(numSamples, 0);
#endif
    }

    data->sfBufferDirty = true;
    self->data = std::move(data);
    return 0;
}

PyObject* PySoundBuffer::repr(PyObject* obj) {
    auto* self = (PySoundBufferObject*)obj;
    std::ostringstream ss;
    if (!self->data) {
        ss << "<SoundBuffer [invalid]>";
    } else {
        ss << "<SoundBuffer duration=" << std::fixed << std::setprecision(3)
           << self->data->duration() << "s samples=" << self->data->samples.size()
           << " rate=" << self->data->sampleRate
           << " ch=" << self->data->channels << ">";
    }
    std::string s = ss.str();
    return PyUnicode_FromString(s.c_str());
}

// ============================================================================
// Properties
// ============================================================================

PyObject* PySoundBuffer::get_duration(PySoundBufferObject* self, void*) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    return PyFloat_FromDouble(self->data->duration());
}

PyObject* PySoundBuffer::get_sample_count(PySoundBufferObject* self, void*) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    return PyLong_FromSize_t(self->data->samples.size());
}

PyObject* PySoundBuffer::get_sample_rate(PySoundBufferObject* self, void*) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    return PyLong_FromUnsignedLong(self->data->sampleRate);
}

PyObject* PySoundBuffer::get_channels(PySoundBufferObject* self, void*) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    return PyLong_FromUnsignedLong(self->data->channels);
}

PyObject* PySoundBuffer::get_sfxr_params(PySoundBufferObject* self, void*) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    if (!self->data->sfxrParams) {
        Py_RETURN_NONE;
    }
    return sfxr_params_to_dict(*self->data->sfxrParams);
}

// ============================================================================
// Class method: from_samples
// ============================================================================

PyObject* PySoundBuffer::from_samples(PyObject* cls, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"data", "channels", "sample_rate", nullptr};
    Py_buffer buf;
    unsigned int ch = 1;
    unsigned int rate = 44100;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "y*II", const_cast<char**>(keywords),
                                     &buf, &ch, &rate)) {
        return NULL;
    }

    if (ch == 0 || rate == 0) {
        PyBuffer_Release(&buf);
        PyErr_SetString(PyExc_ValueError, "channels and sample_rate must be > 0");
        return NULL;
    }

    size_t numSamples = buf.len / sizeof(int16_t);
    auto data = std::make_shared<SoundBufferData>();
    data->samples.resize(numSamples);
    memcpy(data->samples.data(), buf.buf, numSamples * sizeof(int16_t));
    data->channels = ch;
    data->sampleRate = rate;
    data->sfBufferDirty = true;

    PyBuffer_Release(&buf);
    return PySoundBuffer_from_data(std::move(data));
}

// ============================================================================
// Class method: tone
// ============================================================================

PyObject* PySoundBuffer::tone(PyObject* cls, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {
        "frequency", "duration", "waveform",
        "attack", "decay", "sustain", "release",
        "sample_rate", nullptr
    };
    double freq = 440.0;
    double dur = 0.5;
    const char* waveform = "sine";
    double attack = 0.01, decay_time = 0.0, sustain = 1.0, release = 0.01;
    unsigned int rate = 44100;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "dd|sddddI", const_cast<char**>(keywords),
                                     &freq, &dur, &waveform, &attack, &decay_time,
                                     &sustain, &release, &rate)) {
        return NULL;
    }

    if (dur <= 0.0 || freq <= 0.0) {
        PyErr_SetString(PyExc_ValueError, "frequency and duration must be positive");
        return NULL;
    }

    size_t totalSamples = static_cast<size_t>(dur * rate);
    std::vector<int16_t> samples(totalSamples);

    std::string wf(waveform);
    std::mt19937 noiseRng(42); // Deterministic noise

    // Generate waveform
    for (size_t i = 0; i < totalSamples; i++) {
        double t = static_cast<double>(i) / rate;
        double phase = fmod(t * freq, 1.0);
        double sample = 0.0;

        if (wf == "sine") {
            sample = sin(2.0 * M_PI * phase);
        } else if (wf == "square") {
            // PolyBLEP square
            double naive = phase < 0.5 ? 1.0 : -1.0;
            double dt = freq / rate;
            // PolyBLEP correction at transitions
            auto polyblep = [](double t, double dt) -> double {
                if (t < dt) { t /= dt; return t + t - t * t - 1.0; }
                if (t > 1.0 - dt) { t = (t - 1.0) / dt; return t * t + t + t + 1.0; }
                return 0.0;
            };
            sample = naive + polyblep(phase, dt) - polyblep(fmod(phase + 0.5, 1.0), dt);
        } else if (wf == "saw") {
            // PolyBLEP saw
            double naive = 2.0 * phase - 1.0;
            double dt = freq / rate;
            auto polyblep = [](double t, double dt) -> double {
                if (t < dt) { t /= dt; return t + t - t * t - 1.0; }
                if (t > 1.0 - dt) { t = (t - 1.0) / dt; return t * t + t + t + 1.0; }
                return 0.0;
            };
            sample = naive - polyblep(phase, dt);
        } else if (wf == "triangle") {
            sample = 4.0 * fabs(phase - 0.5) - 1.0;
        } else if (wf == "noise") {
            std::uniform_real_distribution<double> dist(-1.0, 1.0);
            sample = dist(noiseRng);
        } else {
            PyErr_Format(PyExc_ValueError,
                "Unknown waveform '%s'. Use: sine, square, saw, triangle, noise", waveform);
            return NULL;
        }

        // ADSR envelope
        double env = 1.0;
        double noteEnd = dur - release;
        if (t < attack) {
            env = (attack > 0.0) ? t / attack : 1.0;
        } else if (t < attack + decay_time) {
            double decayProgress = (decay_time > 0.0) ? (t - attack) / decay_time : 1.0;
            env = 1.0 - (1.0 - sustain) * decayProgress;
        } else if (t < noteEnd) {
            env = sustain;
        } else {
            double releaseProgress = (release > 0.0) ? (t - noteEnd) / release : 1.0;
            env = sustain * (1.0 - std::min(releaseProgress, 1.0));
        }

        sample *= env;
        sample = std::max(-1.0, std::min(1.0, sample));
        samples[i] = static_cast<int16_t>(sample * 32000.0);
    }

    auto data = std::make_shared<SoundBufferData>(std::move(samples), rate, 1);
    return PySoundBuffer_from_data(std::move(data));
}

// ============================================================================
// Class method: sfxr
// ============================================================================

PyObject* PySoundBuffer::sfxr(PyObject* cls, PyObject* args, PyObject* kwds) {
    // Accept either: sfxr("preset") or sfxr(wave_type=0, base_freq=0.3, ...)
    static const char* keywords[] = {
        "preset", "seed",
        "wave_type", "base_freq", "freq_limit", "freq_ramp", "freq_dramp",
        "duty", "duty_ramp",
        "vib_strength", "vib_speed",
        "env_attack", "env_sustain", "env_decay", "env_punch",
        "lpf_freq", "lpf_ramp", "lpf_resonance",
        "hpf_freq", "hpf_ramp",
        "pha_offset", "pha_ramp",
        "repeat_speed",
        "arp_speed", "arp_mod",
        nullptr
    };

    const char* preset = nullptr;
    PyObject* seed_obj = Py_None;

    // sfxr params - initialized to -999 as sentinel (unset)
    int wave_type = -999;
    double base_freq = -999, freq_limit = -999, freq_ramp = -999, freq_dramp = -999;
    double duty = -999, duty_ramp = -999;
    double vib_strength = -999, vib_speed = -999;
    double env_attack = -999, env_sustain = -999, env_decay = -999, env_punch = -999;
    double lpf_freq = -999, lpf_ramp = -999, lpf_resonance = -999;
    double hpf_freq = -999, hpf_ramp = -999;
    double pha_offset = -999, pha_ramp = -999;
    double repeat_speed = -999;
    double arp_speed = -999, arp_mod = -999;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|zOidddddddddddddddddddddd",
                                     const_cast<char**>(keywords),
                                     &preset, &seed_obj,
                                     &wave_type, &base_freq, &freq_limit, &freq_ramp, &freq_dramp,
                                     &duty, &duty_ramp,
                                     &vib_strength, &vib_speed,
                                     &env_attack, &env_sustain, &env_decay, &env_punch,
                                     &lpf_freq, &lpf_ramp, &lpf_resonance,
                                     &hpf_freq, &hpf_ramp,
                                     &pha_offset, &pha_ramp,
                                     &repeat_speed,
                                     &arp_speed, &arp_mod)) {
        return NULL;
    }

    // Get seed
    uint32_t seed = 0;
    bool hasSeed = false;
    if (seed_obj != Py_None) {
        if (PyLong_Check(seed_obj)) {
            seed = static_cast<uint32_t>(PyLong_AsUnsignedLong(seed_obj));
            if (PyErr_Occurred()) return NULL;
            hasSeed = true;
        } else {
            PyErr_SetString(PyExc_TypeError, "seed must be an integer");
            return NULL;
        }
    }

    SfxrParams params;

    if (preset) {
        // Generate from preset
        std::string presetName(preset);
        std::mt19937 rng;
        if (hasSeed) {
            rng.seed(seed);
        } else {
            std::random_device rd;
            rng.seed(rd());
        }

        if (!sfxr_preset(presetName, params, rng)) {
            PyErr_Format(PyExc_ValueError,
                "Unknown sfxr preset '%s'. Valid: coin, laser, explosion, powerup, hurt, jump, blip",
                preset);
            return NULL;
        }
    } else {
        // Custom params - start with defaults
        params = SfxrParams();
        if (wave_type != -999) params.wave_type = wave_type;
        if (base_freq != -999) params.base_freq = static_cast<float>(base_freq);
        if (freq_limit != -999) params.freq_limit = static_cast<float>(freq_limit);
        if (freq_ramp != -999) params.freq_ramp = static_cast<float>(freq_ramp);
        if (freq_dramp != -999) params.freq_dramp = static_cast<float>(freq_dramp);
        if (duty != -999) params.duty = static_cast<float>(duty);
        if (duty_ramp != -999) params.duty_ramp = static_cast<float>(duty_ramp);
        if (vib_strength != -999) params.vib_strength = static_cast<float>(vib_strength);
        if (vib_speed != -999) params.vib_speed = static_cast<float>(vib_speed);
        if (env_attack != -999) params.env_attack = static_cast<float>(env_attack);
        if (env_sustain != -999) params.env_sustain = static_cast<float>(env_sustain);
        if (env_decay != -999) params.env_decay = static_cast<float>(env_decay);
        if (env_punch != -999) params.env_punch = static_cast<float>(env_punch);
        if (lpf_freq != -999) params.lpf_freq = static_cast<float>(lpf_freq);
        if (lpf_ramp != -999) params.lpf_ramp = static_cast<float>(lpf_ramp);
        if (lpf_resonance != -999) params.lpf_resonance = static_cast<float>(lpf_resonance);
        if (hpf_freq != -999) params.hpf_freq = static_cast<float>(hpf_freq);
        if (hpf_ramp != -999) params.hpf_ramp = static_cast<float>(hpf_ramp);
        if (pha_offset != -999) params.pha_offset = static_cast<float>(pha_offset);
        if (pha_ramp != -999) params.pha_ramp = static_cast<float>(pha_ramp);
        if (repeat_speed != -999) params.repeat_speed = static_cast<float>(repeat_speed);
        if (arp_speed != -999) params.arp_speed = static_cast<float>(arp_speed);
        if (arp_mod != -999) params.arp_mod = static_cast<float>(arp_mod);
    }

    // Synthesize
    std::vector<int16_t> samples = sfxr_synthesize(params);

    auto data = std::make_shared<SoundBufferData>(std::move(samples), 44100, 1);
    data->sfxrParams = std::make_shared<SfxrParams>(params);
    return PySoundBuffer_from_data(std::move(data));
}

// ============================================================================
// DSP effect methods (each returns new SoundBuffer)
// ============================================================================

PyObject* PySoundBuffer::pitch_shift(PySoundBufferObject* self, PyObject* args) {
    double factor;
    if (!PyArg_ParseTuple(args, "d", &factor)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    if (factor <= 0.0) { PyErr_SetString(PyExc_ValueError, "pitch factor must be positive"); return NULL; }

    auto result = AudioEffects::pitchShift(self->data->samples, self->data->channels, factor);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::low_pass(PySoundBufferObject* self, PyObject* args) {
    double cutoff;
    if (!PyArg_ParseTuple(args, "d", &cutoff)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::lowPass(self->data->samples, self->data->sampleRate, self->data->channels, cutoff);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::high_pass(PySoundBufferObject* self, PyObject* args) {
    double cutoff;
    if (!PyArg_ParseTuple(args, "d", &cutoff)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::highPass(self->data->samples, self->data->sampleRate, self->data->channels, cutoff);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::echo(PySoundBufferObject* self, PyObject* args) {
    double delay_ms, feedback, wet;
    if (!PyArg_ParseTuple(args, "ddd", &delay_ms, &feedback, &wet)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::echo(self->data->samples, self->data->sampleRate, self->data->channels,
                                      delay_ms, feedback, wet);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::reverb(PySoundBufferObject* self, PyObject* args) {
    double room_size, damping, wet;
    if (!PyArg_ParseTuple(args, "ddd", &room_size, &damping, &wet)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::reverb(self->data->samples, self->data->sampleRate, self->data->channels,
                                        room_size, damping, wet);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::distortion(PySoundBufferObject* self, PyObject* args) {
    double drive;
    if (!PyArg_ParseTuple(args, "d", &drive)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::distortion(self->data->samples, drive);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::bit_crush(PySoundBufferObject* self, PyObject* args) {
    int bits, rateDiv;
    if (!PyArg_ParseTuple(args, "ii", &bits, &rateDiv)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::bitCrush(self->data->samples, bits, rateDiv);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::gain(PySoundBufferObject* self, PyObject* args) {
    double factor;
    if (!PyArg_ParseTuple(args, "d", &factor)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::gain(self->data->samples, factor);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::normalize(PySoundBufferObject* self, PyObject* args) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::normalize(self->data->samples);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::reverse(PySoundBufferObject* self, PyObject* args) {
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::reverse(self->data->samples, self->data->channels);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::slice(PySoundBufferObject* self, PyObject* args) {
    double startSec, endSec;
    if (!PyArg_ParseTuple(args, "dd", &startSec, &endSec)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }

    auto result = AudioEffects::slice(self->data->samples, self->data->sampleRate, self->data->channels,
                                       startSec, endSec);
    auto data = std::make_shared<SoundBufferData>(std::move(result), self->data->sampleRate, self->data->channels);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::sfxr_mutate(PySoundBufferObject* self, PyObject* args) {
    double amount = 0.05;
    PyObject* seed_obj = Py_None;
    if (!PyArg_ParseTuple(args, "|dO", &amount, &seed_obj)) return NULL;
    if (!self->data) { PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer"); return NULL; }
    if (!self->data->sfxrParams) {
        PyErr_SetString(PyExc_RuntimeError, "SoundBuffer was not created with sfxr - no params to mutate");
        return NULL;
    }

    std::mt19937 rng;
    if (seed_obj != Py_None && PyLong_Check(seed_obj)) {
        rng.seed(static_cast<uint32_t>(PyLong_AsUnsignedLong(seed_obj)));
    } else {
        std::random_device rd;
        rng.seed(rd());
    }

    SfxrParams mutated = sfxr_mutate_params(*self->data->sfxrParams, static_cast<float>(amount), rng);
    std::vector<int16_t> samples = sfxr_synthesize(mutated);

    auto data = std::make_shared<SoundBufferData>(std::move(samples), 44100, 1);
    data->sfxrParams = std::make_shared<SfxrParams>(mutated);
    return PySoundBuffer_from_data(std::move(data));
}

// ============================================================================
// Composition class methods
// ============================================================================

PyObject* PySoundBuffer::concat(PyObject* cls, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"buffers", "overlap", nullptr};
    PyObject* bufList;
    double overlap = 0.0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|d", const_cast<char**>(keywords),
                                     &bufList, &overlap)) {
        return NULL;
    }

    if (!PySequence_Check(bufList)) {
        PyErr_SetString(PyExc_TypeError, "buffers must be a sequence of SoundBuffer objects");
        return NULL;
    }

    Py_ssize_t count = PySequence_Size(bufList);
    if (count <= 0) {
        PyErr_SetString(PyExc_ValueError, "buffers must not be empty");
        return NULL;
    }

    // Gather all buffer data
    std::vector<std::shared_ptr<SoundBufferData>> buffers;
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject* item = PySequence_GetItem(bufList, i);
        if (!item || !PyObject_IsInstance(item, (PyObject*)&mcrfpydef::PySoundBufferType)) {
            Py_XDECREF(item);
            PyErr_SetString(PyExc_TypeError, "All items must be SoundBuffer objects");
            return NULL;
        }
        auto* sbObj = (PySoundBufferObject*)item;
        if (!sbObj->data) {
            Py_DECREF(item);
            PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer in list");
            return NULL;
        }
        buffers.push_back(sbObj->data);
        Py_DECREF(item);
    }

    // Verify matching channels
    unsigned int ch = buffers[0]->channels;
    unsigned int rate = buffers[0]->sampleRate;
    for (auto& b : buffers) {
        if (b->channels != ch) {
            PyErr_SetString(PyExc_ValueError, "All buffers must have the same number of channels");
            return NULL;
        }
    }

    // Build concatenated samples with optional crossfade overlap
    size_t overlapSamples = static_cast<size_t>(overlap * rate * ch);

    std::vector<int16_t> result;
    for (size_t i = 0; i < buffers.size(); i++) {
        auto& src = buffers[i]->samples;
        if (i == 0 || overlapSamples == 0 || result.size() < overlapSamples) {
            result.insert(result.end(), src.begin(), src.end());
        } else {
            // Crossfade overlap region
            size_t ovl = std::min(overlapSamples, std::min(result.size(), src.size()));
            size_t startInResult = result.size() - ovl;
            for (size_t j = 0; j < ovl; j++) {
                float fade = static_cast<float>(j) / static_cast<float>(ovl);
                float a = result[startInResult + j] * (1.0f - fade);
                float b = src[j] * fade;
                result[startInResult + j] = static_cast<int16_t>(std::max(-32768.0f, std::min(32767.0f, a + b)));
            }
            // Append remaining
            if (ovl < src.size()) {
                result.insert(result.end(), src.begin() + ovl, src.end());
            }
        }
    }

    auto data = std::make_shared<SoundBufferData>(std::move(result), rate, ch);
    return PySoundBuffer_from_data(std::move(data));
}

PyObject* PySoundBuffer::mix(PyObject* cls, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"buffers", nullptr};
    PyObject* bufList;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O", const_cast<char**>(keywords), &bufList)) {
        return NULL;
    }

    if (!PySequence_Check(bufList)) {
        PyErr_SetString(PyExc_TypeError, "buffers must be a sequence of SoundBuffer objects");
        return NULL;
    }

    Py_ssize_t count = PySequence_Size(bufList);
    if (count <= 0) {
        PyErr_SetString(PyExc_ValueError, "buffers must not be empty");
        return NULL;
    }

    std::vector<std::shared_ptr<SoundBufferData>> buffers;
    for (Py_ssize_t i = 0; i < count; i++) {
        PyObject* item = PySequence_GetItem(bufList, i);
        if (!item || !PyObject_IsInstance(item, (PyObject*)&mcrfpydef::PySoundBufferType)) {
            Py_XDECREF(item);
            PyErr_SetString(PyExc_TypeError, "All items must be SoundBuffer objects");
            return NULL;
        }
        auto* sbObj = (PySoundBufferObject*)item;
        if (!sbObj->data) {
            Py_DECREF(item);
            PyErr_SetString(PyExc_RuntimeError, "Invalid SoundBuffer in list");
            return NULL;
        }
        buffers.push_back(sbObj->data);
        Py_DECREF(item);
    }

    unsigned int ch = buffers[0]->channels;
    unsigned int rate = buffers[0]->sampleRate;

    // Find longest buffer
    size_t maxLen = 0;
    for (auto& b : buffers) maxLen = std::max(maxLen, b->samples.size());

    // Mix: sum and clamp
    std::vector<int16_t> result(maxLen, 0);
    for (auto& b : buffers) {
        for (size_t i = 0; i < b->samples.size(); i++) {
            int32_t sum = static_cast<int32_t>(result[i]) + static_cast<int32_t>(b->samples[i]);
            result[i] = static_cast<int16_t>(std::max(-32768, std::min(32767, sum)));
        }
    }

    auto data = std::make_shared<SoundBufferData>(std::move(result), rate, ch);
    return PySoundBuffer_from_data(std::move(data));
}

// ============================================================================
// Method/GetSet tables
// ============================================================================

PyMethodDef PySoundBuffer::methods[] = {
    // Class methods (factories)
    {"from_samples", (PyCFunction)PySoundBuffer::from_samples, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(SoundBuffer, from_samples,
         MCRF_SIG("(data: bytes, channels: int, sample_rate: int)", "SoundBuffer"),
         MCRF_DESC("Create a SoundBuffer from raw int16 PCM sample data."),
         MCRF_ARGS_START
         MCRF_ARG("data", "Raw PCM data as bytes (int16 little-endian)")
         MCRF_ARG("channels", "Number of audio channels (1=mono, 2=stereo)")
         MCRF_ARG("sample_rate", "Sample rate in Hz (e.g. 44100)")
     )},
    {"tone", (PyCFunction)PySoundBuffer::tone, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(SoundBuffer, tone,
         MCRF_SIG("(frequency: float, duration: float, waveform: str = 'sine', ...)", "SoundBuffer"),
         MCRF_DESC("Generate a tone with optional ADSR envelope."),
         MCRF_ARGS_START
         MCRF_ARG("frequency", "Frequency in Hz")
         MCRF_ARG("duration", "Duration in seconds")
         MCRF_ARG("waveform", "One of: sine, square, saw, triangle, noise")
         MCRF_ARG("attack", "ADSR attack time in seconds (default 0.01)")
         MCRF_ARG("decay", "ADSR decay time in seconds (default 0.0)")
         MCRF_ARG("sustain", "ADSR sustain level 0.0-1.0 (default 1.0)")
         MCRF_ARG("release", "ADSR release time in seconds (default 0.01)")
     )},
    {"sfxr", (PyCFunction)PySoundBuffer::sfxr, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(SoundBuffer, sfxr,
         MCRF_SIG("(preset: str = None, seed: int = None, **params)", "SoundBuffer"),
         MCRF_DESC("Generate retro sound effects using sfxr synthesis."),
         MCRF_ARGS_START
         MCRF_ARG("preset", "One of: coin, laser, explosion, powerup, hurt, jump, blip")
         MCRF_ARG("seed", "Random seed for deterministic generation")
         MCRF_RETURNS("SoundBuffer with sfxr_params set for later mutation")
     )},
    {"concat", (PyCFunction)PySoundBuffer::concat, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(SoundBuffer, concat,
         MCRF_SIG("(buffers: list[SoundBuffer], overlap: float = 0.0)", "SoundBuffer"),
         MCRF_DESC("Concatenate multiple SoundBuffers with optional crossfade overlap."),
         MCRF_ARGS_START
         MCRF_ARG("buffers", "List of SoundBuffer objects to concatenate")
         MCRF_ARG("overlap", "Crossfade overlap duration in seconds")
     )},
    {"mix", (PyCFunction)PySoundBuffer::mix, METH_VARARGS | METH_KEYWORDS | METH_CLASS,
     MCRF_METHOD(SoundBuffer, mix,
         MCRF_SIG("(buffers: list[SoundBuffer])", "SoundBuffer"),
         MCRF_DESC("Mix multiple SoundBuffers together (additive, clamped)."),
         MCRF_ARGS_START
         MCRF_ARG("buffers", "List of SoundBuffer objects to mix")
     )},

    // Instance methods (DSP effects)
    {"pitch_shift", (PyCFunction)PySoundBuffer::pitch_shift, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, pitch_shift,
         MCRF_SIG("(factor: float)", "SoundBuffer"),
         MCRF_DESC("Resample to shift pitch. factor>1 = higher+shorter.")
     )},
    {"low_pass", (PyCFunction)PySoundBuffer::low_pass, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, low_pass,
         MCRF_SIG("(cutoff_hz: float)", "SoundBuffer"),
         MCRF_DESC("Apply single-pole IIR low-pass filter.")
     )},
    {"high_pass", (PyCFunction)PySoundBuffer::high_pass, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, high_pass,
         MCRF_SIG("(cutoff_hz: float)", "SoundBuffer"),
         MCRF_DESC("Apply single-pole IIR high-pass filter.")
     )},
    {"echo", (PyCFunction)PySoundBuffer::echo, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, echo,
         MCRF_SIG("(delay_ms: float, feedback: float, wet: float)", "SoundBuffer"),
         MCRF_DESC("Apply echo effect with delay, feedback, and wet/dry mix.")
     )},
    {"reverb", (PyCFunction)PySoundBuffer::reverb, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, reverb,
         MCRF_SIG("(room_size: float, damping: float, wet: float)", "SoundBuffer"),
         MCRF_DESC("Apply simplified Freeverb-style reverb.")
     )},
    {"distortion", (PyCFunction)PySoundBuffer::distortion, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, distortion,
         MCRF_SIG("(drive: float)", "SoundBuffer"),
         MCRF_DESC("Apply tanh soft clipping distortion.")
     )},
    {"bit_crush", (PyCFunction)PySoundBuffer::bit_crush, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, bit_crush,
         MCRF_SIG("(bits: int, rate_divisor: int)", "SoundBuffer"),
         MCRF_DESC("Reduce bit depth and sample rate for lo-fi effect.")
     )},
    {"gain", (PyCFunction)PySoundBuffer::gain, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, gain,
         MCRF_SIG("(factor: float)", "SoundBuffer"),
         MCRF_DESC("Multiply all samples by a scalar factor. Use for volume/amplitude control before mixing."),
         MCRF_ARGS_START
         MCRF_ARG("factor", "Amplitude multiplier (0.5 = half volume, 2.0 = double). Clamps to int16 range.")
     )},
    {"normalize", (PyCFunction)PySoundBuffer::normalize, METH_NOARGS,
     MCRF_METHOD(SoundBuffer, normalize,
         MCRF_SIG("()", "SoundBuffer"),
         MCRF_DESC("Scale samples to 95%% of int16 max.")
     )},
    {"reverse", (PyCFunction)PySoundBuffer::reverse, METH_NOARGS,
     MCRF_METHOD(SoundBuffer, reverse,
         MCRF_SIG("()", "SoundBuffer"),
         MCRF_DESC("Reverse the sample order.")
     )},
    {"slice", (PyCFunction)PySoundBuffer::slice, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, slice,
         MCRF_SIG("(start: float, end: float)", "SoundBuffer"),
         MCRF_DESC("Extract a time range in seconds.")
     )},
    {"sfxr_mutate", (PyCFunction)PySoundBuffer::sfxr_mutate, METH_VARARGS,
     MCRF_METHOD(SoundBuffer, sfxr_mutate,
         MCRF_SIG("(amount: float = 0.05, seed: int = None)", "SoundBuffer"),
         MCRF_DESC("Jitter sfxr params and re-synthesize. Only works on sfxr-generated buffers.")
     )},
    {NULL}
};

PyGetSetDef PySoundBuffer::getsetters[] = {
    {"duration", (getter)PySoundBuffer::get_duration, NULL,
     MCRF_PROPERTY(duration, "Total duration in seconds (read-only)."), NULL},
    {"sample_count", (getter)PySoundBuffer::get_sample_count, NULL,
     MCRF_PROPERTY(sample_count, "Total number of samples (read-only)."), NULL},
    {"sample_rate", (getter)PySoundBuffer::get_sample_rate, NULL,
     MCRF_PROPERTY(sample_rate, "Sample rate in Hz (read-only)."), NULL},
    {"channels", (getter)PySoundBuffer::get_channels, NULL,
     MCRF_PROPERTY(channels, "Number of audio channels (read-only)."), NULL},
    {"sfxr_params", (getter)PySoundBuffer::get_sfxr_params, NULL,
     MCRF_PROPERTY(sfxr_params, "Dict of sfxr parameters if sfxr-generated, else None (read-only)."), NULL},
    {NULL}
};
