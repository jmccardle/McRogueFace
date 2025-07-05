#include "UIEntity.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include "PyObjectUtils.h"
#include "PyVector.h"


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

PyObject* UIEntity::index(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored)) {
    // Check if entity has an associated grid
    if (!self->data || !self->data->grid) {
        PyErr_SetString(PyExc_RuntimeError, "Entity is not associated with a grid");
        return NULL;
    }
    
    // Get the grid's entity collection
    auto entities = self->data->grid->entities;
    if (!entities) {
        PyErr_SetString(PyExc_RuntimeError, "Grid has no entity collection");
        return NULL;
    }
    
    // Find this entity in the collection
    int index = 0;
    for (auto it = entities->begin(); it != entities->end(); ++it, ++index) {
        if (it->get() == self->data.get()) {
            return PyLong_FromLong(index);
        }
    }
    
    // Entity not found in its grid's collection
    PyErr_SetString(PyExc_ValueError, "Entity not found in its grid's entity collection");
    return NULL;
}

int UIEntity::init(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    //static const char* keywords[] = { "x", "y", "texture", "sprite_index", "grid", nullptr };
    //float x = 0.0f, y = 0.0f, scale = 1.0f;
    static const char* keywords[] = { "pos", "texture", "sprite_index", "grid", nullptr };
    PyObject* pos;
    float scale = 1.0f;
    int sprite_index = -1;
    PyObject* texture = NULL;
    PyObject* grid = NULL;

    //if (!PyArg_ParseTupleAndKeywords(args, kwds, "ffOi|O",
    //    const_cast<char**>(keywords), &x, &y, &texture, &sprite_index, &grid))
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OiO",
        const_cast<char**>(keywords), &pos, &texture, &sprite_index, &grid))
    {
        return -1;
    }

    PyVectorObject* pos_result = PyVector::from_arg(pos);
    if (!pos_result)
    {
        PyErr_SetString(PyExc_TypeError, "pos must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
        return -1;
    }

    // check types for texture
    //
    // Set Texture - allow None or use default
    //
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (texture != NULL && texture != Py_None && !PyObject_IsInstance(texture, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))){
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
        return -1;
    } else if (texture != NULL && texture != Py_None) {
        auto pytexture = (PyTextureObject*)texture;
        texture_ptr = pytexture->data;
    } else {
        // Use default texture when None or not provided
        texture_ptr = McRFPy_API::default_texture;
    }
    
    if (!texture_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "No texture provided and no default texture available");
        return -1;
    }

    if (grid != NULL && !PyObject_IsInstance(grid, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }

    if (grid == NULL)
        self->data = std::make_shared<UIEntity>();
    else
        self->data = std::make_shared<UIEntity>(*((PyUIGridObject*)grid)->data);

    // TODO - PyTextureObjects and IndexTextures are a little bit of a mess with shared/unshared pointers
    self->data->sprite = UISprite(texture_ptr, sprite_index, sf::Vector2f(0,0), 1.0);
    self->data->position = pos_result->data;
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

PyObject* sfVector2f_to_PyObject(sf::Vector2f vec) {
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        obj->data = vec;
    }
    return (PyObject*)obj;
}

PyObject* sfVector2i_to_PyObject(sf::Vector2i vec) {
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        obj->data = sf::Vector2f(static_cast<float>(vec.x), static_cast<float>(vec.y));
    }
    return (PyObject*)obj;
}

sf::Vector2f PyObject_to_sfVector2f(PyObject* obj) {
    PyVectorObject* vec = PyVector::from_arg(obj);
    if (!vec) {
        // PyVector::from_arg already set the error
        return sf::Vector2f(0, 0);
    }
    return vec->data;
}

sf::Vector2i PyObject_to_sfVector2i(PyObject* obj) {
    PyVectorObject* vec = PyVector::from_arg(obj);
    if (!vec) {
        // PyVector::from_arg already set the error
        return sf::Vector2i(0, 0);
    }
    return sf::Vector2i(static_cast<int>(vec->data.x), static_cast<int>(vec->data.y));
}

// TODO - deprecate / remove this helper
PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state) {
    // This function is incomplete - it creates an empty object without setting state data
    // Should use PyObjectUtils::createGridPointState() instead
    return PyObjectUtils::createPyObjectGeneric("GridPointState");
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
    if (reinterpret_cast<long>(closure) == 0) {
        return sfVector2f_to_PyObject(self->data->position);
    } else {
        return sfVector2i_to_PyObject(self->data->collision_pos);
    }
}

int UIEntity::set_position(PyUIEntityObject* self, PyObject* value, void* closure) {
    if (reinterpret_cast<long>(closure) == 0) {
        sf::Vector2f vec = PyObject_to_sfVector2f(value);
        if (PyErr_Occurred()) {
            return -1;  // Error already set by PyObject_to_sfVector2f
        }
        self->data->position = vec;
    } else {
        sf::Vector2i vec = PyObject_to_sfVector2i(value);
        if (PyErr_Occurred()) {
            return -1;  // Error already set by PyObject_to_sfVector2i
        }
        self->data->collision_pos = vec;
    }
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
    {"index", (PyCFunction)UIEntity::index, METH_NOARGS, "Return the index of this entity in its grid's entity collection"},
    {NULL, NULL, 0, NULL}
};

PyGetSetDef UIEntity::getsetters[] = {
    {"draw_pos", (getter)UIEntity::get_position, (setter)UIEntity::set_position, "Entity position (graphically)", (void*)0},
    {"pos", (getter)UIEntity::get_position, (setter)UIEntity::set_position, "Entity position (integer grid coordinates)", (void*)1},
    {"gridstate", (getter)UIEntity::get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"sprite_number", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite number (index) on the texture on the display", NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIEntity::repr(PyUIEntityObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<Entity (invalid internal object)>";
    else {
        auto ent = self->data;
        ss << "<Entity (x=" << self->data->position.x << ", y=" << self->data->position.y << ", sprite_number=" << self->data->sprite.getSpriteIndex() <<
         ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// Property system implementation for animations
bool UIEntity::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        collision_pos.x = static_cast<int>(value);
        // Update sprite position based on grid position
        // Note: This is a simplified version - actual grid-to-pixel conversion depends on grid properties
        sprite.setPosition(sf::Vector2f(position.x, position.y));
        return true;
    }
    else if (name == "y") {
        position.y = value;
        collision_pos.y = static_cast<int>(value);
        // Update sprite position based on grid position
        sprite.setPosition(sf::Vector2f(position.x, position.y));
        return true;
    }
    else if (name == "sprite_scale") {
        sprite.setScale(sf::Vector2f(value, value));
        return true;
    }
    return false;
}

bool UIEntity::setProperty(const std::string& name, int value) {
    if (name == "sprite_number") {
        sprite.setSpriteIndex(value);
        return true;
    }
    return false;
}

bool UIEntity::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = position.x;
        return true;
    }
    else if (name == "y") {
        value = position.y;
        return true;
    }
    else if (name == "sprite_scale") {
        value = sprite.getScale().x;  // Assuming uniform scale
        return true;
    }
    return false;
}
