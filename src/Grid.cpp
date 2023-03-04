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

bool Grid::inBounds(int x, int y) {
    return (x >= 0 && y >= 0 && x < grid_x && y < grid_y);
}

void Grid::screenToGrid(int sx, int sy, int& gx, int& gy) {
    float width_sq = box.getSize().x / (grid_size * zoom);
    float height_sq = box.getSize().y / (grid_size * zoom);
    float left_edge = center_x - (width_sq / 2.0);
    float right_edge = center_x + (width_sq / 2.0);
    float top_edge = center_y - (height_sq / 2.0);
    float bottom_edge = center_y + (height_sq / 2.0);

    float grid_px = zoom * grid_size;
    //std::cout <<  "##############################" << 
    //    "\nscreen coord: (" << sx << ", " << sy << ")" << std::endl;

    sx -= box.getPosition().x;
    sy -= box.getPosition().y;

    //std::cout << "box coord: (" << sx << ", " << sy << ")" << std::endl;
    float mouse_x_sq = sx / grid_px;
    float mouse_y_sq = sy / grid_px;

    float ans_x = mouse_x_sq + left_edge;
    float ans_y = mouse_y_sq + top_edge;

    // casting float turns -0.5 to 0; I want any negative coord to be OOB
    if (ans_x < 0) ans_x = -1;
    if (ans_y < 0) ans_y = -1;

    gx = ans_x;
    gy = ans_y;
    /*
    std::cout <<
        "C: (" << center_x << ", " << center_y << ")" << std::endl <<
        "W: " << width_sq << " H: " << height_sq << std::endl <<
        "L: " << left_edge << " T: " << top_edge << std::endl <<
        "R: " << right_edge << " B: " << bottom_edge << std::endl <<
        "Grid Px: " << grid_px << "( zoom: " << zoom << ")" << std::endl <<
        "answer: G(" << ans_x << ", " << ans_y << ")" << std::endl << 
        "##############################" << 
        std::endl;
    */
}

void Grid::render(sf::RenderWindow & window)
{
    renderTexture.clear();
    //renderTexture.draw(box);

    // sprites that are visible according to zoom, center_x, center_y, and box width
    float width_sq = box.getSize().x / (grid_size * zoom);
    float height_sq = box.getSize().y / (grid_size * zoom);
    float left_edge = center_x - (width_sq / 2.0);
    float right_edge = center_x + (width_sq / 2.0);
    float top_edge = center_y - (height_sq / 2.0);
    float bottom_edge = center_y + (height_sq / 2.0);

    //auto box_size = box.getSize();
    //float view_width = box_size.x / (grid_size * zoom);
    //float view_height = box_size.y / (grid_size * zoom);

    //float top_offset = (center_y * grid_size) - box_size.y/2.0f;
    //float left_offset = (center_x * grid_size) - box_size.x/2.0f;

    sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(grid_size * zoom, grid_size * zoom));
    r.setOutlineThickness(0);

    //auto box_pos = box.getPosition();

    //int x_start = std::floor(center_x - view_width/2.0f);
    //int x_end = std::ceil(center_x + view_width/2.0f);
    //int y_start = std::floor(center_y - view_height/2.0f);
    //int y_end = std::ceil(center_y + view_height/2.0f);
    int x_limit = left_edge + width_sq + 1;
    if (x_limit > grid_x) x_limit = grid_x;

    int y_limit = top_edge + height_sq + 1;
    if (y_limit > grid_y) y_limit = grid_y;

    for (float x = (left_edge >= 0 ? left_edge : 0); 
        x < x_limit; //x < view_width; 
        x+=1.0)
    {
        for (float y = (top_edge >= 0 ? top_edge : 0); 
            y < y_limit; //y < view_height;
            y+=1.0)
        {
            auto pixel_pos = sf::Vector2f(
                (x - left_edge) * (zoom * grid_size),
                (y - top_edge) * (zoom * grid_size));
            auto gridpoint = at(std::floor(x), std::floor(y));

            // convert grid's coordinate to pixel coords to draw
            //float window_x = (x_start + x) * grid_size * zoom;
            //float window_y = (y_start + y) * grid_size * zoom;
            //float natural_x = x * grid_size * zoom;
            //float natural_y = y * grid_size * zoom;
            sprite.setPosition(pixel_pos);
                //sf::Vector2f(natural_x - left_offset, 
                //             natural_y - top_offset));
            
            // color?
            //r.setPosition(sf::Vector2f(natural_x - left_offset,
            //            natural_y - top_offset));
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

            // overlay

            // uisprite

        }
    }

    // grid lines for testing & validation
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


    // render to window
    renderTexture.display();
    window.draw(output);
}

GridPoint& Grid::at(int x, int y)
{
    return points[y * grid_x + x];
}

GridPoint* Grid::atScreenPixel(int sx, int sy, int* gx=NULL, int* gy=NULL) {

    int _x, _y;
    screenToGrid(sx, sy, _x, _y);
    std::cout << "screenToGrid gave: (" << _x << ", " << _y << ")" << std::endl;

    auto p = box.getPosition();
    auto s = box.getSize();

    // debug render values
    int x_start = std::floor(center_x - s.x/2.0f);
    int x_end = std::ceil(center_x + s.x/2.0f);
    int y_start = std::floor(center_y - s.y/2.0f);
    int y_end = std::ceil(center_y + s.y/2.0f);
    std::cout << "Center: " << center_x << ", " << center_y << std::endl <<
        "Start grid: " << x_start << ", " << y_start << std::endl <<
        "End grid: " << x_end << ", " << y_end << std::endl;


    // check if the mouse is even over the grid
    if (sx < p.x || sx > p.x+s.x || sy < p.y || sy > p.y+s.y) {
        std::cout << "(" << sx << ", " << sy << ") not over grid" << std::endl;
        return NULL;
    }
    // get dx, dy to box's center
    int dx = sx - (s.x/2.0 + p.x),
        dy = sy - (s.y/2.0 + p.y);

    // divide dx, dy by (gridsize * zoom) to get # in boxes
    int gdx = dx / (grid_size * zoom),
        gdy = dy / (grid_size * zoom);

    int targetx = gdx + center_x,
        targety = gdy + center_y;
    // return
    if (gx) {
        *gx = targetx;
    }

    if (gy) {
        *gy = targety;
    }

    if (targetx >= 0 && targetx <= grid_x && targety >= 0 && targety <= grid_y) {
        return &points[targety * grid_x + targetx];
    }
    else {
        std::cout << "(" << sx << ", " << sy << ") not over actual grid content" << std::endl;
        return NULL;
    }

}
