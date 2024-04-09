#include "UIDrawable.h"

UIDrawable::UIDrawable() { click_callable = NULL;  }

void UIDrawable::click_unregister()
{
    click_callable.reset();
}

void UIDrawable::render()
{
    render(sf::Vector2f());
}
