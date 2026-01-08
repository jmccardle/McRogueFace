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
#include "Animation.h"
#include "PyAnimation.h"
#include "PyEasing.h"
#include "PySceneObject.h"  // #183: For scene parent lookup

UIDrawable::UIDrawable() : position(0.0f, 0.0f) { click_callable = NULL;  }

UIDrawable::UIDrawable(const UIDrawable& other)
    : z_index(other.z_index),
      name(other.name),
      position(other.position),
      visible(other.visible),
      opacity(other.opacity),
      hovered(false),  // Don't copy hover state
      serial_number(0),  // Don't copy serial number
      use_render_texture(other.use_render_texture),
      render_dirty(true)  // Force redraw after copy
{
    // Deep copy click_callable if it exists
    if (other.click_callable) {
        click_callable = std::make_unique<PyClickCallable>(*other.click_callable);
    }
    // #140 - Deep copy enter/exit callables
    if (other.on_enter_callable) {
        on_enter_callable = std::make_unique<PyClickCallable>(*other.on_enter_callable);
    }
    if (other.on_exit_callable) {
        on_exit_callable = std::make_unique<PyClickCallable>(*other.on_exit_callable);
    }
    // #141 - Deep copy move callable
    if (other.on_move_callable) {
        on_move_callable = std::make_unique<PyClickCallable>(*other.on_move_callable);
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
        hovered = false;  // Don't copy hover state
        use_render_texture = other.use_render_texture;
        render_dirty = true;  // Force redraw after copy

        // Deep copy click_callable
        if (other.click_callable) {
            click_callable = std::make_unique<PyClickCallable>(*other.click_callable);
        } else {
            click_callable.reset();
        }
        // #140 - Deep copy enter/exit callables
        if (other.on_enter_callable) {
            on_enter_callable = std::make_unique<PyClickCallable>(*other.on_enter_callable);
        } else {
            on_enter_callable.reset();
        }
        if (other.on_exit_callable) {
            on_exit_callable = std::make_unique<PyClickCallable>(*other.on_exit_callable);
        } else {
            on_exit_callable.reset();
        }
        // #141 - Deep copy move callable
        if (other.on_move_callable) {
            on_move_callable = std::make_unique<PyClickCallable>(*other.on_move_callable);
        } else {
            on_move_callable.reset();
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
      hovered(other.hovered),
      serial_number(other.serial_number),
      click_callable(std::move(other.click_callable)),
      on_enter_callable(std::move(other.on_enter_callable)),  // #140
      on_exit_callable(std::move(other.on_exit_callable)),    // #140
      on_move_callable(std::move(other.on_move_callable)),    // #141
      render_texture(std::move(other.render_texture)),
      render_sprite(std::move(other.render_sprite)),
      use_render_texture(other.use_render_texture),
      render_dirty(other.render_dirty)
{
    // Clear the moved-from object's serial number to avoid cache issues
    other.serial_number = 0;
    other.hovered = false;  // #140
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
        hovered = other.hovered;  // #140
        serial_number = other.serial_number;
        use_render_texture = other.use_render_texture;
        render_dirty = other.render_dirty;

        // Move unique_ptr members
        click_callable = std::move(other.click_callable);
        on_enter_callable = std::move(other.on_enter_callable);  // #140
        on_exit_callable = std::move(other.on_exit_callable);    // #140
        on_move_callable = std::move(other.on_move_callable);    // #141
        render_texture = std::move(other.render_texture);
        render_sprite = std::move(other.render_sprite);

        // Clear the moved-from object's serial number
        other.serial_number = 0;
        other.hovered = false;  // #140
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure)); // trust me bro, it's an Enum
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure)); // trust me bro, it's an Enum
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

// #140 - Mouse enter/exit callback registration
void UIDrawable::on_enter_register(PyObject* callable)
{
    on_enter_callable = std::make_unique<PyClickCallable>(callable);
}

void UIDrawable::on_enter_unregister()
{
    on_enter_callable.reset();
}

void UIDrawable::on_exit_register(PyObject* callable)
{
    on_exit_callable = std::make_unique<PyClickCallable>(callable);
}

void UIDrawable::on_exit_unregister()
{
    on_exit_callable.reset();
}

// #141 - Mouse move callback registration
void UIDrawable::on_move_register(PyObject* callable)
{
    on_move_callable = std::make_unique<PyClickCallable>(callable);
}

void UIDrawable::on_move_unregister()
{
    on_move_callable.reset();
}

PyObject* UIDrawable::get_int(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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
    parent_scene.clear();  // #183: Clear scene parent when setting drawable parent
}

void UIDrawable::setParentScene(const std::string& scene_name) {
    parent.reset();        // #183: Clear drawable parent when setting scene parent
    parent_scene = scene_name;
}

std::shared_ptr<UIDrawable> UIDrawable::getParent() const {
    return parent.lock();
}

void UIDrawable::removeFromParent() {
    // #183: Handle scene parent removal
    if (!parent_scene.empty()) {
        auto ui = Resources::game->scene_ui(parent_scene);
        if (ui) {
            for (auto it = ui->begin(); it != ui->end(); ++it) {
                if (it->get() == this) {
                    ui->erase(it);
                    break;
                }
            }
        }
        parent_scene.clear();
        return;
    }

    // Handle drawable parent removal
    auto p = parent.lock();
    if (!p) return;

    // Check if parent is a UIFrame or UIGrid (both have children vector)
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
    else if (p->derived_type() == PyObjectsEnum::UIGRID) {
        auto grid = std::static_pointer_cast<UIGrid>(p);
        auto& children = *grid->children;

        for (auto it = children.begin(); it != children.end(); ++it) {
            if (it->get() == this) {
                children.erase(it);
                break;
            }
        }
        grid->children_need_sort = true;
    }

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

// #138 - Global bounds (bounds in screen coordinates)
sf::FloatRect UIDrawable::get_global_bounds() const {
    sf::FloatRect local_bounds = get_bounds();
    sf::Vector2f global_pos = get_global_position();

    // Return bounds offset to global position
    return sf::FloatRect(global_pos.x, global_pos.y, local_bounds.width, local_bounds.height);
}

// #138 - Hit testing
bool UIDrawable::contains_point(float x, float y) const {
    sf::FloatRect global_bounds = get_global_bounds();
    return global_bounds.contains(x, y);
}

// #144: Content dirty - texture needs rebuild
void UIDrawable::markContentDirty() {
    if (render_dirty) return;  // Already dirty, no need to propagate

    render_dirty = true;
    composite_dirty = true;  // If content changed, composite also needs update

    // Propagate to parent - parent's composite is dirty (child content changed)
    auto p = parent.lock();
    if (p) {
        p->markContentDirty();  // Parent also needs to rebuild to include our changes
    }
}

// #144: Composite dirty - position changed, texture still valid
void UIDrawable::markCompositeDirty() {
    // Don't set render_dirty - our cached texture is still valid
    // Only mark composite_dirty so parent knows to re-blit us

    // Propagate to parent - parent needs to re-composite
    auto p = parent.lock();
    if (p) {
        p->composite_dirty = true;
        p->render_dirty = true;  // Parent needs to re-render (re-composite children)
        p->markCompositeDirty();  // Continue propagating up
    }
}

// Legacy method - calls markContentDirty for backwards compatibility
void UIDrawable::markDirty() {
    markContentDirty();
}

// Python API - get parent drawable
PyObject* UIDrawable::get_parent(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

    // #183: Check for scene parent first
    if (!drawable->parent_scene.empty()) {
        PyObject* scene = PySceneClass::get_scene_by_name(drawable->parent_scene);
        if (scene) {
            return scene;  // Already has new reference from get_scene_by_name
        }
        // Scene not found in python_scenes (shouldn't happen, but fall through to None)
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
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

    // Value must be a Frame, Grid, or Scene (things with children collections)
    PyTypeObject* frame_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
    PyTypeObject* grid_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
    PyTypeObject* scene_type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Scene");

    bool is_frame = frame_type && PyObject_IsInstance(value, (PyObject*)frame_type);
    bool is_grid = grid_type && PyObject_IsInstance(value, (PyObject*)grid_type);
    bool is_scene = scene_type && PyObject_IsInstance(value, (PyObject*)scene_type);

    Py_XDECREF(frame_type);
    Py_XDECREF(grid_type);
    Py_XDECREF(scene_type);

    if (!is_frame && !is_grid && !is_scene) {
        PyErr_SetString(PyExc_TypeError, "parent must be a Frame, Grid, Scene, or None");
        return -1;
    }

    // Handle Scene parent specially - add to scene's children
    if (is_scene) {
        PySceneObject* scene_obj = (PySceneObject*)value;
        std::string scene_name = scene_obj->name;

        // Remove from old parent first
        drawable->removeFromParent();

        // Get the scene's UI elements and add
        auto ui = Resources::game->scene_ui(scene_name);
        if (ui) {
            // Check if already in this scene (prevent duplicates)
            bool already_present = false;
            for (const auto& child : *ui) {
                if (child.get() == drawable.get()) {
                    already_present = true;
                    break;
                }
            }

            if (!already_present) {
                ui->push_back(drawable);
                drawable->setParentScene(scene_name);
            }
        }
        return 0;
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
        // Check if already in this parent's collection (prevent duplicates)
        bool already_present = false;
        for (const auto& child : **children_ptr) {
            if (child.get() == drawable.get()) {
                already_present = true;
                break;
            }
        }

        if (!already_present) {
            // Add to new parent's children
            (*children_ptr)->push_back(drawable);
            drawable->setParent(new_parent);
        }
    }

    return 0;
}

// Python API - get global position (read-only)
PyObject* UIDrawable::get_global_pos(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

// #138, #188 - Python API for bounds property - returns (pos, size) as pair of Vectors
PyObject* UIDrawable::get_bounds_py(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

    sf::FloatRect bounds = drawable->get_bounds();

    // Get Vector type from mcrfpy module
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) return NULL;

    // Create pos vector
    PyObject* pos_args = Py_BuildValue("(ff)", bounds.left, bounds.top);
    PyObject* pos = PyObject_CallObject(vector_type, pos_args);
    Py_DECREF(pos_args);
    if (!pos) {
        Py_DECREF(vector_type);
        return NULL;
    }

    // Create size vector
    PyObject* size_args = Py_BuildValue("(ff)", bounds.width, bounds.height);
    PyObject* size = PyObject_CallObject(vector_type, size_args);
    Py_DECREF(size_args);
    Py_DECREF(vector_type);
    if (!size) {
        Py_DECREF(pos);
        return NULL;
    }

    // Return tuple of two vectors (N steals reference)
    return Py_BuildValue("(NN)", pos, size);
}

// #138, #188 - Python API for global_bounds property - returns (pos, size) as pair of Vectors
PyObject* UIDrawable::get_global_bounds_py(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

    sf::FloatRect bounds = drawable->get_global_bounds();

    // Get Vector type from mcrfpy module
    PyObject* vector_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    if (!vector_type) return NULL;

    // Create pos vector
    PyObject* pos_args = Py_BuildValue("(ff)", bounds.left, bounds.top);
    PyObject* pos = PyObject_CallObject(vector_type, pos_args);
    Py_DECREF(pos_args);
    if (!pos) {
        Py_DECREF(vector_type);
        return NULL;
    }

    // Create size vector
    PyObject* size_args = Py_BuildValue("(ff)", bounds.width, bounds.height);
    PyObject* size = PyObject_CallObject(vector_type, size_args);
    Py_DECREF(size_args);
    Py_DECREF(vector_type);
    if (!size) {
        Py_DECREF(pos);
        return NULL;
    }

    // Return tuple of two vectors (N steals reference)
    return Py_BuildValue("(NN)", pos, size);
}

// #140 - Python API for on_enter property
PyObject* UIDrawable::get_on_enter(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    PyObject* ptr = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            if (((PyUIFrameObject*)self)->data->on_enter_callable)
                ptr = ((PyUIFrameObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UICAPTION:
            if (((PyUICaptionObject*)self)->data->on_enter_callable)
                ptr = ((PyUICaptionObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UISPRITE:
            if (((PyUISpriteObject*)self)->data->on_enter_callable)
                ptr = ((PyUISpriteObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UIGRID:
            if (((PyUIGridObject*)self)->data->on_enter_callable)
                ptr = ((PyUIGridObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UILINE:
            if (((PyUILineObject*)self)->data->on_enter_callable)
                ptr = ((PyUILineObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UICIRCLE:
            if (((PyUICircleObject*)self)->data->on_enter_callable)
                ptr = ((PyUICircleObject*)self)->data->on_enter_callable->borrow();
            break;
        case PyObjectsEnum::UIARC:
            if (((PyUIArcObject*)self)->data->on_enter_callable)
                ptr = ((PyUIArcObject*)self)->data->on_enter_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_enter");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        Py_RETURN_NONE;
}

int UIDrawable::set_on_enter(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* target = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            target = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            target = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            target = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            target = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_enter");
            return -1;
    }

    if (value == Py_None) {
        target->on_enter_unregister();
    } else {
        target->on_enter_register(value);
    }
    return 0;
}

// #140 - Python API for on_exit property
PyObject* UIDrawable::get_on_exit(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    PyObject* ptr = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            if (((PyUIFrameObject*)self)->data->on_exit_callable)
                ptr = ((PyUIFrameObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UICAPTION:
            if (((PyUICaptionObject*)self)->data->on_exit_callable)
                ptr = ((PyUICaptionObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UISPRITE:
            if (((PyUISpriteObject*)self)->data->on_exit_callable)
                ptr = ((PyUISpriteObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UIGRID:
            if (((PyUIGridObject*)self)->data->on_exit_callable)
                ptr = ((PyUIGridObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UILINE:
            if (((PyUILineObject*)self)->data->on_exit_callable)
                ptr = ((PyUILineObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UICIRCLE:
            if (((PyUICircleObject*)self)->data->on_exit_callable)
                ptr = ((PyUICircleObject*)self)->data->on_exit_callable->borrow();
            break;
        case PyObjectsEnum::UIARC:
            if (((PyUIArcObject*)self)->data->on_exit_callable)
                ptr = ((PyUIArcObject*)self)->data->on_exit_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_exit");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        Py_RETURN_NONE;
}

int UIDrawable::set_on_exit(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* target = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            target = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            target = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            target = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            target = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_exit");
            return -1;
    }

    if (value == Py_None) {
        target->on_exit_unregister();
    } else {
        target->on_exit_register(value);
    }
    return 0;
}

// #140 - Python API for hovered property (read-only)
PyObject* UIDrawable::get_hovered(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
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

    return PyBool_FromLong(drawable->hovered);
}

// #141 - Python API for on_move property
PyObject* UIDrawable::get_on_move(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    PyObject* ptr = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            if (((PyUIFrameObject*)self)->data->on_move_callable)
                ptr = ((PyUIFrameObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UICAPTION:
            if (((PyUICaptionObject*)self)->data->on_move_callable)
                ptr = ((PyUICaptionObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UISPRITE:
            if (((PyUISpriteObject*)self)->data->on_move_callable)
                ptr = ((PyUISpriteObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UIGRID:
            if (((PyUIGridObject*)self)->data->on_move_callable)
                ptr = ((PyUIGridObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UILINE:
            if (((PyUILineObject*)self)->data->on_move_callable)
                ptr = ((PyUILineObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UICIRCLE:
            if (((PyUICircleObject*)self)->data->on_move_callable)
                ptr = ((PyUICircleObject*)self)->data->on_move_callable->borrow();
            break;
        case PyObjectsEnum::UIARC:
            if (((PyUIArcObject*)self)->data->on_move_callable)
                ptr = ((PyUIArcObject*)self)->data->on_move_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_move");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        Py_RETURN_NONE;
}

int UIDrawable::set_on_move(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* target = nullptr;

    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            target = ((PyUIFrameObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICAPTION:
            target = ((PyUICaptionObject*)self)->data.get();
            break;
        case PyObjectsEnum::UISPRITE:
            target = ((PyUISpriteObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRID:
            target = ((PyUIGridObject*)self)->data.get();
            break;
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_move");
            return -1;
    }

    if (value == Py_None) {
        target->on_move_unregister();
    } else {
        target->on_move_register(value);
    }
    return 0;
}

// Animation shorthand helper - creates and starts an animation on a UIDrawable
// This is a free function (not a member) to avoid incomplete type issues in UIBase.h template
PyObject* UIDrawable_animate_impl(std::shared_ptr<UIDrawable> self, PyObject* args, PyObject* kwds) {
    static const char* keywords[] = {"property", "target", "duration", "easing", "delta", "callback", "conflict_mode", nullptr};

    const char* property_name;
    PyObject* target_value;
    float duration;
    PyObject* easing_arg = Py_None;
    int delta = 0;
    PyObject* callback = nullptr;
    const char* conflict_mode_str = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "sOf|OpOs", const_cast<char**>(keywords),
                                      &property_name, &target_value, &duration,
                                      &easing_arg, &delta, &callback, &conflict_mode_str)) {
        return NULL;
    }

    // Validate property exists on this drawable
    if (!self->hasProperty(property_name)) {
        PyErr_Format(PyExc_ValueError,
            "Property '%s' is not valid for animation on this object. "
            "Check spelling or use a supported property name.",
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
    else if (PyTuple_Check(target_value)) {
        Py_ssize_t size = PyTuple_Size(target_value);
        if (size == 2) {
            // Vector2f
            float x = PyFloat_AsDouble(PyTuple_GetItem(target_value, 0));
            float y = PyFloat_AsDouble(PyTuple_GetItem(target_value, 1));
            if (PyErr_Occurred()) return NULL;
            animValue = sf::Vector2f(x, y);
        }
        else if (size == 3 || size == 4) {
            // Color (RGB or RGBA)
            int r = PyLong_AsLong(PyTuple_GetItem(target_value, 0));
            int g = PyLong_AsLong(PyTuple_GetItem(target_value, 1));
            int b = PyLong_AsLong(PyTuple_GetItem(target_value, 2));
            int a = size == 4 ? PyLong_AsLong(PyTuple_GetItem(target_value, 3)) : 255;
            if (PyErr_Occurred()) return NULL;
            animValue = sf::Color(r, g, b, a);
        }
        else {
            PyErr_SetString(PyExc_ValueError, "Tuple must have 2 elements (vector) or 3-4 elements (color)");
            return NULL;
        }
    }
    else if (PyUnicode_Check(target_value)) {
        // String for text animation
        const char* str = PyUnicode_AsUTF8(target_value);
        animValue = std::string(str);
    }
    else {
        PyErr_SetString(PyExc_TypeError, "Target value must be float, int, list, tuple, or string");
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
    auto animation = std::make_shared<Animation>(property_name, animValue, duration, easingFunc, delta != 0, callback);

    // Start on this drawable
    animation->start(self);

    // Add to AnimationManager
    AnimationManager::getInstance().addAnimation(animation, conflict_mode);

    // Check if ERROR mode raised an exception
    if (PyErr_Occurred()) {
        return NULL;
    }

    // Create and return a PyAnimation wrapper
    PyTypeObject* animType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Animation");
    if (!animType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find Animation type");
        return NULL;
    }

    PyAnimationObject* pyAnim = (PyAnimationObject*)animType->tp_alloc(animType, 0);
    Py_DECREF(animType);

    if (!pyAnim) {
        return NULL;
    }

    pyAnim->data = animation;
    return (PyObject*)pyAnim;
}
