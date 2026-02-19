#pragma once
#include <vector>
#include <cstdint>
#include <random>
#include <string>
#include "Python.h"

// sfxr parameter set (24 floats + wave_type)
struct SfxrParams {
    int wave_type = 0;          // 0=square, 1=sawtooth, 2=sine, 3=noise

    float base_freq = 0.3f;     // Base frequency
    float freq_limit = 0.0f;    // Frequency cutoff
    float freq_ramp = 0.0f;     // Frequency slide
    float freq_dramp = 0.0f;    // Delta slide

    float duty = 0.5f;          // Square wave duty cycle
    float duty_ramp = 0.0f;     // Duty sweep

    float vib_strength = 0.0f;  // Vibrato depth
    float vib_speed = 0.0f;     // Vibrato speed

    float env_attack = 0.0f;    // Envelope attack
    float env_sustain = 0.3f;   // Envelope sustain
    float env_decay = 0.4f;     // Envelope decay
    float env_punch = 0.0f;     // Sustain punch

    float lpf_freq = 1.0f;      // Low-pass filter cutoff
    float lpf_ramp = 0.0f;      // Low-pass filter sweep
    float lpf_resonance = 0.0f; // Low-pass filter resonance

    float hpf_freq = 0.0f;      // High-pass filter cutoff
    float hpf_ramp = 0.0f;      // High-pass filter sweep

    float pha_offset = 0.0f;    // Phaser offset
    float pha_ramp = 0.0f;      // Phaser sweep

    float repeat_speed = 0.0f;  // Repeat speed

    float arp_speed = 0.0f;     // Arpeggiator speed
    float arp_mod = 0.0f;       // Arpeggiator frequency multiplier
};

// Synthesize samples from sfxr parameters (44100 Hz, mono, int16)
std::vector<int16_t> sfxr_synthesize(const SfxrParams& params);

// Generate preset parameters
bool sfxr_preset(const std::string& name, SfxrParams& out, std::mt19937& rng);

// Mutate existing parameters
SfxrParams sfxr_mutate_params(const SfxrParams& base, float amount, std::mt19937& rng);

// Convert params to Python dict
PyObject* sfxr_params_to_dict(const SfxrParams& params);
