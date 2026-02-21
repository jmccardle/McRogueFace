#pragma once
#include <vector>
#include <cstdint>

// Pure DSP functions: vector<int16_t> -> vector<int16_t>
// All return NEW vectors, never modify input.
namespace AudioEffects {

// Resample to shift pitch. factor>1 = higher pitch + shorter duration.
std::vector<int16_t> pitchShift(const std::vector<int16_t>& samples, unsigned int channels, double factor);

// Single-pole IIR low-pass filter
std::vector<int16_t> lowPass(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels, double cutoffHz);

// High-pass filter (complement of low-pass)
std::vector<int16_t> highPass(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels, double cutoffHz);

// Delay-line echo with feedback
std::vector<int16_t> echo(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                          double delayMs, double feedback, double wet);

// Simplified Freeverb: 4 comb filters + 2 allpass
std::vector<int16_t> reverb(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                            double roomSize, double damping, double wet);

// tanh soft clipping
std::vector<int16_t> distortion(const std::vector<int16_t>& samples, double drive);

// Reduce bit depth and sample rate
std::vector<int16_t> bitCrush(const std::vector<int16_t>& samples, int bits, int rateDivisor);

// Scale to 95% of int16 max
std::vector<int16_t> normalize(const std::vector<int16_t>& samples);

// Multiply all samples by a scalar factor (volume/amplitude control)
std::vector<int16_t> gain(const std::vector<int16_t>& samples, double factor);

// Reverse sample order (frame-aware for multichannel)
std::vector<int16_t> reverse(const std::vector<int16_t>& samples, unsigned int channels);

// Extract sub-range by time offsets
std::vector<int16_t> slice(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                           double startSec, double endSec);

} // namespace AudioEffects
