#ifndef HEADLESS_RENDERER_H
#define HEADLESS_RENDERER_H

#include "Common.h"
#include <memory>
#include <string>

class HeadlessRenderer {
private:
    sf::RenderTexture render_texture;
    
public:
    bool init(int width = 1024, int height = 768);
    sf::RenderTarget& getRenderTarget();
    void saveScreenshot(const std::string& path);
    void display();  // Finalize the current frame
    bool isOpen() const { return true; }  // Always "open" in headless mode
};

#endif // HEADLESS_RENDERER_H