#include "EngineRandom.h"

#include <array>
#include <cstddef>

namespace {

constexpr std::size_t kStreamCount =
    static_cast<std::size_t>(mcrf::RandomStream::COUNT);

struct RandomState {
    bool     seeded = false;
    uint32_t master = 0;
    std::array<std::mt19937, kStreamCount> streams;
};

// Function-local static: constructed on first use, with no ordering dependency on
// any other translation unit's globals. This is the "off namespace scope" half of
// #394 -- the previous shape was a namespace-scope object whose constructor read
// std::random_device before main() could possibly have been told a seed.
RandomState& state()
{
    static RandomState s;
    return s;
}

// Derive each stream from the master seed. std::seed_seq mixes, so adjacent
// masters (0, 1, 2 ...) do not produce correlated streams -- which matters
// because sweeps are usually run at exactly those seeds.
void reseedAllStreams(RandomState& s)
{
    for (std::size_t i = 0; i < kStreamCount; ++i) {
        std::seed_seq seq{ s.master, static_cast<uint32_t>(i) };
        s.streams[i].seed(seq);
    }
}

} // namespace

namespace mcrf {

uint32_t EngineRandom::seed()
{
    RandomState& s = state();
    if (!s.seeded) {
        std::random_device rd;
        s.master = static_cast<uint32_t>(rd());
        s.seeded = true;
        reseedAllStreams(s);
    }
    return s.master;
}

void EngineRandom::setSeed(uint32_t seed)
{
    RandomState& s = state();
    s.master = seed;
    s.seeded = true;
    reseedAllStreams(s);
}

std::mt19937& EngineRandom::stream(RandomStream which)
{
    RandomState& s = state();
    if (!s.seeded) {
        seed();  // materialise and record, never draw from an unrecorded seed
    }
    return s.streams[static_cast<std::size_t>(which)];
}

} // namespace mcrf
