#pragma once
#include "Common.h"

class VectorShape
{
    public:
        VectorShape();
        std::vector<sf::Vector2f> points;
        void render(sf::RenderWindow & window);
        float angle;
        sf::Vector2f position;
        void miner();
    protected:

    private:
};
