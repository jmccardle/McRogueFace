#include "SfxrSynth.h"
#include <cmath>
#include <algorithm>
#include <cstring>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

// ============================================================================
// sfxr synthesis engine
// Based on the original sfxr by DrPetter
// 8x supersampled, 44100 Hz mono output
// ============================================================================

std::vector<int16_t> sfxr_synthesize(const SfxrParams& p) {
    // Convert parameters to internal representation
    const int OVERSAMPLE = 8;
    const int SAMPLE_RATE = 44100;

    double fperiod;
    double fmaxperiod;
    double fslide;
    double fdslide;
    int period;
    double square_duty;
    double square_slide;

    // Envelope
    int env_length[3];
    double env_vol;
    int env_stage;
    int env_time;

    // Vibrato
    double vib_phase;
    double vib_speed;
    double vib_amp;

    // Low-pass filter
    double fltp;
    double fltdp;
    double fltw;
    double fltw_d;
    double fltdmp;
    double fltphp;
    double flthp;
    double flthp_d;

    // Phaser
    double phaser_buffer[1024];
    int phaser_pos;
    double phaser_offset;
    double phaser_delta;

    // Noise buffer
    double noise_buffer[32];

    // Arpeggio
    double arp_time;
    double arp_limit;
    double arp_mod;

    // Repeat
    double rep_time;
    double rep_limit;

    int phase;

    // Initialize
    auto reset = [&](bool restart) {
        if (!restart) {
            phase = 0;
        }
        fperiod = 100.0 / (p.base_freq * p.base_freq + 0.001);
        period = static_cast<int>(fperiod);
        fmaxperiod = 100.0 / (p.freq_limit * p.freq_limit + 0.001);
        fslide = 1.0 - std::pow(p.freq_ramp, 3.0) * 0.01;
        fdslide = -std::pow(p.freq_dramp, 3.0) * 0.000001;
        square_duty = 0.5 - p.duty * 0.5;
        square_slide = -p.duty_ramp * 0.00005;

        if (p.arp_mod >= 0.0f) {
            arp_mod = 1.0 - std::pow(p.arp_mod, 2.0) * 0.9;
        } else {
            arp_mod = 1.0 + std::pow(p.arp_mod, 2.0) * 10.0;
        }
        arp_time = 0;
        arp_limit = (p.arp_speed == 1.0f) ? 0 : static_cast<int>(std::pow(1.0 - p.arp_speed, 2.0) * 20000 + 32);

        if (!restart) {
            // Noise buffer
            for (int i = 0; i < 32; i++) {
                noise_buffer[i] = ((std::rand() % 20001) / 10000.0) - 1.0;
            }

            // Phaser
            std::memset(phaser_buffer, 0, sizeof(phaser_buffer));
            phaser_pos = 0;
            phaser_offset = std::pow(p.pha_offset, 2.0) * 1020.0;
            if (p.pha_offset < 0.0f) phaser_offset = -phaser_offset;
            phaser_delta = std::pow(p.pha_ramp, 2.0) * 1.0;
            if (p.pha_ramp < 0.0f) phaser_delta = -phaser_delta;

            // Filter
            fltp = 0.0;
            fltdp = 0.0;
            fltw = std::pow(p.lpf_freq, 3.0) * 0.1;
            fltw_d = 1.0 + p.lpf_ramp * 0.0001;
            fltdmp = 5.0 / (1.0 + std::pow(p.lpf_resonance, 2.0) * 20.0) * (0.01 + fltw);
            if (fltdmp > 0.8) fltdmp = 0.8;
            fltphp = 0.0;
            flthp = std::pow(p.hpf_freq, 2.0) * 0.1;
            flthp_d = 1.0 + p.hpf_ramp * 0.0003;

            // Vibrato
            vib_phase = 0.0;
            vib_speed = std::pow(p.vib_speed, 2.0) * 0.01;
            vib_amp = p.vib_strength * 0.5;

            // Envelope
            env_vol = 0.0;
            env_stage = 0;
            env_time = 0;
            env_length[0] = static_cast<int>(p.env_attack * p.env_attack * 100000.0);
            env_length[1] = static_cast<int>(p.env_sustain * p.env_sustain * 100000.0);
            env_length[2] = static_cast<int>(p.env_decay * p.env_decay * 100000.0);

            // Repeat
            rep_time = 0;
            rep_limit = (p.repeat_speed == 0.0f) ? 0 :
                static_cast<int>(std::pow(1.0 - p.repeat_speed, 2.0) * 20000 + 32);
        }
    };

    // Seed RNG deterministically based on params
    std::srand(42);

    reset(false);

    // Generate samples - max 4 seconds of audio
    int maxSamples = SAMPLE_RATE * 4;
    std::vector<int16_t> output;
    output.reserve(maxSamples);

    for (int si = 0; si < maxSamples; si++) {
        // Repeat
        rep_time++;
        if (rep_limit != 0 && rep_time >= rep_limit) {
            rep_time = 0;
            reset(true);
        }

        // Arpeggio
        arp_time++;
        if (arp_limit != 0 && arp_time >= arp_limit) {
            arp_limit = 0;
            fperiod *= arp_mod;
        }

        // Frequency slide
        fslide += fdslide;
        fperiod *= fslide;
        if (fperiod > fmaxperiod) {
            fperiod = fmaxperiod;
            if (p.freq_limit > 0.0f) {
                // Sound has ended
                break;
            }
        }

        // Vibrato
        double rfperiod = fperiod;
        if (vib_amp > 0.0) {
            vib_phase += vib_speed;
            rfperiod = fperiod * (1.0 + std::sin(vib_phase) * vib_amp);
        }
        period = static_cast<int>(rfperiod);
        if (period < 8) period = 8;

        // Duty cycle
        square_duty += square_slide;
        if (square_duty < 0.0) square_duty = 0.0;
        if (square_duty > 0.5) square_duty = 0.5;

        // Envelope
        env_time++;
        if (env_time > env_length[env_stage]) {
            env_time = 0;
            env_stage++;
            if (env_stage == 3) {
                break; // Sound complete
            }
        }
        if (env_stage == 0) {
            env_vol = (env_length[0] > 0) ?
                static_cast<double>(env_time) / env_length[0] : 1.0;
        } else if (env_stage == 1) {
            env_vol = 1.0 + (1.0 - static_cast<double>(env_time) / std::max(1, env_length[1])) * 2.0 * p.env_punch;
        } else {
            env_vol = 1.0 - static_cast<double>(env_time) / std::max(1, env_length[2]);
        }

        // Phaser
        phaser_offset += phaser_delta;
        int iphaser_offset = std::abs(static_cast<int>(phaser_offset));
        if (iphaser_offset > 1023) iphaser_offset = 1023;

        // Filter
        if (flthp_d != 0.0) {
            flthp *= flthp_d;
            if (flthp < 0.00001) flthp = 0.00001;
            if (flthp > 0.1) flthp = 0.1;
        }

        // 8x supersampling
        double ssample = 0.0;
        for (int si2 = 0; si2 < OVERSAMPLE; si2++) {
            double sample = 0.0;
            phase++;

            // Wrap phase at period boundary (critical for square/saw waveforms)
            if (phase >= period) {
                phase %= period;
                if (p.wave_type == 3) { // Refresh noise buffer each period
                    for (int i = 0; i < 32; i++) {
                        noise_buffer[i] = ((std::rand() % 20001) / 10000.0) - 1.0;
                    }
                }
            }

            double fphase = static_cast<double>(phase) / period;

            // Waveform generation
            switch (p.wave_type) {
                case 0: // Square
                    sample = (fphase < square_duty) ? 0.5 : -0.5;
                    break;
                case 1: // Sawtooth
                    sample = 1.0 - fphase * 2.0;
                    break;
                case 2: // Sine
                    sample = std::sin(fphase * 2.0 * M_PI);
                    break;
                case 3: // Noise
                    sample = noise_buffer[static_cast<int>(fphase * 32) % 32];
                    break;
            }

            // Low-pass filter
            double pp = fltp;
            fltw *= fltw_d;
            if (fltw < 0.0) fltw = 0.0;
            if (fltw > 0.1) fltw = 0.1;
            if (p.lpf_freq != 1.0f) {
                fltdp += (sample - fltp) * fltw;
                fltdp -= fltdp * fltdmp;
            } else {
                fltp = sample;
                fltdp = 0.0;
            }
            fltp += fltdp;

            // High-pass filter
            fltphp += fltp - pp;
            fltphp -= fltphp * flthp;
            sample = fltphp;

            // Phaser
            phaser_buffer[phaser_pos & 1023] = sample;
            sample += phaser_buffer[(phaser_pos - iphaser_offset + 1024) & 1023];
            phaser_pos = (phaser_pos + 1) & 1023;

            // Accumulate
            ssample += sample * env_vol;
        }

        // Average supersamples and scale
        ssample = ssample / OVERSAMPLE * 0.2; // master_vol
        ssample *= 2.0; // Boost

        // Clamp
        if (ssample > 1.0) ssample = 1.0;
        if (ssample < -1.0) ssample = -1.0;

        output.push_back(static_cast<int16_t>(ssample * 32000.0));
    }

    return output;
}

// ============================================================================
// Presets
// ============================================================================

static float rnd(std::mt19937& rng, float range) {
    std::uniform_real_distribution<float> dist(0.0f, range);
    return dist(rng);
}

static float rnd01(std::mt19937& rng) {
    return rnd(rng, 1.0f);
}

bool sfxr_preset(const std::string& name, SfxrParams& p, std::mt19937& rng) {
    p = SfxrParams(); // Reset to defaults

    if (name == "coin" || name == "pickup") {
        p.base_freq = 0.4f + rnd(rng, 0.5f);
        p.env_attack = 0.0f;
        p.env_sustain = rnd(rng, 0.1f);
        p.env_decay = 0.1f + rnd(rng, 0.4f);
        p.env_punch = 0.3f + rnd(rng, 0.3f);
        if (rnd01(rng) < 0.5f) {
            p.arp_speed = 0.5f + rnd(rng, 0.2f);
            p.arp_mod = 0.2f + rnd(rng, 0.4f);
        }
    }
    else if (name == "laser" || name == "shoot") {
        p.wave_type = static_cast<int>(rnd(rng, 3.0f));
        if (p.wave_type == 2 && rnd01(rng) < 0.5f)
            p.wave_type = static_cast<int>(rnd(rng, 2.0f));
        p.base_freq = 0.5f + rnd(rng, 0.5f);
        p.freq_limit = std::max(0.2f, p.base_freq - 0.2f - rnd(rng, 0.6f));
        p.freq_ramp = -0.15f - rnd(rng, 0.2f);
        if (rnd01(rng) < 0.33f) {
            p.base_freq = 0.3f + rnd(rng, 0.6f);
            p.freq_limit = rnd(rng, 0.1f);
            p.freq_ramp = -0.35f - rnd(rng, 0.3f);
        }
        if (rnd01(rng) < 0.5f) {
            p.duty = rnd(rng, 0.5f);
            p.duty_ramp = rnd(rng, 0.2f);
        } else {
            p.duty = 0.4f + rnd(rng, 0.5f);
            p.duty_ramp = -rnd(rng, 0.7f);
        }
        p.env_attack = 0.0f;
        p.env_sustain = 0.1f + rnd(rng, 0.2f);
        p.env_decay = rnd(rng, 0.4f);
        if (rnd01(rng) < 0.5f) p.env_punch = rnd(rng, 0.3f);
        if (rnd01(rng) < 0.33f) {
            p.pha_offset = rnd(rng, 0.2f);
            p.pha_ramp = -rnd(rng, 0.2f);
        }
        if (rnd01(rng) < 0.5f) p.hpf_freq = rnd(rng, 0.3f);
    }
    else if (name == "explosion") {
        p.wave_type = 3; // noise
        if (rnd01(rng) < 0.5f) {
            p.base_freq = 0.1f + rnd(rng, 0.4f);
            p.freq_ramp = -0.1f + rnd(rng, 0.4f);
        } else {
            p.base_freq = 0.2f + rnd(rng, 0.7f);
            p.freq_ramp = -0.2f - rnd(rng, 0.2f);
        }
        p.base_freq *= p.base_freq;
        if (rnd01(rng) < 0.2f) p.freq_ramp = 0.0f;
        if (rnd01(rng) < 0.33f) p.repeat_speed = 0.3f + rnd(rng, 0.5f);
        p.env_attack = 0.0f;
        p.env_sustain = 0.1f + rnd(rng, 0.3f);
        p.env_decay = rnd(rng, 0.5f);
        if (rnd01(rng) < 0.5f) {
            p.pha_offset = -0.3f + rnd(rng, 0.9f);
            p.pha_ramp = -rnd(rng, 0.3f);
        }
        p.env_punch = 0.2f + rnd(rng, 0.6f);
        if (rnd01(rng) < 0.5f) {
            p.vib_strength = rnd(rng, 0.7f);
            p.vib_speed = rnd(rng, 0.6f);
        }
        if (rnd01(rng) < 0.33f) {
            p.arp_speed = 0.6f + rnd(rng, 0.3f);
            p.arp_mod = 0.8f - rnd(rng, 1.6f);
        }
    }
    else if (name == "powerup") {
        if (rnd01(rng) < 0.5f) {
            p.wave_type = 1; // saw
        } else {
            p.duty = rnd(rng, 0.6f);
        }
        if (rnd01(rng) < 0.5f) {
            p.base_freq = 0.2f + rnd(rng, 0.3f);
            p.freq_ramp = 0.1f + rnd(rng, 0.4f);
            p.repeat_speed = 0.4f + rnd(rng, 0.4f);
        } else {
            p.base_freq = 0.2f + rnd(rng, 0.3f);
            p.freq_ramp = 0.05f + rnd(rng, 0.2f);
            if (rnd01(rng) < 0.5f) {
                p.vib_strength = rnd(rng, 0.7f);
                p.vib_speed = rnd(rng, 0.6f);
            }
        }
        p.env_attack = 0.0f;
        p.env_sustain = rnd(rng, 0.4f);
        p.env_decay = 0.1f + rnd(rng, 0.4f);
    }
    else if (name == "hurt" || name == "hit") {
        p.wave_type = static_cast<int>(rnd(rng, 3.0f));
        if (p.wave_type == 2) p.wave_type = 3; // prefer noise over sine
        if (p.wave_type == 0) p.duty = rnd(rng, 0.6f);
        p.base_freq = 0.2f + rnd(rng, 0.6f);
        p.freq_ramp = -0.3f - rnd(rng, 0.4f);
        p.env_attack = 0.0f;
        p.env_sustain = rnd(rng, 0.1f);
        p.env_decay = 0.1f + rnd(rng, 0.2f);
        if (rnd01(rng) < 0.5f) p.hpf_freq = rnd(rng, 0.3f);
    }
    else if (name == "jump") {
        p.wave_type = 0; // square
        p.duty = rnd(rng, 0.6f);
        p.base_freq = 0.3f + rnd(rng, 0.3f);
        p.freq_ramp = 0.1f + rnd(rng, 0.2f);
        p.env_attack = 0.0f;
        p.env_sustain = 0.1f + rnd(rng, 0.3f);
        p.env_decay = 0.1f + rnd(rng, 0.2f);
        if (rnd01(rng) < 0.5f) p.hpf_freq = rnd(rng, 0.3f);
        if (rnd01(rng) < 0.5f) p.lpf_freq = 1.0f - rnd(rng, 0.6f);
    }
    else if (name == "blip" || name == "select") {
        p.wave_type = static_cast<int>(rnd(rng, 2.0f));
        if (p.wave_type == 0) p.duty = rnd(rng, 0.6f);
        p.base_freq = 0.2f + rnd(rng, 0.4f);
        p.env_attack = 0.0f;
        p.env_sustain = 0.1f + rnd(rng, 0.1f);
        p.env_decay = rnd(rng, 0.2f);
        p.hpf_freq = 0.1f;
    }
    else {
        return false;
    }

    return true;
}

// ============================================================================
// Mutate
// ============================================================================

SfxrParams sfxr_mutate_params(const SfxrParams& base, float amount, std::mt19937& rng) {
    SfxrParams p = base;
    std::uniform_real_distribution<float> dist(-1.0f, 1.0f);

    auto jitter = [&](float val) -> float {
        return std::max(0.0f, std::min(1.0f, val + dist(rng) * amount));
    };
    auto jitterSigned = [&](float val) -> float {
        return std::max(-1.0f, std::min(1.0f, val + dist(rng) * amount));
    };

    p.base_freq = jitter(p.base_freq);
    p.freq_ramp = jitterSigned(p.freq_ramp);
    p.freq_dramp = jitterSigned(p.freq_dramp);
    p.duty = jitter(p.duty);
    p.duty_ramp = jitterSigned(p.duty_ramp);
    p.vib_strength = jitter(p.vib_strength);
    p.vib_speed = jitter(p.vib_speed);
    p.env_attack = jitter(p.env_attack);
    p.env_sustain = jitter(p.env_sustain);
    p.env_decay = jitter(p.env_decay);
    p.env_punch = jitter(p.env_punch);
    p.lpf_freq = jitter(p.lpf_freq);
    p.lpf_ramp = jitterSigned(p.lpf_ramp);
    p.lpf_resonance = jitter(p.lpf_resonance);
    p.hpf_freq = jitter(p.hpf_freq);
    p.hpf_ramp = jitterSigned(p.hpf_ramp);
    p.pha_offset = jitterSigned(p.pha_offset);
    p.pha_ramp = jitterSigned(p.pha_ramp);
    p.repeat_speed = jitter(p.repeat_speed);
    p.arp_speed = jitter(p.arp_speed);
    p.arp_mod = jitterSigned(p.arp_mod);

    return p;
}

// ============================================================================
// Convert params to Python dict
// ============================================================================

PyObject* sfxr_params_to_dict(const SfxrParams& p) {
    PyObject* d = PyDict_New();
    if (!d) return NULL;

    PyDict_SetItemString(d, "wave_type", PyLong_FromLong(p.wave_type));
    PyDict_SetItemString(d, "base_freq", PyFloat_FromDouble(p.base_freq));
    PyDict_SetItemString(d, "freq_limit", PyFloat_FromDouble(p.freq_limit));
    PyDict_SetItemString(d, "freq_ramp", PyFloat_FromDouble(p.freq_ramp));
    PyDict_SetItemString(d, "freq_dramp", PyFloat_FromDouble(p.freq_dramp));
    PyDict_SetItemString(d, "duty", PyFloat_FromDouble(p.duty));
    PyDict_SetItemString(d, "duty_ramp", PyFloat_FromDouble(p.duty_ramp));
    PyDict_SetItemString(d, "vib_strength", PyFloat_FromDouble(p.vib_strength));
    PyDict_SetItemString(d, "vib_speed", PyFloat_FromDouble(p.vib_speed));
    PyDict_SetItemString(d, "env_attack", PyFloat_FromDouble(p.env_attack));
    PyDict_SetItemString(d, "env_sustain", PyFloat_FromDouble(p.env_sustain));
    PyDict_SetItemString(d, "env_decay", PyFloat_FromDouble(p.env_decay));
    PyDict_SetItemString(d, "env_punch", PyFloat_FromDouble(p.env_punch));
    PyDict_SetItemString(d, "lpf_freq", PyFloat_FromDouble(p.lpf_freq));
    PyDict_SetItemString(d, "lpf_ramp", PyFloat_FromDouble(p.lpf_ramp));
    PyDict_SetItemString(d, "lpf_resonance", PyFloat_FromDouble(p.lpf_resonance));
    PyDict_SetItemString(d, "hpf_freq", PyFloat_FromDouble(p.hpf_freq));
    PyDict_SetItemString(d, "hpf_ramp", PyFloat_FromDouble(p.hpf_ramp));
    PyDict_SetItemString(d, "pha_offset", PyFloat_FromDouble(p.pha_offset));
    PyDict_SetItemString(d, "pha_ramp", PyFloat_FromDouble(p.pha_ramp));
    PyDict_SetItemString(d, "repeat_speed", PyFloat_FromDouble(p.repeat_speed));
    PyDict_SetItemString(d, "arp_speed", PyFloat_FromDouble(p.arp_speed));
    PyDict_SetItemString(d, "arp_mod", PyFloat_FromDouble(p.arp_mod));

    return d;
}
