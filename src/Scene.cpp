#include "Scene.h"

//Scene::Scene() { game = 0; std::cout << "WARN: default Scene constructor called. (game = " << game << ")" << std::endl;};
Scene::Scene(GameEngine* g) { game = g; }
void Scene::registerAction(int code, std::string name)
{
    actions[code] = name;
    actionState[name] = false;
}
bool Scene::hasAction(std::string name)
{
    for (auto& item : actions)
        if (item.second == name) return true;
    return false;
}

bool Scene::hasAction(int code)
{
    return (actions.find(code) != actions.end());
}

std::string Scene::action(int code)
{
    return actions[code];
}
