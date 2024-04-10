#include "UIEntity.h"

UIEntity::UIEntity() {} // this will not work lol. TODO remove default constructor by finding the shared pointer inits that use it

UIEntity::UIEntity(UIGrid& grid)
: gridstate(grid.grid_x * grid.grid_y)
{
}

PyObject* UIEntity::at(PyUIEntityObject* self, PyObject* o) {
    int x, y;
    if (!PyArg_ParseTuple(o, "ii", &x, &y)) {
        PyErr_SetString(PyExc_TypeError, "UIEntity.at requires two integer arguments: (x, y)");
        return NULL;
    }
    
    if (self->data->grid == NULL) {
        PyErr_SetString(PyExc_ValueError, "Entity cannot access surroundings because it is not associated with a grid");
        return NULL;
    }
    
    PyUIGridPointStateObject* obj = (PyUIGridPointStateObject*)((&PyUIGridPointStateType)->tp_alloc(&PyUIGridPointStateType, 0));
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->gridstate[y + self->data->grid->grid_x * x]);
    obj->grid = self->data->grid;
    obj->entity = self->data;
    return (PyObject*)obj;

}

int PyUIEntity::init(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = { "x", "y", "texture", "sprite_index", "grid", nullptr };
    float x = 0.0f, y = 0.0f, scale = 1.0f;
    int sprite_index = -1;
    PyObject* texture = NULL;
    PyObject* grid = NULL;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ffOi|O",
        const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &grid))
    {
        return -1;
    }

    // check types for texture
    //
    // Set Texture
    //
    if (texture != NULL && !PyObject_IsInstance(texture, (PyObject*)&mcrfpydef::PyTextureType)){
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    } /*else if (texture != NULL) // this section needs to go; texture isn't optional and isn't managed by the UI objects anymore
    {
        self->texture = texture;
        Py_INCREF(texture);
    } else
    {
        // default tex?
    }*/

    if (grid != NULL && !PyObject_IsInstance(grid, (PyObject*)&PyUIGridType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }

    auto pytexture = (PyTextureObject*)texture;
    if (grid == NULL)
        self->data = std::make_shared<UIEntity>();
    else
        self->data = std::make_shared<UIEntity>(*((PyUIGridObject*)grid)->data);

    // TODO - PyTextureObjects and IndexTextures are a little bit of a mess with shared/unshared pointers
    self->data->sprite = UISprite(pytexture->data, sprite_index, sf::Vector2f(0,0), 1.0);
    self->data->position = sf::Vector2f(x, y);
    if (grid != NULL) {
        PyUIGridObject* pygrid = (PyUIGridObject*)grid;
        self->data->grid = pygrid->data;
        // todone - on creation of Entity with Grid assignment, also append it to the entity list
        pygrid->data->entities->push_back(self->data);
    }
    return 0;
}
