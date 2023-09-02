#include "Scene.h"
#include "UI.h"

//Scene::Scene() { game = 0; std::cout << "WARN: default Scene constructor called. (game = " << game << ")" << std::endl;};
Scene::Scene(GameEngine* g)
{
    game = g; 
    ui_elements = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}
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

bool Scene::registerActionInjected(int code, std::string name)
{
    std::cout << "Inject registered action - default implementation\n";
    return false;
}

bool Scene::unregisterActionInjected(int code, std::string name)
{
    return false;
}
