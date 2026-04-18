#pragma once
#include <cstddef>
#include <cstdint>

// DiscreteMap - a dense uint8 grid owning its buffer.
//
// Shared-ownership C++ type wrapped by PyDiscreteMapObject and also held by
// UIEntity for per-entity perspective (issue #294). Dimensions are fixed at
// construction; use size() / width() / height() for bounds checks.
class DiscreteMap {
public:
    DiscreteMap(int w, int h, uint8_t fill = 0);
    ~DiscreteMap();

    DiscreteMap(const DiscreteMap&) = delete;
    DiscreteMap& operator=(const DiscreteMap&) = delete;

    int width() const { return w_; }
    int height() const { return h_; }
    size_t size() const { return static_cast<size_t>(w_) * static_cast<size_t>(h_); }

    uint8_t* data() { return values_; }
    const uint8_t* data() const { return values_; }

    // Demote every cell with value == 2 back to 1. Used at the start of
    // UIEntity::updateVisibility() -- the 3-state perspective model promotes
    // freshly-visible cells from 1 (or 0) to 2, and this call handles the
    // per-tick demotion of "was visible last tick" to "discovered".
    void demoteVisible();

private:
    int w_;
    int h_;
    uint8_t* values_;
};
