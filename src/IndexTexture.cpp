#include "IndexTexture.h"

sf::IntRect IndexTexture::spriteCoordinates(int index) {
    int tx = index % grid_width, ty = index / grid_width;
    return sf::IntRect(tx * grid_size, ty * grid_size, grid_size, grid_size);
}

IndexTexture::IndexTexture (sf::Texture t, int gs, int gw, int gh):
    grid_size(gs), grid_width(gw), grid_height(gh) {
    texture = t;
}
