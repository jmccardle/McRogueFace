#include "AudioEffects.h"
#include <cmath>
#include <algorithm>
#include <cstring>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

namespace AudioEffects {

// ============================================================================
// Pitch shift via linear interpolation resampling
// ============================================================================

std::vector<int16_t> pitchShift(const std::vector<int16_t>& samples, unsigned int channels, double factor) {
    if (samples.empty() || factor <= 0.0) return samples;

    size_t frames = samples.size() / channels;
    size_t newFrames = static_cast<size_t>(frames / factor);
    if (newFrames == 0) newFrames = 1;

    std::vector<int16_t> result(newFrames * channels);

    for (size_t i = 0; i < newFrames; i++) {
        double srcPos = i * factor;
        size_t idx0 = static_cast<size_t>(srcPos);
        double frac = srcPos - idx0;
        size_t idx1 = std::min(idx0 + 1, frames - 1);

        for (unsigned int ch = 0; ch < channels; ch++) {
            double s0 = samples[idx0 * channels + ch];
            double s1 = samples[idx1 * channels + ch];
            double interp = s0 + (s1 - s0) * frac;
            result[i * channels + ch] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, interp)));
        }
    }

    return result;
}

// ============================================================================
// Low-pass filter (single-pole IIR)
// ============================================================================

std::vector<int16_t> lowPass(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels, double cutoffHz) {
    if (samples.empty()) return samples;

    double rc = 1.0 / (2.0 * M_PI * cutoffHz);
    double dt = 1.0 / sampleRate;
    double alpha = dt / (rc + dt);

    std::vector<int16_t> result(samples.size());
    std::vector<double> prev(channels, 0.0);

    size_t frames = samples.size() / channels;
    for (size_t i = 0; i < frames; i++) {
        for (unsigned int ch = 0; ch < channels; ch++) {
            double input = samples[i * channels + ch];
            prev[ch] = prev[ch] + alpha * (input - prev[ch]);
            result[i * channels + ch] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, prev[ch])));
        }
    }

    return result;
}

// ============================================================================
// High-pass filter (complement of low-pass)
// ============================================================================

std::vector<int16_t> highPass(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels, double cutoffHz) {
    if (samples.empty()) return samples;

    double rc = 1.0 / (2.0 * M_PI * cutoffHz);
    double dt = 1.0 / sampleRate;
    double alpha = rc / (rc + dt);

    std::vector<int16_t> result(samples.size());
    std::vector<double> prevIn(channels, 0.0);
    std::vector<double> prevOut(channels, 0.0);

    size_t frames = samples.size() / channels;
    for (size_t i = 0; i < frames; i++) {
        for (unsigned int ch = 0; ch < channels; ch++) {
            double input = samples[i * channels + ch];
            prevOut[ch] = alpha * (prevOut[ch] + input - prevIn[ch]);
            prevIn[ch] = input;
            result[i * channels + ch] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, prevOut[ch])));
        }
    }

    return result;
}

// ============================================================================
// Echo (circular delay buffer with feedback)
// ============================================================================

std::vector<int16_t> echo(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                          double delayMs, double feedback, double wet) {
    if (samples.empty()) return samples;

    size_t delaySamples = static_cast<size_t>(delayMs * sampleRate * channels / 1000.0);
    if (delaySamples == 0) return samples;

    std::vector<double> delay(delaySamples, 0.0);
    std::vector<int16_t> result(samples.size());
    size_t pos = 0;

    for (size_t i = 0; i < samples.size(); i++) {
        double input = samples[i];
        double delayed = delay[pos % delaySamples];
        double output = input + delayed * wet;
        delay[pos % delaySamples] = input + delayed * feedback;
        result[i] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, output)));
        pos++;
    }

    return result;
}

// ============================================================================
// Reverb (simplified Freeverb: 4 comb filters + 2 allpass)
// ============================================================================

namespace {
    struct CombFilter {
        std::vector<double> buffer;
        size_t pos = 0;
        double filterStore = 0.0;

        CombFilter(size_t size) : buffer(size, 0.0) {}

        double process(double input, double feedback, double damp) {
            double output = buffer[pos];
            filterStore = output * (1.0 - damp) + filterStore * damp;
            buffer[pos] = input + filterStore * feedback;
            pos = (pos + 1) % buffer.size();
            return output;
        }
    };

    struct AllpassFilter {
        std::vector<double> buffer;
        size_t pos = 0;

        AllpassFilter(size_t size) : buffer(size, 0.0) {}

        double process(double input) {
            double buffered = buffer[pos];
            double output = -input + buffered;
            buffer[pos] = input + buffered * 0.5;
            pos = (pos + 1) % buffer.size();
            return output;
        }
    };
}

std::vector<int16_t> reverb(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                            double roomSize, double damping, double wet) {
    if (samples.empty()) return samples;

    // Comb filter delays (in samples, scaled for sample rate)
    double scale = sampleRate / 44100.0;
    size_t combSizes[4] = {
        static_cast<size_t>(1116 * scale),
        static_cast<size_t>(1188 * scale),
        static_cast<size_t>(1277 * scale),
        static_cast<size_t>(1356 * scale)
    };
    size_t allpassSizes[2] = {
        static_cast<size_t>(556 * scale),
        static_cast<size_t>(441 * scale)
    };

    CombFilter combs[4] = {
        CombFilter(combSizes[0]), CombFilter(combSizes[1]),
        CombFilter(combSizes[2]), CombFilter(combSizes[3])
    };
    AllpassFilter allpasses[2] = {
        AllpassFilter(allpassSizes[0]), AllpassFilter(allpassSizes[1])
    };

    double feedback = roomSize * 0.9 + 0.05;
    double dry = 1.0 - wet;

    std::vector<int16_t> result(samples.size());

    // Process mono (mix channels if stereo, then duplicate)
    for (size_t i = 0; i < samples.size(); i += channels) {
        // Mix to mono for reverb processing
        double mono = 0.0;
        for (unsigned int ch = 0; ch < channels; ch++) {
            mono += samples[i + ch];
        }
        mono /= channels;
        mono /= 32768.0; // Normalize to -1..1

        // Parallel comb filters
        double reverbSample = 0.0;
        for (int c = 0; c < 4; c++) {
            reverbSample += combs[c].process(mono, feedback, damping);
        }

        // Series allpass filters
        for (int a = 0; a < 2; a++) {
            reverbSample = allpasses[a].process(reverbSample);
        }

        // Mix wet/dry and write to all channels
        for (unsigned int ch = 0; ch < channels; ch++) {
            double original = samples[i + ch] / 32768.0;
            double output = original * dry + reverbSample * wet;
            result[i + ch] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, output * 32768.0)));
        }
    }

    return result;
}

// ============================================================================
// Distortion (tanh soft clip)
// ============================================================================

std::vector<int16_t> distortion(const std::vector<int16_t>& samples, double drive) {
    if (samples.empty()) return samples;

    std::vector<int16_t> result(samples.size());
    for (size_t i = 0; i < samples.size(); i++) {
        double s = samples[i] / 32768.0;
        s = std::tanh(s * drive);
        result[i] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, s * 32768.0)));
    }
    return result;
}

// ============================================================================
// Bit crush (quantize + sample rate reduce)
// ============================================================================

std::vector<int16_t> bitCrush(const std::vector<int16_t>& samples, int bits, int rateDivisor) {
    if (samples.empty()) return samples;

    bits = std::max(1, std::min(16, bits));
    rateDivisor = std::max(1, rateDivisor);

    int levels = 1 << bits;
    double quantStep = 65536.0 / levels;

    std::vector<int16_t> result(samples.size());
    int16_t held = 0;

    for (size_t i = 0; i < samples.size(); i++) {
        if (i % rateDivisor == 0) {
            // Quantize
            double s = samples[i] + 32768.0; // Shift to 0..65536
            s = std::floor(s / quantStep) * quantStep;
            held = static_cast<int16_t>(s - 32768.0);
        }
        result[i] = held;
    }

    return result;
}

// ============================================================================
// Normalize (scale to 95% of int16 max)
// ============================================================================

std::vector<int16_t> normalize(const std::vector<int16_t>& samples) {
    if (samples.empty()) return samples;

    int16_t peak = 0;
    for (auto s : samples) {
        int16_t abs_s = (s < 0) ? static_cast<int16_t>(-s) : s;
        if (abs_s > peak) peak = abs_s;
    }

    if (peak == 0) return samples;

    double scale = 31128.0 / peak; // 95% of 32767
    std::vector<int16_t> result(samples.size());
    for (size_t i = 0; i < samples.size(); i++) {
        double s = samples[i] * scale;
        result[i] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, s)));
    }

    return result;
}

// ============================================================================
// Gain (multiply all samples by scalar factor)
// ============================================================================

std::vector<int16_t> gain(const std::vector<int16_t>& samples, double factor) {
    if (samples.empty()) return samples;

    std::vector<int16_t> result(samples.size());
    for (size_t i = 0; i < samples.size(); i++) {
        double s = samples[i] * factor;
        result[i] = static_cast<int16_t>(std::max(-32768.0, std::min(32767.0, s)));
    }
    return result;
}

// ============================================================================
// Reverse (frame-aware for multichannel)
// ============================================================================

std::vector<int16_t> reverse(const std::vector<int16_t>& samples, unsigned int channels) {
    if (samples.empty()) return samples;

    size_t frames = samples.size() / channels;
    std::vector<int16_t> result(samples.size());

    for (size_t i = 0; i < frames; i++) {
        size_t srcFrame = frames - 1 - i;
        for (unsigned int ch = 0; ch < channels; ch++) {
            result[i * channels + ch] = samples[srcFrame * channels + ch];
        }
    }

    return result;
}

// ============================================================================
// Slice (extract sub-range by time)
// ============================================================================

std::vector<int16_t> slice(const std::vector<int16_t>& samples, unsigned int sampleRate, unsigned int channels,
                           double startSec, double endSec) {
    if (samples.empty()) return {};

    size_t frames = samples.size() / channels;
    size_t startFrame = static_cast<size_t>(std::max(0.0, startSec) * sampleRate);
    size_t endFrame = static_cast<size_t>(std::max(0.0, endSec) * sampleRate);

    startFrame = std::min(startFrame, frames);
    endFrame = std::min(endFrame, frames);

    if (startFrame >= endFrame) return {};

    size_t numFrames = endFrame - startFrame;
    std::vector<int16_t> result(numFrames * channels);
    std::memcpy(result.data(), &samples[startFrame * channels], numFrames * channels * sizeof(int16_t));

    return result;
}

} // namespace AudioEffects
