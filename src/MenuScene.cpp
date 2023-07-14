#include "MenuScene.h"
#include "ActionCode.h"

MenuScene::MenuScene(GameEngine* g) : Scene(g)
{
    text.setFont(game->getFont());
    text.setString("McRogueFace Engine - r/RoguelikeDev Tutorial 2023");
    text.setCharacterSize(24);
    //std::cout << "MenuScene Initialized. " << game << std::endl;
    //std::cout << "Font: " << game->getFont().getInfo().family << std::endl;

    text2.setFont(game->getFont());
    text2.setString("Press 'Spacebar' to run demo");
    text2.setCharacterSize(16);
    text2.setPosition(0.0f, 50.0f);
    
    text3.setFont(game->getFont());
    text3.setString("use 'W' 'A' 'S' 'D' to move (even when blank; it's a bug)");
    text3.setCharacterSize(16);
    text3.setPosition(0.0f, 80.0f);

    registerAction(ActionCode::KEY + sf::Keyboard::Space, "start_game");
    registerAction(ActionCode::KEY + sf::Keyboard::Up, "up");
    registerAction(ActionCode::KEY + sf::Keyboard::Down, "down");
}

void MenuScene::update()
{
    //std::cout << "MenuScene update" << std::endl;
}

void MenuScene::doAction(std::string name, std::string type)
{
    //std::cout << "MenuScene doAction: " << name << ", " << type << std::endl;
    //if (name.compare("start_game") == 0 and type.compare("start") == 0)
    if(ACTION("start_game", "start"))
        game->changeScene("py");
    /*
    else if(ACTIONONCE("up"))
        game->getWindow().setSize(sf::Vector2u(1280, 800));
    else if(ACTIONONCE("down"))
        game->getWindow().setSize(sf::Vector2u(1024, 768));
    */
}

void MenuScene::sRender()
{
    game->getWindow().clear();
    game->getWindow().draw(text);
    game->getWindow().draw(text2);
    game->getWindow().draw(text3);
    game->getWindow().display();
}
