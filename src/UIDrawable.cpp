#include "UIDrawable.h"
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"

UIDrawable::UIDrawable() : position(0.0f, 0.0f) { click_callable = NULL;  }

UIDrawable::UIDrawable(const UIDrawable& other) 
    : z_index(other.z_index),
      name(other.name),
      position(other.position),
      visible(other.visible),
      opacity(other.opacity),
      serial_number(0),  // Don't copy serial number
      use_render_texture(other.use_render_texture),
      render_dirty(true)  // Force redraw after copy
{
    // Deep copy click_callable if it exists
    if (other.click_callable) {
        click_callable = std::make_unique<PyClickCallable>(*other.click_callable);
    }
    
    // Deep copy render texture if needed
    if (other.render_texture && other.use_render_texture) {
        auto size = other.render_texture->getSize();
        enableRenderTexture(size.x, size.y);
    }
}

UIDrawable& UIDrawable::operator=(const UIDrawable& other) {
    if (this != &other) {
        // Copy basic members
        z_index = other.z_index;
        name = other.name;
        position = other.position;
        visible = other.visible;
        opacity = other.opacity;
        use_render_texture = other.use_render_texture;
        render_dirty = true;  // Force redraw after copy
        
        // Deep copy click_callable
        if (other.click_callable) {
            click_callable = std::make_unique<PyClickCallable>(*other.click_callable);
        } else {
            click_callable.reset();
        }
        
        // Deep copy render texture if needed
        if (other.render_texture && other.use_render_texture) {
            auto size = other.render_texture->getSize();
            enableRenderTexture(size.x, size.y);
        } else {
            render_texture.reset();
            use_render_texture = false;
        }
    }
    return *this;
}

UIDrawable::UIDrawable(UIDrawable&& other) noexcept
    : z_index(other.z_index),
      name(std::move(other.name)),
      position(other.position),
      visible(other.visible),
      opacity(other.opacity),
      serial_number(other.serial_number),
      click_callable(std::move(other.click_callable)),
      render_texture(std::move(other.render_texture)),
      render_sprite(std::move(other.render_sprite)),
      use_render_texture(other.use_render_texture),
      render_dirty(other.render_dirty)
{
    // Clear the moved-from object's serial number to avoid cache issues
    other.serial_number = 0;
}

UIDrawable& UIDrawable::operator=(UIDrawable&& other) noexcept {
    if (this != &other) {
        // Clear our own cache entry if we have one
        if (serial_number != 0) {
            PythonObjectCache::getInstance().remove(serial_number);
        }
        
        // Move basic members
        z_index = other.z_index;
        name = std::move(other.name);
        position = other.position;
        visible = other.visible;
        opacity = other.opacity;
        serial_number = other.serial_number;
        use_render_texture = other.use_render_texture;
        render_dirty = other.render_dirty;
        
        // Move unique_ptr members
        click_callable = std::move(other.click_callable);
        render_texture = std::move(other.render_texture);
        render_sprite = std::move(other.render_sprite);
        
        // Clear the moved-from object's serial number
        other.serial_number = 0;
    }
    return *this;
}

UIDrawable::~UIDrawable() {
    if (serial_number != 0) {
        PythonObjectCache::getInstance().remove(serial_number);
    }
}

void UIDrawable::click_unregister()
{
    click_callable.reset();
}

void UIDrawable::render()
{
    render(sf::Vector2f(), Resources::game->getRenderTarget());
}

PyObject* UIDrawable::get_click(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure)); // trust me bro, it's an Enum
    PyObject* ptr;

    switch (objtype)
    {
        case PyObjectsEnum::UIFRAME:
            if (((PyUIFrameObject*)self)->data->click_callable)
                ptr = ((PyUIFrameObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UICAPTION:
            if (((PyUICaptionObject*)self)->data->click_callable)
                ptr = ((PyUICaptionObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UISPRITE:
            if (((PyUISpriteObject*)self)->data->click_callable)
                ptr = ((PyUISpriteObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UIGRID:
            if (((PyUIGridObject*)self)->data->click_callable)
                ptr = ((PyUIGridObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UILINE:
            if (((PyUILineObject*)self)->data->click_callable)
                ptr = ((PyUILineObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UICIRCLE:
            if (((PyUICircleObject*)self)->data->click_callable)
                ptr = ((PyUICircleObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        case PyObjectsEnum::UIARC:
            if (((PyUIArcObject*)self)->data->click_callable)
                ptr = ((PyUIArcObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _get_click");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        return Py_None;
}

int UIDrawable::set_click(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure)); // trust me bro, it's an Enum
    UIDrawable* target;
    switch (objtype)
    {
        case PyObjectsEnum::UIFRAME:
            target = (((PyUIFrameObject*)self)->data.get());
            break;
        case PyObjectsEnum::UICAPTION:
            target = (((PyUICaptionObject*)self)->data.get());
            break;
        case PyObjectsEnum::UISPRITE:
            target = (((PyUISpriteObject*)self)->data.get());
            break;
        case PyObjectsEnum::UIGRID:
            target = (((PyUIGridObject*)self)->data.get());
            break;
        case PyObjectsEnum::UILINE:
            target = (((PyUILineObject*)self)->data.get());
            break;
        case PyObjectsEnum::UICIRCLE:
            target = (((PyUICircleObject*)self)->data.get());
            break;
        case PyObjectsEnum::UIARC:
            target = (((PyUIArcObject*)self)->data.get());
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _set_click");
            return -1;
    }

    if (value == Py_None)
    {
        target->click_unregister();
    } else {
        target->click_register(value);
    }
    return 0;
}

void UIDrawable::click_register(PyObject* callable)
{
    click_callable = std::make_unique<PyClickCallable>(callable);
}

PyObject* UIDrawable::get_int(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;
    
    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    return PyLong_FromLong(drawable->z_index);
}

int UIDrawable::set_int(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return -1;
    }

    if (!PyLong_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "z_index must be an integer");
        return -1;
    }
    
    long z = PyLong_AsLong(value);
    if (z == -1 && PyErr_Occurred()) {
        return -1;
    }
    
    // Clamp to int range
    if (z < INT_MIN) z = INT_MIN;
    if (z > INT_MAX) z = INT_MAX;
    
    int old_z_index = drawable->z_index;
    drawable->z_index = static_cast<int>(z);
    
    // Notify of z_index change
    if (old_z_index != drawable->z_index) {
        drawable->notifyZIndexChanged();
    }
    
    return 0;
}

void UIDrawable::notifyZIndexChanged() {
    // Mark the current scene as needing sort
    // This works for elements in the scene's ui_elements collection
    McRFPy_API::markSceneNeedsSort();
    
    // TODO: In the future, we could add parent tracking to handle Frame children
    // For now, Frame children will need manual sorting or collection modification
    // to trigger a resort
}

PyObject* UIDrawable::get_name(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    return PyUnicode_FromString(drawable->name.c_str());
}

int UIDrawable::set_name(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return -1;
    }

    if (value == NULL || value == Py_None) {
        drawable->name = "";
        return 0;
    }
    
    if (!PyUnicode_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "name must be a string");
        return -1;
    }
    
    const char* name_str = PyUnicode_AsUTF8(value);
    if (!name_str) {
        return -1;
    }
    
    drawable->name = name_str;
    return 0;
}

void UIDrawable::enableRenderTexture(unsigned int width, unsigned int height) {
    // Create or recreate RenderTexture if size changed
    if (!render_texture || render_texture->getSize().x != width || render_texture->getSize().y != height) {
        render_texture = std::make_unique<sf::RenderTexture>();
        if (!render_texture->create(width, height)) {
            render_texture.reset();
            use_render_texture = false;
            return;
        }
        render_sprite.setTexture(render_texture->getTexture());
    }
    
    use_render_texture = true;
    render_dirty = true;
}

void UIDrawable::updateRenderTexture() {
    if (!use_render_texture || !render_texture) {
        return;
    }
    
    // Clear the RenderTexture
    render_texture->clear(sf::Color::Transparent);
    
    // Render content to RenderTexture
    // This will be overridden by derived classes
    // For now, just display the texture
    render_texture->display();
    
    // Update the sprite
    render_sprite.setTexture(render_texture->getTexture());
}

PyObject* UIDrawable::get_float_member(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure) >> 8);
    int member = reinterpret_cast<intptr_t>(closure) & 0xFF;
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    switch (member) {
        case 0: // x
            return PyFloat_FromDouble(drawable->position.x);
        case 1: // y
            return PyFloat_FromDouble(drawable->position.y);
        case 2: // w (width) - delegate to get_bounds
            return PyFloat_FromDouble(drawable->get_bounds().width);
        case 3: // h (height) - delegate to get_bounds
            return PyFloat_FromDouble(drawable->get_bounds().height);
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return NULL;
    }
}

int UIDrawable::set_float_member(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure) >> 8);
    int member = reinterpret_cast<intptr_t>(closure) & 0xFF;
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return -1;
    }

    float val = 0.0f;
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    
    switch (member) {
        case 0: // x
            drawable->position.x = val;
            drawable->onPositionChanged();
            break;
        case 1: // y
            drawable->position.y = val;
            drawable->onPositionChanged();
            break;
        case 2: // w
        case 3: // h
            {
                sf::FloatRect bounds = drawable->get_bounds();
                if (member == 2) {
                    drawable->resize(val, bounds.height);
                } else {
                    drawable->resize(bounds.width, val);
                }
            }
            break;
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return -1;
    }
    
    return 0;
}

PyObject* UIDrawable::get_pos(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    // Create a Python Vector object from position
    PyObject* module = PyImport_ImportModule("mcrfpy");
    if (!module) return NULL;
    
    PyObject* vector_type = PyObject_GetAttrString(module, "Vector");
    Py_DECREF(module);
    if (!vector_type) return NULL;
    
    PyObject* args = Py_BuildValue("(ff)", drawable->position.x, drawable->position.y);
    PyObject* result = PyObject_CallObject(vector_type, args);
    Py_DECREF(vector_type);
    Py_DECREF(args);
    
    return result;
}

int UIDrawable::set_pos(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return -1;
    }

    // Accept tuple or Vector
    float x, y;
    if (PyTuple_Check(value) && PyTuple_Size(value) == 2) {
        PyObject* x_obj = PyTuple_GetItem(value, 0);
        PyObject* y_obj = PyTuple_GetItem(value, 1);
        
        if (PyFloat_Check(x_obj) || PyLong_Check(x_obj)) {
            x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : static_cast<float>(PyLong_AsLong(x_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "Position x must be a number");
            return -1;
        }
        
        if (PyFloat_Check(y_obj) || PyLong_Check(y_obj)) {
            y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : static_cast<float>(PyLong_AsLong(y_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "Position y must be a number");
            return -1;
        }
    } else {
        // Try to get as Vector
        PyObject* module = PyImport_ImportModule("mcrfpy");
        if (!module) return -1;
        
        PyObject* vector_type = PyObject_GetAttrString(module, "Vector");
        Py_DECREF(module);
        if (!vector_type) return -1;
        
        int is_vector = PyObject_IsInstance(value, vector_type);
        Py_DECREF(vector_type);
        
        if (is_vector) {
            PyVectorObject* vec = (PyVectorObject*)value;
            x = vec->data.x;
            y = vec->data.y;
        } else {
            PyErr_SetString(PyExc_TypeError, "Position must be a tuple (x, y) or Vector");
            return -1;
        }
    }
    
    drawable->position = sf::Vector2f(x, y);
    drawable->onPositionChanged();
    return 0;
}

// #122 - Parent-child hierarchy implementation
void UIDrawable::setParent(std::shared_ptr<UIDrawable> new_parent) {
    parent = new_parent;
}

std::shared_ptr<UIDrawable> UIDrawable::getParent() const {
    return parent.lock();
}

void UIDrawable::removeFromParent() {
    auto p = parent.lock();
    if (!p) return;

    // Check if parent is a UIFrame (has children vector)
    if (p->derived_type() == PyObjectsEnum::UIFRAME) {
        auto frame = std::static_pointer_cast<UIFrame>(p);
        auto& children = *frame->children;

        // Find and remove this drawable from parent's children
        // We need to find ourselves - but we don't have shared_from_this
        // Instead, compare raw pointers
        for (auto it = children.begin(); it != children.end(); ++it) {
            if (it->get() == this) {
                children.erase(it);
                break;
            }
        }
        frame->children_need_sort = true;
    }
    // TODO: Handle UIGrid children when needed

    parent.reset();
}

// #102 - Global position calculation
sf::Vector2f UIDrawable::get_global_position() const {
    sf::Vector2f global_pos = position;

    auto p = parent.lock();
    while (p) {
        global_pos += p->position;
        p = p->parent.lock();
    }

    return global_pos;
}

// #116 - Dirty flag propagation up parent chain
void UIDrawable::markDirty() {
    if (render_dirty) return;  // Already dirty, no need to propagate

    render_dirty = true;

    // Propagate to parent
    auto p = parent.lock();
    if (p) {
        p->markDirty();
    }
}

// Python API - get parent drawable
PyObject* UIDrawable::get_parent(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    auto parent_ptr = drawable->getParent();
    if (!parent_ptr) {
        Py_RETURN_NONE;
    }

    // Convert parent to Python object using the cache/conversion system
    // Re-use the pattern from UICollection
    PyTypeObject* type = nullptr;
    PyObject* obj = nullptr;

    switch (parent_ptr->derived_type()) {
        case PyObjectsEnum::UIFRAME:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
            if (!type) return nullptr;
            auto pyObj = (PyUIFrameObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIFrame>(parent_ptr);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UICAPTION:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
            if (!type) return nullptr;
            auto pyObj = (PyUICaptionObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UICaption>(parent_ptr);
                pyObj->font = nullptr;
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UISPRITE:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
            if (!type) return nullptr;
            auto pyObj = (PyUISpriteObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UISprite>(parent_ptr);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        case PyObjectsEnum::UIGRID:
        {
            type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
            if (!type) return nullptr;
            auto pyObj = (PyUIGridObject*)type->tp_alloc(type, 0);
            if (pyObj) {
                pyObj->data = std::static_pointer_cast<UIGrid>(parent_ptr);
                pyObj->weakreflist = NULL;
            }
            obj = (PyObject*)pyObj;
            break;
        }
        default:
            Py_RETURN_NONE;
    }

    if (type) {
        Py_DECREF(type);
    }
    return obj;
}

// Python API - set parent drawable (or None to remove from parent)
int UIDrawable::set_parent(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    std::shared_ptr<UIDrawable> drawable = nullptr;

    // Get the shared_ptr for self
    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data;
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data;
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data;
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data;
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data;
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data;
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data;
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return -1;
    }

    // Handle None - remove from parent
    if (value == Py_None) {
        drawable->removeFromParent();
        return 0;
    }

    // Value must be a Frame or Grid (things with children collections)
    // Check if it's a Frame
    PyTypeObject* frame_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
    PyTypeObject* grid_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");

    bool is_frame = frame_type && PyObject_IsInstance(value, (PyObject*)frame_type);
    bool is_grid = grid_type && PyObject_IsInstance(value, (PyObject*)grid_type);

    Py_XDECREF(frame_type);
    Py_XDECREF(grid_type);

    if (!is_frame && !is_grid) {
        PyErr_SetString(PyExc_TypeError, "parent must be a Frame, Grid, or None");
        return -1;
    }

    // Remove from old parent first
    drawable->removeFromParent();

    // Get the new parent's children collection and append
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>* children_ptr = nullptr;
    std::shared_ptr<UIDrawable> new_parent = nullptr;

    if (is_frame) {
        auto frame = ((PyUIFrameObject*)value)->data;
        children_ptr = &frame->children;
        new_parent = frame;
    } else if (is_grid) {
        auto grid = ((PyUIGridObject*)value)->data;
        children_ptr = &grid->children;
        new_parent = grid;
    }

    if (children_ptr && *children_ptr) {
        // Add to new parent's children
        (*children_ptr)->push_back(drawable);
        drawable->setParent(new_parent);
    }

    return 0;
}

// Python API - get global position (read-only)
PyObject* UIDrawable::get_global_pos(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure));
    UIDrawable* drawable = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            drawable = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            drawable = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            drawable = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            drawable = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return NULL;
    }

    sf::Vector2f global_pos = drawable->get_global_position();

    // Create a Python Vector object
    PyObject* module = PyImport_ImportModule("mcrfpy");
    if (!module) return NULL;

    PyObject* vector_type = PyObject_GetAttrString(module, "Vector");
    Py_DECREF(module);
    if (!vector_type) return NULL;

    PyObject* args = Py_BuildValue("(ff)", global_pos.x, global_pos.y);
    PyObject* result = PyObject_CallObject(vector_type, args);
    Py_DECREF(vector_type);
    Py_DECREF(args);

    return result;
}
