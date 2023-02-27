#include "Grid.h"
#include <cmath>

GridPoint::GridPoint():
    color(0, 0, 0, 0), walkable(true), tilesprite(-1), transparent(true), visible(false), discovered(false), color_overlay(0,0,0,255), tile_overlay(-1), uisprite(-1)
{};

void Grid::setSprite(int ti)
{
        int tx = ti % texture_width, ty = ti / texture_width;
            sprite.setTextureRect(sf::IntRect(tx * grid_size, ty * grid_size, grid_size, grid_size));
}

Grid::Grid(int gx, int gy, int gs, int _x, int _y, int _w, int _h):
    grid_size(gs), 
    grid_x(gx), grid_y(gy), 
    zoom(1.0f), center_x(gx), center_y(gy),
    texture_width(12), texture_height(11)
{
    //grid_size = gs;
    //zoom = 1.0f;
    //grid_x = gx;
    //grid_y = gy;
    points.resize(gx*gy);
    box.setSize(sf::Vector2f(_w, _h));
    box.setPosition(sf::Vector2f(_x, _y));
    box.setFillColor(sf::Color(0,0,0,0));

    renderTexture.create(_w, _h);

    texture.loadFromFile("./assets/kenney_tinydungeon.png");
    texture.setSmooth(false);
    sprite.setTexture(texture);

    //output.setSize(box.getSize());
    output.setTextureRect(
        sf::IntRect(0, 0,
        box.getSize().x, box.getSize().y));
    output.setPosition(box.getPosition());
    // textures are upside-down inside renderTexture
    output.setTexture(renderTexture.getTexture());

    // Show one texture at a time
    sprite.setTexture(texture);
}

void Grid::render(sf::RenderWindow & window)
{
    renderTexture.clear();
    //renderTexture.draw(box);

    // sprites that are visible according to zoom, center_x, center_y, and box width
    auto box_size = box.getSize();
    float view_width = box_size.x / (grid_size * zoom);
    float view_height = box_size.y / (grid_size * zoom);

    float top_offset = (center_y * grid_size) - box_size.y/2.0f;
    float left_offset = (center_x * grid_size) - box_size.x/2.0f;

    sprite.setScale(sf::Vector2f(zoom, zoom));

    auto box_pos = box.getPosition();

    int x_start = std::floor(center_x - view_width/2.0f);
    int x_end = std::ceil(center_x + view_width/2.0f);
    int y_start = std::floor(center_y - view_height/2.0f);
    int y_end = std::ceil(center_y + view_height/2.0f);

    for (int x = 0; 
        x < grid_x; //x < view_width; 
        x++)
    {
        for (int y = 0; 
            y < grid_y; //y < view_height;
            y++)
        {
            // convert grid's coordinate to pixel coords to draw
            //float window_x = (x_start + x) * grid_size * zoom;
            //float window_y = (y_start + y) * grid_size * zoom;
            float natural_x = x * grid_size * zoom;
            float natural_y = y * grid_size * zoom;
            sprite.setPosition(
                sf::Vector2f(natural_x - left_offset, 
                             natural_y - top_offset));
            
            auto gridPoint = at(x, y);
            // color?

            // tilesprite
            // if discovered but not visible, set opacity to 90%
            // if not discovered... just don't draw it?
            setSprite(at(x, y).tilesprite);
            renderTexture.draw(sprite);

            // overlay

            // uisprite

        }
    }

    // grid lines for testing & validation


    // render to window
    renderTexture.display();
    window.draw(output);
}

GridPoint& Grid::at(int x, int y)
{
    return points[y * grid_x + x];
}
