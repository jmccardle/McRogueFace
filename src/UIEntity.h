#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyDrawable.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"

#include "UIGridPoint.h"
#include "UIBase.h"
#include "UISprite.h"

class UIGrid;

// UIEntity
/*

 ****************************************
 *       say it with me:                *
 *  ✨ UIEntity is not a UIDrawable ✨  * 
 ****************************************

            **Why Not, John?**
  Doesn't it say "UI" on the front of it?
  It sure does. Probably should have called it "GridEntity", but it's a bit late now.

  UIDrawables have positions in **screen pixel coordinates**. Their position is an offset from their parent's position, and they are deeply nestable (Scene -> Frame -> Frame -> ...)

  However:
  UIEntity has a position in **Grid tile coordinates**.
  UIEntity is not nestable at all. Grid -> Entity.
  UIEntity has a strict one/none relationship with a Grid: if you add it to another grid, it will have itself removed from the losing grid's collection.
  UIEntity originally only allowed a single-tile sprite, but around mid-July 2025, I'm working to change that to allow any UIDrawable to go there, or multi-tile sprites.
  UIEntity is, at its core, the container for *a perspective of map data*.
  The Grid should contain the true, complete contents of the game's space, and the Entity should use pathfinding, field of view, and game logic to interact with the Grid's layer data.

  In Conclusion, because UIEntity cannot be drawn on a Frame or Scene, and has the unique role of serving as a filter of the data contained in a Grid, UIEntity will not become a UIDrawable.

*/

//class UIEntity;
//typedef struct {
//    PyObject_HEAD
//    std::shared_ptr<UIEntity> data;
//} PyUIEntityObject;

// helper methods with no namespace requirement
PyObject* sfVector2f_to_PyObject(sf::Vector2f vector);
sf::Vector2f PyObject_to_sfVector2f(PyObject* obj);
PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state);
PyObject* UIGridPointStateVector_to_PyList(const std::vector<UIGridPointState>& vec);

class UIEntity
{
public:
    PyObject* self = nullptr;  // Reference to the Python object (if created from Python)
    uint64_t serial_number = 0;  // For Python object cache
    std::shared_ptr<UIGrid> grid;
    std::vector<UIGridPointState> gridstate;
    UISprite sprite;
    sf::Vector2f position; //(x,y) in grid coordinates; float for animation
    //void render(sf::Vector2f); //override final;

    UIEntity();
    ~UIEntity();
    
    // Visibility methods
    void updateVisibility();  // Update gridstate from current FOV
    
    // Property system for animations
    bool setProperty(const std::string& name, float value);
    bool setProperty(const std::string& name, int value);
    bool getProperty(const std::string& name, float& value) const;
    
    // Methods that delegate to sprite
    sf::FloatRect get_bounds() const { return sprite.get_bounds(); }
    void move(float dx, float dy) { sprite.move(dx, dy); position.x += dx; position.y += dy; }
    void resize(float w, float h) { /* Entities don't support direct resizing */ }
    
    static PyObject* at(PyUIEntityObject* self, PyObject* o);
    static PyObject* index(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* die(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static PyObject* path_to(PyUIEntityObject* self, PyObject* args, PyObject* kwds);
    static PyObject* update_visibility(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored));
    static int init(PyUIEntityObject* self, PyObject* args, PyObject* kwds);

    static PyObject* get_position(PyUIEntityObject* self, void* closure);
    static int set_position(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyObject* get_gridstate(PyUIEntityObject* self, void* closure);
    static PyObject* get_spritenumber(PyUIEntityObject* self, void* closure);
    static int set_spritenumber(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyObject* get_float_member(PyUIEntityObject* self, void* closure);
    static int set_float_member(PyUIEntityObject* self, PyObject* value, void* closure);
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
    static PyObject* repr(PyUIEntityObject* self);
};

// Forward declaration of methods array
extern PyMethodDef UIEntity_all_methods[];

namespace mcrfpydef {
    static PyTypeObject PyUIEntityType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Entity",
        .tp_basicsize = sizeof(PyUIEntityObject),
        .tp_itemsize = 0,
        .tp_repr = (reprfunc)UIEntity::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
        .tp_doc = PyDoc_STR("Entity(grid_pos=None, texture=None, sprite_index=0, **kwargs)\n\n"
                            "A game entity that exists on a grid with sprite rendering.\n\n"
                            "Args:\n"
                            "    grid_pos (tuple, optional): Grid position as (x, y) tuple. Default: (0, 0)\n"
                            "    texture (Texture, optional): Texture object for sprite. Default: default texture\n"
                            "    sprite_index (int, optional): Index into texture atlas. Default: 0\n\n"
                            "Keyword Args:\n"
                            "    grid (Grid): Grid to attach entity to. Default: None\n"
                            "    visible (bool): Visibility state. Default: True\n"
                            "    opacity (float): Opacity (0.0-1.0). Default: 1.0\n"
                            "    name (str): Element name for finding. Default: None\n"
                            "    x (float): X grid position override. Default: 0\n"
                            "    y (float): Y grid position override. Default: 0\n\n"
                            "Attributes:\n"
                            "    pos (tuple): Grid position as (x, y) tuple\n"
                            "    x, y (float): Grid position coordinates\n"
                            "    draw_pos (tuple): Pixel position for rendering\n"
                            "    gridstate (GridPointState): Visibility state for grid points\n"
                            "    sprite_index (int): Current sprite index\n"
                            "    visible (bool): Visibility state\n"
                            "    opacity (float): Opacity value\n"
                            "    name (str): Element name"),
        .tp_methods = UIEntity_all_methods,
        .tp_getset = UIEntity::getsetters,
        .tp_base = NULL,
        .tp_init = (initproc)UIEntity::init,
        .tp_new = PyType_GenericNew,
    };
}
