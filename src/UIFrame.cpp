#include "UIFrame.h"
#include "UICollection.h"
#include "GameEngine.h"

UIDrawable* UIFrame::click_at(sf::Vector2f point)
{
    for (auto e: *children)
    {
        auto p = e->click_at(point + box.getPosition());
        if (p)
            return p;
    }
    if (click_callable)
    {
        float x = box.getPosition().x, y = box.getPosition().y, w = box.getSize().x, h = box.getSize().y;
        if (point.x > x && point.y > y && point.x < x+w && point.y < y+h) return this;
    }
    return NULL;
}

UIFrame::UIFrame()
: outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    box.setPosition(0, 0);
    box.setSize(sf::Vector2f(0, 0));
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h)
: outline(0)
{
    box.setPosition(_x, _y);
    box.setSize(sf::Vector2f(_w, _h));
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}

UIFrame::~UIFrame()
{
    children.reset();
}

PyObjectsEnum UIFrame::derived_type()
{
    return PyObjectsEnum::UIFRAME;
}

void UIFrame::render(sf::Vector2f offset)
{
    box.move(offset);
    Resources::game->getWindow().draw(box);
    box.move(-offset);

    for (auto drawable : *children) {
        drawable->render(offset + box.getPosition());
    }
}

PyObject* UIFrame::get_children(PyUIFrameObject* self, void* closure)
{
    // create PyUICollection instance pointing to self->data->children
    PyUICollectionObject* o = (PyUICollectionObject*)mcrfpydef::PyUICollectionType.tp_alloc(&mcrfpydef::PyUICollectionType, 0);
    if (o)
        o->data = self->data->children;
    return (PyObject*)o;
}


namespace mcrfpydef {

    // TODO: move to class scope; but this should at least get us compiling
    static PyObject* PyUIFrame_get_children(PyUIFrameObject* self, void* closure)
    {
        // create PyUICollection instance pointing to self->data->children
        PyUICollectionObject* o = (PyUICollectionObject*)PyUICollectionType.tp_alloc(&PyUICollectionType, 0);
        if (o)
            o->data = self->data->children;
        return (PyObject*)o;
    }
}

