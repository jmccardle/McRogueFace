#include "UITestScene.h"
#include "ActionCode.h"
#include "Resources.h"

UITestScene::UITestScene(GameEngine* g) : Scene(g)
{
    text.setFont(game->getFont());
    text.setString("Test Scene for UI elements");
    text.setCharacterSize(24);


    //registerAction(ActionCode::KEY + sf::Keyboard::Space, "start_game");
    //registerAction(ActionCode::KEY + sf::Keyboard::Up, "up");
    //registerAction(ActionCode::KEY + sf::Keyboard::Down, "down");
    
    auto ui = Resources::game->scene_ui("uitest");
    if (ui)
    {
        std::cout << "Got back a UI vector from Resources::game.\n";
    } else {
        std::cout << "No UI vector was returned.\n";
    }

    // Create a UI element or three?
    auto e1 = std::make_shared<UIFrame>(100,150,400,400);
    e1->box.setPosition(100, 150);
    e1->box.setSize(sf::Vector2f(400,400));
    e1->box.setFillColor(sf::Color(255, 0, 0));
    //e1.fillColor(sf::Color(255,0,0));
    //if (ui) ui->push_back(e1);
    ui_elements.push_back(e1);

    auto e1a = std::make_shared<UIFrame>(50,50,200,200);
    e1a->box.setPosition(50, 50);
    e1a->box.setSize(sf::Vector2f(200,200));
    e1a->box.setFillColor(sf::Color(0, 255, 0));
    //e1a.fillColor(sf::Color(0, 255, 0));
    e1->children.push_back(e1a);
    
    auto e1aa = std::make_shared<UIFrame>(5,5,100,100);
    e1aa->box.setPosition(5, 5);
    e1aa->box.setSize(sf::Vector2f(100,100));
    e1aa->box.setFillColor(sf::Color(0, 0, 255));
    //e1aa.fillColor(sf::Color(0, 0, 255));  
    e1a->children.push_back(e1aa);
    
    auto e2 = std::make_shared<UICaption>();
    e2->text.setFont(game->getFont());
    e2->text.setString("Hello World.");
    //e2.text.setColor(sf::Color(255, 255, 255));
    e2->text.setPosition(50, 250);
    
    //if (ui) ui->push_back(e2);
    ui_elements.push_back(e2);
    //ui_elements.push_back(&e1);
    //ui_elements.push_back(&e2);
    
    if (ui)
    std::cout << "pointer to ui_elements now shows size=" << ui->size() << std::endl;
}

void UITestScene::update()
{
    //std::cout << "MenuScene update" << std::endl;
}

void UITestScene::doAction(std::string name, std::string type)
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

void UITestScene::sRender()
{
    game->getWindow().clear();
    game->getWindow().draw(text);
    
    // draw all UI elements
    //for (auto e: ui_elements)
    //auto ui = Resources::game->scene_ui("uitest");
    //if (ui)
    for (auto e: ui_elements)
    {
        //std::cout << "Rendering element\n";
        if (e)
            e->render();
    }
    
    //e1.render(sf::Vector2f(0, 0));
    
    //e1.render(sf::Vector2f(-100, -100));
    
    game->getWindow().display();
    
    McRFPy_API::REPL();
}
