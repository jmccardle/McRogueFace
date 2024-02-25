#pragma once

#include "Common.h"
#include "Entity.h"
#include "EntityManager.h"
#include "Scene.h"
#include "McRFPy_API.h"
#include "IndexTexture.h"

class GameEngine
{
    sf::RenderWindow window;
    sf::Font font;
    std::string scene;
    std::map<std::string, Scene*> scenes;
    bool running = true;
    bool paused = false;
    int currentFrame = 0;
    sf::View visible;
    sf::Clock clock;
    float frameTime;
    std::string window_title;

public:
    GameEngine();
    Scene* currentScene();
    void changeScene(std::string);
    void quit();
    void setPause(bool);
    sf::Font & getFont();
    sf::RenderWindow & getWindow();
    void run();
    void sUserInput();
    int getFrame() { return currentFrame; }
    float getFrameTime() { return frameTime; }
    sf::View getView() { return visible; }

    // global textures for scripts to access
    std::vector<IndexTexture> textures;
    
    // global audio storage
    std::vector<sf::SoundBuffer> sfxbuffers;
    sf::Music music;
    sf::Sound sfx;
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> scene_ui(std::string scene);
    
};
