#include "HeadlessRenderer.h"
#include "Display.h"
#include <iostream>
#include <stdexcept>

sf::RenderTarget& HeadlessRenderer::getRenderTarget() {
    if (!render_texture) {
        mcrf::require_display("rendering");
        auto texture = std::make_unique<sf::RenderTexture>();
        if (!texture->create(size.x, size.y)) {
            throw std::runtime_error("Failed to create headless render texture");
        }
        render_texture = std::move(texture);
    }
    return *render_texture;
}

void HeadlessRenderer::saveScreenshot(const std::string& path) {
    auto& texture = static_cast<sf::RenderTexture&>(getRenderTarget());
    sf::Image screenshot = texture.getTexture().copyToImage();
    if (!screenshot.saveToFile(path)) {
        std::cerr << "Failed to save screenshot to: " << path << std::endl;
    } else {
        std::cout << "Screenshot saved to: " << path << std::endl;
    }
}

void HeadlessRenderer::display() {
    if (render_texture) render_texture->display();
}
