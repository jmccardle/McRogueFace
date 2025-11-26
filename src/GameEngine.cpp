#include "GameEngine.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
#include "PyScene.h"
#include "UITestScene.h"
#include "Resources.h"
#include "Animation.h"
#include "Timer.h"
#include <cmath>

GameEngine::GameEngine() : GameEngine(McRogueFaceConfig{})
{
}

GameEngine::GameEngine(const McRogueFaceConfig& cfg)
    : config(cfg), headless(cfg.headless)
{
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
        if (!Py_IsInitialized()) {
            McRFPy_API::api_init();
        }
        McRFPy_API::executePyString("import mcrfpy");
        McRFPy_API::executeScript("scripts/game.py");
    }
    
    // Execute any --exec scripts in order
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

    clock.restart();
    runtime.restart();
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
    
    // Force close the window if it's still open
    if (window && window->isOpen()) {
        window->close();
    }
}

Scene* GameEngine::currentScene() { return scenes[scene]; }
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

void GameEngine::run()
{
    //std::cout << "GameEngine::run() starting main loop..." << std::endl;
    float fps = 0.0;
    frameTime = 0.016f; // Initialize to ~60 FPS
    clock.restart();
    while (running)
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

        // Display the frame
        if (headless) {
            headless_renderer->display();
            // Take screenshot if requested
            if (config.take_screenshot) {
                headless_renderer->saveScreenshot(config.screenshot_path.empty() ? "screenshot.png" : config.screenshot_path);
                config.take_screenshot = false; // Only take one screenshot
            }
        } else {
            window->display();
        }
        
        currentFrame++;
        frameTime = clock.restart().asSeconds();
        fps = 1 / frameTime;
        
        // Update profiling metrics
        metrics.updateFrameTime(frameTime * 1000.0f); // Convert to milliseconds
        
        int whole_fps = metrics.fps;
        int tenth_fps = (metrics.fps * 10) % 10;
        
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
    
    // Clean up before exiting the run loop
    cleanup();
}

std::shared_ptr<Timer> GameEngine::getTimer(const std::string& name)
{
    auto it = timers.find(name);
    if (it != timers.end()) {
        return it->second;
    }
    return nullptr;
}

void GameEngine::manageTimer(std::string name, PyObject* target, int interval)
{
    auto it = timers.find(name);
    if (it != timers.end()) // overwrite existing
    {
        if (target == NULL || target == Py_None)
        {
            // Delete: Overwrite existing timer with one that calls None. This will be deleted in the next timer check
            // see gitea issue #4: this allows for a timer to be deleted during its own call to itself
            timers[name] = std::make_shared<Timer>(Py_None, 1000, runtime.getElapsedTime().asMilliseconds());
            return;
        }
    }
    if (target == NULL || target == Py_None)
    {
        std::cout << "Refusing to initialize timer to None. It's not an error, it's just pointless." << std::endl;
        return;
    }
    timers[name] = std::make_shared<Timer>(target, interval, runtime.getElapsedTime().asMilliseconds());
}

void GameEngine::testTimers()
{
    int now = runtime.getElapsedTime().asMilliseconds();
    auto it = timers.begin();
    while (it != timers.end())
    {
        it->second->test(now);
        
        // Remove timers that have been cancelled or are one-shot and fired
        if (!it->second->getCallback() || it->second->getCallback() == Py_None)
        {
            it = timers.erase(it);
        }
        else
            it++;
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
        McRFPy_API::triggerResize(event.size.width, event.size.height);
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
    else
        return;

    if (currentScene()->hasAction(actionCode))
    {
        std::string name = currentScene()->action(actionCode);
        currentScene()->doAction(name, actionType);
    }
    else if (currentScene()->key_callable && 
             (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased))
    {
        currentScene()->key_callable->call(ActionCode::key_str(event.key.code), actionType);
    }
}

void GameEngine::sUserInput()
{
    sf::Event event;
    while (window && window->pollEvent(event))
    {
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
