#include "PyScene.h"
#include "ActionCode.h"
#include "Resources.h"

PyScene::PyScene(GameEngine* g) : Scene(g)
{
}

void PyScene::update()
{
}

void PyScene::doAction(std::string name, std::string type)
{
}

void PyScene::sRender()
{
    game->getWindow().clear();
    
    auto vec = *ui_elements;
    for (auto e: vec)
    {
        if (e)
            e->render();
    }
    
    game->getWindow().display();
    
    McRFPy_API::REPL();
}
