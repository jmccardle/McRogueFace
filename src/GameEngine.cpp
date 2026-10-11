#include "GameEngine.h"
#include "Display.h"
#include "ActionCode.h"
#include <sys/stat.h>
#include "McRFPy_API.h"
#include "PyScene.h"
#include "UITestScene.h"
#include "Resources.h"
#include "Animation.h"
#include "Timer.h"
#include "BenchmarkLogger.h"
#include "platform/GLContext.h"
// ImGui is only available for SFML builds (not headless, not SDL2)
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
#include "imgui.h"
#include "imgui-SFML.h"
#endif
#include <cmath>
#include <Python.h>
#include "Audio.h"
#ifdef __EMSCRIPTEN__
#include <emscripten/html5.h>
#endif

// Static member definitions for shader intermediate texture (#106)
std::unique_ptr<sf::RenderTexture> GameEngine::shaderIntermediate;
bool GameEngine::shaderIntermediateInitialized = false;

// #219 - FrameLock implementation for thread-safe UI updates

void FrameLock::acquire() {
    waiting++;

    // #412 - THE GIL IS RELEASED BEFORE `mtx` IS TAKEN, AND RE-ACQUIRED ONLY AFTER IT
    // IS DROPPED. Do not reorder these; it is a lock-ordering constraint, not a
    // performance choice.
    //
    // The previous shape took `mtx` while still holding the GIL and then held `mtx`
    // across Py_END_ALLOW_THREADS (cv.wait re-locks the mutex before returning). With
    // two background threads that is a textbook ABBA inversion:
    //
    //   thread A: woken from cv.wait, HOLDS mtx, blocks acquiring the GIL
    //   thread B: HOLDS the GIL, blocks acquiring mtx
    //
    // Neither can proceed, and because one of them is holding the GIL the entire
    // interpreter stops with it -- the main thread, every timer, every other thread.
    // Verified by backtrace: A parked in take_gil() under FrameLock::acquire(),
    // B parked in pthread_mutex_lock() under FrameLock::acquire().
    //
    // It needed exactly two threads and no unusual usage; one thread never hit it,
    // which is why it survived until FrameLock got contention coverage (#395).
    //
    // With the GIL released for the whole critical section, no thread ever holds `mtx`
    // while blocking on the GIL, so the cycle cannot form. release() and openWindow()
    // take `mtx` while holding the GIL, but they never wait for the GIL, so they are
    // only ever the second edge -- and the other holders (this function and
    // closeWindow(), both GIL-free) release `mtx` inside cv.wait(), so they cannot
    // hold it for long either.
    Py_BEGIN_ALLOW_THREADS
    {
        std::unique_lock<std::mutex> lock(mtx);
        cv.wait(lock, [this]{ return safe_window; });
        // Under `mtx`, so closeWindow()'s two predicates observe the handoff from
        // `waiting` to `active` as a single step and cannot see a moment where this
        // thread counts as neither.
        waiting--;
        active++;
    }
    Py_END_ALLOW_THREADS

    depth()++;  // B7: this thread is now a holder; see heldByCurrentThread()
}

void FrameLock::release() {
    std::unique_lock<std::mutex> lock(mtx);
    depth()--;  // B7: symmetric with acquire(); PyLockContext only ever pairs them
    active--;
    if (active == 0) {
        cv.notify_all();  // Wake up closeWindow() if it's waiting
    }
}

void FrameLock::openWindow() {
    std::lock_guard<std::mutex> lock(mtx);
    safe_window = true;
    cv.notify_all();  // Wake up all waiting threads
}

void FrameLock::closeWindow() {
    std::unique_lock<std::mutex> lock(mtx);
    // First wait for all waiting threads to have entered the critical section
    // (or confirm none were waiting). This prevents the race where we set
    // safe_window=false before a waiting thread can check the condition.
    cv.wait(lock, [this]{ return waiting == 0; });
    // Then wait for all active threads to finish their critical sections
    cv.wait(lock, [this]{ return active == 0; });
    // Now safe to close the window
    safe_window = false;
}

GameEngine::GameEngine() : GameEngine(McRogueFaceConfig{})
{
}

GameEngine::GameEngine(const McRogueFaceConfig& cfg)
    : config(cfg), headless(cfg.headless)
{
    // #219 - Store main thread ID for lock() thread detection
    main_thread_id = std::this_thread::get_id();
    // #411 - A windowed engine's clock belongs to its display loop on this thread from the
    // start; headless leaves it unclaimed until the first step()/advance().
    if (!headless) claimClock();

    // The engine font is loaded by getFont(), on first use (#451).
    Resources::game = this;
    window_title = "McRogueFace Engine";

    // Ensure save/ directory exists for persistent game data
#ifndef __EMSCRIPTEN__
    // Desktop: create save/ in working directory (WASM uses IDBFS mount from JS).
    // Not for -c / -m, which run no game and may be run from any directory (#451).
    const bool runs_game = cfg.python_command.empty() && cfg.python_module.empty();
    struct stat st;
    if (runs_game && stat("save", &st) != 0) {
#ifdef _WIN32
        mkdir("save");
#else
        mkdir("save", 0755);
#endif
    }
#endif
    
    // Initialize rendering based on headless mode
    if (headless) {
        // #451: the render texture is created by the first frame that draws; until then
        // there is no target, and a process that never renders never needs a display.
        headless_renderer = std::make_unique<HeadlessRenderer>(1024, 768);
        render_target = nullptr;
    } else {
        window = std::make_unique<sf::RenderWindow>();
#ifdef __EMSCRIPTEN__
        // Read actual canvas size from HTML template (may be fullscreen or layout-constrained)
        // gameResolution stays at its default (1024x768) - the viewport system maps it to the canvas
        int cw = 1024, ch = 768;
        emscripten_get_canvas_element_size("#canvas", &cw, &ch);
        window->create(sf::VideoMode(cw, ch), window_title, sf::Style::Titlebar | sf::Style::Close | sf::Style::Resize);
#else
        window->create(sf::VideoMode(1024, 768), window_title, sf::Style::Titlebar | sf::Style::Close | sf::Style::Resize);
#endif
        window->setFramerateLimit(60);
        render_target = window.get();

        // Initialize OpenGL function pointers via GLAD for 3D rendering
        if (!mcrf::gl::initGL()) {
            // Non-fatal: 3D features will be unavailable but 2D still works
            fprintf(stderr, "Warning: OpenGL initialization failed. 3D features disabled.\n");
        }

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
        // Initialize ImGui for the window (SFML builds only)
        if (ImGui::SFML::Init(*window)) {
            imguiInitialized = true;
            // Register settings handler before .ini is loaded (happens on first frame)
            ImGuiConsole::registerSettingsHandler();
            // Load JetBrains Mono for crisp console text (will be overridden by .ini if present)
            ImGuiConsole::reloadFont(16.0f);
        }
#endif
    }

    const sf::Vector2u size = renderSize();
    visible = sf::View(sf::FloatRect(0.f, 0.f, static_cast<float>(size.x), static_cast<float>(size.y)));
    
    // Initialize the game view
    gameView.setSize(static_cast<float>(gameResolution.x), static_cast<float>(gameResolution.y));
    // Use integer center coordinates for pixel-perfect rendering
    gameView.setCenter(std::floor(gameResolution.x / 2.0f), std::floor(gameResolution.y / 2.0f));
    updateViewport();
    scene = "uitest";
    scenes["uitest"] = std::make_shared<UITestScene>(this);

    McRFPy_API::game = this;
    mcrf::audio::configure(config.audio_enabled);  // #406: before any Python runs

    // Initialize profiler overlay
    // (Never shown headless, and it would load the font, #451.)
    if (!headless) profilerOverlay = new ProfilerOverlay(getFont());
    
    // Only load game.py if no custom script/command/module/exec is specified
    bool should_load_game = config.script_path.empty() && 
                           config.python_command.empty() && 
                           config.python_module.empty() &&
                           config.exec_scripts.empty() &&
                           !config.interactive_mode &&
                           !config.python_mode;
    
    if (should_load_game) {
        if (!Py_IsInitialized()) {
            McRFPy_API::api_init();
        }
        McRFPy_API::executePyString("import mcrfpy");
        McRFPy_API::executeScript("scripts/game.py", /*main_script=*/true);
    }

    // Note: --exec scripts are NOT executed here.
    // They are executed via executeStartupScripts() after the final engine is set up.
    // This prevents double-execution when main.cpp creates multiple GameEngine instances.

    clock.restart();
    runtime.restart();
}

void GameEngine::executeStartupScripts()
{
    // Execute any --exec scripts in order
    // This is called ONCE from main.cpp after the final engine is set up
    if (!config.exec_scripts.empty()) {
        if (!Py_IsInitialized()) {
            McRFPy_API::api_init();
        }
        McRFPy_API::executePyString("import mcrfpy");

        for (const auto& exec_script : config.exec_scripts) {
            std::cout << "Executing script: " << exec_script << std::endl;
            McRFPy_API::executeScript(exec_script.string());
        }
        std::cout << "All --exec scripts completed" << std::endl;
    }
}

GameEngine::~GameEngine()
{
    cleanup();
    // scenes map uses shared_ptr, will clean up automatically
    scenes.clear();
    delete profilerOverlay;
}

void GameEngine::cleanup()
{
    if (cleaned_up) return;
    cleaned_up = true;
    
    // Clear all animations first (RAII handles invalidation)
    AnimationManager::getInstance().clear();
    
    // Clear Python references before destroying C++ objects
    // Clear all timers (they hold Python callables)
    timers.clear();
    
    // Clear McRFPy_API's reference to this game engine
    if (McRFPy_API::game == this) {
        McRFPy_API::game = nullptr;
    }
    
    // Close window FIRST - ImGui-SFML requires window to be closed before Shutdown()
    // because Shutdown() destroys sf::Cursor objects that the window may reference.
    // See: modules/imgui-sfml/README.md - "Call ImGui::SFML::Shutdown() after window.close()"
    if (window && window->isOpen()) {
        window->close();
    }

    // Shutdown ImGui AFTER window is closed to avoid X11 BadCursor errors
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    if (imguiInitialized) {
        ImGui::SFML::Shutdown();
        imguiInitialized = false;
    }
#endif
}

Scene* GameEngine::currentScene() { return scenes[scene].get(); }
Scene* GameEngine::getScene(const std::string& name) {
    auto it = scenes.find(name);
    return (it != scenes.end()) ? it->second.get() : nullptr;
}

std::shared_ptr<Scene> GameEngine::getSceneShared(const std::string& name) {
    auto it = scenes.find(name);
    return (it != scenes.end()) ? it->second : nullptr;
}

std::vector<std::string> GameEngine::getSceneNames() const {
    std::vector<std::string> names;
    names.reserve(scenes.size());
    for (const auto& [name, scene] : scenes) {
        names.push_back(name);
    }
    return names;
}

void GameEngine::changeScene(std::string s)
{
    changeScene(s, TransitionType::None, 0.0f);
}

void GameEngine::changeScene(std::string sceneName, TransitionType transitionType, float duration)
{
    if (scenes.find(sceneName) == scenes.end())
    {
        std::cout << "Attempted to change to a scene that doesn't exist (`" << sceneName << "`)" << std::endl;
        return;
    }
    
    // #379: a transition needs something to transition FROM. Until the first Python
    // scene is activated the engine sits on the internal "uitest" bootstrap scene, which
    // is not a PyScene and has no Python wrapper -- so mcrfpy.current_scene reports None
    // for it. Because current_scene reports the OUTGOING scene until a transition
    // completes, fading from the bootstrap left current_scene as None for the whole
    // transition, right after the user had assigned it. Nothing meaningful to transition
    // from means change now.
    const bool have_outgoing_scene =
        !scene.empty() &&
        scenes.find(scene) != scenes.end() &&
        dynamic_cast<PyScene*>(scenes[scene].get()) != nullptr;

    if (transitionType == TransitionType::None || duration <= 0.0f || !have_outgoing_scene)
    {
        // Immediate scene change
        std::string old_scene = scene;
        scene = sceneName;

        // Trigger Python scene lifecycle events
        McRFPy_API::triggerSceneChange(old_scene, sceneName);
    }
    else
    {
        mcrf::require_display("a scene transition");  // #451: renders to two textures
        // Start transition with current game resolution
        transition.width = gameResolution.x;
        transition.height = gameResolution.y;
        transition.start(transitionType, scene, sceneName, duration);
        
        // Render current scene to texture
        sf::RenderTarget* original_target = render_target;
        render_target = transition.oldSceneTexture.get();
        transition.oldSceneTexture->clear();
        currentScene()->render();
        transition.oldSceneTexture->display();
        
        // Change to new scene
        std::string old_scene = scene;
        scene = sceneName;
        
        // Render new scene to texture
        render_target = transition.newSceneTexture.get();
        transition.newSceneTexture->clear();
        currentScene()->render();
        transition.newSceneTexture->display();
        
        // Restore original render target and scene
        render_target = original_target;
        scene = old_scene;
    }
}
void GameEngine::quit() { running = false; }
void GameEngine::setPause(bool p) { paused = p; }
sf::Font & GameEngine::getFont() {
    // Loaded on first use, not at startup (#451): -c / -m runs from any directory.
    static bool loaded = false;
    if (!loaded) {
        loaded = true;
        Resources::font.loadFromFile("./assets/JetbrainsMono.ttf");
    }
    return Resources::font;
}
sf::RenderWindow & GameEngine::getWindow() { 
    if (!window) {
        throw std::runtime_error("Window not available in headless mode");
    }
    return *window; 
}

sf::RenderTarget & GameEngine::getRenderTarget() {
    if (!render_target) {
        // #451: headless creates its texture here, on first use. Throws NoDisplayError.
        render_target = &headless_renderer->getRenderTarget();
        render_target->setView(gameView);
    }
    return *render_target;
}

sf::Vector2u GameEngine::renderSize() const {
    if (headless) return headless_renderer->getSize();
    return window->getSize();
}

void GameEngine::createScene(std::string s) { scenes[s] = std::make_shared<PyScene>(this); }

void GameEngine::registerScene(const std::string& name, std::shared_ptr<Scene> scenePtr) {
    scenes[name] = scenePtr;
}

void GameEngine::unregisterScene(const std::string& name) {
    auto it = scenes.find(name);
    if (it != scenes.end()) {
        // If this was the active scene, we need to handle that
        if (scene == name) {
            // Find another scene to switch to, or leave empty
            scene.clear();
            for (const auto& [sceneName, scenePtr] : scenes) {
                if (sceneName != name) {
                    scene = sceneName;
                    break;
                }
            }
        }
        scenes.erase(it);
    }
}

void GameEngine::setWindowScale(float multiplier)
{
    if (!headless && window) {
        window->setSize(sf::Vector2u(gameResolution.x * multiplier, gameResolution.y * multiplier));
        updateViewport();
    }
}

// Emscripten callback support
#ifdef __EMSCRIPTEN__
#include <emscripten.h>

// Static callback for emscripten_set_main_loop_arg
static void emscriptenMainLoopCallback(void* arg) {
    GameEngine* engine = static_cast<GameEngine*>(arg);
    if (!engine->isRunning()) {
        emscripten_cancel_main_loop();
        engine->cleanup();
        return;
    }
    engine->doFrame();
}
#endif

void GameEngine::run()
{
    //std::cout << "GameEngine::run() starting main loop..." << std::endl;

    // #411 - The engine's own loop drives the clock from here on. If a background thread
    // already claimed it with step()/advance() (headless --run-forever), the two would run
    // frame bodies concurrently over one scene graph. Refuse, loudly, rather than race.
    if (!claimClock()) {
        std::cerr << "mcrogueface: the main loop cannot start: a background thread is already "
                     "driving the simulation clock with mcrfpy.step()/advance().\n"
                     "  Only one thread may run frames. Either let the main loop run them, or "
                     "drive the clock from one thread and do not pass --run-forever.\n";
        running = false;
        McRFPy_API::signalPythonException();
        return;
    }

    frameTime = 0.016f; // Initialize to ~60 FPS
    clock.restart();

#ifdef __EMSCRIPTEN__
    // Browser: use callback-based loop (non-blocking)
    // Start with 0 (requestAnimationFrame), then set timing based on framerate_limit
    emscripten_set_main_loop_arg(emscriptenMainLoopCallback, this, 0, 1);

    // Apply framerate_limit setting (0 = use RAF, >0 = use setTimeout)
    if (framerate_limit == 0) {
        emscripten_set_main_loop_timing(EM_TIMING_RAF, 1);
    } else {
        int interval_ms = 1000 / framerate_limit;
        emscripten_set_main_loop_timing(EM_TIMING_SETTIMEOUT, interval_ms);
    }
#else
    // Desktop: traditional blocking loop
    while (running)
    {
        doFrame();
    }

    // Clean up before exiting the run loop
    cleanup();

    // #144: Quick exit to avoid cleanup segfaults in Python/C++ destructor ordering
    // This is a pragmatic workaround - proper cleanup would require careful
    // attention to shared_ptr cycles and Python GC interaction
    std::_Exit(0);
#endif
}

void GameEngine::doFrame()
{
    // #341: simulation metrics belong to this frame's sim pass; render counters are
    // cleared/published around the render pass below.
    metrics.beginSimFrame();

    currentScene()->update();
    testTimers(headless ? simulation_time : runtime.getElapsedTime().asMilliseconds());

    // Update Python scenes
    {
        ScopedTimer pyTimer(metrics.pythonScriptTime);
        McRFPy_API::updatePythonScenes(frameTime);
    }
    mcrf::audio::sweep();  // #440: release sounds that finished playing

    // Update animations with the whole frame time. A long frame (a stall, a load in a
    // callback) is time that passed: dropping it used to leave every running animation
    // permanently behind the clock (#397). An animation clamps at its end value.
    if (frameTime > 0.0f) {
        ScopedTimer animTimer(metrics.animationTime);
        AnimationManager::getInstance().update(frameTime);
    }

    if (!headless) {
        sUserInput();

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
        // Update ImGui (SFML builds only)
        if (imguiInitialized) {
            ImGui::SFML::Update(*window, clock.getElapsedTime());
        }
#endif
    }
    if (!paused)
    {
    }

    metrics.beginRender();  // #341

    // Handle scene transitions
    if (transition.type != TransitionType::None)
    {
        transition.update(frameTime);

        if (transition.isComplete())
        {
            // Transition complete - finalize scene change
            scene = transition.toScene;
            transition.type = TransitionType::None;

            // Trigger Python scene lifecycle events
            McRFPy_API::triggerSceneChange(transition.fromScene, transition.toScene);
        }
        else
        {
            // Render transition
            getRenderTarget().clear();
            transition.render(getRenderTarget());
        }
    }
    else
    {
        // Normal scene rendering
        currentScene()->render();
    }

    metrics.endRender();  // #341: publish this frame's counters for get_metrics()

    // Update and render profiler overlay (if enabled)
    if (profilerOverlay && !headless) {
        profilerOverlay->update(metrics);
        profilerOverlay->render(*render_target);
    }

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
    // Render ImGui overlays (console and scene explorer) - SFML builds only
    if (imguiInitialized && !headless) {
        console.render();
        sceneExplorer.render(*this);
        ImGui::SFML::Render(*window);
    }
#endif

    // Record work time before display (which may block for vsync/framerate limit)
    metrics.workTime = clock.getElapsedTime().asSeconds() * 1000.0f;

    // Display the frame
    // #219 - Release GIL during display() to allow background threads to run
    if (headless) {
        Py_BEGIN_ALLOW_THREADS
        headless_renderer->display();
        Py_END_ALLOW_THREADS
        // Take screenshot if requested
        if (config.take_screenshot) {
            headless_renderer->saveScreenshot(config.screenshot_path.empty() ? "screenshot.png" : config.screenshot_path);
            config.take_screenshot = false; // Only take one screenshot
        }
    } else {
        Py_BEGIN_ALLOW_THREADS
        window->display();
        Py_END_ALLOW_THREADS
    }

    // #219 - Safe window for background threads to modify UI
    // This runs AFTER display() but BEFORE the next frame's processing
    if (frameLock.hasWaiting()) {
        frameLock.openWindow();
        // Release GIL so waiting threads can proceed with their mcrfpy.lock() blocks
        Py_BEGIN_ALLOW_THREADS
        frameLock.closeWindow();  // Wait for all lock holders to complete
        Py_END_ALLOW_THREADS
    }

    currentFrame++;
    frameTime = clock.restart().asSeconds();
    float fps = 1 / frameTime;

    // Update profiling metrics
    metrics.updateFrameTime(frameTime * 1000.0f); // Convert to milliseconds

    // Record frame data for benchmark logging (if running)
    g_benchmarkLogger.recordFrame(metrics);

    int whole_fps = metrics.fps;
    int tenth_fps = (metrics.fps * 10) % 10;
    (void)whole_fps; (void)tenth_fps; (void)fps; // Suppress unused variable warnings

    if (!headless && window) {
        window->setTitle(window_title);
    }

    // In windowed mode, check if window was closed
    if (!headless && window && !window->isOpen()) {
        running = false;
    }

    // In headless exec mode, auto-exit when no timers remain
    if (config.auto_exit_after_exec && timers.empty()) {
        running = false;
    }

    // Check if a Python exception has signaled exit
    if (McRFPy_API::shouldExit()) {
        running = false;
    }
}

std::shared_ptr<Timer> GameEngine::getTimer(const std::string& name)
{
    auto it = timers.find(name);
    if (it != timers.end()) {
        return it->second;
    }
    return nullptr;
}

// Note: manageTimer() removed in #173 - use Timer objects directly

// #411 - The clock owner. File-static rather than an engine member because the release
// runs from a thread_local destructor at thread exit, which can outlive the engine.
namespace {
std::atomic<std::thread::id> clock_owner{};

struct ClockOwnerRelease {
    bool owns = false;
    ~ClockOwnerRelease() {
        if (!owns) return;
        std::thread::id me = std::this_thread::get_id();
        clock_owner.compare_exchange_strong(me, std::thread::id{});
    }
};
thread_local ClockOwnerRelease clock_owner_release;
}

bool GameEngine::claimClock()
{
    const std::thread::id me = std::this_thread::get_id();
    std::thread::id expected{};
    if (clock_owner.compare_exchange_strong(expected, me)) {
        clock_owner_release.owns = true;
        return true;
    }
    return expected == me;
}

bool GameEngine::ownsClock() const
{
    const std::thread::id owner = clock_owner.load();
    if (owner == std::thread::id{}) return isMainThread();
    return owner == std::this_thread::get_id();
}

void GameEngine::testTimers(int now)
{
    auto it = timers.begin();
    while (it != timers.end())
    {
        // Keep a local copy of the timer to prevent use-after-free.
        // If the callback calls stop(), the timer may be marked for removal,
        // but we need the Timer object to survive until test() returns.
        auto timer = it->second;

        // Skip stopped timers (they'll be removed below)
        if (!timer->isStopped()) {
            timer->test(now);
        }

        // Remove timers that have been stopped (including one-shot timers that fired), and
        // any whose callback was cleared. Before #397 the headless pass checked only the
        // callback and this one only `stopped`, so a fired one-shot stayed in the headless map.
        // Note: Check it->second (current map value) in case callback replaced it.
        if (it->second->isStopped() || it->second->getCallback() == Py_None)
        {
            it = timers.erase(it);
        }
        else
        {
            it++;
        }
    }
}

void GameEngine::processEvent(const sf::Event& event)
{
    std::string actionType;
    int actionCode = 0;

    if (event.type == sf::Event::Closed) { running = false; return; }

    // Handle F3 for profiler overlay toggle
    if (event.type == sf::Event::KeyPressed && event.key.code == sf::Keyboard::F3) {
        if (profilerOverlay) {
            profilerOverlay->toggle();
        }
        return;
    }
    // Handle window resize events
    else if (event.type == sf::Event::Resized) {
        // Update the viewport to handle the new window size
        updateViewport();
        
        // Notify Python scenes about the resize
        McRFPy_API::triggerResize(sf::Vector2u(event.size.width, event.size.height));
    }

    else if (event.type == sf::Event::KeyPressed || event.type == sf::Event::MouseButtonPressed || event.type == sf::Event::MouseWheelScrolled) actionType = "start";
    else if (event.type == sf::Event::KeyReleased || event.type == sf::Event::MouseButtonReleased) actionType = "end";

    if (event.type == sf::Event::MouseButtonPressed || event.type == sf::Event::MouseButtonReleased)
        actionCode = ActionCode::keycode(event.mouseButton.button);
    else if (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased)
        actionCode = ActionCode::keycode(event.key.code);
    else if (event.type == sf::Event::MouseWheelScrolled)
    {
        if (event.mouseWheelScroll.wheel == sf::Mouse::VerticalWheel)
        {
            int delta = 1;
            if (event.mouseWheelScroll.delta < 0) delta = -1;
            actionCode = ActionCode::keycode(event.mouseWheelScroll.wheel, delta );
        }
    }
    // #140 - Handle mouse movement for hover detection
    else if (event.type == sf::Event::MouseMoved)
    {
        // Cast to PyScene to call do_mouse_hover
        if (auto* pyscene = dynamic_cast<PyScene*>(currentScene())) {
            pyscene->do_mouse_hover(event.mouseMove.x, event.mouseMove.y);
        }
        return;
    }
    // #363 - The cursor left the window. No further MouseMoved will arrive, so
    // whatever is hovered must be exited now or it stays hovered forever.
    //
    // #367 - Losing focus strands hover identically. The cursor may still be physically
    // over the window, but an unfocused window is delivered no MouseMoved, so the hover
    // walk never runs and the last hovered drawable stays lit while the game sits in the
    // background. Once unfocused we genuinely do not know where the pointer is, and
    // "hovering nothing" is the only truthful state to hold; the next MouseMoved after
    // focus returns restores hover.
    else if (event.type == sf::Event::MouseLeft || event.type == sf::Event::LostFocus)
    {
        if (auto* pyscene = dynamic_cast<PyScene*>(currentScene())) {
            pyscene->do_mouse_leave();
        }
        return;
    }
    else
        return;

    if (currentScene()->hasAction(actionCode))
    {
        std::string name = currentScene()->action(actionCode);
        currentScene()->doAction(name, actionType);
    }
    else if (currentScene()->key_callable && !currentScene()->key_callable->isNone() &&
             (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased))
    {
        // Property-assigned handler (scene.on_key = callable)
        currentScene()->key_callable->call(ActionCode::key_str(event.key.code), actionType);
    }
    else if (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased)
    {
        // Try subclass on_key method if no property handler is set
        McRFPy_API::triggerKeyEvent(ActionCode::key_str(event.key.code), actionType);
    }
}

void GameEngine::sUserInput()
{
    sf::Event event;
    while (window && window->pollEvent(event))
    {
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
        // Process event through ImGui first (SFML builds only)
        if (imguiInitialized) {
            ImGui::SFML::ProcessEvent(*window, event);
        }

        // Handle grave/tilde key for console toggle (before other processing)
        if (event.type == sf::Event::KeyPressed && event.key.code == sf::Keyboard::Grave) {
            console.toggle();
            continue;  // Don't pass grave key to game
        }

        // Handle F4 for scene explorer toggle
        if (event.type == sf::Event::KeyPressed && event.key.code == sf::Keyboard::F4) {
            sceneExplorer.toggle();
            continue;  // Don't pass F4 to game
        }

        // If console wants keyboard, don't pass keyboard events to game
        if (console.wantsKeyboardInput()) {
            // Still process non-keyboard events (mouse, window close, etc.)
            if (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased ||
                event.type == sf::Event::TextEntered) {
                continue;
            }
        }
#endif

        processEvent(event);
    }
}

std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> GameEngine::scene_ui(std::string target)
{
    /* 
    // facts about maps
    // You just can't do this during scenes["new_menu"] being assigned.
    std::cout << "Current scene is: " << scene << ". Searching for: " << target << ".\n";
    std::cout << "scenes.size(): " << scenes.size() << std::endl;
    std::cout << "scenes.count(target): " << scenes.count(target) << std::endl;
    std::cout << "scenes.find(target): " << std::distance(scenes.begin(), scenes.find(target)) << std::endl;
    std::cout << "iterators: " << std::distance(scenes.begin(), scenes.begin()) << " " <<
        std::distance(scenes.begin(), scenes.end()) << std::endl;
    std::cout << "scenes.contains(target): " << scenes.contains(target) << std::endl;
    std::cout << "scenes[target]: " << (long)(scenes[target].get()) << std::endl;
    */
    if (scenes.count(target) == 0) return NULL;
    return scenes[target]->ui_elements;
}

void GameEngine::setWindowTitle(const std::string& title)
{
    window_title = title;
    if (!headless && window) {
        window->setTitle(title);
    }
}

void GameEngine::setVSync(bool enabled)
{
    vsync_enabled = enabled;
    if (!headless && window) {
        window->setVerticalSyncEnabled(enabled);
    }
}

void GameEngine::setFramerateLimit(unsigned int limit)
{
    framerate_limit = limit;

#ifdef __EMSCRIPTEN__
    // For Emscripten: change loop timing dynamically
    if (limit == 0) {
        // Unlimited: use requestAnimationFrame (browser-controlled, typically 60fps)
        emscripten_set_main_loop_timing(EM_TIMING_RAF, 1);
    } else {
        // Specific FPS: use setTimeout with calculated interval
        int interval_ms = 1000 / limit;
        emscripten_set_main_loop_timing(EM_TIMING_SETTIMEOUT, interval_ms);
    }
#else
    // For desktop: use SFML's setFramerateLimit
    if (!headless && window) {
        window->setFramerateLimit(limit);
    }
#endif
}

void GameEngine::setGameResolution(unsigned int width, unsigned int height) {
    gameResolution = sf::Vector2u(width, height);
    gameView.setSize(static_cast<float>(width), static_cast<float>(height));
    // Use integer center coordinates for pixel-perfect rendering
    gameView.setCenter(std::floor(width / 2.0f), std::floor(height / 2.0f));
    updateViewport();
}

void GameEngine::setViewportMode(ViewportMode mode) {
    viewportMode = mode;
    updateViewport();
}

std::string GameEngine::getViewportModeString() const {
    switch (viewportMode) {
        case ViewportMode::Center:  return "center";
        case ViewportMode::Stretch: return "stretch";
        case ViewportMode::Fit:     return "fit";
    }
    return "unknown";
}

void GameEngine::updateViewport() {
    auto windowSize = renderSize();
    
    switch (viewportMode) {
        case ViewportMode::Center: {
            // 1:1 pixels, centered in window
            float viewportWidth = std::min(static_cast<float>(gameResolution.x), static_cast<float>(windowSize.x));
            float viewportHeight = std::min(static_cast<float>(gameResolution.y), static_cast<float>(windowSize.y));
            
            // Floor offsets to ensure integer pixel alignment
            float offsetX = std::floor((windowSize.x - viewportWidth) / 2.0f);
            float offsetY = std::floor((windowSize.y - viewportHeight) / 2.0f);
            
            gameView.setViewport(sf::FloatRect(
                offsetX / windowSize.x,
                offsetY / windowSize.y,
                viewportWidth / windowSize.x,
                viewportHeight / windowSize.y
            ));
            break;
        }
        
        case ViewportMode::Stretch: {
            // Fill entire window, ignore aspect ratio
            gameView.setViewport(sf::FloatRect(0, 0, 1, 1));
            break;
        }
        
        case ViewportMode::Fit: {
            // Maintain aspect ratio with black bars
            float windowAspect = static_cast<float>(windowSize.x) / windowSize.y;
            float gameAspect = static_cast<float>(gameResolution.x) / gameResolution.y;
            
            float viewportWidth, viewportHeight;
            float offsetX = 0, offsetY = 0;
            
            if (windowAspect > gameAspect) {
                // Window is wider - black bars on sides
                // Calculate viewport size in pixels and floor for pixel-perfect scaling
                float pixelHeight = static_cast<float>(windowSize.y);
                float pixelWidth = std::floor(pixelHeight * gameAspect);
                
                viewportHeight = 1.0f;
                viewportWidth = pixelWidth / windowSize.x;
                offsetX = (1.0f - viewportWidth) / 2.0f;
            } else {
                // Window is taller - black bars on top/bottom
                // Calculate viewport size in pixels and floor for pixel-perfect scaling
                float pixelWidth = static_cast<float>(windowSize.x);
                float pixelHeight = std::floor(pixelWidth / gameAspect);
                
                viewportWidth = 1.0f;
                viewportHeight = pixelHeight / windowSize.y;
                offsetY = (1.0f - viewportHeight) / 2.0f;
            }
            
            gameView.setViewport(sf::FloatRect(offsetX, offsetY, viewportWidth, viewportHeight));
            break;
        }
    }
    
    // Apply the view (a headless target not yet created gets it when it is, #451)
    if (render_target) render_target->setView(gameView);
}

sf::Vector2f GameEngine::windowToGameCoords(const sf::Vector2f& windowPos) const {
    // Convert window coordinates to game coordinates using the view
    if (render_target) return render_target->mapPixelToCoords(sf::Vector2i(windowPos), gameView);

    // #451: a headless target that doesn't exist yet. The same mapping
    // sf::RenderTarget::mapPixelToCoords does, from the size it will have.
    const sf::Vector2u size = renderSize();
    const sf::FloatRect vp = gameView.getViewport();
    const float left = static_cast<int>(0.5f + size.x * vp.left);
    const float top = static_cast<int>(0.5f + size.y * vp.top);
    const float width = static_cast<int>(0.5f + size.x * vp.width);
    const float height = static_cast<int>(0.5f + size.y * vp.height);
    const sf::Vector2i pixel(windowPos);
    const sf::Vector2f normalized(-1.f + 2.f * (pixel.x - left) / width,
                                  1.f - 2.f * (pixel.y - top) / height);
    return gameView.getInverseTransform().transformPoint(normalized);
}

// #106 - Shader intermediate texture: shared texture for shader rendering
void GameEngine::initShaderIntermediate(unsigned int width, unsigned int height) {
    if (!sf::Shader::isAvailable()) {
        std::cerr << "GameEngine: Shaders not available, skipping intermediate texture init" << std::endl;
        return;
    }

    if (!shaderIntermediate) {
        shaderIntermediate = std::make_unique<sf::RenderTexture>();
    }

    if (!shaderIntermediate->create(width, height)) {
        std::cerr << "GameEngine: Failed to create shader intermediate texture ("
                  << width << "x" << height << ")" << std::endl;
        shaderIntermediate.reset();
        shaderIntermediateInitialized = false;
        return;
    }

    shaderIntermediate->setSmooth(false);  // Pixel-perfect rendering
    shaderIntermediateInitialized = true;
}

sf::RenderTexture& GameEngine::getShaderIntermediate() {
    if (!shaderIntermediateInitialized) {
        // Initialize with game resolution from the engine instance
        unsigned int w = 1024, h = 768;
        if (Resources::game) {
            auto res = Resources::game->getGameResolution();
            w = res.x;
            h = res.y;
        }
        initShaderIntermediate(w, h);
    }
    return *shaderIntermediate;
}

// #153 - Headless simulation control: step() advances simulation time
float GameEngine::step(float dt) {
    // In windowed mode, step() is a no-op
    if (!headless) {
        return 0.0f;
    }

    float actual_dt;
    int advance_ms;

    if (dt < 0) {
        // dt < 0 means "advance to next event"
        // Find the minimum time until next timer fires
        int min_remaining = INT_MAX;

        for (auto& [name, timer] : timers) {
            if (timer && timer->isActive()) {
                int remaining = timer->getRemaining(simulation_time);
                if (remaining > 0 && remaining < min_remaining) {
                    min_remaining = remaining;
                }
            }
        }

        // Also consider animations - find minimum time to completion
        // AnimationManager doesn't expose this, so we'll just step by 1ms if no timers
        if (min_remaining == INT_MAX) {
            // No pending timers - check if there are active animations
            // Step by a small amount to advance any running animations
            min_remaining = 1;  // 1ms minimum step
        }

        actual_dt = static_cast<float>(min_remaining) / 1000.0f;  // Convert to seconds
        advance_ms = min_remaining;
    } else {
        // Advance by specified amount
        actual_dt = dt;
        advance_ms = static_cast<int>(dt * 1000.0f);  // Convert seconds to ms
    }

    return runSimFrame(advance_ms, actual_dt);
}

// #396 - Advance the clock by exactly `ms` and run ONE simulation frame.
//
// step() and advance() share this body so there is exactly one place that moves
// simulation_time and exactly one definition of "a simulation frame". `ms` is applied to
// the clock as an integer (no float round-trip, so advance() lands on timer boundaries
// exactly), while `dt_seconds` is the value the frame reports to animations and
// Scene.update() -- step(float) still passes through the caller's own float unchanged.
float GameEngine::runSimFrame(int ms, float actual_dt) {
    simulation_time += ms;

    // #350: step() is a full SIMULATION frame -- everything doFrame() does except
    // render and input, which are deliberately not on the clock (render costs zero
    // simulation time; see renderScene()). Previously step() advanced only animations
    // and timers, so under step() a Scene.update() override never fired, scene
    // transitions never progressed or completed, and current_frame never advanced --
    // headless behaved measurably differently from a real frame.
    metrics.beginSimFrame();

    // C++ scene update
    currentScene()->update();

    // Timers run on simulation_time (not runtime): step() is the deterministic headless
    // clock, which is the whole point of driving time explicitly from a test.
    testTimers(simulation_time);

    // Python Scene.update(dt) hook -- the originally-filed omission
    {
        ScopedTimer pyTimer(metrics.pythonScriptTime);
        McRFPy_API::updatePythonScenes(actual_dt);
    }
    mcrf::audio::sweep();  // #440: release sounds that finished playing

    // Update animations with the whole dt. The old `< 10.0f` "sanity check" made a wide
    // step() silently drop a running animation's progress (#397).
    if (actual_dt > 0.0f) {
        ScopedTimer animTimer(metrics.animationTime);
        AnimationManager::getInstance().update(actual_dt);
    }

    // Advance scene transitions, and finalize them when complete. Without this a
    // transition started headlessly would never end, and the scene never changed.
    if (transition.type != TransitionType::None) {
        transition.update(actual_dt);
        if (transition.isComplete()) {
            scene = transition.toScene;
            transition.type = TransitionType::None;
            McRFPy_API::triggerSceneChange(transition.fromScene, transition.toScene);
        }
    }

    metrics.endSimFrame();
    metrics.updateFrameTime(actual_dt * 1000.0f);  // ms

    // #219 safe window for background threads, in headless too.
    //
    // doFrame() opens this window after display() (see renderScene's caller); a
    // simulation frame never gets there, so before this a background thread that
    // entered `with mcrfpy.lock():` under a step()/advance()-driven main loop blocked
    // in FrameLock::acquire() forever -- the condition variable it waits on was only
    // ever signalled from the render path. Headless is the mode embedders drive a
    // world from, so it is precisely the mode where a bus/worker thread needs to
    // hand mutations back safely.
    //
    // Placed after the frame's work and before currentFrame++, matching doFrame():
    // lock holders observe a fully-settled frame, and the main thread parks here (GIL
    // released) until every holder is done. Guarded by hasWaiting(), so the no-threads
    // case is one relaxed atomic load per frame.
    if (frameLock.hasWaiting()) {
        frameLock.openWindow();
        Py_BEGIN_ALLOW_THREADS
        frameLock.closeWindow();  // Wait for all lock holders to complete
        Py_END_ALLOW_THREADS
    }

    currentFrame++;

    return actual_dt;
}

// #396 - Advance the clock by exactly `ms`, honoring EVERY timer interval in the span.
//
// step(dt) is one frame, and one frame tests each timer at most once: a single step of
// 10000ms fires a 1000ms repeating timer ONCE, not ten times, and (because Timer::test
// stamps last_ran = now) silently re-phases it to the end of the step. That makes a wide
// step lossy -- fine for "run a frame", wrong for "let ten seconds pass".
//
// advance() closes that gap by walking the span boundary by boundary: it repeatedly finds
// the nearest pending timer deadline inside the remaining span and runs one simulation
// frame that lands exactly on it, then a final frame for any residual. Because each frame
// lands exactly on last_ran + interval, Timer::test's last_ran = now is exact and no phase
// drift accumulates -- the residual is carried, not discarded.
//
// This is a loop over step()'s own frame body, NOT a second clock: simulation_time is
// still the only counter and runSimFrame() is still the only thing that moves it.
int GameEngine::advance(int ms) {
    // In windowed mode, advance() is a no-op (same contract as step())
    if (!headless) {
        return 0;
    }
    if (ms <= 0) {
        // Zero (or nothing) to advance: the clock does not move and no frame runs.
        // Use step(0.0) to run a frame without advancing time.
        return 0;
    }

    const int target = simulation_time + ms;

    while (simulation_time < target) {
        // Nearest timer deadline strictly ahead of now, clamped to the end of the span.
        int next = target;
        for (auto& [name, timer] : timers) {
            if (timer && timer->isActive()) {
                int remaining = timer->getRemaining(simulation_time);
                // remaining <= 0 means the timer is ALREADY overdue at the current
                // instant; it is not a future boundary. It fires at the end of the next
                // frame regardless, which is no later than it would have fired anyway.
                if (remaining > 0 && simulation_time + remaining < next) {
                    next = simulation_time + remaining;
                }
            }
        }

        // next > simulation_time always (target > simulation_time in the loop condition,
        // and every candidate boundary uses remaining > 0), so this terminates.
        const int delta = next - simulation_time;
        runSimFrame(delta, static_cast<float>(delta) / 1000.0f);
    }

    return ms;
}

// #153 - Force render the current scene (for synchronous screenshots)
// Render the current state on demand, advancing NO simulation time (#341/#350).
// Rendering is orthogonal to the clock: any state can be drawn at any moment. This is
// the path a screenshot takes, and -- since step() deliberately never renders -- it is
// how a headless script gets real render metrics without the clock moving.
void GameEngine::renderScene() {
    sf::RenderTarget& target = getRenderTarget();  // #451: created here when headless

    metrics.beginRender();

    // Handle scene transitions
    if (transition.type != TransitionType::None) {
        transition.update(0);  // Don't advance transition time, just render current state
        target.clear();
        transition.render(target);
    } else {
        // Normal scene rendering
        currentScene()->render();
    }

    metrics.endRender();

    // For RenderTexture (headless), we need to call display()
    if (headless && headless_renderer) {
        headless_renderer->display();
    }
}
