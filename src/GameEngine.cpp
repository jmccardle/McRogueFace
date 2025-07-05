#include "GameEngine.h"
#include "ActionCode.h"
#include "McRFPy_API.h"
#include "PyScene.h"
#include "UITestScene.h"
#include "Resources.h"
#include "Animation.h"

GameEngine::GameEngine() : GameEngine(McRogueFaceConfig{})
{
}

GameEngine::GameEngine(const McRogueFaceConfig& cfg)
    : config(cfg), headless(cfg.headless)
{
    Resources::font.loadFromFile("./assets/JetbrainsMono.ttf");
    Resources::game = this;
    window_title = "Crypt of Sokoban - 7DRL 2025, McRogueface Engine";
    
    // Initialize rendering based on headless mode
    if (headless) {
        headless_renderer = std::make_unique<HeadlessRenderer>();
        if (!headless_renderer->init(1024, 768)) {
            throw std::runtime_error("Failed to initialize headless renderer");
        }
        render_target = &headless_renderer->getRenderTarget();
    } else {
        window = std::make_unique<sf::RenderWindow>();
        window->create(sf::VideoMode(1024, 768), window_title, sf::Style::Titlebar | sf::Style::Close);
        window->setFramerateLimit(60);
        render_target = window.get();
    }
    
    visible = render_target->getDefaultView();
    scene = "uitest";
    scenes["uitest"] = new UITestScene(this);
    
    McRFPy_API::game = this;
    
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
    for (auto& [name, scene] : scenes) {
        delete scene;
    }
}

Scene* GameEngine::currentScene() { return scenes[scene]; }
void GameEngine::changeScene(std::string s)
{
    /*std::cout << "Current scene is now '" << s << "'\n";*/
    if (scenes.find(s) != scenes.end())
        scene = s;
    else
        std::cout << "Attempted to change to a scene that doesn't exist (`" << s << "`)" << std::endl;
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
        window->setSize(sf::Vector2u(1024 * multiplier, 768 * multiplier)); // 7DRL 2024: window scaling
    }
    //window.create(sf::VideoMode(1024 * multiplier, 768 * multiplier), window_title, sf::Style::Titlebar | sf::Style::Close);
}

void GameEngine::run()
{
    std::cout << "GameEngine::run() starting main loop..." << std::endl;
    float fps = 0.0;
    frameTime = 0.016f; // Initialize to ~60 FPS
    clock.restart();
    while (running)
    {
        currentScene()->update();
        testTimers();
        
        // Update animations (only if frameTime is valid)
        if (frameTime > 0.0f && frameTime < 1.0f) {
            AnimationManager::getInstance().update(frameTime);
        }
        
        if (!headless) {
            sUserInput();
        }
        if (!paused)
        {
        }
        currentScene()->render();
        
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
        int whole_fps = (int)fps;
        int tenth_fps = int(fps * 100) % 10;
        
        if (!headless && window) {
            window->setTitle(window_title + " " + std::to_string(whole_fps) + "." + std::to_string(tenth_fps) + " FPS");
        }
        
        // In windowed mode, check if window was closed
        if (!headless && window && !window->isOpen()) {
            running = false;
        }
    }
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
            timers[name] = std::make_shared<PyTimerCallable>(Py_None, 1000, runtime.getElapsedTime().asMilliseconds());
            return;
        }
    }
    if (target == NULL || target == Py_None)
    {
        std::cout << "Refusing to initialize timer to None. It's not an error, it's just pointless." << std::endl;
        return;
    }
    timers[name] = std::make_shared<PyTimerCallable>(target, interval, runtime.getElapsedTime().asMilliseconds());
}

void GameEngine::testTimers()
{
    int now = runtime.getElapsedTime().asMilliseconds();
    auto it = timers.begin();
    while (it != timers.end())
    {
        it->second->test(now);
        
        if (it->second->isNone())
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
    // TODO: add resize event to Scene to react; call it after constructor too, maybe
    else if (event.type == sf::Event::Resized) {
        return; // 7DRL short circuit. Resizing manually disabled
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
