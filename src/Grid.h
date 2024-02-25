#pragma once
#include "Common.h"
#include "libtcod.h"

//#include "Entity.h"
class Entity; // forward declare

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
public:
    Grid();
    sf::RectangleShape box; // view on window
    bool visible;
    sf::Texture texture;
    sf::Sprite sprite, output;
    sf::RenderTexture renderTexture;
    TCODMap* tcodmap;
    void setSprite(int);
    const int texture_width, texture_height;
    auto contains(sf::Vector2i p) { return box.getGlobalBounds().contains(p.x, p.y); }

    Grid(int gx, int gy, int gs, int _x, int _y, int _w, int _h);
    int grid_x, grid_y; // rectangle map size (integer - sprites)
    int grid_size; // pixel size of 1 sprite
    float zoom;
    int center_x, center_y; // center in 1.0x Pixels

    std::vector<GridPoint> points; // grid visible contents
    std::vector<std::shared_ptr<Entity>> entities;
    void render(sf::RenderWindow&); // draw to screen
    GridPoint& at(int, int);
    bool inBounds(int, int);
    void screenToGrid(int, int, int&, int&);

    void renderPxToGrid(int, int, int&, int&);
    void gridToRenderPx(int, int, int&, int&);
    void integerGrid(float, float, int&, int&);
    
    void refreshTCODmap();
    void refreshTCODsight(int, int);
    TCODDijkstra *dijkstra; //= new TCODDijkstra(myMap);
};
