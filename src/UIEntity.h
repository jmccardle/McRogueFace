#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

#include "UIGridPoint.h"
#include "UIDrawable.h"

class UIGrid;

// TODO: make UIEntity a drawable
class UIEntity//: public UIDrawable
{
public:
    //PyObject* self;
    std::shared_ptr<UIGrid> grid;
    std::vector<UIGridPointState> gridstate;
    UISprite sprite;
    sf::Vector2f position; //(x,y) in grid coordinates; float for animation
    void render(sf::Vector2f); //override final;

    UIEntity();
    UIEntity(UIGrid&);
    
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<UIEntity> data;
    //PyObject* texture;
} PyUIEntityObject;
