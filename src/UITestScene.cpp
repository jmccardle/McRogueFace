#include "UITestScene.h"
#include "ActionCode.h"
#include <math.h>
#include <random>

sf::Texture texture;

int texture_index = 0;
const int texture_size = 16, texture_width = 12, texture_height = 11;
const int texture_sprite_count = texture_width * texture_height;
sf::Sprite test_sprite;

sf::SoundBuffer buffer;
sf::Sound sound;

void setSpriteTexture(int ti)
{
    int tx = ti % texture_width, ty = ti / texture_width;
    test_sprite.setTextureRect(sf::IntRect(tx * texture_size, ty * texture_size, texture_size, texture_size));
}

// random for this test
std::random_device rd;  // Will be used to obtain a seed for the random number engine
std::mt19937 gen(rd()); // Standard mersenne_twister_engine seeded with rd()
std::uniform_int_distribution<> distrib(0, 10);
std::uniform_int_distribution<> coldistrib(64, 192);
std::uniform_real_distribution<> snoise(-3, 3);

UITestScene::UITestScene(GameEngine* g)
: Scene(g), grid(10, 20, 16, 20, 20, 800, 520) 
{
    // demo sprites from texture file
    texture.loadFromFile("./assets/kenney_tinydungeon.png");
    texture.setSmooth(false);

    // Show one texture at a time
    test_sprite.setTexture(texture);
    test_sprite.setPosition(sf::Vector2f(20.0f, 20.0f));
    test_sprite.setScale(sf::Vector2f(4.0f, 4.0f));
    setSpriteTexture(0);



    // Test grid with random sprite noise

    //std::array<int, 11> ground = {0, 12, 24, 48, 42, 48, 49, 50, 51, -1, -1};
    std::array<int, 11> ground = {0, 0, 0, -1, -1, -1, -1, -1, -1, -1, 51};

    for (int _x = 0; _x < 10; _x++)
        for (int _y = 0; _y < 20; _y++) {
            //grid.at(_x, _y).tilesprite = _y*11 + _x;
            //if (!_x % 2 || _y == 0) grid.at(_x, _y).tilesprite = 121;
            //else 
            auto &gridpoint = grid.at(_x, _y);
            grid.at(_x, _y).tilesprite = ground[distrib(gen)];
            grid.at(_x, _y).color = sf::Color(
                    coldistrib(gen), 0, 0);

        }

    for (int _x = 0; _x < 10; _x++)
    {
        grid.at(_x, 0).tilesprite = 121;
        grid.at(_x, 5).tilesprite = 123;
        grid.at(_x, 9).tilesprite = 10;
    }

    // Load sound
    buffer.loadFromFile("./assets/boom.wav");
    sound.setBuffer(buffer);

    viewport = game->getView(); // scrolling view is identical to start
    resolution = viewport.getSize();
    text.setFont(game->getFont());
    text.setString("Test");
    text.setCharacterSize(16);

    registerAction(ActionCode::KEY + sf::Keyboard::Num1, "show1");
    registerAction(ActionCode::KEY + sf::Keyboard::Num2, "show2");
    registerAction(ActionCode::KEY + sf::Keyboard::Num3, "show3");
    registerAction(ActionCode::MOUSEBUTTON + sf::Mouse::Left, "click");

    registerAction(ActionCode::KEY + sf::Keyboard::Left, "left");
    registerAction(ActionCode::KEY + sf::Keyboard::Right, "right");
    registerAction(ActionCode::KEY + sf::Keyboard::Up, "up");
    registerAction(ActionCode::KEY + sf::Keyboard::Down, "down");
    registerAction(ActionCode::KEY + sf::Keyboard::Comma, "zoom_down");
    registerAction(ActionCode::KEY + sf::Keyboard::Period, "zoom_up");

    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_DEL, "wheel_up");
    registerAction(ActionCode::MOUSEWHEEL + ActionCode::WHEEL_NEG + ActionCode::WHEEL_DEL, "wheel_down");

    registerAction(ActionCode::KEY + sf::Keyboard::Num4, "sound_test");
    registerAction(ActionCode::KEY + sf::Keyboard::Q, "gridtests");

    registerAction(0, "event");

    UIMenu test_menu(game->getFont());
    UIMenu test_menu2(game->getFont());
    test_menu.visible = false;
    test_menu.box.setSize(sf::Vector2f(350, 200));
    test_menu.add_caption("debug to stdout", 16, sf::Color(255, 255, 0));
    test_menu.add_button(Button(0, 0, 130, 40, sf::Color(0, 0, 192), sf::Color(0,0,0), "REPL", game->getFont(), "startrepl"));

    test_menu2.visible = true;
    test_menu2.box.setPosition(150, 180);

    test_menu2.box.setFillColor(sf::Color(255, 0, 0));
    test_menu2.add_caption("1: show UI 1 (this)", 18, sf::Color(255, 255, 0));
    test_menu2.add_caption("2: show UI 2", 18, sf::Color(255, 255, 0));
    test_menu2.add_caption("3: hide UIs", 18, sf::Color(255, 255, 0));
    test_menu2.add_caption("> and <: zoom", 18, sf::Color(255, 255, 0));
    test_menu2.add_caption("arrows: pan", 18, sf::Color(255, 255, 0));
    test_menu2.add_caption("click: turn (buggy)", 18, sf::Color(255, 255, 0));
    test_menu2.next_button += 100;

    menus.push_back(test_menu);
    menus.push_back(test_menu2);

    /*
    test_ship.miner();
    test_ship.angle = 180.0;
    test_ship.position.x = 250;
    test_ship.position.y = 120;
    */
    //std::cout << menus.size() << std::endl;

}


void UITestScene::update()
{
    /*
    if (abs(desired_angle - test_ship.angle) < 1)
    {
        test_ship.angle = desired_angle;
    } else if (test_ship.angle < desired_angle)
    {
        test_ship.angle += 1;
    } else if (test_ship.angle > desired_angle){
        test_ship.angle -= 1;
    }
    */

    /*
    // Too slow: updating every grid manually
    // Restrict to visible squares... use noise for coherence?
    for (int _x = 0; _x < grid.grid_x; _x++)
        for (int _y = 0; _y < grid.grid_y; _y++) {
            auto &square = grid.at(_x, _y);
            square.color.r += snoise(gen);
            if (square.color.r > 254) square.color.r = 254;
            if (square.color.r < 1) square.color.r = 1;
        }
    */

    entities.update();

    // All fixed vector movement
    for (auto e : entities.getEntities())
    {
        //if(e->cPython) e->cPython->update();
        //e->cTransform->pos += e->cTransform->velocity;
        //e->cShape->circle.setPosition(e->cTransform->pos.x, e->cTransform->pos.y);
    }

}

void UITestScene::doButton(std::string b_action)
{
    if (!b_action.compare("startrepl"))
    {
        McRFPy_API::REPL();
        //std::cout << viewport.getSize().x << ", " << viewport.getSize().y << ": "
        //    << viewport.getCenter().x << ", " << viewport.getCenter().y << std::endl;
    }
}

void UITestScene::doAction(std::string name, std::string type)
{
    if (ACTIONONCE("show1"))
    {
        menus[0].visible = false;
        menus[1].visible = true;
    }
    if (ACTIONONCE("show2"))
    {
        menus[0].visible = true;
        menus[1].visible = false;
    }
    if (ACTIONONCE("show3"))
    {
        menus[0].visible = false;
        menus[1].visible = false;
    }

    if (ACTIONONCE("click"))
    {
        auto mousepos = sf::Mouse::getPosition(game->getWindow());
        bool ui_clicked = false;
        for ( auto ui : menus)
        {
            if (!ui.visible) continue;
            for (auto b : ui.buttons)
            {
                if (b.contains(mousepos)) {
                    std::cout << b.getAction() << std::endl;
                    doButton(b.getAction());
                    ui_clicked = true;
                }
            }
        }
        if (!ui_clicked) {
            for (auto pair : McRFPy_API::menus) {
                if (!pair.second->visible) continue;
                for (auto b : pair.second->buttons)
                {
                    if (b.contains(mousepos)) {
                        std::cout << "(api) " << b.getAction() <<std::endl;
                        McRFPy_API::doAction(b.getAction());
                        ui_clicked = true;
                    }
                }
            }

        }
        if (!ui_clicked) {
            auto mousepos = sf::Mouse::getPosition(game->getWindow());
            auto worldpos = game->getWindow().mapPixelToCoords(mousepos, viewport);
            desired_angle = atan((1.0f * worldpos.y) / worldpos.x) * 180 / 3.14159 + 90.0f;
            //std::cout << (1.0f * worldpos.y) / worldpos.x << " -> " << desired_angle << std::endl;
        }
    }

    if (ACTION("wheel_up", "start")) {
        texture_index++;
        if (texture_index >= texture_sprite_count) texture_index = 0;
        setSpriteTexture(texture_index);
        std::string caption = "Texture index: ";
        caption += std::to_string(texture_index);
        text.setString(caption);

    }
    if (ACTION("wheel_down", "start")) {
        texture_index--;
        if (texture_index < 0) texture_index = texture_sprite_count - 1;
        setSpriteTexture(texture_index);
        std::string caption = "Texture index: ";
        caption += std::to_string(texture_index);
        text.setString(caption);
    }

    if (ACTION("sound_test", "start")) { sound.play(); }

    if (ACTION("left", "start"))  {
        grid.center_x -= 0.5;
    }
    if (ACTION("right", "start")) {
        grid.center_x += 0.5;
    }
    if (ACTION("up", "start"))    {
        grid.center_y -= 0.5;
    }
    if (ACTION("down", "start"))  {
        grid.center_y += 0.5;
    }
    if (ACTION("zoom_down", "start"))  {
        if (grid.zoom > 0.75f) grid.zoom -= 0.25f;
    }
    if (ACTION("zoom_up", "start"))    { 
        if (grid.zoom < 5.0f) grid.zoom += 0.25f;
    }
    //std::cout << "viewport: " << viewport.getCenter().x << ", " << viewport.getCenter().y << std::endl;
    //
    

    if (type.compare("resize")) // get center coordinate from game coordinate viewport, apply to new window viewport, restore zoom level
    {
        auto center = viewport.getCenter();
        viewport = game->getView();
        viewport.setCenter(center);
        viewport.zoom(zoom);
    }

    if (ACTION("gridtests", "start")) {
        
        int tx, ty;
        auto mousepos = sf::Mouse::getPosition(game->getWindow());
        /*
        GridPoint* pgrid = grid.atScreenPixel(mousepos.x, mousepos.y, &tx, &ty);
        std::cout << "\ntx: " << tx << " ty: " << ty << std::endl;
        */
        grid.screenToGrid(mousepos.x, mousepos.y, tx, ty);
        if (grid.inBounds(tx, ty)) {
            auto gridsq = grid.at(tx, ty);
            std::cout << "At (" << tx << ", " << ty << "): " << gridsq.tilesprite << std::endl;
        }

    }

    // after processing: set actionState
    if      (type.compare("start") == 0 && !actionState[name]) { actionState[name] = true; }
    else if (type.compare("end") == 0   &&  actionState[name]) { actionState[name] = false; }
}

void UITestScene::sRender()
{
    game->getWindow().clear();

    // Scrolling Viewport Objects (under the UI) --- entities, etc.
    game->getWindow().setView(viewport);

    for (auto e : entities.getEntities())
    {
        //game->getWindow().draw(e->cShape->circle);
    }

    //draw grid
    grid.render(game->getWindow());

    // Fixed position objects
    game->getWindow().setView(game->getView());
    game->getWindow().draw(text);

    for ( auto ui : menus)
    {
        //std::cout << ui.buttons[0].getAction() << std::endl;
        if (!ui.visible) continue;
        ui.render(game->getWindow());

    }

    // Python API menus
    for (auto pair: McRFPy_API::menus)
    {
        if (!pair.second->visible) continue;
        pair.second->render(game->getWindow());
    }

    // test Python sprite code
    //McRFPy_API::executePyString("mcrfpy.drawSprite(123, 36, 10)");

    // draw test sprite on top of everything
    //game->getWindow().draw(test_sprite); 

    game->getWindow().display();
}

