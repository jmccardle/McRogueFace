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
