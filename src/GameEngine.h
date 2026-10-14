#pragma once

#include "Common.h"
#include <climits>
#include "Scene.h"
#include "McRFPy_API.h"
#include "IndexTexture.h"
#include "Timer.h"
#include "PyCallable.h"
#include "McRogueFaceConfig.h"
#include "HeadlessRenderer.h"
#include "SceneTransition.h"
#include "Profiler.h"
// ImGui is only available for SFML builds (not headless, not SDL2)
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
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
    int historyCount = 0;             // #341: frames recorded so far, capped at HISTORY_SIZE

    /**
     * @brief Per-frame values from the last COMPLETED frame (#341).
     *
     * The counters above are live accumulators: they are zeroed at the top of the
     * frame and filled during render(), which runs AFTER every Python callback.
     * A script calling get_metrics() therefore always read zeros. These published
     * copies hold the previous frame's totals, which is what Python should see.
     *
     * In-engine consumers that run after render() (ProfilerOverlay, BenchmarkLogger)
     * keep reading the live values -- they are fresher and already correct there.
     */
    struct PublishedFrame {
        int drawCalls = 0;
        int uiElements = 0;
        int visibleElements = 0;
        int gridCellsRendered = 0;
        int entitiesRendered = 0;
        int totalEntities = 0;
        float gridRenderTime = 0.0f;
        float entityRenderTime = 0.0f;
        float fovOverlayTime = 0.0f;
        float pythonScriptTime = 0.0f;
        float animationTime = 0.0f;
    } published;

    void updateFrameTime(float deltaMs) {
        frameTime = deltaMs;
        frameTimeHistory[historyIndex] = deltaMs;
        historyIndex = (historyIndex + 1) % HISTORY_SIZE;
        if (historyCount < HISTORY_SIZE) ++historyCount;

        // Average over frames actually recorded. Dividing by the full HISTORY_SIZE
        // while the zero-initialized buffer is still filling diluted the average and
        // reported a wildly inflated FPS for the first 60 frames (#341).
        float sum = 0.0f;
        for (int i = 0; i < historyCount; ++i) {
            sum += frameTimeHistory[i];
        }
        avgFrameTime = historyCount > 0 ? sum / historyCount : 0.0f;
        // Saturate: a tiny step(dt) gives a rate past INT_MAX, and that cast is UB (#460).
        const double rate = avgFrameTime > 0 ? 1000.0 / avgFrameTime : 0.0;
        fps = rate >= static_cast<double>(INT_MAX) ? INT_MAX : static_cast<int>(rate);
    }

    // #341/#350: simulation and rendering are separate passes with separate metrics.
    //
    // Rendering costs zero simulation time and can happen at any moment (a screenshot
    // renders arbitrary state without advancing the clock), so the render counters are
    // owned by the render pass and the simulation timings by the step/frame pass.
    // Keeping them separate means a step() cannot wipe the counters from the last
    // render, and a render cannot disturb the simulation clock.

    void beginRender() {
        drawCalls = 0;
        uiElements = 0;
        visibleElements = 0;
        gridCellsRendered = 0;
        entitiesRendered = 0;
        totalEntities = 0;
        gridRenderTime = 0.0f;
        entityRenderTime = 0.0f;
        fovOverlayTime = 0.0f;
    }

    void endRender() {
        published.drawCalls = drawCalls;
        published.uiElements = uiElements;
        published.visibleElements = visibleElements;
        published.gridCellsRendered = gridCellsRendered;
        published.entitiesRendered = entitiesRendered;
        published.totalEntities = totalEntities;
        published.gridRenderTime = gridRenderTime;
        published.entityRenderTime = entityRenderTime;
        published.fovOverlayTime = fovOverlayTime;
    }

    void beginSimFrame() {
        pythonScriptTime = 0.0f;
        animationTime = 0.0f;
    }

    void endSimFrame() {
        published.pythonScriptTime = pythonScriptTime;
        published.animationTime = animationTime;
    }
};

/**
 * @brief Thread synchronization primitive for safe UI updates from background threads (#219)
 *
 * Allows background Python threads to safely update UI objects by waiting for
 * a "safe window" between frames when the main thread is not iterating the scene graph.
 *
 * The window is opened once per frame in BOTH frame paths: doFrame() (windowed, after
 * display()) and runSimFrame() (headless, driven by mcrfpy.step()/advance()). It must
 * stay that way -- a mode that never opens the window blocks lock() holders forever,
 * since acquire() waits on a condition variable with no timeout.
 *
 * Usage from Python:
 *   with mcrfpy.lock():
 *       frame.x = new_value  # Safe to modify UI here
 *
 * Mutation only, inside the block: the main thread is parked until every holder
 * returns, so I/O or a blocking wait under the lock stalls the whole engine.
 */
class FrameLock {
private:
    std::mutex mtx;
    std::condition_variable cv;
    bool safe_window = false;
    bool closing = false;        // #410: closeWindow() has begun; no new admissions
    uint64_t epoch = 0;          // #410: bumped by openWindow(); deferred waiters wait for a change
    int eligible = 0;            // #410: waiters owed service in the current window (under mtx)
    std::atomic<int> waiting{0}; // blocked in acquire(); written under mtx
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
     * Called once per frame by doFrame() (windowed) and runSimFrame() (headless)
     */
    void openWindow();

    /**
     * @brief Close the safe window, waiting for all active threads to finish
     *
     * Called once per frame by doFrame() (windowed) and runSimFrame() (headless),
     * before the main thread resumes
     */
    void closeWindow();

    /**
     * @brief Check if any threads are waiting for the lock
     */
    bool hasWaiting() const { return waiting.load() > 0; }

    /**
     * @brief Does the CALLING thread currently hold the frame lock? (B7 / #395)
     *
     * Per-thread, not global: `active` counts holders across all threads and cannot
     * answer "am I one of them". The depth is a counter rather than a flag because
     * `with mcrfpy.lock():` nests legally -- an inner acquire() succeeds while the
     * safe window is already open, so a flag would clear on the inner release and
     * report a still-holding thread as free.
     *
     * The main thread never acquires (mcrfpy.lock() is a documented no-op there,
     * src/PyLock.cpp), so its depth stays 0 and this correctly answers false. That
     * is why `with mcrfpy.lock(): mcrfpy.step()` on the main thread keeps working:
     * there is no lock held, so there is nothing to re-enter.
     */
    static bool heldByCurrentThread() { return depth() > 0; }

private:
    // Function-local static, not a namespace-scope thread_local: construction on
    // first use with no static-initialisation-order dependency on any other
    // translation unit (same reasoning as mcrf::EngineRandom, #394).
    static int& depth() { static thread_local int d = 0; return d; }
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
    std::map<std::string, std::shared_ptr<Scene>> scenes;
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

// ImGui is only available for SFML builds
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    // ImGui console overlay
    ImGuiConsole console;
    ImGuiSceneExplorer sceneExplorer;
    bool imguiInitialized = false;
#endif

    // #219 - Thread synchronization for background Python threads
    FrameLock frameLock;
    std::thread::id main_thread_id;  // For detecting if lock() is called from main thread

    void updateViewport();

    // #397 - The one timer pass, shared by doFrame() and runSimFrame(): fires every due
    // timer (catching up once per elapsed interval, see Timer::test) and drops stopped ones.
    void testTimers(int now);

    // #396 - The single simulation-frame implementation shared by step() and advance().
    // ms is the exact integer millisecond advance applied to simulation_time; actual_dt
    // is what the frame reports to animations/Scene.update(). They are passed separately
    // so step(float) can keep handing callers the exact float they supplied while
    // advance() keeps the clock on exact integers.
    float runSimFrame(int ms, float actual_dt);

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
    std::shared_ptr<Scene> getSceneShared(const std::string& name);  // #464: for weak links
    std::vector<std::string> getSceneNames() const;  // #136: Get all scene names for explorer
    void changeScene(std::string);
    void changeScene(std::string sceneName, TransitionType transitionType, float duration);
    void createScene(std::string);
    void registerScene(const std::string& name, std::shared_ptr<Scene> scene);
    void unregisterScene(const std::string& name);
    // #468: drop every scene, timer and animation (and the Python objects they hold).
    // Part of McRFPy_API::release_python_references(); the engine runs no frame after.
    void releasePythonReferences();
    void quit();
    void setPause(bool);
    sf::Font & getFont();
    sf::RenderWindow & getWindow();
    // The target frames draw to. Headless creates it here on first use (#451), which needs a
    // display: throws mcrf::NoDisplayError without one.
    sf::RenderTarget & getRenderTarget();
    // The target if it exists yet; nullptr before a headless engine's first frame. Never
    // creates it, so size queries and window checks don't need a display.
    sf::RenderTarget* getRenderTargetPtr() { return render_target; }
    // The size of the render target, whether or not it has been created.
    sf::Vector2u renderSize() const;
    void run();
    void doFrame();  // Single frame update - extracted for Emscripten callback support
    bool isRunning() const { return running; }  // Check if engine should continue running
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

    // #497: the modifiers carried by the key event handled most recently (mcrfpy.keyboard).
    // They come from the event stream, never from polling the hardware, so synthesized
    // events and queued events agree with what on_key is being told. Cleared on focus loss.
    struct KeyModifiers { bool shift = false, ctrl = false, alt = false, system = false; };
    const KeyModifiers& keyModifiers() const { return key_mods; }
    void noteKeyModifiers(const sf::Event& event);
private:
    KeyModifiers key_mods;
public:
    
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
    float step(float dt = -1.0f);  // Advance simulation ONE frame; dt<0 means advance to next event
    // #396 - Advance the simulation clock by exactly `ms` milliseconds, running one
    // simulation frame per timer-interval boundary crossed so no repeating timer skips
    // an interval. Returns the milliseconds actually advanced (0 in windowed mode).
    int advance(int ms);
    int getSimulationTime() const { return simulation_time; }
    void renderScene();  // Force render current scene (for synchronous screenshot)

    // #219 - Thread synchronization for background threads
    FrameLock& getFrameLock() { return frameLock; }
    bool isMainThread() const { return std::this_thread::get_id() == main_thread_id; }

    // #411 - Exactly one thread drives the simulation clock. The first thread to run a
    // frame claims it: the main thread when run() starts the engine's own loop, otherwise
    // the first caller of step()/advance(). Ownership passes on only when the owning
    // thread exits. claimClock() returns false (and claims nothing) when another live
    // thread owns it. ownsClock() is what mcrfpy.lock() asks: the owner never waits on
    // the barrier its own frames open, and before anyone owns the clock the main thread
    // is treated as the owner, as it always was.
    bool claimClock();
    bool ownsClock() const;

    // global textures for scripts to access
    std::vector<IndexTexture> textures;

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
