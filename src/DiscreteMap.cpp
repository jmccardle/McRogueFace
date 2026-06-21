#include "DiscreteMap.h"
#include <cstring>
#include <stdexcept>

DiscreteMap::DiscreteMap(int w, int h, uint8_t fill)
    : w_(w), h_(h), values_(nullptr)
{
    if (w_ <= 0 || h_ <= 0) {
        throw std::invalid_argument("DiscreteMap dimensions must be positive");
    }
    size_t total = static_cast<size_t>(w_) * static_cast<size_t>(h_);
    values_ = new uint8_t[total];
    std::memset(values_, fill, total);
}

DiscreteMap::~DiscreteMap()
{
    delete[] values_;
}

void DiscreteMap::demoteVisible()
{
    size_t total = size();
    for (size_t i = 0; i < total; ++i) {
        if (values_[i] == 2) values_[i] = 1;
    }
}

void DiscreteMap::demoteVisibleRect(int x0, int y0, int x1, int y1)
{
    // Caller guarantees clamped, half-open bounds (see header).
    for (int gy = y0; gy < y1; ++gy) {
        uint8_t* row = values_ + static_cast<size_t>(gy) * w_;
        for (int gx = x0; gx < x1; ++gx) {
            if (row[gx] == 2) row[gx] = 1;
        }
    }
}
