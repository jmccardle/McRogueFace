#include "IndexTexture.h"

sf::IntRect IndexTexture::spriteCoordinates(int index) {
    int tx = index % grid_width, ty = index / grid_width;
    return sf::IntRect(tx * grid_size, ty * grid_size, grid_size, grid_size);
}
