#include "UIEntity.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include <algorithm>
#include "PyObjectUtils.h"
#include "PyVector.h"
#include "PyArgHelpers.h"
// UIDrawable methods now in UIBase.h
#include "UIEntityPyMethods.h"



UIEntity::UIEntity() 
: self(nullptr), grid(nullptr), position(0.0f, 0.0f)
{
    // Initialize sprite with safe defaults (sprite has its own safe constructor now)
    // gridstate vector starts empty - will be lazily initialized when needed
}

// Removed UIEntity(UIGrid&) constructor - using lazy initialization instead

void UIEntity::updateVisibility()
{
    if (!grid) return;
    
    // Lazy initialize gridstate if needed
    if (gridstate.size() == 0) {
        gridstate.resize(grid->grid_x * grid->grid_y);
        // Initialize all cells as not visible/discovered
        for (auto& state : gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }
    
    // First, mark all cells as not visible
    for (auto& state : gridstate) {
        state.visible = false;
    }
    
    // Compute FOV from entity's position
    int x = static_cast<int>(position.x);
    int y = static_cast<int>(position.y);
    
    // Use default FOV radius of 10 (can be made configurable later)
    grid->computeFOV(x, y, 10);
    
    // Update visible cells based on FOV computation
    for (int gy = 0; gy < grid->grid_y; gy++) {
        for (int gx = 0; gx < grid->grid_x; gx++) {
            int idx = gy * grid->grid_x + gx;
            if (grid->isInFOV(gx, gy)) {
                gridstate[idx].visible = true;
                gridstate[idx].discovered = true;  // Once seen, always discovered
            }
        }
    }
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
    
    // Lazy initialize gridstate if needed
    if (self->data->gridstate.size() == 0) {
        self->data->gridstate.resize(self->data->grid->grid_x * self->data->grid->grid_y);
        // Initialize all cells as not visible/discovered
        for (auto& state : self->data->gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }
    
    // Bounds check
    if (x < 0 || x >= self->data->grid->grid_x || y < 0 || y >= self->data->grid->grid_y) {
        PyErr_Format(PyExc_IndexError, "Grid coordinates (%d, %d) out of bounds", x, y);
        return NULL;
    }
    
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState");
    auto obj = (PyUIGridPointStateObject*)type->tp_alloc(type, 0);
    obj->data = &(self->data->gridstate[y * self->data->grid->grid_x + x]);
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
    // Try parsing with PyArgHelpers for grid position
    int arg_idx = 0;
    auto grid_pos_result = PyArgHelpers::parseGridPosition(args, kwds, &arg_idx);
    
    // Default values
    float grid_x = 0.0f, grid_y = 0.0f;
    int sprite_index = 0;
    PyObject* texture = nullptr;
    PyObject* grid_obj = nullptr;
    
    // Case 1: Got grid position from helpers (tuple format)
    if (grid_pos_result.valid) {
        grid_x = grid_pos_result.grid_x;
        grid_y = grid_pos_result.grid_y;
        
        // Parse remaining arguments
        static const char* remaining_keywords[] = { 
            "texture", "sprite_index", "grid", nullptr 
        };
        
        // Create new tuple with remaining args
        Py_ssize_t total_args = PyTuple_Size(args);
        PyObject* remaining_args = PyTuple_GetSlice(args, arg_idx, total_args);
        
        if (!PyArg_ParseTupleAndKeywords(remaining_args, kwds, "|OiO", 
                                         const_cast<char**>(remaining_keywords),
                                         &texture, &sprite_index, &grid_obj)) {
            Py_DECREF(remaining_args);
            if (grid_pos_result.error) PyErr_SetString(PyExc_TypeError, grid_pos_result.error);
            return -1;
        }
        Py_DECREF(remaining_args);
    }
    // Case 2: Traditional format
    else {
        PyErr_Clear();  // Clear any errors from helpers
        
        static const char* keywords[] = { 
            "grid_x", "grid_y", "texture", "sprite_index", "grid", "grid_pos", nullptr 
        };
        PyObject* grid_pos_obj = nullptr;
        
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|ffOiOO", 
                                         const_cast<char**>(keywords), 
                                         &grid_x, &grid_y, &texture, &sprite_index, 
                                         &grid_obj, &grid_pos_obj)) {
            return -1;
        }
        
        // Handle grid_pos keyword override
        if (grid_pos_obj && grid_pos_obj != Py_None) {
            if (PyTuple_Check(grid_pos_obj) && PyTuple_Size(grid_pos_obj) == 2) {
                PyObject* x_val = PyTuple_GetItem(grid_pos_obj, 0);
                PyObject* y_val = PyTuple_GetItem(grid_pos_obj, 1);
                if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                    (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                    grid_x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                    grid_y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "grid_pos must be a tuple (x, y)");
                return -1;
            }
        }
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
    
    // Allow creation without texture for testing purposes
    // if (!texture_ptr) {
    //     PyErr_SetString(PyExc_RuntimeError, "No texture provided and no default texture available");
    //     return -1;
    // }

    if (grid_obj != NULL && !PyObject_IsInstance(grid_obj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid"))) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }

    // Always use default constructor for lazy initialization
    self->data = std::make_shared<UIEntity>();

    // Store reference to Python object
    self->data->self = (PyObject*)self;
    Py_INCREF(self);

    // TODO - PyTextureObjects and IndexTextures are a little bit of a mess with shared/unshared pointers
    if (texture_ptr) {
        self->data->sprite = UISprite(texture_ptr, sprite_index, sf::Vector2f(0,0), 1.0);
    } else {
        // Create an empty sprite for testing
        self->data->sprite = UISprite();
    }
    
    // Set position using grid coordinates
    self->data->position = sf::Vector2f(grid_x, grid_y);
    
    if (grid_obj != NULL) {
        PyUIGridObject* pygrid = (PyUIGridObject*)grid_obj;
        self->data->grid = pygrid->data;
        // todone - on creation of Entity with Grid assignment, also append it to the entity list
        pygrid->data->entities->push_back(self->data);
        
        // Don't initialize gridstate here - lazy initialization to support large numbers of entities
        // gridstate will be initialized when visibility is updated or accessed
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

PyObject* UIGridPointState_to_PyObject(const UIGridPointState& state) {
    // Create a new GridPointState Python object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState");
    if (!type) {
        return NULL;
    }
    
    auto obj = (PyUIGridPointStateObject*)type->tp_alloc(type, 0);
    if (!obj) {
        Py_DECREF(type);
        return NULL;
    }
    
    // Allocate new data and copy values
    obj->data = new UIGridPointState();
    obj->data->visible = state.visible;
    obj->data->discovered = state.discovered;
    
    Py_DECREF(type);
    return (PyObject*)obj;
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
        // Return integer-cast position for grid coordinates
        sf::Vector2i int_pos(static_cast<int>(self->data->position.x), 
                             static_cast<int>(self->data->position.y));
        return sfVector2i_to_PyObject(int_pos);
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
        // For integer position, convert to float and set position
        sf::Vector2i vec = PyObject_to_sfVector2i(value);
        if (PyErr_Occurred()) {
            return -1;  // Error already set by PyObject_to_sfVector2i
        }
        self->data->position = sf::Vector2f(static_cast<float>(vec.x), 
                                            static_cast<float>(vec.y));
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
        PyErr_SetString(PyExc_TypeError, "sprite_index must be an integer");
        return -1;
    }
    //self->data->sprite.sprite_index = val;
    self->data->sprite.setSpriteIndex(val); // todone - I don't like ".sprite.sprite" in this stack of UIEntity.UISprite.sf::Sprite
    return 0;
}

PyObject* UIEntity::get_float_member(PyUIEntityObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0) // x
        return PyFloat_FromDouble(self->data->position.x);
    else if (member_ptr == 1) // y
        return PyFloat_FromDouble(self->data->position.y);
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIEntity::set_float_member(PyUIEntityObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Position must be a number (int or float)");
        return -1;
    }
    if (member_ptr == 0) // x
    {
        self->data->position.x = val;
    }
    else if (member_ptr == 1) // y
    {
        self->data->position.y = val;
    }
    return 0;
}

PyObject* UIEntity::die(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored))
{
    // Check if entity has a grid
    if (!self->data || !self->data->grid) {
        Py_RETURN_NONE;  // Entity not on a grid, nothing to do
    }
    
    // Remove entity from grid's entity list
    auto grid = self->data->grid;
    auto& entities = grid->entities;
    
    // Find and remove this entity from the list
    auto it = std::find_if(entities->begin(), entities->end(),
        [self](const std::shared_ptr<UIEntity>& e) {
            return e.get() == self->data.get();
        });
    
    if (it != entities->end()) {
        entities->erase(it);
        // Clear the grid reference
        self->data->grid.reset();
    }
    
    Py_RETURN_NONE;
}

PyObject* UIEntity::path_to(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"target_x", "target_y", "x", "y", nullptr};
    int target_x = -1, target_y = -1;
    
    // Parse arguments - support both target_x/target_y and x/y parameter names
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ii", const_cast<char**>(keywords), 
                                     &target_x, &target_y)) {
        PyErr_Clear();
        // Try alternative parameter names
        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iiii", const_cast<char**>(keywords), 
                                         &target_x, &target_y, &target_x, &target_y)) {
            PyErr_SetString(PyExc_TypeError, "path_to() requires target_x and target_y integer arguments");
            return NULL;
        }
    }
    
    // Check if entity has a grid
    if (!self->data || !self->data->grid) {
        PyErr_SetString(PyExc_ValueError, "Entity must be associated with a grid to compute paths");
        return NULL;
    }
    
    // Get current position
    int current_x = static_cast<int>(self->data->position.x);
    int current_y = static_cast<int>(self->data->position.y);
    
    // Validate target position
    auto grid = self->data->grid;
    if (target_x < 0 || target_x >= grid->grid_x || target_y < 0 || target_y >= grid->grid_y) {
        PyErr_Format(PyExc_ValueError, "Target position (%d, %d) is out of grid bounds (0-%d, 0-%d)", 
                     target_x, target_y, grid->grid_x - 1, grid->grid_y - 1);
        return NULL;
    }
    
    // Use the grid's Dijkstra implementation
    grid->computeDijkstra(current_x, current_y);
    auto path = grid->getDijkstraPath(target_x, target_y);
    
    // Convert path to Python list of tuples
    PyObject* path_list = PyList_New(path.size());
    if (!path_list) return PyErr_NoMemory();
    
    for (size_t i = 0; i < path.size(); ++i) {
        PyObject* coord_tuple = PyTuple_New(2);
        if (!coord_tuple) {
            Py_DECREF(path_list);
            return PyErr_NoMemory();
        }
        
        PyTuple_SetItem(coord_tuple, 0, PyLong_FromLong(path[i].first));
        PyTuple_SetItem(coord_tuple, 1, PyLong_FromLong(path[i].second));
        PyList_SetItem(path_list, i, coord_tuple);
    }
    
    return path_list;
}

PyObject* UIEntity::update_visibility(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored))
{
    self->data->updateVisibility();
    Py_RETURN_NONE;
}

PyMethodDef UIEntity::methods[] = {
    {"at", (PyCFunction)UIEntity::at, METH_O},
    {"index", (PyCFunction)UIEntity::index, METH_NOARGS, "Return the index of this entity in its grid's entity collection"},
    {"die", (PyCFunction)UIEntity::die, METH_NOARGS, "Remove this entity from its grid"},
    {"path_to", (PyCFunction)UIEntity::path_to, METH_VARARGS | METH_KEYWORDS, "Find path from entity to target position using Dijkstra pathfinding"},
    {"update_visibility", (PyCFunction)UIEntity::update_visibility, METH_NOARGS, "Update entity's visibility state based on current FOV"},
    {NULL, NULL, 0, NULL}
};

// Define the PyObjectType alias for the macros
typedef PyUIEntityObject PyObjectType;

// Combine base methods with entity-specific methods
PyMethodDef UIEntity_all_methods[] = {
    UIDRAWABLE_METHODS,
    {"at", (PyCFunction)UIEntity::at, METH_O},
    {"index", (PyCFunction)UIEntity::index, METH_NOARGS, "Return the index of this entity in its grid's entity collection"},
    {"die", (PyCFunction)UIEntity::die, METH_NOARGS, "Remove this entity from its grid"},
    {"path_to", (PyCFunction)UIEntity::path_to, METH_VARARGS | METH_KEYWORDS, "Find path from entity to target position using Dijkstra pathfinding"},
    {"update_visibility", (PyCFunction)UIEntity::update_visibility, METH_NOARGS, "Update entity's visibility state based on current FOV"},
    {NULL}  // Sentinel
};

PyGetSetDef UIEntity::getsetters[] = {
    {"draw_pos", (getter)UIEntity::get_position, (setter)UIEntity::set_position, "Entity position (graphically)", (void*)0},
    {"pos", (getter)UIEntity::get_position, (setter)UIEntity::set_position, "Entity position (integer grid coordinates)", (void*)1},
    {"gridstate", (getter)UIEntity::get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"sprite_index", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite index on the texture on the display", NULL},
    {"sprite_number", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite index (DEPRECATED: use sprite_index instead)", NULL},
    {"x", (getter)UIEntity::get_float_member, (setter)UIEntity::set_float_member, "Entity x position", (void*)0},
    {"y", (getter)UIEntity::get_float_member, (setter)UIEntity::set_float_member, "Entity y position", (void*)1},
    {"visible", (getter)UIEntity_get_visible, (setter)UIEntity_set_visible, "Visibility flag", NULL},
    {"opacity", (getter)UIEntity_get_opacity, (setter)UIEntity_set_opacity, "Opacity (0.0 = transparent, 1.0 = opaque)", NULL},
    {"name", (getter)UIEntity_get_name, (setter)UIEntity_set_name, "Name for finding elements", NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIEntity::repr(PyUIEntityObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<Entity (invalid internal object)>";
    else {
        auto ent = self->data;
        ss << "<Entity (x=" << self->data->position.x << ", y=" << self->data->position.y << ", sprite_index=" << self->data->sprite.getSpriteIndex() <<
         ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// Property system implementation for animations
bool UIEntity::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        // Don't update sprite position here - UIGrid::render() handles the pixel positioning
        return true;
    }
    else if (name == "y") {
        position.y = value;
        // Don't update sprite position here - UIGrid::render() handles the pixel positioning
        return true;
    }
    else if (name == "sprite_scale") {
        sprite.setScale(sf::Vector2f(value, value));
        return true;
    }
    return false;
}

bool UIEntity::setProperty(const std::string& name, int value) {
    if (name == "sprite_index" || name == "sprite_number") {
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
