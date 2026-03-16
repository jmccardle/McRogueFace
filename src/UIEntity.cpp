#include "UIEntity.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include <algorithm>
#include <cstring>
#include <libtcod.h>
#include "PyVector.h"
#include "PythonObjectCache.h"
#include "PyFOV.h"
#include "Animation.h"
#include "PyAnimation.h"
#include "PyEasing.h"
#include "PyPositionHelper.h"
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support
// UIDrawable methods now in UIBase.h
#include "UIEntityPyMethods.h"



UIEntity::UIEntity()
: grid(nullptr), position(0.0f, 0.0f), sprite_offset(0.0f, 0.0f)
{
    // Initialize sprite with safe defaults (sprite has its own safe constructor now)
    // gridstate vector starts empty - will be lazily initialized when needed
}

UIEntity::~UIEntity() {
    releasePyIdentity();
    if (serial_number != 0) {
        PythonObjectCache::getInstance().remove(serial_number);
    }
}

// Removed UIEntity(UIGrid&) constructor - using lazy initialization instead

void UIEntity::ensureGridstate()
{
    if (!grid) return;
    size_t expected = static_cast<size_t>(grid->grid_w) * grid->grid_h;
    if (gridstate.size() != expected) {
        gridstate.resize(expected);
        for (auto& state : gridstate) {
            state.visible = false;
            state.discovered = false;
        }
    }
}

void UIEntity::updateVisibility()
{
    if (!grid) return;

    ensureGridstate();

    // First, mark all cells as not visible
    for (auto& state : gridstate) {
        state.visible = false;
    }

    // Compute FOV from entity's cell position (#114, #295)
    int x = cell_position.x;
    int y = cell_position.y;

    // Use grid's configured FOV algorithm and radius
    grid->computeFOV(x, y, grid->fov_radius, true, grid->fov_algorithm);

    // Update visible cells based on FOV computation
    for (int gy = 0; gy < grid->grid_h; gy++) {
        for (int gx = 0; gx < grid->grid_w; gx++) {
            int idx = gy * grid->grid_w + gx;
            if (grid->isInFOV(gx, gy)) {
                gridstate[idx].visible = true;
                gridstate[idx].discovered = true;  // Once seen, always discovered
            }
        }
    }

    // #113 - Update any ColorLayers bound to this entity via perspective
    // Get shared_ptr to self for comparison
    std::shared_ptr<UIEntity> self_ptr = nullptr;
    if (grid->entities) {
        for (auto& entity : *grid->entities) {
            if (entity.get() == this) {
                self_ptr = entity;
                break;
            }
        }
    }

    if (self_ptr) {
        for (auto& layer : grid->layers) {
            if (layer->type == GridLayerType::Color) {
                auto color_layer = std::static_pointer_cast<ColorLayer>(layer);
                if (color_layer->has_perspective) {
                    auto bound_entity = color_layer->perspective_entity.lock();
                    if (bound_entity && bound_entity.get() == this) {
                        color_layer->updatePerspective();
                    }
                }
            }
        }
    }
}

PyObject* UIEntity::at(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    int x, y;
    if (!PyPosition_ParseInt(args, kwds, &x, &y)) {
        return NULL;  // Error already set by PyPosition_ParseInt
    }

    if (self->data->grid == NULL) {
        PyErr_SetString(PyExc_ValueError, "Entity cannot access surroundings because it is not associated with a grid");
        return NULL;
    }

    self->data->ensureGridstate();

    // Bounds check
    if (x < 0 || x >= self->data->grid->grid_w || y < 0 || y >= self->data->grid->grid_h) {
        PyErr_Format(PyExc_IndexError, "Grid coordinates (%d, %d) out of bounds", x, y);
        return NULL;
    }

    // Use type directly since GridPointState is internal-only (not exported to module)
    auto type = &mcrfpydef::PyUIGridPointStateType;
    auto obj = (PyUIGridPointStateObject*)type->tp_alloc(type, 0);
    obj->grid = self->data->grid;
    obj->entity = self->data;
    obj->x = x;  // #16 - Store position for .point property
    obj->y = y;
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
    // Define all parameters with defaults
    PyObject* grid_pos_obj = nullptr;
    PyObject* texture = nullptr;
    int sprite_index = 0;
    PyObject* grid_obj = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f;
    PyObject* sprite_offset_obj = nullptr;
    PyObject* labels_obj = nullptr;

    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "grid_pos", "texture", "sprite_index",  // Positional args (as per spec)
        // Keyword-only args
        "grid", "visible", "opacity", "name", "x", "y", "sprite_offset", "labels",
        nullptr
    };

    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOiOifzffOO", const_cast<char**>(kwlist),
                                     &grid_pos_obj, &texture, &sprite_index,  // Positional
                                     &grid_obj, &visible, &opacity, &name, &x, &y, &sprite_offset_obj, &labels_obj)) {
        return -1;
    }
    
    // Handle grid position argument (can be tuple or use x/y keywords)
    if (grid_pos_obj) {
        if (PyTuple_Check(grid_pos_obj) && PyTuple_Size(grid_pos_obj) == 2) {
            PyObject* x_val = PyTuple_GetItem(grid_pos_obj, 0);
            PyObject* y_val = PyTuple_GetItem(grid_pos_obj, 1);
            if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
            } else {
                PyErr_SetString(PyExc_TypeError, "grid_pos tuple must contain numbers");
                return -1;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_pos must be a tuple (x, y)");
            return -1;
        }
    }

    // Handle texture argument
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (texture && texture != Py_None) {
        if (!PyObject_IsInstance(texture, (PyObject*)&mcrfpydef::PyTextureType)) {
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
            return -1;
        }
        auto pytexture = (PyTextureObject*)texture;
        texture_ptr = pytexture->data;
    } else {
        // Use default texture when None or not provided
        texture_ptr = McRFPy_API::default_texture;
    }
    
    // Handle grid argument
    if (grid_obj && !PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyUIGridType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a mcrfpy.Grid instance");
        return -1;
    }

    // Create the entity
    self->data = std::make_shared<UIEntity>();
    
    // Initialize weak reference list
    self->weakreflist = NULL;

    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }

    // Hold a strong reference to preserve Python subclass identity.
    // Without this, the Python wrapper can be GC'd while the C++ entity
    // lives on in a grid, and later access returns a base Entity wrapper
    // that lacks subclass methods. Cleared in die() and set_grid(None).
    self->data->pyobject = (PyObject*)self;
    Py_INCREF(self);
    
    // Set texture and sprite index
    if (texture_ptr) {
        self->data->sprite = UISprite(texture_ptr, sprite_index, sf::Vector2f(0,0), 1.0);
    } else {
        // Create an empty sprite for testing
        self->data->sprite = UISprite();
    }
    
    // Set position using grid coordinates
    self->data->position = sf::Vector2f(x, y);
    // #295: Initialize cell_position from grid coordinates
    self->data->cell_position = sf::Vector2i(static_cast<int>(x), static_cast<int>(y));

    // Handle sprite_offset argument (optional tuple, default (0,0))
    if (sprite_offset_obj && sprite_offset_obj != Py_None) {
        sf::Vector2f offset = PyObject_to_sfVector2f(sprite_offset_obj);
        if (PyErr_Occurred()) {
            return -1;
        }
        self->data->sprite_offset = offset;
    }

    // Set other properties (delegate to sprite)
    self->data->sprite.visible = visible;
    self->data->sprite.opacity = opacity;
    if (name) {
        self->data->sprite.name = std::string(name);
    }
    
    // #296 - Parse labels kwarg
    if (labels_obj && labels_obj != Py_None) {
        PyObject* iter = PyObject_GetIter(labels_obj);
        if (!iter) {
            PyErr_SetString(PyExc_TypeError, "labels must be iterable");
            return -1;
        }
        PyObject* item;
        while ((item = PyIter_Next(iter)) != NULL) {
            if (!PyUnicode_Check(item)) {
                Py_DECREF(item);
                Py_DECREF(iter);
                PyErr_SetString(PyExc_TypeError, "labels must contain only strings");
                return -1;
            }
            self->data->labels.insert(PyUnicode_AsUTF8(item));
            Py_DECREF(item);
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) return -1;
    }

    // Handle grid attachment
    if (grid_obj) {
        PyUIGridObject* pygrid = (PyUIGridObject*)grid_obj;
        self->data->grid = pygrid->data;
        // Append entity to grid's entity list
        pygrid->data->entities->push_back(self->data);
        // Insert into spatial hash for O(1) cell queries (#253)
        pygrid->data->spatial_hash.insert(self->data);

        // Don't initialize gridstate here - lazy initialization to support large numbers of entities
        // gridstate will be initialized when visibility is updated or accessed
    }
    return 0;
}



PyObject* UIEntity::get_spritenumber(PyUIEntityObject* self, void* closure) {
    return PyLong_FromDouble(self->data->sprite.getSpriteIndex());
}

PyObject* sfVector2f_to_PyObject(sf::Vector2f vec) {
    auto type = &mcrfpydef::PyVectorType;
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        obj->data = vec;
    }
    return (PyObject*)obj;
}

PyObject* sfVector2i_to_PyObject(sf::Vector2i vec) {
    auto type = &mcrfpydef::PyVectorType;
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
    // Return a simple namespace with visible/discovered attributes
    // (detached snapshot — not backed by a live entity's gridstate)
    PyObject* types_mod = PyImport_ImportModule("types");
    if (!types_mod) return NULL;
    PyObject* ns_type = PyObject_GetAttrString(types_mod, "SimpleNamespace");
    Py_DECREF(types_mod);
    if (!ns_type) return NULL;
    PyObject* kwargs = Py_BuildValue("{s:O,s:O}",
        "visible", state.visible ? Py_True : Py_False,
        "discovered", state.discovered ? Py_True : Py_False);
    if (!kwargs) { Py_DECREF(ns_type); return NULL; }
    PyObject* obj = PyObject_Call(ns_type, PyTuple_New(0), kwargs);
    Py_DECREF(ns_type);
    Py_DECREF(kwargs);

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
    if (reinterpret_cast<intptr_t>(closure) == 0) {
        return sfVector2f_to_PyObject(self->data->position);
    } else {
        // Return integer-cast position for grid coordinates
        sf::Vector2i int_pos(static_cast<int>(self->data->position.x), 
                             static_cast<int>(self->data->position.y));
        return sfVector2i_to_PyObject(int_pos);
    }
}

int UIEntity::set_position(PyUIEntityObject* self, PyObject* value, void* closure) {
    // Save old position for spatial hash update (#115)
    float old_x = self->data->position.x;
    float old_y = self->data->position.y;

    if (reinterpret_cast<intptr_t>(closure) == 0) {
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

    // Update spatial hash if grid exists (#115)
    if (self->data->grid) {
        self->data->grid->spatial_hash.update(self->data, old_x, old_y);
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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

    // Save old position for spatial hash update (#115)
    float old_x = self->data->position.x;
    float old_y = self->data->position.y;

    if (member_ptr == 0) // x
    {
        self->data->position.x = val;
    }
    else if (member_ptr == 1) // y
    {
        self->data->position.y = val;
    }

    // Update spatial hash if grid exists (#115)
    if (self->data->grid) {
        self->data->grid->spatial_hash.update(self->data, old_x, old_y);
    }

    return 0;
}

// #176 - Helper to get cell dimensions from grid
static void get_cell_dimensions(UIEntity* entity, float& cell_width, float& cell_height) {
    // Default cell dimensions when no texture
    constexpr float DEFAULT_CELL_WIDTH = 16.0f;
    constexpr float DEFAULT_CELL_HEIGHT = 16.0f;

    if (entity->grid) {
        auto ptex = entity->grid->getTexture();
        cell_width = ptex ? static_cast<float>(ptex->sprite_width) : DEFAULT_CELL_WIDTH;
        cell_height = ptex ? static_cast<float>(ptex->sprite_height) : DEFAULT_CELL_HEIGHT;
    } else {
        cell_width = DEFAULT_CELL_WIDTH;
        cell_height = DEFAULT_CELL_HEIGHT;
    }
}

// #176 - Pixel position: pos = draw_pos * tile_size
PyObject* UIEntity::get_pixel_pos(PyUIEntityObject* self, void* closure) {
    if (!self->data->grid) {
        PyErr_SetString(PyExc_RuntimeError, "entity is not attached to a Grid");
        return NULL;
    }

    float cell_width, cell_height;
    get_cell_dimensions(self->data.get(), cell_width, cell_height);

    sf::Vector2f pixel_pos(
        self->data->position.x * cell_width,
        self->data->position.y * cell_height
    );
    return sfVector2f_to_PyObject(pixel_pos);
}

int UIEntity::set_pixel_pos(PyUIEntityObject* self, PyObject* value, void* closure) {
    if (!self->data->grid) {
        PyErr_SetString(PyExc_RuntimeError, "entity is not attached to a Grid");
        return -1;
    }

    sf::Vector2f pixel_vec = PyObject_to_sfVector2f(value);
    if (PyErr_Occurred()) {
        return -1;
    }

    float cell_width, cell_height;
    get_cell_dimensions(self->data.get(), cell_width, cell_height);

    // Save old position for spatial hash update
    float old_x = self->data->position.x;
    float old_y = self->data->position.y;

    // Convert pixels to tile coordinates
    self->data->position.x = pixel_vec.x / cell_width;
    self->data->position.y = pixel_vec.y / cell_height;

    // Update spatial hash
    self->data->grid->spatial_hash.update(self->data, old_x, old_y);

    return 0;
}

// #176 - Individual pixel coordinates (x, y)
PyObject* UIEntity::get_pixel_member(PyUIEntityObject* self, void* closure) {
    if (!self->data->grid) {
        PyErr_SetString(PyExc_RuntimeError, "entity is not attached to a Grid");
        return NULL;
    }

    float cell_width, cell_height;
    get_cell_dimensions(self->data.get(), cell_width, cell_height);

    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0) // x
        return PyFloat_FromDouble(self->data->position.x * cell_width);
    else // y
        return PyFloat_FromDouble(self->data->position.y * cell_height);
}

int UIEntity::set_pixel_member(PyUIEntityObject* self, PyObject* value, void* closure) {
    if (!self->data->grid) {
        PyErr_SetString(PyExc_RuntimeError, "entity is not attached to a Grid");
        return -1;
    }

    float val;
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = PyLong_AsLong(value);
    } else {
        PyErr_SetString(PyExc_TypeError, "Position must be a number (int or float)");
        return -1;
    }

    float cell_width, cell_height;
    get_cell_dimensions(self->data.get(), cell_width, cell_height);

    // Save old position for spatial hash update
    float old_x = self->data->position.x;
    float old_y = self->data->position.y;

    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0) // x
        self->data->position.x = val / cell_width;
    else // y
        self->data->position.y = val / cell_height;

    // Update spatial hash
    self->data->grid->spatial_hash.update(self->data, old_x, old_y);

    return 0;
}

// #176 - Integer grid position (grid_x, grid_y)
PyObject* UIEntity::get_grid_int_member(PyUIEntityObject* self, void* closure) {
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0) // grid_x
        return PyLong_FromLong(static_cast<int>(self->data->position.x));
    else // grid_y
        return PyLong_FromLong(static_cast<int>(self->data->position.y));
}

int UIEntity::set_grid_int_member(PyUIEntityObject* self, PyObject* value, void* closure) {
    int val;
    if (PyLong_Check(value)) {
        val = PyLong_AsLong(value);
    } else if (PyFloat_Check(value)) {
        val = static_cast<int>(PyFloat_AsDouble(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "Grid position must be an integer");
        return -1;
    }

    // Save old position for spatial hash update
    float old_x = self->data->position.x;
    float old_y = self->data->position.y;

    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0) // grid_x
        self->data->position.x = static_cast<float>(val);
    else // grid_y
        self->data->position.y = static_cast<float>(val);

    // Update spatial hash if grid exists
    if (self->data->grid) {
        self->data->grid->spatial_hash.update(self->data, old_x, old_y);
    }

    return 0;
}

PyObject* UIEntity::get_grid(PyUIEntityObject* self, void* closure)
{
    if (!self->data || !self->data->grid) {
        Py_RETURN_NONE;
    }

    auto& grid = self->data->grid;

    // Check cache first — preserves identity (entity.grid is entity.grid)
    if (grid->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(grid->serial_number);
        if (cached) {
            return cached;  // Already INCREF'd by lookup
        }
    }

    // No cached wrapper — allocate a new one
    auto grid_type = &mcrfpydef::PyUIGridType;
    auto pyGrid = (PyUIGridObject*)grid_type->tp_alloc(grid_type, 0);

    if (pyGrid) {
        pyGrid->data = grid;
        pyGrid->weakreflist = NULL;

        // Register in cache so future accesses return the same wrapper
        if (grid->serial_number == 0) {
            grid->serial_number = PythonObjectCache::getInstance().assignSerial();
        }
        PyObject* weakref = PyWeakref_NewRef((PyObject*)pyGrid, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(grid->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }
    return (PyObject*)pyGrid;
}

int UIEntity::set_grid(PyUIEntityObject* self, PyObject* value, void* closure)
{
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return -1;
    }

    // Handle None - remove from current grid
    if (value == Py_None) {
        if (self->data->grid) {
            // Remove from spatial hash before removing from entity list
            self->data->grid->spatial_hash.remove(self->data);
            // Remove from current grid's entity list
            auto& entities = self->data->grid->entities;
            auto it = std::find_if(entities->begin(), entities->end(),
                [self](const std::shared_ptr<UIEntity>& e) {
                    return e.get() == self->data.get();
                });
            if (it != entities->end()) {
                entities->erase(it);
            }
            self->data->grid.reset();

            // Release identity strong ref — entity left grid
            self->data->releasePyIdentity();
        }
        return 0;
    }

    // Value must be a Grid
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a Grid or None");
        return -1;
    }

    auto new_grid = ((PyUIGridObject*)value)->data;

    // Remove from old grid first (if any)
    if (self->data->grid && self->data->grid != new_grid) {
        self->data->grid->spatial_hash.remove(self->data);
        auto& old_entities = self->data->grid->entities;
        auto it = std::find_if(old_entities->begin(), old_entities->end(),
            [self](const std::shared_ptr<UIEntity>& e) {
                return e.get() == self->data.get();
            });
        if (it != old_entities->end()) {
            old_entities->erase(it);
        }
    }

    // Add to new grid
    if (self->data->grid != new_grid) {
        new_grid->entities->push_back(self->data);
        self->data->grid = new_grid;

        // Resize gridstate to match new grid dimensions
        self->data->ensureGridstate();
    }

    return 0;
}

// sprite_offset property - Vector (tuple)
PyObject* UIEntity::get_sprite_offset(PyUIEntityObject* self, void* closure) {
    return sfVector2f_to_PyObject(self->data->sprite_offset);
}

int UIEntity::set_sprite_offset(PyUIEntityObject* self, PyObject* value, void* closure) {
    sf::Vector2f vec = PyObject_to_sfVector2f(value);
    if (PyErr_Occurred()) return -1;
    self->data->sprite_offset = vec;
    if (self->data->grid) self->data->grid->markDirty();
    return 0;
}

// sprite_offset_x / sprite_offset_y individual components
PyObject* UIEntity::get_sprite_offset_member(PyUIEntityObject* self, void* closure) {
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->sprite_offset.x);
    else
        return PyFloat_FromDouble(self->data->sprite_offset.y);
}

int UIEntity::set_sprite_offset_member(PyUIEntityObject* self, PyObject* value, void* closure) {
    float val;
    if (PyFloat_Check(value))
        val = PyFloat_AsDouble(value);
    else if (PyLong_Check(value))
        val = PyLong_AsLong(value);
    else {
        PyErr_SetString(PyExc_TypeError, "sprite_offset component must be a number");
        return -1;
    }
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0)
        self->data->sprite_offset.x = val;
    else
        self->data->sprite_offset.y = val;
    if (self->data->grid) self->data->grid->markDirty();
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
        // Remove from spatial hash before erasing (#115)
        grid->spatial_hash.remove(self->data);

        entities->erase(it);
        // Clear the grid reference
        self->data->grid.reset();

        // Release identity strong ref — entity is no longer in a grid
        self->data->releasePyIdentity();
    }

    Py_RETURN_NONE;
}

PyObject* UIEntity::path_to(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    int target_x, target_y;

    // Parse position using flexible position helper
    // Supports: path_to(x, y), path_to((x, y)), path_to(pos=(x, y)), path_to(Vector(x, y))
    if (!PyPosition_ParseInt(args, kwds, &target_x, &target_y)) {
        return NULL;  // Error already set by PyPosition_ParseInt
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
    if (target_x < 0 || target_x >= grid->grid_w || target_y < 0 || target_y >= grid->grid_h) {
        PyErr_Format(PyExc_ValueError, "Target position (%d, %d) is out of grid bounds (0-%d, 0-%d)",
                     target_x, target_y, grid->grid_w - 1, grid->grid_h - 1);
        return NULL;
    }

    // Use A* pathfinding via temporary TCODPath
    TCODPath tcod_path(grid->getTCODMap(), 1.41f);
    if (!tcod_path.compute(current_x, current_y, target_x, target_y)) {
        // No path found - return empty list
        return PyList_New(0);
    }

    // Convert path to Python list of tuples
    PyObject* path_list = PyList_New(tcod_path.size());
    if (!path_list) return PyErr_NoMemory();

    for (int i = 0; i < tcod_path.size(); ++i) {
        int px, py;
        tcod_path.get(i, &px, &py);

        PyObject* coord_tuple = PyTuple_New(2);
        if (!coord_tuple) {
            Py_DECREF(path_list);
            return PyErr_NoMemory();
        }

        PyTuple_SetItem(coord_tuple, 0, PyLong_FromLong(px));
        PyTuple_SetItem(coord_tuple, 1, PyLong_FromLong(py));
        PyList_SetItem(path_list, i, coord_tuple);
    }

    return path_list;
}

PyObject* UIEntity::update_visibility(PyUIEntityObject* self, PyObject* Py_UNUSED(ignored))
{
    self->data->updateVisibility();
    Py_RETURN_NONE;
}

PyObject* UIEntity::visible_entities(PyUIEntityObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"fov", "radius", nullptr};
    PyObject* fov_arg = nullptr;
    int radius = -1;  // -1 means use grid default

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|Oi", const_cast<char**>(keywords),
                                     &fov_arg, &radius)) {
        return NULL;
    }

    // Check if entity has a grid
    if (!self->data || !self->data->grid) {
        PyErr_SetString(PyExc_ValueError, "Entity must be associated with a grid to find visible entities");
        return NULL;
    }

    auto grid = self->data->grid;

    // Parse FOV algorithm - use grid default if not specified
    TCOD_fov_algorithm_t algorithm = grid->fov_algorithm;
    bool fov_was_none = false;
    if (fov_arg && fov_arg != Py_None) {
        if (PyFOV::from_arg(fov_arg, &algorithm, &fov_was_none) < 0) {
            return NULL;  // Error already set
        }
    }

    // Use grid radius if not specified
    if (radius < 0) {
        radius = grid->fov_radius;
    }

    // Get current cell position (#295)
    int x = self->data->cell_position.x;
    int y = self->data->cell_position.y;

    // Compute FOV from this entity's cell position
    grid->computeFOV(x, y, radius, true, algorithm);

    // Create result list
    PyObject* result = PyList_New(0);
    if (!result) return PyErr_NoMemory();

    // Get Entity type for creating Python objects
    auto entity_type = &mcrfpydef::PyUIEntityType;

    // Iterate through all entities in the grid
    if (grid->entities) {
        for (auto& entity : *grid->entities) {
            // Skip self
            if (entity.get() == self->data.get()) {
                continue;
            }

            // Check if entity is in FOV (#295: use cell_position)
            int ex = entity->cell_position.x;
            int ey = entity->cell_position.y;

            if (grid->isInFOV(ex, ey)) {
                // Create Python Entity object for this entity
                auto pyEntity = (PyUIEntityObject*)entity_type->tp_alloc(entity_type, 0);
                if (!pyEntity) {
                    Py_DECREF(result);
                    return PyErr_NoMemory();
                }

                pyEntity->data = entity;
                pyEntity->weakreflist = NULL;

                if (PyList_Append(result, (PyObject*)pyEntity) < 0) {
                    Py_DECREF(pyEntity);
                    Py_DECREF(result);
                    return NULL;
                }
                Py_DECREF(pyEntity);  // List now owns the reference
            }
        }
    }

    return result;
}

PyMethodDef UIEntity::methods[] = {
    {"at", (PyCFunction)UIEntity::at, METH_VARARGS | METH_KEYWORDS,
     "at(x, y) or at(pos) -> GridPointState\n\n"
     "Get the grid point state at the specified position.\n\n"
     "Args:\n"
     "    x, y: Grid coordinates as two integers, OR\n"
     "    pos: Grid coordinates as tuple, list, or Vector\n\n"
     "Returns:\n"
     "    GridPointState for the entity's view of that grid cell.\n\n"
     "Example:\n"
     "    state = entity.at(5, 3)\n"
     "    state = entity.at((5, 3))\n"
     "    state = entity.at(pos=(5, 3))"},
    {"index", (PyCFunction)UIEntity::index, METH_NOARGS, "Return the index of this entity in its grid's entity collection"},
    {"die", (PyCFunction)UIEntity::die, METH_NOARGS,
     "Remove this entity from its grid.\n\n"
     "Warning: Do not call during iteration over grid.entities.\n"
     "Modifying the collection during iteration raises RuntimeError."},
    {"path_to", (PyCFunction)UIEntity::path_to, METH_VARARGS | METH_KEYWORDS,
     "path_to(x, y) or path_to(target) -> list\n\n"
     "Find a path to the target position using Dijkstra pathfinding.\n\n"
     "Args:\n"
     "    x, y: Target coordinates as two integers, OR\n"
     "    target: Target coordinates as tuple, list, or Vector\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path.\n\n"
     "Example:\n"
     "    path = entity.path_to(10, 5)\n"
     "    path = entity.path_to((10, 5))\n"
     "    path = entity.path_to(pos=(10, 5))"},
    {"update_visibility", (PyCFunction)UIEntity::update_visibility, METH_NOARGS,
     "update_visibility() -> None\n\n"
     "Update entity's visibility state based on current FOV.\n\n"
     "Recomputes which cells are visible from the entity's position and updates\n"
     "the entity's gridstate to track explored areas. This is called automatically\n"
     "when the entity moves if it has a grid with perspective set."},
    {"visible_entities", (PyCFunction)UIEntity::visible_entities, METH_VARARGS | METH_KEYWORDS,
     "visible_entities(fov=None, radius=None) -> list[Entity]\n\n"
     "Get list of other entities visible from this entity's position.\n\n"
     "Args:\n"
     "    fov (FOV, optional): FOV algorithm to use. Default: grid.fov\n"
     "    radius (int, optional): FOV radius. Default: grid.fov_radius\n\n"
     "Returns:\n"
     "    List of Entity objects that are within field of view.\n\n"
     "Computes FOV from this entity's position and returns all other entities\n"
     "whose positions fall within the visible area."},
    {NULL, NULL, 0, NULL}
};

// Define the PyObjectType alias for the macros
typedef PyUIEntityObject PyObjectType;

// Combine base methods with entity-specific methods
// Note: Use UIDRAWABLE_METHODS_BASE (not UIDRAWABLE_METHODS) because UIEntity is NOT a UIDrawable
// and the template-based animate helper won't work. Entity has its own animate() method.
// #296 - Label system implementations
PyObject* UIEntity::get_labels(PyUIEntityObject* self, void* closure) {
    PyObject* frozen = PyFrozenSet_New(NULL);
    if (!frozen) return NULL;

    for (const auto& label : self->data->labels) {
        PyObject* str = PyUnicode_FromString(label.c_str());
        if (!str) { Py_DECREF(frozen); return NULL; }
        if (PySet_Add(frozen, str) < 0) {
            Py_DECREF(str); Py_DECREF(frozen); return NULL;
        }
        Py_DECREF(str);
    }
    return frozen;
}

int UIEntity::set_labels(PyUIEntityObject* self, PyObject* value, void* closure) {
    PyObject* iter = PyObject_GetIter(value);
    if (!iter) {
        PyErr_SetString(PyExc_TypeError, "labels must be iterable");
        return -1;
    }

    std::unordered_set<std::string> new_labels;
    PyObject* item;
    while ((item = PyIter_Next(iter)) != NULL) {
        if (!PyUnicode_Check(item)) {
            Py_DECREF(item);
            Py_DECREF(iter);
            PyErr_SetString(PyExc_TypeError, "labels must contain only strings");
            return -1;
        }
        new_labels.insert(PyUnicode_AsUTF8(item));
        Py_DECREF(item);
    }
    Py_DECREF(iter);
    if (PyErr_Occurred()) return -1;

    self->data->labels = std::move(new_labels);
    return 0;
}

PyObject* UIEntity::py_add_label(PyUIEntityObject* self, PyObject* arg) {
    if (!PyUnicode_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "label must be a string");
        return NULL;
    }
    self->data->labels.insert(PyUnicode_AsUTF8(arg));
    Py_RETURN_NONE;
}

PyObject* UIEntity::py_remove_label(PyUIEntityObject* self, PyObject* arg) {
    if (!PyUnicode_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "label must be a string");
        return NULL;
    }
    self->data->labels.erase(PyUnicode_AsUTF8(arg));
    Py_RETURN_NONE;
}

PyObject* UIEntity::py_has_label(PyUIEntityObject* self, PyObject* arg) {
    if (!PyUnicode_Check(arg)) {
        PyErr_SetString(PyExc_TypeError, "label must be a string");
        return NULL;
    }
    if (self->data->labels.count(PyUnicode_AsUTF8(arg))) {
        Py_RETURN_TRUE;
    }
    Py_RETURN_FALSE;
}

// #299 - Step callback and default_behavior implementations
PyObject* UIEntity::get_step(PyUIEntityObject* self, void* closure) {
    if (self->data->step_callback) {
        Py_INCREF(self->data->step_callback);
        return self->data->step_callback;
    }
    Py_RETURN_NONE;
}

int UIEntity::set_step(PyUIEntityObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        Py_XDECREF(self->data->step_callback);
        self->data->step_callback = nullptr;
        return 0;
    }
    if (!PyCallable_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "step must be callable or None");
        return -1;
    }
    Py_XDECREF(self->data->step_callback);
    Py_INCREF(value);
    self->data->step_callback = value;
    return 0;
}

PyObject* UIEntity::get_default_behavior(PyUIEntityObject* self, void* closure) {
    return PyLong_FromLong(self->data->default_behavior);
}

int UIEntity::set_default_behavior(PyUIEntityObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (val == -1 && PyErr_Occurred()) return -1;
    self->data->default_behavior = static_cast<int>(val);
    return 0;
}

// #300 - Behavior system property implementations
PyObject* UIEntity::get_behavior_type(PyUIEntityObject* self, void* closure) {
    return PyLong_FromLong(static_cast<int>(self->data->behavior.type));
}

PyObject* UIEntity::get_turn_order(PyUIEntityObject* self, void* closure) {
    return PyLong_FromLong(self->data->turn_order);
}

int UIEntity::set_turn_order(PyUIEntityObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (val == -1 && PyErr_Occurred()) return -1;
    self->data->turn_order = static_cast<int>(val);
    return 0;
}

PyObject* UIEntity::get_move_speed(PyUIEntityObject* self, void* closure) {
    return PyFloat_FromDouble(self->data->move_speed);
}

int UIEntity::set_move_speed(PyUIEntityObject* self, PyObject* value, void* closure) {
    double val = PyFloat_AsDouble(value);
    if (val == -1.0 && PyErr_Occurred()) return -1;
    self->data->move_speed = static_cast<float>(val);
    return 0;
}

PyObject* UIEntity::get_target_label(PyUIEntityObject* self, void* closure) {
    if (self->data->target_label.empty()) Py_RETURN_NONE;
    return PyUnicode_FromString(self->data->target_label.c_str());
}

int UIEntity::set_target_label(PyUIEntityObject* self, PyObject* value, void* closure) {
    if (value == Py_None) {
        self->data->target_label.clear();
        return 0;
    }
    if (!PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "target_label must be a string or None");
        return -1;
    }
    self->data->target_label = PyUnicode_AsUTF8(value);
    return 0;
}

PyObject* UIEntity::get_sight_radius(PyUIEntityObject* self, void* closure) {
    return PyLong_FromLong(self->data->sight_radius);
}

int UIEntity::set_sight_radius(PyUIEntityObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (val == -1 && PyErr_Occurred()) return -1;
    self->data->sight_radius = static_cast<int>(val);
    return 0;
}

PyObject* UIEntity::py_set_behavior(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"type", "waypoints", "turns", "path", nullptr};
    int type_val = 0;
    PyObject* waypoints_obj = nullptr;
    int turns = 0;
    PyObject* path_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "i|OiO", const_cast<char**>(kwlist),
                                     &type_val, &waypoints_obj, &turns, &path_obj)) {
        return NULL;
    }

    auto& behavior = self->data->behavior;
    behavior.reset();
    behavior.type = static_cast<BehaviorType>(type_val);

    // Parse waypoints
    if (waypoints_obj && waypoints_obj != Py_None) {
        PyObject* iter = PyObject_GetIter(waypoints_obj);
        if (!iter) {
            PyErr_SetString(PyExc_TypeError, "waypoints must be iterable");
            return NULL;
        }
        PyObject* item;
        while ((item = PyIter_Next(iter)) != NULL) {
            if (!PyTuple_Check(item) || PyTuple_Size(item) != 2) {
                Py_DECREF(item);
                Py_DECREF(iter);
                PyErr_SetString(PyExc_TypeError, "Each waypoint must be a (x, y) tuple");
                return NULL;
            }
            int wx = PyLong_AsLong(PyTuple_GetItem(item, 0));
            int wy = PyLong_AsLong(PyTuple_GetItem(item, 1));
            Py_DECREF(item);
            if (PyErr_Occurred()) { Py_DECREF(iter); return NULL; }
            behavior.waypoints.push_back({wx, wy});
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) return NULL;
    }

    // Parse path
    if (path_obj && path_obj != Py_None) {
        PyObject* iter = PyObject_GetIter(path_obj);
        if (!iter) {
            PyErr_SetString(PyExc_TypeError, "path must be iterable");
            return NULL;
        }
        PyObject* item;
        while ((item = PyIter_Next(iter)) != NULL) {
            if (!PyTuple_Check(item) || PyTuple_Size(item) != 2) {
                Py_DECREF(item);
                Py_DECREF(iter);
                PyErr_SetString(PyExc_TypeError, "Each path step must be a (x, y) tuple");
                return NULL;
            }
            int px = PyLong_AsLong(PyTuple_GetItem(item, 0));
            int py_val = PyLong_AsLong(PyTuple_GetItem(item, 1));
            Py_DECREF(item);
            if (PyErr_Occurred()) { Py_DECREF(iter); return NULL; }
            behavior.current_path.push_back({px, py_val});
        }
        Py_DECREF(iter);
        if (PyErr_Occurred()) return NULL;
    }

    // Set sleep turns
    if (turns > 0) {
        behavior.sleep_turns_remaining = turns;
    }

    Py_RETURN_NONE;
}

// #295 - cell_pos property implementations
PyObject* UIEntity::get_cell_pos(PyUIEntityObject* self, void* closure) {
    return sfVector2i_to_PyObject(self->data->cell_position);
}

int UIEntity::set_cell_pos(PyUIEntityObject* self, PyObject* value, void* closure) {
    int old_x = self->data->cell_position.x;
    int old_y = self->data->cell_position.y;

    sf::Vector2f vec = PyObject_to_sfVector2f(value);
    if (PyErr_Occurred()) return -1;

    self->data->cell_position.x = static_cast<int>(vec.x);
    self->data->cell_position.y = static_cast<int>(vec.y);

    // Update spatial hash
    if (self->data->grid) {
        self->data->grid->spatial_hash.updateCell(self->data, old_x, old_y);
    }
    return 0;
}

PyObject* UIEntity::get_cell_member(PyUIEntityObject* self, void* closure) {
    if (reinterpret_cast<intptr_t>(closure) == 0) {
        return PyLong_FromLong(self->data->cell_position.x);
    } else {
        return PyLong_FromLong(self->data->cell_position.y);
    }
}

int UIEntity::set_cell_member(PyUIEntityObject* self, PyObject* value, void* closure) {
    long val = PyLong_AsLong(value);
    if (val == -1 && PyErr_Occurred()) return -1;

    int old_x = self->data->cell_position.x;
    int old_y = self->data->cell_position.y;

    if (reinterpret_cast<intptr_t>(closure) == 0) {
        self->data->cell_position.x = static_cast<int>(val);
    } else {
        self->data->cell_position.y = static_cast<int>(val);
    }

    if (self->data->grid) {
        self->data->grid->spatial_hash.updateCell(self->data, old_x, old_y);
    }
    return 0;
}

PyMethodDef UIEntity_all_methods[] = {
    UIDRAWABLE_METHODS_BASE,
    {"animate", (PyCFunction)UIEntity::animate, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(Entity, animate,
         MCRF_SIG("(property: str, target: Any, duration: float, easing=None, delta=False, loop=False, callback=None, conflict_mode='replace')", "Animation"),
         MCRF_DESC("Create and start an animation on this entity's property."),
         MCRF_ARGS_START
         MCRF_ARG("property", "Name of the property to animate: 'draw_x', 'draw_y' (tile coords), 'sprite_scale', 'sprite_index'")
         MCRF_ARG("target", "Target value - float, int, or list of int (for sprite frame sequences)")
         MCRF_ARG("duration", "Animation duration in seconds")
         MCRF_ARG("easing", "Easing function: Easing enum value, string name, or None for linear")
         MCRF_ARG("delta", "If True, target is relative to current value; if False, target is absolute")
         MCRF_ARG("loop", "If True, animation repeats from start when it reaches the end (default False)")
         MCRF_ARG("callback", "Optional callable invoked when animation completes (not called for looping animations)")
         MCRF_ARG("conflict_mode", "'replace' (default), 'queue', or 'error' if property already animating")
         MCRF_RETURNS("Animation object for monitoring progress")
         MCRF_RAISES("ValueError", "If property name is not valid for Entity (draw_x, draw_y, sprite_scale, sprite_index)")
         MCRF_NOTE("Use 'draw_x'/'draw_y' to animate tile coordinates for smooth movement between grid cells. "
                   "Use list target with loop=True for repeating sprite frame animations.")
     )},
    {"at", (PyCFunction)UIEntity::at, METH_VARARGS | METH_KEYWORDS,
     "at(x, y) or at(pos) -> GridPointState\n\n"
     "Get the grid point state at the specified position.\n\n"
     "Args:\n"
     "    x, y: Grid coordinates as two integers, OR\n"
     "    pos: Grid coordinates as tuple, list, or Vector\n\n"
     "Returns:\n"
     "    GridPointState for the entity's view of that grid cell.\n\n"
     "Example:\n"
     "    state = entity.at(5, 3)\n"
     "    state = entity.at((5, 3))\n"
     "    state = entity.at(pos=(5, 3))"},
    {"index", (PyCFunction)UIEntity::index, METH_NOARGS, "Return the index of this entity in its grid's entity collection"},
    {"die", (PyCFunction)UIEntity::die, METH_NOARGS,
     "Remove this entity from its grid.\n\n"
     "Warning: Do not call during iteration over grid.entities.\n"
     "Modifying the collection during iteration raises RuntimeError."},
    {"path_to", (PyCFunction)UIEntity::path_to, METH_VARARGS | METH_KEYWORDS,
     "path_to(x, y) or path_to(target) -> list\n\n"
     "Find a path to the target position using Dijkstra pathfinding.\n\n"
     "Args:\n"
     "    x, y: Target coordinates as two integers, OR\n"
     "    target: Target coordinates as tuple, list, or Vector\n\n"
     "Returns:\n"
     "    List of (x, y) tuples representing the path.\n\n"
     "Example:\n"
     "    path = entity.path_to(10, 5)\n"
     "    path = entity.path_to((10, 5))\n"
     "    path = entity.path_to(pos=(10, 5))"},
    {"update_visibility", (PyCFunction)UIEntity::update_visibility, METH_NOARGS,
     "update_visibility() -> None\n\n"
     "Update entity's visibility state based on current FOV.\n\n"
     "Recomputes which cells are visible from the entity's position and updates\n"
     "the entity's gridstate to track explored areas. This is called automatically\n"
     "when the entity moves if it has a grid with perspective set."},
    {"visible_entities", (PyCFunction)UIEntity::visible_entities, METH_VARARGS | METH_KEYWORDS,
     "visible_entities(fov=None, radius=None) -> list[Entity]\n\n"
     "Get list of other entities visible from this entity's position.\n\n"
     "Args:\n"
     "    fov (FOV, optional): FOV algorithm to use. Default: grid.fov\n"
     "    radius (int, optional): FOV radius. Default: grid.fov_radius\n\n"
     "Returns:\n"
     "    List of Entity objects that are within field of view.\n\n"
     "Computes FOV from this entity's position and returns all other entities\n"
     "whose positions fall within the visible area."},
    // #296 - Label methods
    {"add_label", (PyCFunction)UIEntity::py_add_label, METH_O,
     "add_label(label: str) -> None\n\n"
     "Add a label to this entity. Idempotent (adding same label twice is safe)."},
    {"remove_label", (PyCFunction)UIEntity::py_remove_label, METH_O,
     "remove_label(label: str) -> None\n\n"
     "Remove a label from this entity. No-op if label not present."},
    {"has_label", (PyCFunction)UIEntity::py_has_label, METH_O,
     "has_label(label: str) -> bool\n\n"
     "Check if this entity has the given label."},
    // #300 - Behavior system
    {"set_behavior", (PyCFunction)UIEntity::py_set_behavior, METH_VARARGS | METH_KEYWORDS,
     "set_behavior(type, waypoints=None, turns=0, path=None) -> None\n\n"
     "Configure this entity's behavior for grid.step() turn management.\n\n"
     "Args:\n"
     "    type (int/Behavior): Behavior type (e.g., Behavior.PATROL)\n"
     "    waypoints (list): List of (x, y) tuples for WAYPOINT/PATROL/LOOP\n"
     "    turns (int): Number of turns for SLEEP behavior\n"
     "    path (list): Pre-computed path as list of (x, y) tuples for PATH behavior"},
    {NULL}  // Sentinel
};

PyGetSetDef UIEntity::getsetters[] = {
    // #176 - Pixel coordinates (relative to grid, like UIDrawable.pos)
    {"pos", (getter)UIEntity::get_pixel_pos, (setter)UIEntity::set_pixel_pos,
     "Pixel position relative to grid (Vector). Computed as draw_pos * tile_size. "
     "Requires entity to be attached to a grid.", NULL},
    {"x", (getter)UIEntity::get_pixel_member, (setter)UIEntity::set_pixel_member,
     "Pixel X position relative to grid. Requires entity to be attached to a grid.", (void*)0},
    {"y", (getter)UIEntity::get_pixel_member, (setter)UIEntity::set_pixel_member,
     "Pixel Y position relative to grid. Requires entity to be attached to a grid.", (void*)1},

    // #295 - Integer cell position (decoupled from float draw_pos)
    {"cell_pos", (getter)UIEntity::get_cell_pos, (setter)UIEntity::set_cell_pos,
     "Integer logical cell position (Vector). Decoupled from draw_pos. "
     "Determines which cell this entity logically occupies for collision, pathfinding, etc.", NULL},
    {"cell_x", (getter)UIEntity::get_cell_member, (setter)UIEntity::set_cell_member,
     "Integer X cell coordinate.", (void*)0},
    {"cell_y", (getter)UIEntity::get_cell_member, (setter)UIEntity::set_cell_member,
     "Integer Y cell coordinate.", (void*)1},
    // grid_pos now aliases cell_pos (#295 BREAKING: no longer derives from float position)
    {"grid_pos", (getter)UIEntity::get_cell_pos, (setter)UIEntity::set_cell_pos,
     "Grid position as integer cell coordinates (Vector). Alias for cell_pos.", NULL},
    {"grid_x", (getter)UIEntity::get_cell_member, (setter)UIEntity::set_cell_member,
     "Grid X position as integer cell coordinate. Alias for cell_x.", (void*)0},
    {"grid_y", (getter)UIEntity::get_cell_member, (setter)UIEntity::set_cell_member,
     "Grid Y position as integer cell coordinate. Alias for cell_y.", (void*)1},

    // Float tile coordinates (for smooth animation between tiles)
    {"draw_pos", (getter)UIEntity::get_position, (setter)UIEntity::set_position,
     "Fractional tile position for rendering (Vector). Use for smooth animation between grid cells.", (void*)0},

    {"gridstate", (getter)UIEntity::get_gridstate, NULL, "Grid point states for the entity", NULL},
    {"grid", (getter)UIEntity::get_grid, (setter)UIEntity::set_grid,
     "Grid this entity belongs to. "
     "Get: Returns the Grid or None. "
     "Set: Assign a Grid to move entity, or None to remove from grid.", NULL},
    {"sprite_index", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite index on the texture on the display", NULL},
    {"sprite_number", (getter)UIEntity::get_spritenumber, (setter)UIEntity::set_spritenumber, "Sprite index (DEPRECATED: use sprite_index instead)", NULL},
    {"visible", (getter)UIEntity_get_visible, (setter)UIEntity_set_visible, "Visibility flag", NULL},
    {"opacity", (getter)UIEntity_get_opacity, (setter)UIEntity_set_opacity, "Opacity (0.0 = transparent, 1.0 = opaque)", NULL},
    {"name", (getter)UIEntity_get_name, (setter)UIEntity_set_name, "Name for finding elements", NULL},
    {"shader", (getter)UIEntity_get_shader, (setter)UIEntity_set_shader,
     "Shader for GPU visual effects (Shader or None). "
     "When set, the entity is rendered through the shader program. "
     "Set to None to disable shader effects.", NULL},
    {"uniforms", (getter)UIEntity_get_uniforms, NULL,
     "Collection of shader uniforms (read-only access to collection). "
     "Set uniforms via dict-like syntax: entity.uniforms['name'] = value. "
     "Supports float, vec2/3/4 tuples, PropertyBinding, and CallableBinding.", NULL},
    {"sprite_offset", (getter)UIEntity::get_sprite_offset, (setter)UIEntity::set_sprite_offset,
     "Pixel offset for oversized sprites (Vector). Applied pre-zoom during grid rendering.", NULL},
    {"sprite_offset_x", (getter)UIEntity::get_sprite_offset_member, (setter)UIEntity::set_sprite_offset_member,
     "X component of sprite pixel offset.", (void*)0},
    {"sprite_offset_y", (getter)UIEntity::get_sprite_offset_member, (setter)UIEntity::set_sprite_offset_member,
     "Y component of sprite pixel offset.", (void*)1},
    // #296 - Label system
    {"labels", (getter)UIEntity::get_labels, (setter)UIEntity::set_labels,
     "Set of string labels for collision/targeting (frozenset). "
     "Assign any iterable of strings to replace all labels.", NULL},
    // #299 - Step callback and default behavior
    {"step", (getter)UIEntity::get_step, (setter)UIEntity::set_step,
     "Step callback for grid.step() turn management. "
     "Called with (trigger, data) when behavior triggers fire. "
     "Set to None to clear.", NULL},
    {"default_behavior", (getter)UIEntity::get_default_behavior, (setter)UIEntity::set_default_behavior,
     "Default behavior type (int, maps to Behavior enum). "
     "Entity reverts to this after DONE trigger. Default: 0 (IDLE).", NULL},
    // #300 - Behavior system
    {"behavior_type", (getter)UIEntity::get_behavior_type, NULL,
     "Current behavior type (int, read-only). Use set_behavior() to change.", NULL},
    {"turn_order", (getter)UIEntity::get_turn_order, (setter)UIEntity::set_turn_order,
     "Turn order for grid.step() (int). 0 = skip, higher values go later. Default: 1.", NULL},
    {"move_speed", (getter)UIEntity::get_move_speed, (setter)UIEntity::set_move_speed,
     "Animation duration for behavior movement in seconds (float). 0 = instant. Default: 0.15.", NULL},
    {"target_label", (getter)UIEntity::get_target_label, (setter)UIEntity::set_target_label,
     "Label to search for with TARGET trigger (str or None). Default: None.", NULL},
    {"sight_radius", (getter)UIEntity::get_sight_radius, (setter)UIEntity::set_sight_radius,
     "FOV radius for TARGET trigger (int). Default: 10.", NULL},
    {NULL}  /* Sentinel */
};

PyObject* UIEntity::repr(PyUIEntityObject* self) {
    std::ostringstream ss;
    if (!self->data) ss << "<Entity (invalid internal object)>";
    else {
        // #217 - Show actual float position (draw_pos) to avoid confusion
        // Position is stored in tile coordinates; use draw_pos for float values
        ss << "<Entity (draw_pos=(" << self->data->position.x
           << ", " << self->data->position.y << ")"
           << ", sprite_index=" << self->data->sprite.getSpriteIndex() << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

// Property system implementation for animations
// #176 - Animation properties use tile coordinates (draw_x, draw_y)
// "x" and "y" are kept as aliases for backwards compatibility
bool UIEntity::setProperty(const std::string& name, float value) {
    if (name == "draw_x" || name == "x") {  // #176 - draw_x is preferred, x is alias
        position.x = value;
        // Don't update sprite position here - UIGrid::render() handles the pixel positioning
        if (grid) grid->markCompositeDirty();  // #144 - Propagate to parent grid for texture caching
        return true;
    }
    else if (name == "draw_y" || name == "y") {  // #176 - draw_y is preferred, y is alias
        position.y = value;
        // Don't update sprite position here - UIGrid::render() handles the pixel positioning
        if (grid) grid->markCompositeDirty();  // #144 - Propagate to parent grid for texture caching
        return true;
    }
    else if (name == "sprite_scale") {
        sprite.setScale(sf::Vector2f(value, value));
        if (grid) grid->markCompositeDirty();  // #144 - Content change
        return true;
    }
    else if (name == "sprite_offset_x") {
        sprite_offset.x = value;
        if (grid) grid->markCompositeDirty();
        return true;
    }
    else if (name == "sprite_offset_y") {
        sprite_offset.y = value;
        if (grid) grid->markCompositeDirty();
        return true;
    }
    // #106: Shader uniform properties - delegate to sprite
    if (sprite.setShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UIEntity::setProperty(const std::string& name, int value) {
    if (name == "sprite_index" || name == "sprite_number") {
        sprite.setSpriteIndex(value);
        if (grid) grid->markDirty();  // #144 - Content change
        return true;
    }
    return false;
}

bool UIEntity::getProperty(const std::string& name, float& value) const {
    if (name == "draw_x" || name == "x") {  // #176
        value = position.x;
        return true;
    }
    else if (name == "draw_y" || name == "y") {  // #176
        value = position.y;
        return true;
    }
    else if (name == "sprite_scale") {
        value = sprite.getScale().x;  // Assuming uniform scale
        return true;
    }
    else if (name == "sprite_offset_x") {
        value = sprite_offset.x;
        return true;
    }
    else if (name == "sprite_offset_y") {
        value = sprite_offset.y;
        return true;
    }
    // #106: Shader uniform properties - delegate to sprite
    if (sprite.getShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UIEntity::hasProperty(const std::string& name) const {
    // #176 - Float properties (draw_x/draw_y preferred, x/y are aliases)
    if (name == "draw_x" || name == "draw_y" || name == "x" || name == "y" || name == "sprite_scale"
        || name == "sprite_offset_x" || name == "sprite_offset_y") {
        return true;
    }
    // Int properties
    if (name == "sprite_index" || name == "sprite_number") {
        return true;
    }
    // #106: Shader uniform properties - delegate to sprite
    if (sprite.hasShaderProperty(name)) {
        return true;
    }
    return false;
}

// Animation shorthand for Entity - creates and starts an animation
PyObject* UIEntity::animate(PyUIEntityObject* self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"property", "target", "duration", "easing", "delta", "loop", "callback", "conflict_mode", nullptr};

    const char* property_name;
    PyObject* target_value;
    float duration;
    PyObject* easing_arg = Py_None;
    int delta = 0;
    int loop_val = 0;
    PyObject* callback = nullptr;
    const char* conflict_mode_str = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOf|OppOs", const_cast<char**>(keywords),
                                      &property_name, &target_value, &duration,
                                      &easing_arg, &delta, &loop_val, &callback, &conflict_mode_str)) {
        return NULL;
    }

    // Validate property exists on this entity
    if (!self->data->hasProperty(property_name)) {
        PyErr_Format(PyExc_ValueError,
            "Property '%s' is not valid for animation on Entity. "
            "Valid properties: draw_x, draw_y (tile coords), sprite_scale, sprite_index",
            property_name);
        return NULL;
    }

    // Validate callback is callable if provided
    if (callback && callback != Py_None && !PyCallable_Check(callback)) {
        PyErr_SetString(PyExc_TypeError, "callback must be callable");
        return NULL;
    }

    // Convert None to nullptr for C++
    if (callback == Py_None) {
        callback = nullptr;
    }

    // Convert Python target value to AnimationValue
    // Entity supports float, int, and list of int (for sprite frame animation)
    AnimationValue animValue;

    if (PyFloat_Check(target_value)) {
        animValue = static_cast<float>(PyFloat_AsDouble(target_value));
    }
    else if (PyLong_Check(target_value)) {
        animValue = static_cast<int>(PyLong_AsLong(target_value));
    }
    else if (PyList_Check(target_value)) {
        // List of integers for sprite animation
        std::vector<int> indices;
        Py_ssize_t size = PyList_Size(target_value);
        for (Py_ssize_t i = 0; i < size; i++) {
            PyObject* item = PyList_GetItem(target_value, i);
            if (PyLong_Check(item)) {
                indices.push_back(PyLong_AsLong(item));
            } else {
                PyErr_SetString(PyExc_TypeError, "Sprite animation list must contain only integers");
                return NULL;
            }
        }
        animValue = indices;
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Entity animations support float, int, or list of int target values");
        return NULL;
    }

    // Get easing function from argument
    EasingFunction easingFunc;
    if (!PyEasing::from_arg(easing_arg, &easingFunc, nullptr)) {
        return NULL;  // Error already set by from_arg
    }

    // Parse conflict mode
    AnimationConflictMode conflict_mode = AnimationConflictMode::REPLACE;
    if (conflict_mode_str) {
        if (strcmp(conflict_mode_str, "replace") == 0) {
            conflict_mode = AnimationConflictMode::REPLACE;
        } else if (strcmp(conflict_mode_str, "queue") == 0) {
            conflict_mode = AnimationConflictMode::QUEUE;
        } else if (strcmp(conflict_mode_str, "error") == 0) {
            conflict_mode = AnimationConflictMode::RAISE_ERROR;
        } else {
            PyErr_Format(PyExc_ValueError,
                "Invalid conflict_mode '%s'. Must be 'replace', 'queue', or 'error'.", conflict_mode_str);
            return NULL;
        }
    }

    // Create the Animation
    auto animation = std::make_shared<Animation>(property_name, animValue, duration, easingFunc, delta != 0, loop_val != 0, callback);

    // Start on this entity (uses startEntity, not start)
    animation->startEntity(self->data);

    // Add to AnimationManager
    AnimationManager::getInstance().addAnimation(animation, conflict_mode);

    // Check if ERROR mode raised an exception
    if (PyErr_Occurred()) {
        return NULL;
    }

    // Create and return a PyAnimation wrapper
    auto animType = &mcrfpydef::PyAnimationType;

    PyAnimationObject* pyAnim = (PyAnimationObject*)animType->tp_alloc(animType, 0);

    if (!pyAnim) {
        return NULL;
    }

    pyAnim->data = animation;
    return (PyObject*)pyAnim;
}
