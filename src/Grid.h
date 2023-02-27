#include "Common.h"

class GridPoint
{
public:
    // Layers: color, walkable, tilesprite, transparent, visible, discovered, overlay, uisprite
    sf::Color color;
    bool walkable;
    int tilesprite;
    bool transparent, visible, discovered;
    sf::Color color_overlay;
    int tile_overlay, uisprite;
    GridPoint();
};

class Grid
{
private:
    Grid();
    sf::RectangleShape box; // view on window
    sf::Texture texture;
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    void setSprite(int);
    const int texture_width, texture_height;

public:
    Grid(int gx, int gy, int gs, int _x, int _y, int _w, int _h);
    int grid_x, grid_y; // rectangle map size (integer - sprites)
    int grid_size; // pixel size of 1 sprite
    float zoom, center_x, center_y; // center in fractional sprites

    std::vector<GridPoint> points; // grid visible contents
    void render(sf::RenderWindow&); // draw to screen
    GridPoint& at(int, int);

};
