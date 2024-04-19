#include "UIEntity.h"
#include "UIGrid.h"
#include "McRFPy_API.h"

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
    /*
    PyUIGridPointStateObject* obj = (PyUIGridPointStateObject*)((&mcrfpydef::PyUIGridPointStateType)->tp_alloc(&mcrfpydef::PyUIGridPointStateType, 0));
    */
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState");
    auto obj = (PyUIGridPointStateObject*)type->tp_alloc(type, 0);
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->gridstate[y + self->data->grid->grid_x * x]);
    obj->grid = self->data->grid;
    obj->entity = self->data;
    return (PyObject*)obj;

}

int UIEntity::init(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
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
    if (texture != NULL && !PyObject_IsInstance(texture, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))){
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

    if (grid != NULL && !PyObject_IsInstance(grid, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
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



PyObject* UIEntity::get_spritenumber(PyUIEntityObject* self, void* closure) {
    return PyLong_FromDouble(self->data->sprite.getSpriteIndex());
}

PyObject* sfVector2f_to_PyObject(sf::Vector2f vector) {
    return Py_BuildValue("(ff)", vector.x, vector.y);
}

sf::Vector2f PyObject_to_sfVector2f(PyObject* obj) {
    float x, y;
    if (!PyArg_ParseTuple(obj, "ff", &x, &y)) {
        return sf::Vector2f(); // TODO / reconsider this default: Return default vector on parse error
    }
    return sf::Vector2f(x, y);
}

// TODO - deprecate / remove this helper
PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state) {
    return PyObject_New(PyObject, (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState"));
}

PyObject* UIGridPointStateVector_to_PyList(const std::vector<UIGridPointState>& vec) {
    PyObject* list = PyList_New(vec.size());
    if (!list) return PyErr_NoMemory();

    for (size_t i = 0; i < vec.size(); ++i) {
        PyObject* obj = UIGridPointState_to_PyObject(vec[i]);
        if (!obj) { // Cleanup on failure
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, obj); // This steals a reference to obj
    }

    return list;
}

PyObject* UIEntity::get_position(PyUIEntityObject* self, void* closure) {
    return sfVector2f_to_PyObject(self->data->position);
}

int UIEntity::set_position(PyUIEntityObject* self, PyObject* value, void* closure) {
    self->data->position = PyObject_to_sfVector2f(value);
    return 0;
}

PyObject* UIEntity::get_gridstate(PyUIEntityObject* self, void* closure) {
    // Assuming a function to convert std::vector<UIGridPointState> to PyObject* list
    return UIGridPointStateVector_to_PyList(self->data->gridstate);
}

int UIEntity::set_spritenumber(PyUIEntityObject* self, PyObject* value, void* closure) {
    int val;
    if (PyLong_Check(value))
        val = PyLong_AsLong(value);
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
        return -1;
    }
    //self->data->sprite.sprite_index = val;
    self->data->sprite.setSpriteIndex(val); // todone - I don't like ".sprite.sprite" in this stack of UIEntity.UISprite.sf::Sprite
    return 0;
}

PyMethodDef UIEntity::methods[] = {
    {"at", (PyCFunction)UIEntity::at, METH_O},
    {NULL, NULL, 0, NULL}
};

PyGetSetDef UIEntity::getsetters[] = {
    {"position", (getter)UIEntity::get_position, (setter)UIEntity::set_position, "Entity position", NULL},
    {"gridstate", (getter)UIEntity::get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"sprite_number", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite number (index) on the texture on the display", NULL},
    {NULL}  /* Sentinel */
};
