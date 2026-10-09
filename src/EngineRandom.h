#pragma once
#include <cstdint>
#include <random>

// =============================================================================
// EngineRandom -- the engine's internal pseudo-random streams (#394)
//
// Every RNG the engine consults *on its own behalf* -- i.e. one the caller never
// supplies a seed for -- lives here. Two properties are the whole point:
//
//   1. The seed is settable from outside (mcrfpy.set_random_seed) before anything
//      consumes randomness.
//   2. The seed is READABLE BACK even when nobody set one. A run that was not
//      seeded explicitly still knows the number it used, so a surprising run stays
//      reproducible after the fact. A setter bolted onto a `std::random_device`
//      seed cannot do this, which is why the state lives here rather than as a
//      namespace-scope object next to its one consumer.
//
// The state is a function-local static, so there is no static-initialisation-order
// dependency between translation units: the first Python call that reaches it
// constructs it.
//
// Streams are INDEPENDENT and derived from one master seed. That matters: it means
// enabling audio does not shift the entity-behaviour sequence, so an audio-on and
// an audio-off run at the same seed produce the same world. Sharing a single
// std::mt19937 across subsystems would couple them and quietly destroy that.
//
// THREADING: draws are unsynchronised, exactly like the world state they feed.
// Behaviour execution mutates entity positions, so it is already governed by the
// engine's single-writer discipline (mcrfpy.lock()); an RNG draw is subject to the
// same rule and adds no new hazard class. Do not add a mutex here expecting it to
// buy determinism -- it would not: two threads interleaving draws produce an
// unreproducible consumption order whether or not the draw itself is atomic.
// =============================================================================

namespace mcrf {

// One stream per subsystem that consumes engine-internal randomness.
// Append before COUNT; the numeric value participates in stream derivation, so
// reordering existing members changes every sequence at a given seed.
enum class RandomStream : uint32_t {
    BEHAVIOR = 0,   // entity behaviour selection (EntityBehavior.cpp)
    AUDIO    = 1,   // playback variation (PySound::py_play_varied)
    COUNT
};

class EngineRandom {
public:
    // The master seed in use. If none was ever set, one is generated from
    // std::random_device, recorded, and returned -- so this never fails to answer.
    static uint32_t seed();

    // Set the master seed and reset every stream to its start. Callable at any
    // time; calling it before any behaviour runs is what makes a run replayable.
    static void setSeed(uint32_t seed);

    // The generator for one subsystem. Materialises the master seed on first use.
    static std::mt19937& stream(RandomStream which);
};

} // namespace mcrf
