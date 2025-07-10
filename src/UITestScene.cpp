#include "UITestScene.h"
#include "ActionCode.h"
#include "Resources.h"

UITestScene::UITestScene(GameEngine* g) : Scene(g)
{
    registerAction(ActionCode::KEY + sf::Keyboard::Grave, "debug_menu");

    text.setFont(game->getFont());
    text.setString("UITest: surprised to be here? game.py raised an exception.");
    text.setCharacterSize(24);


    //registerAction(ActionCode::KEY + sf::Keyboard::Space, "start_game");
    //registerAction(ActionCode::KEY + sf::Keyboard::Up, "up");
    //registerAction(ActionCode::KEY + sf::Keyboard::Down, "down");
    
    // note - you can't use the pointer to UI elements in constructor.
    // The scene map is still being assigned to, so this object can't be looked up. 
    /*
    auto ui = Resources::game->scene_ui("uitest");
    if (ui)
    {
        std::cout << "Got back a UI vector from Resources::game.\n";
    } else {
        std::cout << "No UI vector was returned.\n";
    }
    */

    // Create a UI element or three?
    auto e1 = std::make_shared<UIFrame>(100,150,400,400);
    e1->box.setPosition(100, 150);
    e1->box.setSize(sf::Vector2f(400,400));
    e1->box.setFillColor(sf::Color(255, 0, 0));
    //e1.fillColor(sf::Color(255,0,0));
    //if (ui) ui->push_back(e1);
    ui_elements->push_back(e1);

    auto e1a = std::make_shared<UIFrame>(50,50,200,200);
    e1a->box.setPosition(50, 50);
    e1a->box.setSize(sf::Vector2f(200,200));
    e1a->box.setFillColor(sf::Color(0, 255, 0));
    //e1a.fillColor(sf::Color(0, 255, 0));
    e1->children->push_back(e1a);
    
    auto e1aa = std::make_shared<UIFrame>(5,5,100,100);
    e1aa->box.setPosition(5, 5);
    e1aa->box.setSize(sf::Vector2f(100,100));
    e1aa->box.setFillColor(sf::Color(0, 0, 255));
    //e1aa.fillColor(sf::Color(0, 0, 255));  
    e1a->children->push_back(e1aa);
    
    auto e2 = std::make_shared<UICaption>();
    e2->text.setFont(game->getFont());
    e2->text.setString("Hello World.");
    //e2.text.setColor(sf::Color(255, 255, 255));
    e2->text.setPosition(50, 250);
    
    //if (ui) ui->push_back(e2);
    ui_elements->push_back(e2);
    //ui_elements.push_back(&e1);
    //ui_elements.push_back(&e2);

    //t.loadFromFile("./assets/kenney_tinydungeon.png");
    //t.setSmooth(false);
    //auto* indextex = new IndexTexture(t, 16, 12, 11);
    //Resources::game->textures.push_back(*indextex);

    auto ptex = std::make_shared<PyTexture>("./assets/kenney_tinydungeon.png", 16, 16);

    //std::cout << Resources::game->textures.size() << " textures loaded.\n";
    auto e3 = std::make_shared<UISprite>(ptex, 84, sf::Vector2f(10, 10), 4.0);

    // Make UISprite more like IndexSprite: this is bad
    //e3->x = 10; e3->y = 10;
    //e3->texture_index = 0;
    //e3->sprite_index = 84;
    //e3->scale = 4.0f;
    //e3->update();

    // This goes to show how inconvenient the default constructor is. It should be removed
    //e3->itex = &Resources::game->textures[0];
    //e3->sprite.setTexture(e3->itex->texture);
    //e3->sprite_index = 84;
    //e3->sprite.setTextureRect(e3->itex->spriteCoordinates(e3->sprite_index));
    //e3->setPosition(10, 10);
    //e3->setScale(4.0f);

    e1aa->children->push_back(e3);



    auto e4 = std::make_shared<UISprite>(
            ptex, //indextex, //&Resources::game->textures[0],
            85, sf::Vector2f(90, 10), 4.0);
    e1aa->children->push_back(e4);
    //std::cout << "UISprite built: " << e4->sprite.getPosition().x << " " << e4->sprite.getPosition().y << " " << e4->sprite.getScale().x << " " <<
    //    e4->sprite_index << " " << std::endl;

    /*
    // note - you can't use the pointer to UI elements in constructor.
    // The scene map is still being assigned to, so this object can't be looked up. 
    if (ui)
    std::cout << "pointer to ui_elements now shows size=" << ui->size() << std::endl;
    */

    // UIGrid test:                (in grid cells)         (          in screen pixels            )
    //              constructor args:  w  h  texture             x    y                  w    h   
    auto e5 = std::make_shared<UIGrid>(4, 4, ptex, sf::Vector2f(550, 150), sf::Vector2f(200, 200));
    e5->zoom=2.0;
    e5->points[0].color =  sf::Color(255, 0, 0);
    e5->points[1].tilesprite = 1;
    e5->points[5].color =  sf::Color(0, 255, 0);
    e5->points[6].tilesprite = 2;
    e5->points[10].color = sf::Color(0, 0, 255);
    e5->points[11].tilesprite = 3;
    e5->points[15].color = sf::Color(255, 255, 255);

    ui_elements->push_back(e5);

    //UIEntity test:
    // asdf
    // TODO - reimplement UISprite style rendering within UIEntity class. Entities don't have a screen pixel position, they have a grid position, and grid sets zoom when rendering them.
    auto e5a = std::make_shared<UIEntity>(); // Default constructor - lazy initialization
    e5a->grid = e5;
    //auto e5as = UISprite(indextex, 85, sf::Vector2f(0, 0), 1.0);
    //e5a->sprite = e5as; // will copy constructor even exist for UISprite...?
    e5a->sprite = UISprite(ptex, 85, sf::Vector2f(0, 0), 1.0);
    e5a->position = sf::Vector2f(1, 0);

    e5->entities->push_back(e5a);

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
    else if ACTIONONCE("debug_menu") {
        McRFPy_API::REPL();
    }
    /*
    else if(ACTIONONCE("up"))
        game->getWindow().setSize(sf::Vector2u(1280, 800));
    else if(ACTIONONCE("down"))
        game->getWindow().setSize(sf::Vector2u(1024, 768));
    */
}

void UITestScene::render()
{
    game->getRenderTarget().clear();
    game->getRenderTarget().draw(text);
    
    // draw all UI elements
    //for (auto e: ui_elements)
    //auto ui = Resources::game->scene_ui("uitest");
    //if (ui)
    auto vec = *ui_elements;
    for (auto e: vec)
    {
        //std::cout << "Rendering element\n";
        if (e)
            e->render();
    }
    
    //e1.render(sf::Vector2f(0, 0));
    
    //e1.render(sf::Vector2f(-100, -100));
    
    // Display is handled by GameEngine
    
    //McRFPy_API::REPL();
}
