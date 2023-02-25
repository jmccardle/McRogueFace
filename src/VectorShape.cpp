#include "VectorShape.h"

VectorShape::VectorShape()
{
    sf::Vector2f p(0, 0);
    points.push_back(sf::Vector2f(0, 40));
    points.push_back(sf::Vector2f(-30, -30));
    points.push_back(sf::Vector2f(0, -20));
    points.push_back(sf::Vector2f(30, -30));
}

void VectorShape::render(sf::RenderWindow & window)
{
    sf::Transform t;
    //t.scale(sf::Vector2f(0.5, 0.5));
    //t.scale(sf::Vector2f(3, 3));
    t.translate(position);
    t.rotate(angle);

    sf::VertexArray lines(sf::LineStrip, int(points.size())+1);
    for ( int i = 0; i < points.size(); i++)
    {
        lines[i] = points[i];
    }
    lines[points.size()] = points[0];

    window.draw(lines, t);
}

void VectorShape::miner()
{
    points.clear();
    points.push_back(sf::Vector2f(0, -40));

    float mirror_x[12] = {-1, -1, -.5, -.5, -2, -2, -3, -3, -2, -2, -1.5, -0.5};
    float fixed_y[12] = {-3, -2, -1.5, -1, -1, -.5, 0, 1, 1.5, 2, 3, 3};

    for (int i = 0; i < 12; i++)
    {
        points.push_back(sf::Vector2f(mirror_x[i] * 10, fixed_y[i] * 10));
    }
    points.push_back(sf::Vector2f(0, 20));

    for (int i = 11; i >= 0; i--)
    {
        points.push_back(sf::Vector2f(mirror_x[i] * -10, fixed_y[i] * 10));
    }
}
