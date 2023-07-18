#include "Grid.h"
#include <cmath>
#include "Entity.h"

GridPoint::GridPoint():
    color(0, 0, 0, 0), walkable(false), tilesprite(-1), transparent(false), visible(false), discovered(false), color_overlay(0,0,0,255), tile_overlay(-1), uisprite(-1)
{};

void Grid::setSprite(int ti)
{
        int tx = ti % texture_width, ty = ti / texture_width;
            sprite.setTextureRect(sf::IntRect(tx * grid_size, ty * grid_size, grid_size, grid_size));
}

Grid::Grid(int gx, int gy, int gs, int _x, int _y, int _w, int _h):
    grid_size(gs),
    grid_x(gx), grid_y(gy), 
    zoom(1.0f), center_x((gx/2) * gs), center_y((gy/2) * gs),
    texture_width(12), texture_height(11), visible(false)
{
    //grid_size = gs;
    //zoom = 1.0f;
    //grid_x = gx;
    //grid_y = gy;
    tcodmap = new TCODMap(gx, gy);
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

void Grid::refreshTCODmap() {
	//int total = 0, walkable = 0, transparent = 0;
	for (int x = 0; x < grid_x; x++) {
		for (int y = 0; y < grid_y; y++) {
			auto p = at(x, y);
			//total++; if (p.walkable) walkable++; if (p.transparent) transparent++;
			tcodmap->setProperties(x, y, p.transparent, p.walkable);
		}
	}
	//std::cout << "Map refreshed: " << total << " squares, " << walkable << "walkable, " << transparent << " transparent" << std::endl;
}
void Grid::refreshTCODsight(int x, int y) {
	tcodmap->computeFov(x,y, 0, true, FOV_PERMISSIVE_8);
	for (int x = 0; x < grid_x; x++) {
		for (int y = 0; y < grid_y; y++) {
			auto& p = at(x, y);
			if (p.visible && !tcodmap->isInFov(x, y)) {
				p.discovered = true;
				p.visible = false;
			} else if (!p.visible && tcodmap->isInFov(x,y)) {
				p.discovered = true;
				p.visible = true;
			}
		}
	}
}

bool Grid::inBounds(int x, int y) {
    return (x >= 0 && y >= 0 && x < grid_x && y < grid_y);
}

void Grid::screenToGrid(int sx, int sy, int& gx, int& gy) {

    float center_x_sq = center_x / grid_size;
    float center_y_sq = center_y / grid_size;

    float width_sq = box.getSize().x / (grid_size * zoom);
    float height_sq = box.getSize().y / (grid_size * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float right_edge = center_x_sq + (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);
    float bottom_edge = center_y_sq + (height_sq / 2.0);

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

    // compare integer method with this (mostly working) one
    //int diff_realpixel_x = box.getSize().x / 2.0 - sx;
    //int diff_realpixel_y = box.getSize().y / 2.0 - sy;
    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    std::cout << "Float method got ans (" << ans_x << ", " << ans_y << ")"
        << std::endl << "Int method px (" << left_spritepixels + (sx/zoom) << ", " << 
        top_spritepixels + (sy/zoom) << ")" << std::endl << 
        "Int grid (" << (left_spritepixels + (sx/zoom) ) / grid_size << 
        ", " << (top_spritepixels + (sy/zoom)) / grid_size << ")" << 

        std::endl;

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

void Grid::renderPxToGrid(int sx, int sy, int& gx, int& gy) {
    // just like screen px coversion, but no offset by grid's position
    float center_x_sq = center_x / grid_size;
    float center_y_sq = center_y / grid_size;

    float width_sq = box.getSize().x / (grid_size * zoom);
    float height_sq = box.getSize().y / (grid_size * zoom);

    int width_px = box.getSize().x / 2.0;
    int height_px = box.getSize().y / 2.0;

    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    float grid_px = zoom * grid_size;
    float sx_sq = sx / grid_px;
    float sy_sq = sy / grid_px;

    float ans_x = sx_sq + left_edge;
    float ans_y = sy_sq + top_edge;

    if (ans_x < 0) ans_x = -1;
    if (ans_y < 0) ans_y = -1;

    gx = ans_x;
    gy = ans_y;
}

void Grid::integerGrid(float fx, float fy, int& gx, int& gy) {
    if (fx < 0) fx -= 0.5;
    if (fy < 0) fy -= 0.5;
    gx = fx;
    gy = fy;
}

void Grid::gridToRenderPx(int gx, int gy, int& sx, int& sy) {
    // integer grid square (gx, gy) - what pixel (on rendertexture)
    // should it's top left corner be at (the sprite's position)

    // eff_gridsize = grid_size * zoom
    // if center_x = 161, and grid_size is 16, that's 10 + 1/16 sprites
    // center_x - (box.getSize().x / 2 / zoom) = left edge (in px)
    // gx * eff_gridsize = pixel position without panning
    // pixel_gx - left_edge = grid's render position

    sx = (gx * grid_size * zoom) - (center_x - (box.getSize().x / 2.0 / zoom));
    sy = (gy * grid_size * zoom) - (center_y - (box.getSize().y / 2.0 / zoom));
}

void Grid::render(sf::RenderWindow & window)
{
    renderTexture.clear();
    //renderTexture.draw(box);

    // sprites that are visible according to zoom, center_x, center_y, and box width
    float center_x_sq = center_x / grid_size;
    float center_y_sq = center_y / grid_size;

    float width_sq = box.getSize().x / (grid_size * zoom);
    float height_sq = box.getSize().y / (grid_size * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    //float right_edge = center_x_sq + (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);
    //float bottom_edge = center_y_sq + (height_sq / 2.0);


    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(grid_size * zoom, grid_size * zoom));
    r.setOutlineThickness(0);

    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_x) x_limit = grid_x;

    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_y) y_limit = grid_y;

    //for (float x = (left_edge >= 0 ? left_edge : 0); 
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width; 
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0); 
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {
            // Converting everything to integer pixels to avoid jitter
            //auto pixel_pos = sf::Vector2f(
            //    (x - left_edge) * (zoom * grid_size),
            //    (y - top_edge) * (zoom * grid_size));

            // This failed horribly:
            //int gx, gy; integerGrid(x, y, gx, gy);
            //int px_x, px_y; gridToRenderPx(gx, gy, px_x, px_y);
            //auto pixel_pos = sf::Vector2f(px_x, px_y);
           
            // this draws coherently, but the coordinates
            // don't match up with the mouse cursor function
            // jitter not eliminated
            auto pixel_pos = sf::Vector2f(
                    (x*grid_size - left_spritepixels) * zoom,
                    (y*grid_size - top_spritepixels) * zoom );

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
    
    for (auto e : entities) {
		auto drawent = e->cGrid->indexsprite.drawable();
		drawent.setScale(zoom, zoom);
		auto pixel_pos = sf::Vector2f(
			(drawent.getPosition().x*grid_size - left_spritepixels) * zoom,
			(drawent.getPosition().y*grid_size - top_spritepixels) * zoom );
		drawent.setPosition(pixel_pos);
		renderTexture.draw(drawent);
	}
	
	// loop again and draw on top of entities
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
                    (x*grid_size - left_spritepixels) * zoom,
                    (y*grid_size - top_spritepixels) * zoom );

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
    window.draw(output);
}

GridPoint& Grid::at(int x, int y)
{
    return points[y * grid_x + x];
}
