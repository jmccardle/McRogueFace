#include "Scene.h"
#include "UI.h"

//Scene::Scene() { game = 0; std::cout << "WARN: default Scene constructor called. (game = " << game << ")" << std::endl;};
Scene::Scene(GameEngine* g)
{
    key_callable = std::make_unique<PyKeyCallable>();
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


void Scene::key_register(PyObject* callable)
{
    /*
    if (key_callable)
    {
        // decrement reference before overwriting
        Py_DECREF(key_callable);
    }
    key_callable = callable;
    Py_INCREF(key_callable);
    */
    key_callable = std::make_unique<PyKeyCallable>(callable);
}

void Scene::key_unregister()
{
    /*
    if (key_callable == NULL) return;
    Py_DECREF(key_callable);
    key_callable = NULL;
    */
    key_callable.reset();
}

// #118: Scene animation property support
bool Scene::setProperty(const std::string& name, float value)
{
    if (name == "x") {
        position.x = value;
        return true;
    }
    if (name == "y") {
        position.y = value;
        return true;
    }
    if (name == "opacity") {
        opacity = std::max(0.0f, std::min(1.0f, value));
        return true;
    }
    if (name == "visible") {
        visible = (value != 0.0f);
        return true;
    }
    return false;
}

bool Scene::setProperty(const std::string& name, const sf::Vector2f& value)
{
    if (name == "pos" || name == "position") {
        position = value;
        return true;
    }
    return false;
}

float Scene::getProperty(const std::string& name) const
{
    if (name == "x") return position.x;
    if (name == "y") return position.y;
    if (name == "opacity") return opacity;
    if (name == "visible") return visible ? 1.0f : 0.0f;
    return 0.0f;
}
