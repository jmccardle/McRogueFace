#include "UI.h"
#include "Resources.h"
#include "GameEngine.h"

/* //callability fields & methods
    PyObject* click_callable;
    virtual UIDrawable* click_at(sf::Vector2f point);
    void click_register(PyObject*);
    void click_unregister();
*/

UIDrawable::UIDrawable() { click_callable = NULL;  }

UIDrawable* UIFrame::click_at(sf::Vector2f point)
{
    for (auto e: *children)
    {
        auto p = e->click_at(point + box.getPosition());
        if (p)
            return p;
    }
    if (click_callable)
    {
        float x = box.getPosition().x, y = box.getPosition().y, w = box.getSize().x, h = box.getSize().y;
        if (point.x > x && point.y > y && point.x < x+w && point.y < y+h) return this;
    }
    return NULL;
}

UIDrawable* UICaption::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if (text.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

UIDrawable* UISprite::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if(sprite.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

UIDrawable* UIGrid::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if(box.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}

void UIDrawable::click_register(PyObject* callable)
{
    if (click_callable)
    {
        // decrement reference before overwriting
        Py_DECREF(click_callable);
    }
    click_callable = callable;
    Py_INCREF(click_callable);
}

void UIDrawable::click_unregister()
{
    if (click_callable == NULL) return;
    Py_DECREF(click_callable);
    click_callable = NULL;
}

void UIDrawable::render()
{
    //std::cout << "Rendering base UIDrawable\n";
    render(sf::Vector2f());
}
UIFrame::UIFrame():
//x(0), y(0), w(0), h(0), 
outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    box.setPosition(0, 0);
    box.setSize(sf::Vector2f(0, 0));
    /*
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
    */
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h):
//x(_x), y(_y), w(_w), h(_h),
outline(0)
{
    box.setPosition(_x, _y);
    box.setSize(sf::Vector2f(_w, _h));
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    /*
    pyOutlineColor = NULL;
    pyFillColor = NULL;
    _outlineColor = NULL;
    _fillColor = NULL;
    */
}

UIFrame::~UIFrame()
{
    children.reset();
    /*
    if (pyOutlineColor) Py_DECREF(pyOutlineColor);
    else if (_outlineColor) delete _outlineColor;
    if (pyFillColor) Py_DECREF(pyFillColor);
    else if (_fillColor) delete _fillColor;
    */
}

/*
    sf::Color& fillColor(); // getter
    void fillColor(sf::Color c); // C++ setter
    void fillColor(PyObject* pyColor); // Python setter
    
    sf::Color& outlineColor(); // getter
    void outlineColor(sf::Color c); // C++ setter
    void outlineColor(PyObject* pyColor); // Python setter
*/


PyObjectsEnum UIFrame::derived_type()
{
    return PyObjectsEnum::UIFRAME;
}

void UIFrame::render(sf::Vector2f offset)
{
    //std::cout << "Rendering UIFrame w/ offset " << offset.x << ", " << offset.y << "\n";
    //std::cout << "position = " << x << ", " << y << "\n";
    box.move(offset);
    Resources::game->getWindow().draw(box);
    box.move(-offset);
    //sf::RectangleShape box = sf::RectangleShape(sf::Vector2f(w,h));
    //sf::Vector2f pos = sf::Vector2f(x, y);
    //box.setPosition(offset + pos);
    //if (_fillColor) { box.setFillColor(fillColor()); }
    //if (_outlineColor) { box.setOutlineColor(outlineColor()); }
    //box.setOutlineThickness(outline);
    //Resources::game->getWindow().draw(box);
    for (auto drawable : *children) {
        drawable->render(offset + box.getPosition());
    }
}

void UICaption::render(sf::Vector2f offset)
{
    //std::cout << "Rendering Caption with offset\n";
    text.move(offset);
    Resources::game->getWindow().draw(text);
    text.move(-offset);
}

UISprite::UISprite() {}

UISprite::UISprite(IndexTexture* _itex, int _sprite_index, float x = 0.0, float y = 0.0, float s = 1.0)
: itex(_itex), sprite_index(_sprite_index)
{
    sprite.setTexture(_itex->texture);
    sprite.setTextureRect(_itex->spriteCoordinates(_sprite_index));
    sprite.setPosition(sf::Vector2f(x, y));
    sprite.setScale(sf::Vector2f(s, s));
}

UISprite::UISprite(IndexTexture* _itex, int _sprite_index, sf::Vector2f pos, float s = 1.0)
: itex(_itex), sprite_index(_sprite_index)
{
    sprite.setTexture(_itex->texture);
    sprite.setTextureRect(_itex->spriteCoordinates(_sprite_index));
    sprite.setPosition(pos);
    sprite.setScale(sf::Vector2f(s, s));
}

//void UISprite::update()
//{
    //auto& tex = Resources::game->textures[texture_index];
    //sprite.setTexture(tex.texture);
    //sprite.setScale(sf::Vector2f(scale, scale));
    //sprite.setPosition(sf::Vector2f(x, y));
    //std::cout << "Drawable position: " << x << ", " << y << " -> " << s.getPosition().x << ", " << s.getPosition().y << std::endl;
    //sprite.setTextureRect(tex.spriteCoordinates(sprite_index));
//}

void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}

// 7DRL hack; needed to draw entities to UIGrid. TODO, apply this technique to all UIDrawables
void UISprite::render(sf::Vector2f offset, sf::RenderTexture& target)
{
    sprite.move(offset);
    target.draw(sprite);
    sprite.move(-offset);
}

void UISprite::setPosition(float x, float y)
{
    setPosition(sf::Vector2f(x, y));
}

void UISprite::setPosition(sf::Vector2f pos)
{
    sprite.setPosition(pos);
}

void UISprite::setScale(float s)
{
    sprite.setScale(sf::Vector2f(s, s));
}

PyObjectsEnum UICaption::derived_type()
{
    return PyObjectsEnum::UICAPTION;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}

// UIGrid support classes' methods

UIGridPoint::UIGridPoint()
:color(1.0f, 1.0f, 1.0f), color_overlay(0.0f, 0.0f, 0.0f), walkable(false), transparent(false),
 tilesprite(-1), tile_overlay(-1), uisprite(-1)
{
}

UIEntity::UIEntity() {} // this will not work lol. TODO remove default constructor by finding the shared pointer inits that use it

UIEntity::UIEntity(UIGrid& grid)
: gridstate(grid.grid_x * grid.grid_y)
{
}

// UIGrid methods

UIGrid::UIGrid()
{
}

UIGrid::UIGrid(int gx, int gy, IndexTexture* _itex, float _x, float _y, float _w, float _h)
: grid_x(gx), grid_y(gy),
  zoom(1.0f), center_x((gx/2) * _itex->grid_size), center_y((gy/2) * _itex->grid_size),
  itex(_itex), points(gx * gy)
{
    // set up blank list of entities
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    box.setSize(sf::Vector2f(_w, _h));
    box.setPosition(sf::Vector2f(_x, _y));

    box.setFillColor(sf::Color(0,0,0,0));
    renderTexture.create(_w, _h);
    sprite.setTexture(_itex->texture);
    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
     output.setPosition(box.getPosition());
     // textures are upside-down inside renderTexture
     output.setTexture(renderTexture.getTexture());
}

UIGrid::UIGrid(int gx, int gy, IndexTexture* _itex, sf::Vector2f _xy, sf::Vector2f _wh)
: grid_x(gx), grid_y(gy),
  zoom(1.0f), center_x((gx/2) * _itex->grid_size), center_y((gy/2) * _itex->grid_size),
  itex(_itex), points(gx * gy)
{
    // set up blank list of entities
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    box.setSize(_wh);
    box.setPosition(_xy); 

    box.setFillColor(sf::Color(0,0,0,0));
    //renderTexture.create(_wh.x, _wh.y);
    // create renderTexture with maximum theoretical size; sprite can resize to show whatever amount needs to be rendered
    renderTexture.create(1920, 1080); // TODO - renderTexture should be window size; above 1080p this will cause rendering errors
    
    sprite.setTexture(_itex->texture);
    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
     output.setPosition(box.getPosition());
     // textures are upside-down inside renderTexture
     output.setTexture(renderTexture.getTexture());

}

void UIGrid::update()
{
}

void UIGrid::setSprite(int ti)
{
        int tx = ti % itex->grid_width, ty = ti / itex->grid_width;
            sprite.setTextureRect(sf::IntRect(tx * itex->grid_size, ty * itex->grid_size, itex->grid_size, itex->grid_size));
}

void UIGrid::render(sf::Vector2f)
{
    output.setPosition(box.getPosition()); // output sprite can move; update position when drawing
    // output size can change; update size when drawing
    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
    renderTexture.clear(sf::Color(8, 8, 8, 255)); // TODO - UIGrid needs a "background color" field
    // sprites that are visible according to zoom, center_x, center_y, and box width
    float center_x_sq = center_x / itex->grid_size;
    float center_y_sq = center_y / itex->grid_size;

    float width_sq = box.getSize().x / (itex->grid_size * zoom);
    float height_sq = box.getSize().y / (itex->grid_size * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(itex->grid_size * zoom, itex->grid_size * zoom));
    r.setOutlineThickness(0);

    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_x) x_limit = grid_x;

    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_y) y_limit = grid_y;

    // base layer - bottom color, tile sprite ("ground")
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width; 
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0); 
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {
            auto pixel_pos = sf::Vector2f(
                    (x*itex->grid_size - left_spritepixels) * zoom,
                    (y*itex->grid_size - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);
            r.setFillColor(gridpoint.color);
            renderTexture.draw(r);

            // tilesprite
            // if discovered but not visible, set opacity to 90%
            // if not discovered... just don't draw it?
            if (gridpoint.tilesprite != -1) {
                setSprite(gridpoint.tilesprite);
                renderTexture.draw(sprite);
            }
        }
    }

    // middle layer - entities
    // disabling entity rendering until I can render their UISprite inside the rendertexture (not directly to window)
    for (auto e : *entities) {
        // TODO skip out-of-bounds entities (grid square not visible at all, check for partially on visible grid squares / floating point grid position)
        //auto drawent = e->cGrid->indexsprite.drawable();
        auto drawent = e->sprite;
        //drawent.setScale(zoom, zoom);
        drawent.setScale(zoom);
        auto pixel_pos = sf::Vector2f(
            (e->position.x*itex->grid_size - left_spritepixels) * zoom,
            (e->position.y*itex->grid_size - top_spritepixels) * zoom );
        //drawent.setPosition(pixel_pos);
        //renderTexture.draw(drawent);
        drawent.render(pixel_pos, renderTexture);
    }
    

    // top layer - opacity for discovered / visible status (debug, basically)
    /* // Disabled until I attach a "perspective"
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width; 
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0); 
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {

            auto pixel_pos = sf::Vector2f(
                    (x*itex->grid_size - left_spritepixels) * zoom,
                    (y*itex->grid_size - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);

            // visible & discovered layers for testing purposes
            if (!gridpoint.discovered) {
                r.setFillColor(sf::Color(16, 16, 20, 192)); // 255 opacity for actual blackout
                renderTexture.draw(r);
            } else if (!gridpoint.visible) {
                r.setFillColor(sf::Color(32, 32, 40, 128));
                renderTexture.draw(r);
            }

            // overlay

            // uisprite
        }
    }
    */

    // grid lines for testing & validation
    /*
    sf::Vertex line[] =
    {
        sf::Vertex(sf::Vector2f(0, 0), sf::Color::Red),
        sf::Vertex(box.getSize(), sf::Color::Red),

    };

    renderTexture.draw(line, 2, sf::Lines);
    sf::Vertex lineb[] =
    {
        sf::Vertex(sf::Vector2f(0, box.getSize().y), sf::Color::Blue),
        sf::Vertex(sf::Vector2f(box.getSize().x, 0), sf::Color::Blue),

    };

    renderTexture.draw(lineb, 2, sf::Lines);
    */

    // render to window
    renderTexture.display();
    Resources::game->getWindow().draw(output);

}

UIGridPoint& UIGrid::at(int x, int y)
{
    return points[y * grid_x + x];
}

PyObjectsEnum UIGrid::derived_type()
{
    return PyObjectsEnum::UIGRID;
}
