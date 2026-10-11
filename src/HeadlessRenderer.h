#ifndef HEADLESS_RENDERER_H
#define HEADLESS_RENDERER_H

#include "Common.h"
#include <memory>
#include <string>

// The --headless render target. Its texture is a GL resource, which the SFML build can only
// create with a display, so it is created on first use, not at startup (#451): a headless
// process that never renders never needs one.
class HeadlessRenderer {
private:
    std::unique_ptr<sf::RenderTexture> render_texture;
    sf::Vector2u size;

public:
    explicit HeadlessRenderer(unsigned width = 1024, unsigned height = 768) : size(width, height) {}
    sf::Vector2u getSize() const { return size; }
    bool created() const { return render_texture != nullptr; }
    // Creates the texture. Throws mcrf::NoDisplayError when there is no display.
    sf::RenderTarget& getRenderTarget();
    void saveScreenshot(const std::string& path);
    void display();  // Finalize the current frame
    bool isOpen() const { return true; }  // Always "open" in headless mode
};

#endif // HEADLESS_RENDERER_H
