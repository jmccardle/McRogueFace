#include "UITestScene.h"
#include "ActionCode.h"
#include <math.h>

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

UITestScene::UITestScene(GameEngine* g)
: Scene(g)
{
    // demo sprites from texture file
    texture.loadFromFile("./assets/kenney_tinydungeon.png");
    texture.setSmooth(false);

    // Show one texture at a time
    test_sprite.setTexture(texture);
    test_sprite.setPosition(sf::Vector2f(50.0f, 50.0f));
    test_sprite.setScale(sf::Vector2f(4.0f, 4.0f));
    setSpriteTexture(0);

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

    registerAction(0, "event");

    UIMenu test_menu(game->getFont());
    UIMenu test_menu2(game->getFont());
    test_menu.visible = false;
    test_menu.box.setSize(sf::Vector2f(350, 200));
    test_menu.add_caption("debug to stdout", 16, sf::Color(255, 255, 0));
    test_menu.add_button(Button(0, 0, 130, 40, sf::Color(0, 0, 192), sf::Color(0,0,0), "view", game->getFont(), "showviewport"));

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

    test_ship.miner();
    test_ship.angle = 180.0;
    test_ship.position.x = 250;
    test_ship.position.y = 120;
    //std::cout << menus.size() << std::endl;

}


void UITestScene::update()
{

    if (abs(desired_angle - test_ship.angle) < 1)
    {
        test_ship.angle = desired_angle;
    } else if (test_ship.angle < desired_angle)
    {
        test_ship.angle += 1;
    } else if (test_ship.angle > desired_angle){
        test_ship.angle -= 1;
    }

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
    if (!b_action.compare("showviewport"))
    {
        std::cout << viewport.getSize().x << ", " << viewport.getSize().y << ": "
            << viewport.getCenter().x << ", " << viewport.getCenter().y << std::endl;
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

    if (ACTION("left", "start"))  { viewport.move(-10, 0); }
    if (ACTION("right", "start")) { viewport.move(10, 0); }
    if (ACTION("up", "start"))    { viewport.move(0, -10); }
    if (ACTION("down", "start"))  { viewport.move(0, 10); }
    if (ACTION("down", "start"))  { viewport.move(0, 10); }
    if (ACTION("zoom_down", "start"))  { if (zoom > 0.2f)  zoom -= 0.1f; viewport.zoom(zoom); }
    if (ACTION("zoom_up", "start"))    { if (zoom < 10.0f) zoom += 0.1f; viewport.zoom(zoom); }
    //std::cout << "viewport: " << viewport.getCenter().x << ", " << viewport.getCenter().y << std::endl;

    if (type.compare("resize")) // get center coordinate from game coordinate viewport, apply to new window viewport, restore zoom level
    {
        auto center = viewport.getCenter();
        //auto w = viewport.getSize().x;
        //auto h = viewport.getSize().y;
        viewport = game->getView();
        viewport.setCenter(center);
        viewport.zoom(zoom);
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

    int width = viewport.getSize().x;
    int height = viewport.getSize().y;
    int top = viewport.getCenter().y - (height/2);
    int left = viewport.getCenter().x - (width/2);

    int vline_count = height / grid_spacing * 2;
    sf::VertexArray v_lines(sf::Lines, vline_count*2);
    int index = 0;
    for (int x = left - (left % grid_spacing); index < vline_count*2; x += grid_spacing)
    {
        v_lines[index] = sf::Vector2f(x, top);
        v_lines[index + 1] = sf::Vector2f(x, top+height);
        v_lines[index].color = sf::Color(0, 40, 0);
        v_lines[index + 1].color = sf::Color(0, 40, 0);
        index += 2;

    }
    game->getWindow().draw(v_lines);

    int hline_count = width / grid_spacing * 2;
    sf::VertexArray h_lines(sf::Lines, hline_count*2);
    //std::cout << "Width: " << v.width << " Lines:" << vline_count <<
    //    " Point array length: " << vline_count * 2 << std::endl;
    index = 0;
    for (int y = top - (top % grid_spacing); index < hline_count * 2; y += grid_spacing)
    {
        //std::cout << "(" << v.left << ", " << y << ") -> " << "(" << v.left + v.width << ", " << y << ")" << std::endl;
        h_lines[index] = sf::Vector2f(left, y);
        h_lines[index + 1] = sf::Vector2f(left+width, y);
        h_lines[index].color = sf::Color(0, 40, 0);
        h_lines[index + 1].color = sf::Color(0, 40, 0);
        index += 2;
    }

    game->getWindow().draw(h_lines);
    /*for (int i = 0; i < total_lines; i++)
    {
        sf::Vertex p = lines[i];
        std::cout << p.position.x << ", " << p.position.y << std::endl;
    }*/


    for (auto e : entities.getEntities())
    {
        //game->getWindow().draw(e->cShape->circle);
    }
    test_ship.render(game->getWindow());



    // Fixed position objects
    game->getWindow().setView(game->getView());
    game->getWindow().draw(text);



    //test_button.render(game->getWindow());
    //if (test_menu.visible) test_menu.render(game->getWindow());
    //if (test_menu2.visible) test_menu2.render(game->getWindow());
    for ( auto ui : menus)
    {
        //std::cout << ui.buttons[0].getAction() << std::endl;
        if (!ui.visible) continue;
        ui.render(game->getWindow());

    }

    // draw test sprite on top of everything
    game->getWindow().draw(test_sprite); 

    game->getWindow().display();
}

