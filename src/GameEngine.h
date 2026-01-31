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
#include "Profiler.h"
#ifndef MCRF_HEADLESS
#include "ImGuiConsole.h"
#include "ImGuiSceneExplorer.h"
#endif
#include <memory>
#include <sstream>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <thread>

/**
 * @brief Performance profiling metrics structure
 *
 * Tracks frame timing, render counts, and detailed timing breakdowns.
 * Used by GameEngine, ProfilerOverlay (F3), and BenchmarkLogger.
 */
struct ProfilingMetrics {
    float frameTime = 0.0f;          // Current frame time in milliseconds
    float avgFrameTime = 0.0f;       // Average frame time over last N frames
    int fps = 0;                     // Frames per second
    int drawCalls = 0;               // Draw calls per frame
    int uiElements = 0;              // Number of UI elements rendered
    int visibleElements = 0;         // Number of visible elements

    // Detailed timing breakdowns (added for profiling system)
    float gridRenderTime = 0.0f;     // Time spent rendering grids (ms)
    float entityRenderTime = 0.0f;   // Time spent rendering entities (ms)
    float fovOverlayTime = 0.0f;     // Time spent rendering FOV overlays (ms)
    float pythonScriptTime = 0.0f;   // Time spent in Python callbacks (ms)
    float animationTime = 0.0f;      // Time spent updating animations (ms)
    float workTime = 0.0f;           // Total work time before display/sleep (ms)

    // Grid-specific metrics
    int gridCellsRendered = 0;       // Number of grid cells drawn this frame
    int entitiesRendered = 0;        // Number of entities drawn this frame
    int totalEntities = 0;           // Total entities in scene

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

        // Reset per-frame timing metrics
        gridRenderTime = 0.0f;
        entityRenderTime = 0.0f;
        fovOverlayTime = 0.0f;
        pythonScriptTime = 0.0f;
        animationTime = 0.0f;

        // Reset per-frame counters
        gridCellsRendered = 0;
        entitiesRendered = 0;
        totalEntities = 0;
    }
};

/**
 * @brief Thread synchronization primitive for safe UI updates from background threads (#219)
 *
 * Allows background Python threads to safely update UI objects by waiting for
 * a "safe window" between frames when the render loop is not iterating the scene graph.
 *
 * Usage from Python:
 *   with mcrfpy.lock():
 *       frame.x = new_value  # Safe to modify UI here
 */
class FrameLock {
private:
    std::mutex mtx;
    std::condition_variable cv;
    bool safe_window = false;
    std::atomic<int> waiting{0};
    std::atomic<int> active{0};

public:
    /**
     * @brief Acquire the lock, blocking until safe window opens
     *
     * Called by mcrfpy.lock().__enter__. Releases GIL while waiting.
     */
    void acquire();

    /**
     * @brief Release the lock
     *
     * Called by mcrfpy.lock().__exit__
     */
    void release();

    /**
     * @brief Open the safe window, allowing waiting threads to proceed
     *
     * Called by render loop between frames
     */
    void openWindow();

    /**
     * @brief Close the safe window, waiting for all active threads to finish
     *
     * Called by render loop before resuming rendering
     */
    void closeWindow();

    /**
     * @brief Check if any threads are waiting for the lock
     */
    bool hasWaiting() const { return waiting.load() > 0; }
};

class GameEngine
{
public:
    // Forward declare nested class so private section can use it
    class ProfilerOverlay;

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

    // #153 - Headless simulation control
    int simulation_time = 0;           // Simulated time in milliseconds (for headless mode)
    bool simulation_clock_paused = false;  // True when simulation is paused (waiting for step())
    
    // Window state tracking
    bool vsync_enabled = false;
    unsigned int framerate_limit = 60;
    
    // Scene transition state
    SceneTransition transition;
    
    // Viewport system
    sf::Vector2u gameResolution{1024, 768};  // Fixed game resolution
    sf::View gameView;                        // View for the game content
    ViewportMode viewportMode = ViewportMode::Fit;

    // Shader intermediate texture (#106) - shared texture for shader rendering
    static std::unique_ptr<sf::RenderTexture> shaderIntermediate;
    static bool shaderIntermediateInitialized;

    // Profiling overlay
    bool showProfilerOverlay = false;         // F3 key toggles this
    int overlayUpdateCounter = 0;             // Only update overlay every N frames
    ProfilerOverlay* profilerOverlay = nullptr; // The actual overlay renderer

#ifndef MCRF_HEADLESS
    // ImGui console overlay
    ImGuiConsole console;
    ImGuiSceneExplorer sceneExplorer;
    bool imguiInitialized = false;
#endif

    // #219 - Thread synchronization for background Python threads
    FrameLock frameLock;
    std::thread::id main_thread_id;  // For detecting if lock() is called from main thread

    void updateViewport();

    void testTimers();

public:
    sf::Clock runtime;
    std::map<std::string, std::shared_ptr<Timer>> timers;
    std::string scene;
    
    // Profiling metrics (struct defined above class)
    ProfilingMetrics metrics;

    GameEngine();
    GameEngine(const McRogueFaceConfig& cfg);
    ~GameEngine();
    Scene* currentScene();
    Scene* getScene(const std::string& name);  // #118: Get scene by name
    std::vector<std::string> getSceneNames() const;  // #136: Get all scene names for explorer
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
    void executeStartupScripts(); // Execute --exec scripts (called once after final engine setup)
    int getFrame() { return currentFrame; }
    float getFrameTime() { return frameTime; }
    sf::View getView() { return visible; }
    // Note: manageTimer() removed in #173 - use Timer objects directly
    std::shared_ptr<Timer> getTimer(const std::string& name);
    void setWindowScale(float);
    bool isHeadless() const { return headless; }
    const McRogueFaceConfig& getConfig() const { return config; }
    void setAutoExitAfterExec(bool enabled) { config.auto_exit_after_exec = enabled; }
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

    // Shader system (#106) - shared intermediate texture for shader rendering
    static sf::RenderTexture& getShaderIntermediate();
    static void initShaderIntermediate(unsigned int width, unsigned int height);
    static bool isShaderIntermediateReady() { return shaderIntermediateInitialized; }

    // #153 - Headless simulation control
    float step(float dt = -1.0f);  // Advance simulation; dt<0 means advance to next event
    int getSimulationTime() const { return simulation_time; }
    void renderScene();  // Force render current scene (for synchronous screenshot)

    // #219 - Thread synchronization for background threads
    FrameLock& getFrameLock() { return frameLock; }
    bool isMainThread() const { return std::this_thread::get_id() == main_thread_id; }

    // global textures for scripts to access
    std::vector<IndexTexture> textures;
    
    // global audio storage
    std::vector<sf::SoundBuffer> sfxbuffers;
    sf::Music music;
    sf::Sound sfx;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> scene_ui(std::string scene);

};

/**
 * @brief Visual overlay that displays real-time profiling metrics
 */
class GameEngine::ProfilerOverlay {
private:
    sf::Font& font;
    sf::Text text;
    sf::RectangleShape background;
    bool visible;
    int updateInterval;
    int frameCounter;

    sf::Color getPerformanceColor(float frameTimeMs);
    std::string formatFloat(float value, int precision = 1);
    std::string formatPercentage(float part, float total);

public:
    ProfilerOverlay(sf::Font& fontRef);
    void toggle();
    void setVisible(bool vis);
    bool isVisible() const;
    void update(const ProfilingMetrics& metrics);
    void render(sf::RenderTarget& target);
};
