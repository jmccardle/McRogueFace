#pragma once

#include "Common.h"
#include "Scene.h"
#include "McRFPy_API.h"
#include "IndexTexture.h"
#include "Timer.h"
#include "PyCallable.h"
#include "McRogueFaceConfig.h"
#include "HeadlessRenderer.h"
#include <memory>

class GameEngine
{
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

    sf::Clock runtime;
    //std::map<std::string, Timer> timers;
    std::map<std::string, std::shared_ptr<PyTimerCallable>> timers;
    void testTimers();

public:
    std::string scene;
    GameEngine();
    GameEngine(const McRogueFaceConfig& cfg);
    ~GameEngine();
    Scene* currentScene();
    void changeScene(std::string);
    void createScene(std::string);
    void quit();
    void setPause(bool);
    sf::Font & getFont();
    sf::RenderWindow & getWindow();
    sf::RenderTarget & getRenderTarget();
    sf::RenderTarget* getRenderTargetPtr() { return render_target; }
    void run();
    void sUserInput();
    int getFrame() { return currentFrame; }
    float getFrameTime() { return frameTime; }
    sf::View getView() { return visible; }
    void manageTimer(std::string, PyObject*, int);
    void setWindowScale(float);
    bool isHeadless() const { return headless; }
    void processEvent(const sf::Event& event);

    // global textures for scripts to access
    std::vector<IndexTexture> textures;
    
    // global audio storage
    std::vector<sf::SoundBuffer> sfxbuffers;
    sf::Music music;
    sf::Sound sfx;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> scene_ui(std::string scene);
    
};
