#include "HeadlessRenderer.h"
#include <iostream>

bool HeadlessRenderer::init(int width, int height) {
    if (!render_texture.create(width, height)) {
        std::cerr << "Failed to create headless render texture" << std::endl;
        return false;
    }
    return true;
}

sf::RenderTarget& HeadlessRenderer::getRenderTarget() {
    return render_texture;
}

void HeadlessRenderer::saveScreenshot(const std::string& path) {
    sf::Image screenshot = render_texture.getTexture().copyToImage();
    if (!screenshot.saveToFile(path)) {
        std::cerr << "Failed to save screenshot to: " << path << std::endl;
    } else {
        std::cout << "Screenshot saved to: " << path << std::endl;
    }
}

void HeadlessRenderer::display() {
    render_texture.display();
}