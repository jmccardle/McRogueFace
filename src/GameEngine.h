#pragma once

#include "Common.h"
#include "Scene.h"
#include "McRFPy_API.h"
#include "IndexTexture.h"
#include "Timer.h"
#include "PyCallable.h"
#include "McRogueFaceConfig.h"
#include "HeadlessRenderer.h"
#include "SceneTransition.h"
#include <memory>

class GameEngine
{
public:
    // Viewport modes (moved here so private section can use it)
    enum class ViewportMode {
        Center,     // 1:1 pixels, viewport centered in window
        Stretch,    // viewport size = window size, doesn't respect aspect ratio
        Fit         // maintains original aspect ratio, leaves black bars
    };

private:
    std::unique_ptr<sf::RenderWindow> window;
    std::unique_ptr<HeadlessRenderer> headless_renderer;
    sf::RenderTarget* render_target;
    
    sf::Font font;
    std::map<std::string, Scene*> scenes;
    bool running = true;
    bool paused = false;
    int currentFrame = 0;
    sf::View visible;
    sf::Clock clock;
    float frameTime;
    std::string window_title;
    
    bool headless = false;
    McRogueFaceConfig config;
    bool cleaned_up = false;
    
    // Window state tracking
    bool vsync_enabled = false;
    unsigned int framerate_limit = 60;
    
    // Scene transition state
    SceneTransition transition;
    
    // Viewport system
    sf::Vector2u gameResolution{1024, 768};  // Fixed game resolution
    sf::View gameView;                        // View for the game content
    ViewportMode viewportMode = ViewportMode::Fit;
    
    void updateViewport();

    void testTimers();

public:
    sf::Clock runtime;
    std::map<std::string, std::shared_ptr<Timer>> timers;
    std::string scene;
    
    // Profiling metrics
    struct ProfilingMetrics {
        float frameTime = 0.0f;          // Current frame time in milliseconds
        float avgFrameTime = 0.0f;       // Average frame time over last N frames
        int fps = 0;                     // Frames per second
        int drawCalls = 0;               // Draw calls per frame
        int uiElements = 0;              // Number of UI elements rendered
        int visibleElements = 0;         // Number of visible elements
        
        // Frame time history for averaging
        static constexpr int HISTORY_SIZE = 60;
        float frameTimeHistory[HISTORY_SIZE] = {0};
        int historyIndex = 0;
        
        void updateFrameTime(float deltaMs) {
            frameTime = deltaMs;
            frameTimeHistory[historyIndex] = deltaMs;
            historyIndex = (historyIndex + 1) % HISTORY_SIZE;
            
            // Calculate average
            float sum = 0.0f;
            for (int i = 0; i < HISTORY_SIZE; ++i) {
                sum += frameTimeHistory[i];
            }
            avgFrameTime = sum / HISTORY_SIZE;
            fps = avgFrameTime > 0 ? static_cast<int>(1000.0f / avgFrameTime) : 0;
        }
        
        void resetPerFrame() {
            drawCalls = 0;
            uiElements = 0;
            visibleElements = 0;
        }
    } metrics;
    GameEngine();
    GameEngine(const McRogueFaceConfig& cfg);
    ~GameEngine();
    Scene* currentScene();
    void changeScene(std::string);
    void changeScene(std::string sceneName, TransitionType transitionType, float duration);
    void createScene(std::string);
    void quit();
    void setPause(bool);
    sf::Font & getFont();
    sf::RenderWindow & getWindow();
    sf::RenderTarget & getRenderTarget();
    sf::RenderTarget* getRenderTargetPtr() { return render_target; }
    void run();
    void sUserInput();
    void cleanup(); // Clean up Python references before destruction
    int getFrame() { return currentFrame; }
    float getFrameTime() { return frameTime; }
    sf::View getView() { return visible; }
    void manageTimer(std::string, PyObject*, int);
    std::shared_ptr<Timer> getTimer(const std::string& name);
    void setWindowScale(float);
    bool isHeadless() const { return headless; }
    void processEvent(const sf::Event& event);
    
    // Window property accessors
    const std::string& getWindowTitle() const { return window_title; }
    void setWindowTitle(const std::string& title);
    bool getVSync() const { return vsync_enabled; }
    void setVSync(bool enabled);
    unsigned int getFramerateLimit() const { return framerate_limit; }
    void setFramerateLimit(unsigned int limit);
    
    // Viewport system
    void setGameResolution(unsigned int width, unsigned int height);
    sf::Vector2u getGameResolution() const { return gameResolution; }
    void setViewportMode(ViewportMode mode);
    ViewportMode getViewportMode() const { return viewportMode; }
    std::string getViewportModeString() const;
    sf::Vector2f windowToGameCoords(const sf::Vector2f& windowPos) const;

    // global textures for scripts to access
    std::vector<IndexTexture> textures;
    
    // global audio storage
    std::vector<sf::SoundBuffer> sfxbuffers;
    sf::Music music;
    sf::Sound sfx;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> scene_ui(std::string scene);
    
};
