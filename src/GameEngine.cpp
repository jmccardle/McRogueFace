#include "GameEngine.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
#include "PyScene.h"
#include "UITestScene.h"
#include "Resources.h"
#include "Animation.h"
#include "Timer.h"
#include "BenchmarkLogger.h"
// ImGui is only available for SFML builds (not headless, not SDL2)
#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
#include "imgui.h"
#include "imgui-SFML.h"
#endif
#include <cmath>
#include <Python.h>

// Static member definitions for shader intermediate texture (#106)
std::unique_ptr<sf::RenderTexture> GameEngine::shaderIntermediate;
bool GameEngine::shaderIntermediateInitialized = false;

// #219 - FrameLock implementation for thread-safe UI updates

void FrameLock::acquire() {
    waiting++;
    std::unique_lock<std::mutex> lock(mtx);

    // Release GIL while waiting for safe window
    Py_BEGIN_ALLOW_THREADS
    cv.wait(lock, [this]{ return safe_window; });
    Py_END_ALLOW_THREADS

    waiting--;
    active++;
}

void FrameLock::release() {
    std::unique_lock<std::mutex> lock(mtx);
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

    Resources::font.loadFromFile("./assets/JetbrainsMono.ttf");
    Resources::game = this;
    window_title = "McRogueFace Engine";
    
    // Initialize rendering based on headless mode
    if (headless) {
        headless_renderer = std::make_unique<HeadlessRenderer>();
        if (!headless_renderer->init(1024, 768)) {
            throw std::runtime_error("Failed to initialize headless renderer");
        }
        render_target = &headless_renderer->getRenderTarget();
    } else {
        window = std::make_unique<sf::RenderWindow>();
        window->create(sf::VideoMode(1024, 768), window_title, sf::Style::Titlebar | sf::Style::Close | sf::Style::Resize);
        window->setFramerateLimit(60);
        render_target = window.get();

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

    visible = render_target->getDefaultView();
    
    // Initialize the game view
    gameView.setSize(static_cast<float>(gameResolution.x), static_cast<float>(gameResolution.y));
    // Use integer center coordinates for pixel-perfect rendering
    gameView.setCenter(std::floor(gameResolution.x / 2.0f), std::floor(gameResolution.y / 2.0f));
    updateViewport();
    scene = "uitest";
    scenes["uitest"] = new UITestScene(this);

    McRFPy_API::game = this;

    // Initialize profiler overlay
    profilerOverlay = new ProfilerOverlay(Resources::font);
    
    // Only load game.py if no custom script/command/module/exec is specified
    bool should_load_game = config.script_path.empty() && 
                           config.python_command.empty() && 
                           config.python_module.empty() &&
                           config.exec_scripts.empty() &&
                           !config.interactive_mode &&
                           !config.python_mode;
    
    if (should_load_game) {
        std::cerr << "[DEBUG] GameEngine: loading default game.py" << std::endl;
        std::cerr.flush();
        if (!Py_IsInitialized()) {
            std::cerr << "[DEBUG] GameEngine: initializing Python API" << std::endl;
            std::cerr.flush();
            McRFPy_API::api_init();
        }
        std::cerr << "[DEBUG] GameEngine: importing mcrfpy" << std::endl;
        std::cerr.flush();
        McRFPy_API::executePyString("import mcrfpy");
        std::cerr << "[DEBUG] GameEngine: executing scripts/game.py" << std::endl;
        std::cerr.flush();
        McRFPy_API::executeScript("scripts/game.py");
        std::cerr << "[DEBUG] GameEngine: game.py execution complete" << std::endl;
        std::cerr.flush();
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
    for (auto& [name, scene] : scenes) {
        delete scene;
    }
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

Scene* GameEngine::currentScene() { return scenes[scene]; }
Scene* GameEngine::getScene(const std::string& name) {
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
    
    if (transitionType == TransitionType::None || duration <= 0.0f)
    {
        // Immediate scene change
        std::string old_scene = scene;
        scene = sceneName;
        
        // Trigger Python scene lifecycle events
        McRFPy_API::triggerSceneChange(old_scene, sceneName);
    }
    else
    {
        // Start transition
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
sf::Font & GameEngine::getFont() { /*return font; */ return Resources::font; }
sf::RenderWindow & GameEngine::getWindow() { 
    if (!window) {
        throw std::runtime_error("Window not available in headless mode");
    }
    return *window; 
}

sf::RenderTarget & GameEngine::getRenderTarget() { 
    return *render_target; 
}

void GameEngine::createScene(std::string s) { scenes[s] = new PyScene(this); }

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
    frameTime = 0.016f; // Initialize to ~60 FPS
    clock.restart();

#ifdef __EMSCRIPTEN__
    // Browser: use callback-based loop (non-blocking)
    // 0 = use requestAnimationFrame, 1 = simulate infinite loop
    emscripten_set_main_loop_arg(emscriptenMainLoopCallback, this, 0, 1);
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
    // Reset per-frame metrics
    metrics.resetPerFrame();

    currentScene()->update();
    testTimers();

    // Update Python scenes
    {
        ScopedTimer pyTimer(metrics.pythonScriptTime);
        McRFPy_API::updatePythonScenes(frameTime);
    }

    // Update animations (only if frameTime is valid)
    if (frameTime > 0.0f && frameTime < 1.0f) {
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
            render_target->clear();
            transition.render(*render_target);
        }
    }
    else
    {
        // Normal scene rendering
        currentScene()->render();
    }

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

void GameEngine::testTimers()
{
    int now = headless ? simulation_time : runtime.getElapsedTime().asMilliseconds();
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

        // Remove timers that have been stopped (including one-shot timers that fired).
        // The stopped flag is the authoritative marker for "remove from map".
        // Note: Check it->second (current map value) in case callback replaced it.
        if (it->second->isStopped())
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
    std::cout << "scenes[target]: " << (long)(scenes[target]) << std::endl;
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
    if (!headless && window) {
        window->setFramerateLimit(limit);
    }
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
    if (!render_target) return;
    
    auto windowSize = render_target->getSize();
    
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
    
    // Apply the view
    render_target->setView(gameView);
}

sf::Vector2f GameEngine::windowToGameCoords(const sf::Vector2f& windowPos) const {
    if (!render_target) return windowPos;

    // Convert window coordinates to game coordinates using the view
    return render_target->mapPixelToCoords(sf::Vector2i(windowPos), gameView);
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
        // Initialize with default resolution if not already done
        initShaderIntermediate(1024, 768);
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
        simulation_time += min_remaining;
    } else {
        // Advance by specified amount
        actual_dt = dt;
        simulation_time += static_cast<int>(dt * 1000.0f);  // Convert seconds to ms
    }

    // Update animations with the dt in seconds
    if (actual_dt > 0.0f && actual_dt < 10.0f) {  // Sanity check
        AnimationManager::getInstance().update(actual_dt);
    }

    // Test timers with the new simulation time
    auto it = timers.begin();
    while (it != timers.end()) {
        auto timer = it->second;

        // Custom timer test using simulation time instead of runtime
        if (timer && timer->isActive() && timer->hasElapsed(simulation_time)) {
            timer->test(simulation_time);
        }

        // Remove cancelled timers
        if (!it->second->getCallback() || it->second->getCallback() == Py_None) {
            it = timers.erase(it);
        } else {
            it++;
        }
    }

    return actual_dt;
}

// #153 - Force render the current scene (for synchronous screenshots)
void GameEngine::renderScene() {
    if (!render_target) return;

    // Handle scene transitions
    if (transition.type != TransitionType::None) {
        transition.update(0);  // Don't advance transition time, just render current state
        render_target->clear();
        transition.render(*render_target);
    } else {
        // Normal scene rendering
        currentScene()->render();
    }

    // For RenderTexture (headless), we need to call display()
    if (headless && headless_renderer) {
        headless_renderer->display();
    }
}
