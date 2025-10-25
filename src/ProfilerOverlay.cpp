#include "GameEngine.h"
#include <sstream>
#include <iomanip>

GameEngine::ProfilerOverlay::ProfilerOverlay(sf::Font& fontRef)
    : font(fontRef), visible(false), updateInterval(10), frameCounter(0)
{
    text.setFont(font);
    text.setCharacterSize(14);
    text.setFillColor(sf::Color::White);
    text.setPosition(10.0f, 10.0f);

    // Semi-transparent dark background
    background.setFillColor(sf::Color(0, 0, 0, 180));
    background.setPosition(5.0f, 5.0f);
}

void GameEngine::ProfilerOverlay::toggle() {
    visible = !visible;
}

void GameEngine::ProfilerOverlay::setVisible(bool vis) {
    visible = vis;
}

bool GameEngine::ProfilerOverlay::isVisible() const {
    return visible;
}

sf::Color GameEngine::ProfilerOverlay::getPerformanceColor(float frameTimeMs) {
    if (frameTimeMs < 16.6f) {
        return sf::Color::Green;  // 60+ FPS
    } else if (frameTimeMs < 33.3f) {
        return sf::Color::Yellow; // 30-60 FPS
    } else {
        return sf::Color::Red;    // <30 FPS
    }
}

std::string GameEngine::ProfilerOverlay::formatFloat(float value, int precision) {
    std::stringstream ss;
    ss << std::fixed << std::setprecision(precision) << value;
    return ss.str();
}

std::string GameEngine::ProfilerOverlay::formatPercentage(float part, float total) {
    if (total <= 0.0f) return "0%";
    float pct = (part / total) * 100.0f;
    return formatFloat(pct, 0) + "%";
}

void GameEngine::ProfilerOverlay::update(const ProfilingMetrics& metrics) {
    if (!visible) return;

    // Only update text every N frames to reduce overhead
    frameCounter++;
    if (frameCounter < updateInterval) {
        return;
    }
    frameCounter = 0;

    std::stringstream ss;
    ss << "McRogueFace Performance Monitor\n";
    ss << "================================\n";

    // Frame time and FPS
    float frameMs = metrics.avgFrameTime;
    ss << "FPS: " << metrics.fps << " (" << formatFloat(frameMs, 1) << "ms/frame)\n";

    // Performance warning
    if (frameMs > 33.3f) {
        ss << "WARNING: Frame time exceeds 30 FPS target!\n";
    }

    ss << "\n";

    // Timing breakdown
    ss << "Frame Time Breakdown:\n";
    ss << "  Grid Render:  " << formatFloat(metrics.gridRenderTime, 1) << "ms ("
       << formatPercentage(metrics.gridRenderTime, frameMs) << ")\n";
    ss << "    Cells: " << metrics.gridCellsRendered << " rendered\n";
    ss << "    Entities: " << metrics.entitiesRendered << " / " << metrics.totalEntities << " drawn\n";

    if (metrics.fovOverlayTime > 0.01f) {
        ss << "    FOV Overlay: " << formatFloat(metrics.fovOverlayTime, 1) << "ms\n";
    }

    if (metrics.entityRenderTime > 0.01f) {
        ss << "  Entity Render: " << formatFloat(metrics.entityRenderTime, 1) << "ms ("
           << formatPercentage(metrics.entityRenderTime, frameMs) << ")\n";
    }

    if (metrics.pythonScriptTime > 0.01f) {
        ss << "  Python:       " << formatFloat(metrics.pythonScriptTime, 1) << "ms ("
           << formatPercentage(metrics.pythonScriptTime, frameMs) << ")\n";
    }

    if (metrics.animationTime > 0.01f) {
        ss << "  Animations:   " << formatFloat(metrics.animationTime, 1) << "ms ("
           << formatPercentage(metrics.animationTime, frameMs) << ")\n";
    }

    ss << "\n";

    // Other metrics
    ss << "Draw Calls: " << metrics.drawCalls << "\n";
    ss << "UI Elements: " << metrics.uiElements << " (" << metrics.visibleElements << " visible)\n";

    // Calculate unaccounted time
    float accountedTime = metrics.gridRenderTime + metrics.entityRenderTime +
                          metrics.pythonScriptTime + metrics.animationTime;
    float unaccountedTime = frameMs - accountedTime;

    if (unaccountedTime > 1.0f) {
        ss << "\n";
        ss << "Other: " << formatFloat(unaccountedTime, 1) << "ms ("
           << formatPercentage(unaccountedTime, frameMs) << ")\n";
    }

    ss << "\n";
    ss << "Press F3 to hide this overlay";

    text.setString(ss.str());

    // Update background size to fit text
    sf::FloatRect textBounds = text.getLocalBounds();
    background.setSize(sf::Vector2f(textBounds.width + 20.0f, textBounds.height + 20.0f));
}

void GameEngine::ProfilerOverlay::render(sf::RenderTarget& target) {
    if (!visible) return;

    target.draw(background);
    target.draw(text);
}
