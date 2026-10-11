#include "UIDrawable.h"
#include "PyAnimate.h"
#include "PyWrap.h"
#include <iostream>
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "PyGridData.h"
#include "UIGridView.h"
#include "UILine.h"
#include "UICircle.h"
#include "UIArc.h"
#include "3d/Viewport3D.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "Animation.h"
#include "PyAnimation.h"
#include "PyEasing.h"
#include "PySceneObject.h"  // #183: For scene parent lookup
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support

// Helper function to extract UIDrawable* from any Python UI object
// Returns nullptr and sets Python error on failure
static UIDrawable* extractDrawable(PyObject* self, PyObjectsEnum objtype) {
    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            return ((PyUIFrameObject*)self)->data.get();
        case PyObjectsEnum::UICAPTION:
            return ((PyUICaptionObject*)self)->data.get();
        case PyObjectsEnum::UISPRITE:
            return ((PyUISpriteObject*)self)->data.get();
        case PyObjectsEnum::UILINE:
            return ((PyUILineObject*)self)->data.get();
        case PyObjectsEnum::UICIRCLE:
            return ((PyUICircleObject*)self)->data.get();
        case PyObjectsEnum::UIARC:
            return ((PyUIArcObject*)self)->data.get();
        case PyObjectsEnum::UIGRIDVIEW:
            return ((PyUIGridViewObject*)self)->data.get();
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance");
            return nullptr;
    }
}

// Helper to extract shared_ptr<UIDrawable> for ownership tracking
static std::shared_ptr<UIDrawable> extractDrawableShared(PyObject* self, PyObjectsEnum objtype) {
    switch (objtype) {
        case PyObjectsEnum::UIFRAME:
            return ((PyUIFrameObject*)self)->data;
        case PyObjectsEnum::UICAPTION:
            return ((PyUICaptionObject*)self)->data;
        case PyObjectsEnum::UISPRITE:
            return ((PyUISpriteObject*)self)->data;
        case PyObjectsEnum::UILINE:
            return ((PyUILineObject*)self)->data;
        case PyObjectsEnum::UICIRCLE:
            return ((PyUICircleObject*)self)->data;
        case PyObjectsEnum::UIARC:
            return ((PyUIArcObject*)self)->data;
        case PyObjectsEnum::UIGRIDVIEW:
            return ((PyUIGridViewObject*)self)->data;
        default:
            return nullptr;
    }
}

UIDrawable::UIDrawable() : position(0.0f, 0.0f) { click_callable = NULL;  }

UIDrawable::UIDrawable(const UIDrawable& other)
    : z_index(other.z_index),
      name(other.name),
      position(other.position),
      rotation(other.rotation),
      origin(other.origin),
      rotate_with_camera(other.rotate_with_camera),
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
    // #140, #230 - Deep copy enter/exit callables (now PyHoverCallable)
    if (other.on_enter_callable) {
        on_enter_callable = std::make_unique<PyHoverCallable>(*other.on_enter_callable);
    }
    if (other.on_exit_callable) {
        on_exit_callable = std::make_unique<PyHoverCallable>(*other.on_exit_callable);
    }
    // #141, #230 - Deep copy move callable (now PyHoverCallable)
    if (other.on_move_callable) {
        on_move_callable = std::make_unique<PyHoverCallable>(*other.on_move_callable);
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
        rotation = other.rotation;
        origin = other.origin;
        rotate_with_camera = other.rotate_with_camera;
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
        // #140, #230 - Deep copy enter/exit callables (now PyHoverCallable)
        if (other.on_enter_callable) {
            on_enter_callable = std::make_unique<PyHoverCallable>(*other.on_enter_callable);
        } else {
            on_enter_callable.reset();
        }
        if (other.on_exit_callable) {
            on_exit_callable = std::make_unique<PyHoverCallable>(*other.on_exit_callable);
        } else {
            on_exit_callable.reset();
        }
        // #141, #230 - Deep copy move callable (now PyHoverCallable)
        if (other.on_move_callable) {
            on_move_callable = std::make_unique<PyHoverCallable>(*other.on_move_callable);
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
      rotation(other.rotation),
      origin(other.origin),
      rotate_with_camera(other.rotate_with_camera),
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
            mcrf::unregister_wrapper(serial_number);
        }

        // Move basic members
        z_index = other.z_index;
        name = std::move(other.name);
        position = other.position;
        rotation = other.rotation;
        origin = other.origin;
        rotate_with_camera = other.rotate_with_camera;
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
    if (serial_number != 0) mcrf::unregister_wrapper(serial_number);
    if (children_serial != 0) mcrf::unregister_wrapper(children_serial);
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
        case PyObjectsEnum::UIGRIDVIEW:
            if (((PyUIGridViewObject*)self)->data->click_callable)
                ptr = ((PyUIGridViewObject*)self)->data->click_callable->borrow();
            else
                ptr = NULL;
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _get_click");
            return NULL;
    }
    if (ptr && ptr != Py_None) {
        Py_INCREF(ptr);  // Return new reference, not borrowed
        return ptr;
    }
    Py_RETURN_NONE;
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
        case PyObjectsEnum::UILINE:
            target = (((PyUILineObject*)self)->data.get());
            break;
        case PyObjectsEnum::UICIRCLE:
            target = (((PyUICircleObject*)self)->data.get());
            break;
        case PyObjectsEnum::UIARC:
            target = (((PyUIArcObject*)self)->data.get());
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            target = (((PyUIGridViewObject*)self)->data.get());
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

// #140, #230 - Mouse enter/exit callback registration (now PyHoverCallable)
void UIDrawable::on_enter_register(PyObject* callable)
{
    on_enter_callable = std::make_unique<PyHoverCallable>(callable);
}

void UIDrawable::on_enter_unregister()
{
    on_enter_callable.reset();
}

void UIDrawable::on_exit_register(PyObject* callable)
{
    on_exit_callable = std::make_unique<PyHoverCallable>(callable);
}

void UIDrawable::on_exit_unregister()
{
    on_exit_callable.reset();
}

// #141, #230 - Mouse move callback registration (now PyHoverCallable)
void UIDrawable::on_move_register(PyObject* callable)
{
    on_move_callable = std::make_unique<PyHoverCallable>(callable);
}

void UIDrawable::on_move_unregister()
{
    on_move_callable.reset();
}

PyObject* UIDrawable::get_int(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyLong_FromLong(drawable->z_index);
}

int UIDrawable::set_int(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

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
    
    drawable->assignZIndex(static_cast<int>(z));  // #426: shared with animation
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
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyUnicode_FromString(drawable->name.c_str());
}

int UIDrawable::set_name(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

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
            std::cerr << "[McRogueFace] Warning: Failed to create RenderTexture ("
                      << width << "x" << height << ")" << std::endl;
            render_texture.reset();
            use_render_texture = false;
            return;
        }
        render_sprite.setTexture(render_texture->getTexture(), true);  // new size: reset the rect
    }

    use_render_texture = true;
    render_dirty = true;
}

void UIDrawable::disableRenderTexture() {
    if (!use_render_texture) return;

    render_texture.reset();
    render_sprite = sf::Sprite();  // Clear stale texture reference
    use_render_texture = false;
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

// #426: shared property setters. The Python setters and the animation system both
// call these, so assigning and animating a shared property have the same effect.
void UIDrawable::assignPosition(sf::Vector2f p) {
    position = p;
    onPositionChanged();
    markCompositeDirty();  // #290: position change invalidates parent cache
}

void UIDrawable::assignSize(sf::Vector2f s) {
    resize(s.x, s.y);
    markDirty();  // #290: size change invalidates own + parent cache
}

void UIDrawable::assignRotation(float degrees) {
    rotation = degrees;
    markDirty();
}

void UIDrawable::assignOrigin(sf::Vector2f o) {
    origin = o;
    markDirty();
}

void UIDrawable::assignOpacity(float o) {
    opacity = std::clamp(o, 0.0f, 1.0f);
    markDirty();
}

void UIDrawable::assignZIndex(int z) {
    if (z == z_index) return;
    z_index = z;
    notifyZIndexChanged();
    markDirty();
}

bool UIDrawable::setProperty(const std::string& name, float value) {
    const unsigned shared = sharedProperties();
    if (shared & SHARED_POSITION) {
        if (name == "x") { assignPosition({value, position.y}); return true; }
        if (name == "y") { assignPosition({position.x, value}); return true; }
    }
    if (shared & SHARED_SIZE) {
        if (name == "w") { assignSize({value, get_bounds().height}); return true; }
        if (name == "h") { assignSize({get_bounds().width, value}); return true; }
    }
    if ((shared & SHARED_ROTATION) && name == "rotation") { assignRotation(value); return true; }
    if ((shared & SHARED_OPACITY) && name == "opacity") { assignOpacity(value); return true; }
    return false;
}

bool UIDrawable::setProperty(const std::string& name, int value) {
    if ((sharedProperties() & SHARED_Z_INDEX) && name == "z_index") { assignZIndex(value); return true; }
    return false;
}

bool UIDrawable::setProperty(const std::string& name, const sf::Vector2f& value) {
    const unsigned shared = sharedProperties();
    if ((shared & SHARED_POSITION) && name == "pos") { assignPosition(value); return true; }
    if ((shared & SHARED_SIZE) && name == "size") { assignSize(value); return true; }
    if ((shared & SHARED_ROTATION) && name == "origin") { assignOrigin(value); return true; }
    return false;
}

bool UIDrawable::getProperty(const std::string& name, float& value) const {
    const unsigned shared = sharedProperties();
    if (shared & SHARED_POSITION) {
        if (name == "x") { value = position.x; return true; }
        if (name == "y") { value = position.y; return true; }
    }
    if (shared & SHARED_SIZE) {
        if (name == "w") { value = get_bounds().width; return true; }
        if (name == "h") { value = get_bounds().height; return true; }
    }
    if ((shared & SHARED_ROTATION) && name == "rotation") { value = rotation; return true; }
    if ((shared & SHARED_OPACITY) && name == "opacity") { value = opacity; return true; }
    return false;
}

bool UIDrawable::getProperty(const std::string& name, int& value) const {
    if ((sharedProperties() & SHARED_Z_INDEX) && name == "z_index") { value = z_index; return true; }
    return false;
}

bool UIDrawable::getProperty(const std::string& name, sf::Vector2f& value) const {
    const unsigned shared = sharedProperties();
    if ((shared & SHARED_POSITION) && name == "pos") { value = position; return true; }
    if ((shared & SHARED_SIZE) && name == "size") {
        auto b = get_bounds();
        value = {b.width, b.height};
        return true;
    }
    if ((shared & SHARED_ROTATION) && name == "origin") { value = origin; return true; }
    return false;
}

bool UIDrawable::hasProperty(const std::string& name) const {
    const unsigned shared = sharedProperties();
    return ((shared & SHARED_POSITION) && (name == "x" || name == "y" || name == "pos"))
        || ((shared & SHARED_SIZE) && (name == "w" || name == "h" || name == "size"))
        || ((shared & SHARED_ROTATION) && (name == "rotation" || name == "origin"))
        || ((shared & SHARED_OPACITY) && name == "opacity")
        || ((shared & SHARED_Z_INDEX) && name == "z_index");
}

PyObject* UIDrawable::get_float_member(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure) >> 8);
    int member = reinterpret_cast<intptr_t>(closure) & 0xFF;
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

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
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    float val = 0.0f;
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    
    // #426: the same setters the animation system uses
    const sf::Vector2f p = drawable->position;
    const sf::FloatRect b = drawable->get_bounds();
    switch (member) {
        case 0: drawable->assignPosition({val, p.y}); break;        // x
        case 1: drawable->assignPosition({p.x, val}); break;        // y
        case 2: drawable->assignSize({val, b.height}); break;       // w
        case 3: drawable->assignSize({b.width, val}); break;        // h
        default:
            PyErr_SetString(PyExc_AttributeError, "Invalid float member");
            return -1;
    }
    return 0;
}

PyObject* UIDrawable::get_pos(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // #331: direct allocation fast path — no module import or type call per read
    return PyVector(drawable->position).pyObject();
}

int UIDrawable::set_pos(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    sf::Vector2f v;
    if (!mcrf::to_vector2f(value, v, "pos")) return -1;
    drawable->assignPosition(v);
    return 0;
}

// #426: size as a Vector, for types whose w/h are writable (Frame, Viewport3D)
PyObject* UIDrawable::get_size_vec(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;
    auto b = drawable->get_bounds();
    return PyVector(sf::Vector2f(b.width, b.height)).pyObject();
}

int UIDrawable::set_size_vec(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;
    sf::Vector2f size;
    if (!mcrf::to_vector2f(value, size, "size")) return -1;
    drawable->assignSize(size);
    return 0;
}

// Rotation property getter/setter
PyObject* UIDrawable::get_rotation(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyFloat_FromDouble(drawable->rotation);
}

int UIDrawable::set_rotation(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    float val = 0.0f;
    if (PyFloat_Check(value)) {
        val = PyFloat_AsDouble(value);
    } else if (PyLong_Check(value)) {
        val = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "rotation must be a number (int or float)");
        return -1;
    }

    drawable->assignRotation(val);
    return 0;
}

// Origin property getter/setter
PyObject* UIDrawable::get_origin(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // #331: direct allocation fast path — no module import or type call per read
    return PyVector(drawable->origin).pyObject();
}

int UIDrawable::set_origin(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    sf::Vector2f v;
    if (!mcrf::to_vector2f(value, v, "origin")) return -1;
    drawable->assignOrigin(v);
    return 0;
}

// rotate_with_camera property getter/setter
PyObject* UIDrawable::get_rotate_with_camera(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyBool_FromLong(drawable->rotate_with_camera);
}

int UIDrawable::set_rotate_with_camera(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "rotate_with_camera must be a boolean");
        return -1;
    }

    drawable->rotate_with_camera = PyObject_IsTrue(value);
    drawable->markDirty();
    return 0;
}

// #221 - Grid coordinate properties (only valid when the parent is a Grid, i.e. a UIGridView)
PyObject* UIDrawable::get_grid_pos(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // Check if parent is a Grid (UIGridView) -- #361: GridData is not a drawable
    // and can never be a parent.
    auto parent_ptr = drawable->getParent();
    if (!parent_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a child of a Grid");
        return NULL;
    }

    UIGridView* grid = dynamic_cast<UIGridView*>(parent_ptr.get());
    if (!grid) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a direct child of a Grid");
        return NULL;
    }

    // Calculate grid position from pixel position
    sf::Vector2f cell_size = grid->getEffectiveCellSize();
    float grid_x = drawable->position.x / cell_size.x;
    float grid_y = drawable->position.y / cell_size.y;

    // Return as Vector
    PyObject* vector_type = (PyObject*)&mcrfpydef::PyVectorType;

    PyObject* args = Py_BuildValue("(ff)", grid_x, grid_y);
    PyObject* result = PyObject_CallObject(vector_type, args);
    Py_DECREF(args);

    return result;
}

int UIDrawable::set_grid_pos(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    // Check if parent is a Grid (UIGridView) -- #361: GridData is not a drawable
    // and can never be a parent.
    auto parent_ptr = drawable->getParent();
    if (!parent_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a child of a Grid");
        return -1;
    }

    UIGridView* grid = dynamic_cast<UIGridView*>(parent_ptr.get());
    if (!grid) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a direct child of a Grid");
        return -1;
    }

    // Parse the grid position value
    float grid_x, grid_y;
    if (PyTuple_Check(value) && PyTuple_Size(value) == 2) {
        PyObject* x_obj = PyTuple_GetItem(value, 0);
        PyObject* y_obj = PyTuple_GetItem(value, 1);

        if (PyFloat_Check(x_obj) || PyLong_Check(x_obj)) {
            grid_x = PyFloat_Check(x_obj) ? PyFloat_AsDouble(x_obj) : static_cast<float>(PyLong_AsLong(x_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_pos x must be a number");
            return -1;
        }

        if (PyFloat_Check(y_obj) || PyLong_Check(y_obj)) {
            grid_y = PyFloat_Check(y_obj) ? PyFloat_AsDouble(y_obj) : static_cast<float>(PyLong_AsLong(y_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_pos y must be a number");
            return -1;
        }
    } else if (PyObject_HasAttrString(value, "x") && PyObject_HasAttrString(value, "y")) {
        // Vector-like object
        PyObject* x_attr = PyObject_GetAttrString(value, "x");
        PyObject* y_attr = PyObject_GetAttrString(value, "y");

        if (x_attr && (PyFloat_Check(x_attr) || PyLong_Check(x_attr))) {
            grid_x = PyFloat_Check(x_attr) ? PyFloat_AsDouble(x_attr) : static_cast<float>(PyLong_AsLong(x_attr));
        } else {
            Py_XDECREF(x_attr);
            Py_XDECREF(y_attr);
            PyErr_SetString(PyExc_TypeError, "grid_pos x must be a number");
            return -1;
        }

        if (y_attr && (PyFloat_Check(y_attr) || PyLong_Check(y_attr))) {
            grid_y = PyFloat_Check(y_attr) ? PyFloat_AsDouble(y_attr) : static_cast<float>(PyLong_AsLong(y_attr));
        } else {
            Py_XDECREF(x_attr);
            Py_XDECREF(y_attr);
            PyErr_SetString(PyExc_TypeError, "grid_pos y must be a number");
            return -1;
        }

        Py_DECREF(x_attr);
        Py_DECREF(y_attr);
    } else {
        PyErr_SetString(PyExc_TypeError, "grid_pos must be a tuple (x, y) or Vector");
        return -1;
    }

    // Convert grid position to pixel position
    sf::Vector2f cell_size = grid->getEffectiveCellSize();
    drawable->position.x = grid_x * cell_size.x;
    drawable->position.y = grid_y * cell_size.y;
    drawable->onPositionChanged();
    drawable->markCompositeDirty(); // #290: position change invalidates parent cache

    return 0;
}

PyObject* UIDrawable::get_grid_size(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // Check if parent is a Grid (UIGridView) -- #361: GridData is not a drawable
    // and can never be a parent.
    auto parent_ptr = drawable->getParent();
    if (!parent_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a child of a Grid");
        return NULL;
    }

    UIGridView* grid = dynamic_cast<UIGridView*>(parent_ptr.get());
    if (!grid) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a direct child of a Grid");
        return NULL;
    }

    // Calculate grid size from pixel size
    sf::FloatRect bounds = drawable->get_bounds();
    sf::Vector2f cell_size = grid->getEffectiveCellSize();
    float grid_w = bounds.width / cell_size.x;
    float grid_h = bounds.height / cell_size.y;

    // Return as Vector
    PyObject* vector_type = (PyObject*)&mcrfpydef::PyVectorType;

    PyObject* args = Py_BuildValue("(ff)", grid_w, grid_h);
    PyObject* result = PyObject_CallObject(vector_type, args);
    Py_DECREF(args);

    return result;
}

int UIDrawable::set_grid_size(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    // Check if parent is a Grid (UIGridView) -- #361: GridData is not a drawable
    // and can never be a parent.
    auto parent_ptr = drawable->getParent();
    if (!parent_ptr) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a child of a Grid");
        return -1;
    }

    UIGridView* grid = dynamic_cast<UIGridView*>(parent_ptr.get());
    if (!grid) {
        PyErr_SetString(PyExc_RuntimeError, "drawable is not a direct child of a Grid");
        return -1;
    }

    // Parse the grid size value
    float grid_w, grid_h;
    if (PyTuple_Check(value) && PyTuple_Size(value) == 2) {
        PyObject* w_obj = PyTuple_GetItem(value, 0);
        PyObject* h_obj = PyTuple_GetItem(value, 1);

        if (PyFloat_Check(w_obj) || PyLong_Check(w_obj)) {
            grid_w = PyFloat_Check(w_obj) ? PyFloat_AsDouble(w_obj) : static_cast<float>(PyLong_AsLong(w_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_size width must be a number");
            return -1;
        }

        if (PyFloat_Check(h_obj) || PyLong_Check(h_obj)) {
            grid_h = PyFloat_Check(h_obj) ? PyFloat_AsDouble(h_obj) : static_cast<float>(PyLong_AsLong(h_obj));
        } else {
            PyErr_SetString(PyExc_TypeError, "grid_size height must be a number");
            return -1;
        }
    } else if (PyObject_HasAttrString(value, "x") && PyObject_HasAttrString(value, "y")) {
        // Vector-like object
        PyObject* x_attr = PyObject_GetAttrString(value, "x");
        PyObject* y_attr = PyObject_GetAttrString(value, "y");

        if (x_attr && (PyFloat_Check(x_attr) || PyLong_Check(x_attr))) {
            grid_w = PyFloat_Check(x_attr) ? PyFloat_AsDouble(x_attr) : static_cast<float>(PyLong_AsLong(x_attr));
        } else {
            Py_XDECREF(x_attr);
            Py_XDECREF(y_attr);
            PyErr_SetString(PyExc_TypeError, "grid_size width must be a number");
            return -1;
        }

        if (y_attr && (PyFloat_Check(y_attr) || PyLong_Check(y_attr))) {
            grid_h = PyFloat_Check(y_attr) ? PyFloat_AsDouble(y_attr) : static_cast<float>(PyLong_AsLong(y_attr));
        } else {
            Py_XDECREF(x_attr);
            Py_XDECREF(y_attr);
            PyErr_SetString(PyExc_TypeError, "grid_size height must be a number");
            return -1;
        }

        Py_DECREF(x_attr);
        Py_DECREF(y_attr);
    } else {
        PyErr_SetString(PyExc_TypeError, "grid_size must be a tuple (w, h) or Vector");
        return -1;
    }

    // Convert grid size to pixel size and resize
    sf::Vector2f cell_size = grid->getEffectiveCellSize();
    drawable->resize(grid_w * cell_size.x, grid_h * cell_size.y);

    return 0;
}

// #122 - Parent-child hierarchy implementation
void UIDrawable::setParent(std::shared_ptr<UIDrawable> new_parent) {
    parent = new_parent;
    parent_scene.clear();  // #183: Clear scene parent when setting drawable parent

    updatePyIdentityPin();  // #373

    // Apply alignment when parent is set (if alignment is configured)
    if (new_parent && align_type != AlignmentType::NONE) {
        applyAlignment();
    }
}

bool UIDrawable::canAdopt(const std::shared_ptr<UIDrawable>& new_parent, const UIDrawable* child) {
    for (auto p = new_parent; p; p = p->getParent()) {
        if (p.get() == child) {
            PyErr_SetString(PyExc_ValueError,
                p == new_parent
                    ? "cannot add a drawable to its own children"
                    : "cannot add a drawable to one of its descendants (it would become its own ancestor)");
            return false;
        }
    }
    return true;
}

void UIDrawable::setParentScene(const std::string& scene_name) {
    parent.reset();        // #183: Clear drawable parent when setting scene parent
    parent_scene = scene_name;

    updatePyIdentityPin();  // #373

    // Apply alignment when scene parent is set (if alignment is configured)
    if (!scene_name.empty() && align_type != AlignmentType::NONE) {
        applyAlignment();
    }
}

// #373: hold a strong ref to the Python wrapper while, and only while, this drawable
// is a member of a children collection. See the comment on py_identity in UIDrawable.h.
void UIDrawable::updatePyIdentityPin() {
    // #443: every live wrapper, not only subclasses (see py_identity in UIDrawable.h).
    const bool in_collection = !parent.expired() || !parent_scene.empty();
    py_identity.sync(in_collection, serial_number);
}

void UIDrawable::releaseChildPins(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children) {
    if (!children) return;
    for (auto& child : *children) {
        if (child) child->releasePyIdentity();
    }
}

void UIDrawable::releasePyIdentity() {
    py_identity.release();
}

// #441: see mcrf::owns_exclusively in PyWrap.h for when these may run.
int UIDrawable::traverseOwned(visitproc visit, void* arg) {
    MCRF_VISIT(mcrf::visit_callable(click_callable, visit, arg));
    MCRF_VISIT(mcrf::visit_callable(on_enter_callable, visit, arg));
    MCRF_VISIT(mcrf::visit_callable(on_exit_callable, visit, arg));
    MCRF_VISIT(mcrf::visit_callable(on_move_callable, visit, arg));
    return 0;
}

void UIDrawable::clearOwned() {
    click_unregister();
    on_enter_unregister();
    on_exit_unregister();
    on_move_unregister();
}

// A child's pin belongs to the collection named by its parent link; a stale or foreign
// pin is never reported, so no pin is counted twice.
static bool memberOf(const UIDrawable& child, const UIDrawable* owner, const std::string* scene) {
    if (owner) return child.getParent().get() == owner;
    return scene && child.parent_scene == *scene;
}

int UIDrawable::traverseChildren(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children,
                                 const UIDrawable* owner, const std::string* scene,
                                 visitproc visit, void* arg) {
    // A collection wrapper (frame.children) shares the vector and can keep the children
    // alive after the owner dies, so the owner speaks for them only while it is alone.
    if (!children || children.use_count() != 1) return 0;
    for (const auto& child : *children) {
        if (!child) continue;
        if (child->py_identity.pinned()) {
            if (memberOf(*child, owner, scene)) MCRF_VISIT(child->py_identity.visit(visit, arg));
        } else if (child.use_count() == 1) {
            MCRF_VISIT(child->traverseOwned(visit, arg));
        }
    }
    return 0;
}

void UIDrawable::clearChildren(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children,
                               const UIDrawable* owner, const std::string* scene) {
    if (!children || children.use_count() != 1) return;
    // Decide first, act second: releasing a pin frees a wrapper, and a weakref callback
    // on it could run Python that edits this vector.
    std::vector<std::shared_ptr<UIDrawable>> unpin, descend;
    for (const auto& child : *children) {
        if (!child) continue;
        if (child->py_identity.pinned()) {
            if (memberOf(*child, owner, scene)) unpin.push_back(child);
        } else if (child.use_count() == 1) {
            descend.push_back(child);
        }
    }
    for (auto& child : descend) child->clearOwned();
    for (auto& child : unpin) child->releasePyIdentity();
}

std::shared_ptr<UIDrawable> UIDrawable::getParent() const {
    return parent.lock();
}

// #373: this drops the parent link, so it also drops the Python-identity pin -- which
// may release the last reference to the wrapper, whose dealloc drops the wrapper's
// shared_ptr to this drawable. Callers must therefore hold their own strong ref for the
// duration (every one does: they come through a local shared_ptr from extractDrawable).
// updatePyIdentityPin() is the LAST statement on both paths so that even in that case
// no member of a freed `this` is touched afterwards.
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
        updatePyIdentityPin();
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
    // #364: a grid child's parent is the UIGridView. The internal UIGrid (_GridData)
    // holds no drawables, so it can never be a parent and needs no arm here.
    else if (p->derived_type() == PyObjectsEnum::UIGRIDVIEW) {
        auto view = std::static_pointer_cast<UIGridView>(p);
        if (view->children) {
            auto& children = *view->children;
            for (auto it = children.begin(); it != children.end(); ++it) {
                if (it->get() == this) {
                    children.erase(it);
                    break;
                }
            }
            view->children_need_sort = true;
        }
    }

    parent.reset();
    updatePyIdentityPin();
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
//
// #368 - The walk up the parent chain is UNCONDITIONAL. It used to be gated on
// `(!was_dirty || !p->render_dirty)`, which is sound only if render_dirty is reliably
// cleared once a drawable has been drawn. It is not: clearDirty() is called by the two
// classes that actually *cache* a raster (UIFrame's render-texture path, UIGridView),
// and by nobody else. For every ordinary Frame/Caption/Sprite/Line/Circle/Arc,
// render_dirty is a write-once latch -- true from the first mutation until death.
//
// With the flag stuck true, `was_dirty` was always true and the parent's render_dirty
// was always true, so the guard was always false and content invalidation propagated
// NOWHERE. A caching ancestor (Frame(cache_subtree=True), or a GridView) went on
// re-blitting a stale composite: text never updated, colors never changed. Only
// position changes survived, because markCompositeDirty (below) already walked
// unconditionally.
//
// Restoring the guard would mean making every drawable clear the flag honestly, and
// then trusting that every future drawable remembers to. The invariant here is worth
// more than the walk it saves: parent chains are shallow, and this is exactly the cost
// markCompositeDirty has always paid on every move without anyone noticing.
void UIDrawable::markContentDirty() {
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

// #106 - Shader support
void UIDrawable::markShaderDynamic() {
    shader_dynamic = true;

    // Propagate to parent to invalidate caches
    auto p = parent.lock();
    if (p) {
        p->markShaderDynamic();
    }
}

// #106: Shader uniform property helpers for animation support
bool UIDrawable::setShaderProperty(const std::string& name, float value) {
    // Check if name starts with "shader."
    if (name.compare(0, 7, "shader.") != 0) {
        return false;
    }

    // Extract the uniform name after "shader."
    std::string uniform_name = name.substr(7);
    if (uniform_name.empty()) {
        return false;
    }

    // Initialize uniforms collection if needed
    if (!uniforms) {
        uniforms = std::make_unique<UniformCollection>();
    }

    // Set the uniform value
    uniforms->setFloat(uniform_name, value);
    markDirty();
    return true;
}

bool UIDrawable::getShaderProperty(const std::string& name, float& value) const {
    // Check if name starts with "shader."
    if (name.compare(0, 7, "shader.") != 0) {
        return false;
    }

    // Extract the uniform name after "shader."
    std::string uniform_name = name.substr(7);
    if (uniform_name.empty() || !uniforms) {
        return false;
    }

    // Try to get the value from uniforms
    const auto* entry = uniforms->getEntry(uniform_name);
    if (!entry) {
        return false;
    }

    // UniformEntry is variant<UniformValue, shared_ptr<PropertyBinding>, shared_ptr<CallableBinding>>
    // UniformValue is variant<float, vec2, vec3, vec4>
    // So we need to check for UniformValue first, then extract the float from it

    // Try to extract static UniformValue from the entry
    if (const auto* uval = std::get_if<UniformValue>(entry)) {
        // Now try to extract float from UniformValue
        if (const float* fval = std::get_if<float>(uval)) {
            value = *fval;
            return true;
        }
        // Could be vec2/vec3/vec4 - not a float, return false
        return false;
    }

    // For bindings, evaluate and return
    if (const auto* prop_binding = std::get_if<std::shared_ptr<PropertyBinding>>(entry)) {
        auto opt_val = (*prop_binding)->evaluate();
        if (opt_val) {
            value = *opt_val;
            return true;
        }
    } else if (const auto* call_binding = std::get_if<std::shared_ptr<CallableBinding>>(entry)) {
        auto opt_val = (*call_binding)->evaluate();
        if (opt_val) {
            value = *opt_val;
            return true;
        }
    }

    return false;
}

bool UIDrawable::hasShaderProperty(const std::string& name) const {
    // Check if name starts with "shader."
    if (name.compare(0, 7, "shader.") != 0) {
        return false;
    }

    // Shader uniforms are always valid property names (they'll be created on set)
    return true;
}

// Python API for shader property
PyObject* UIDrawable::get_shader(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    if (!drawable->shader) {
        Py_RETURN_NONE;
    }

    // Return the shader object (increment reference)
    Py_INCREF(drawable->shader.get());
    return (PyObject*)drawable->shader.get();
}

int UIDrawable::set_shader(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    if (value == Py_None) {
        // Clear shader
        drawable->shader.reset();
        drawable->shader_dynamic = false;
        drawable->markDirty();
        return 0;
    }

    // Check if it's a Shader object
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyShaderType)) {
        PyErr_SetString(PyExc_TypeError, "shader must be a Shader object or None");
        return -1;
    }

    PyShaderObject* shader_obj = (PyShaderObject*)value;
    if (!shader_obj->shader) {
        PyErr_SetString(PyExc_ValueError, "Shader is not valid (compilation failed?)");
        return -1;
    }

    // Store the shader
    drawable->shader = std::shared_ptr<PyShaderObject>(shader_obj, [](PyShaderObject* p) {
        // Custom deleter that doesn't delete the Python object
        // The Python reference counting handles that
    });
    Py_INCREF(shader_obj);  // Keep the Python object alive

    // Create uniforms collection if needed
    if (!drawable->uniforms) {
        drawable->uniforms = std::make_unique<UniformCollection>();
    }

    // Set dynamic flag if shader is dynamic
    if (shader_obj->dynamic) {
        drawable->markShaderDynamic();
    }

    // Enable RenderTexture for shader rendering (if not already enabled)
    auto bounds = drawable->get_bounds();
    if (bounds.width > 0 && bounds.height > 0) {
        drawable->enableRenderTexture(
            static_cast<unsigned int>(bounds.width),
            static_cast<unsigned int>(bounds.height)
        );
    }

    drawable->markDirty();
    return 0;
}

PyObject* UIDrawable::get_uniforms(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // Create uniforms collection if needed
    if (!drawable->uniforms) {
        drawable->uniforms = std::make_unique<UniformCollection>();
    }

    // Create and return a Python wrapper for the collection
    PyUniformCollectionObject* collection = (PyUniformCollectionObject*)
        mcrfpydef::PyUniformCollectionType.tp_alloc(&mcrfpydef::PyUniformCollectionType, 0);

    if (!collection) return NULL;

    collection->collection = drawable->uniforms.get();
    collection->weakreflist = NULL;
    collection->owner = extractDrawableShared(self, objtype);

    return (PyObject*)collection;
}

// #369: single cache-aware conversion from a C++ drawable to its Python wrapper.
// Every path that hands a drawable back to Python must go through here (via
// mcrf::to_python), or object identity breaks (`x.parent is x.parent` -> False) and
// Python subclasses are lost. A miss registers the fresh wrapper (#430).
PyObject* UIDrawable::pyobject_for(std::shared_ptr<UIDrawable> drawable) {
    if (!drawable) {
        Py_RETURN_NONE;
    }

    // Each wrapper type stores a shared_ptr to its own concrete class.
    PyObject* obj = nullptr;
    #define MCRF_WRAP(ENUM, OBJ, TYPE, CLS, EXTRA)                                   \
        case PyObjectsEnum::ENUM:                                                    \
            obj = mcrf::cached_wrapper<OBJ>(drawable->serial_number,                 \
                &mcrfpydef::TYPE, [&](OBJ* o) {                                      \
                    o->data = std::static_pointer_cast<CLS>(drawable);               \
                    o->weakreflist = NULL;                                           \
                    EXTRA                                                            \
                });                                                                  \
            break;
    switch (drawable->derived_type()) {
        MCRF_WRAP(UIFRAME, PyUIFrameObject, PyUIFrameType, UIFrame, )
        MCRF_WRAP(UICAPTION, PyUICaptionObject, PyUICaptionType, UICaption, o->font = nullptr;)
        MCRF_WRAP(UISPRITE, PyUISpriteObject, PyUISpriteType, UISprite, )
        MCRF_WRAP(UIGRIDVIEW, PyUIGridViewObject, PyUIGridViewType, UIGridView, )
        MCRF_WRAP(UILINE, PyUILineObject, PyUILineType, UILine, )
        MCRF_WRAP(UICIRCLE, PyUICircleObject, PyUICircleType, UICircle, )
        MCRF_WRAP(UIARC, PyUIArcObject, PyUIArcType, UIArc, )
        MCRF_WRAP(UIVIEWPORT3D, PyViewport3DObject, PyViewport3DType, mcrf::Viewport3D, )
        default:
            PyErr_SetString(PyExc_TypeError, "Unknown UIDrawable derived type");
            return nullptr;
    }
    #undef MCRF_WRAP
    // #443: a wrapper made for an object that is already contained is pinned now.
    if (obj) drawable->updatePyIdentityPin();
    return obj;
}

// Python API - get parent drawable
PyObject* UIDrawable::get_parent(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // #183: Check for scene parent first
    if (!drawable->parent_scene.empty()) {
        PyObject* scene = PySceneClass::get_scene_by_name(drawable->parent_scene);
        if (scene) {
            return scene;  // Already has new reference from get_scene_by_name
        }
        // Scene not found in python_scenes (shouldn't happen, but fall through to None)
    }

    return UIDrawable::pyobject_for(drawable->getParent());
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
        case PyObjectsEnum::UILINE:
            drawable = ((PyUILineObject*)self)->data;
            break;
        case PyObjectsEnum::UICIRCLE:
            drawable = ((PyUICircleObject*)self)->data;
            break;
        case PyObjectsEnum::UIARC:
            drawable = ((PyUIArcObject*)self)->data;
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            drawable = ((PyUIGridViewObject*)self)->data;
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

    // Value must be a Frame, Grid, or Scene (things with children collections).
    // #364: the internal _GridData (PyGridDataType) is NOT among them -- it holds
    // entities and cells, never drawables -- so it falls through to the TypeError.
    bool is_frame = PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIFrameType);
    bool is_gridview = PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridViewType);
    bool is_scene = PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PySceneType);

    if (!is_frame && !is_gridview && !is_scene) {
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

    // Get the new parent's children collection and append
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>* children_ptr = nullptr;
    std::shared_ptr<UIDrawable> new_parent = nullptr;

    if (is_frame) {
        auto frame = ((PyUIFrameObject*)value)->data;
        children_ptr = &frame->children;
        new_parent = frame;
    } else if (is_gridview) {
        // #364: overlay children belong to the view itself, not to the grid data.
        auto view = ((PyUIGridViewObject*)value)->data;
        children_ptr = &view->children;
        new_parent = view;
    }

    if (!UIDrawable::canAdopt(new_parent, drawable.get())) return -1;  // #442

    // Remove from old parent first
    drawable->removeFromParent();

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
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    // #331: direct allocation fast path — no module import or type call per read
    return PyVector(drawable->get_global_position()).pyObject();
}

// #138, #188 - Python API for bounds property - returns (pos, size) as pair of Vectors
PyObject* UIDrawable::get_bounds_py(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    sf::FloatRect bounds = drawable->get_bounds();

    // Get Vector type
    PyObject* vector_type = (PyObject*)&mcrfpydef::PyVectorType;

    // Create pos vector
    PyObject* pos_args = Py_BuildValue("(ff)", bounds.left, bounds.top);
    PyObject* pos = PyObject_CallObject(vector_type, pos_args);
    Py_DECREF(pos_args);
    if (!pos) {
        return NULL;
    }

    // Create size vector
    PyObject* size_args = Py_BuildValue("(ff)", bounds.width, bounds.height);
    PyObject* size = PyObject_CallObject(vector_type, size_args);
    Py_DECREF(size_args);
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
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    sf::FloatRect bounds = drawable->get_global_bounds();

    // Get Vector type
    PyObject* vector_type = (PyObject*)&mcrfpydef::PyVectorType;

    // Create pos vector
    PyObject* pos_args = Py_BuildValue("(ff)", bounds.left, bounds.top);
    PyObject* pos = PyObject_CallObject(vector_type, pos_args);
    Py_DECREF(pos_args);
    if (!pos) {
        return NULL;
    }

    // Create size vector
    PyObject* size_args = Py_BuildValue("(ff)", bounds.width, bounds.height);
    PyObject* size = PyObject_CallObject(vector_type, size_args);
    Py_DECREF(size_args);
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
        case PyObjectsEnum::UIGRIDVIEW:
            if (((PyUIGridViewObject*)self)->data->on_enter_callable)
                ptr = ((PyUIGridViewObject*)self)->data->on_enter_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_enter");
            return NULL;
    }
    if (ptr && ptr != Py_None) {
        Py_INCREF(ptr);  // Return new reference, not borrowed
        return ptr;
    }
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
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            target = ((PyUIGridViewObject*)self)->data.get();
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
        case PyObjectsEnum::UIGRIDVIEW:
            if (((PyUIGridViewObject*)self)->data->on_exit_callable)
                ptr = ((PyUIGridViewObject*)self)->data->on_exit_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_exit");
            return NULL;
    }
    if (ptr && ptr != Py_None) {
        Py_INCREF(ptr);  // Return new reference, not borrowed
        return ptr;
    }
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
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            target = ((PyUIGridViewObject*)self)->data.get();
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
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

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
        case PyObjectsEnum::UIGRIDVIEW:
            if (((PyUIGridViewObject*)self)->data->on_move_callable)
                ptr = ((PyUIGridViewObject*)self)->data->on_move_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "Invalid UIDrawable derived instance for on_move");
            return NULL;
    }
    if (ptr && ptr != Py_None) {
        Py_INCREF(ptr);  // Return new reference, not borrowed
        return ptr;
    }
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
        case PyObjectsEnum::UILINE:
            target = ((PyUILineObject*)self)->data.get();
            break;
        case PyObjectsEnum::UICIRCLE:
            target = ((PyUICircleObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIARC:
            target = ((PyUIArcObject*)self)->data.get();
            break;
        case PyObjectsEnum::UIGRIDVIEW:
            target = ((PyUIGridViewObject*)self)->data.get();
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
PyObject* UIDrawable_animate_impl(std::shared_ptr<UIDrawable> self, const char* type_name,
                                  PyObject* args, PyObject* kwds) {
    return mcrf::animate(self, type_name, args, kwds,
        [](Animation& a, const std::shared_ptr<UIDrawable>& t) { a.start(t); });
}

// ============================================================================
// Callback Cache Support (#184) - Python subclass method resolution
// ============================================================================

// Key for storing callback generation on Python type objects
static const char* CALLBACK_GEN_ATTR = "_mcrf_callback_gen";

uint32_t UIDrawable::getCallbackGeneration(PyObject* type) {
    if (!type) return 0;

    PyObject* gen = PyObject_GetAttrString(type, CALLBACK_GEN_ATTR);
    if (gen) {
        uint32_t result = static_cast<uint32_t>(PyLong_AsUnsignedLong(gen));
        Py_DECREF(gen);
        return result;
    }

    // No generation set yet - initialize to 0
    PyErr_Clear();
    return 0;
}

void UIDrawable::incrementCallbackGeneration(PyObject* type) {
    if (!type) return;

    uint32_t current = getCallbackGeneration(type);
    PyObject* new_gen = PyLong_FromUnsignedLong(current + 1);
    if (new_gen) {
        PyObject_SetAttrString(type, CALLBACK_GEN_ATTR, new_gen);
        Py_DECREF(new_gen);
    }
    PyErr_Clear();  // Clear any errors from SetAttr
}

bool UIDrawable::isCallbackCacheValid(PyObject* type) const {
    if (!callback_cache.valid) return false;
    return callback_cache.generation == getCallbackGeneration(type);
}

void UIDrawable::refreshCallbackCache(PyObject* pyObj) {
    if (!pyObj) return;

    PyObject* type = (PyObject*)Py_TYPE(pyObj);

    // Update generation
    callback_cache.generation = getCallbackGeneration(type);
    callback_cache.valid = true;

    // Check for each callback method
    // We check the object (not just the class) to handle instance attributes too

    // on_click
    PyObject* attr = PyObject_GetAttrString(pyObj, "on_click");
    callback_cache.has_on_click = (attr && PyCallable_Check(attr) && attr != Py_None);
    Py_XDECREF(attr);
    PyErr_Clear();

    // on_enter
    attr = PyObject_GetAttrString(pyObj, "on_enter");
    callback_cache.has_on_enter = (attr && PyCallable_Check(attr) && attr != Py_None);
    Py_XDECREF(attr);
    PyErr_Clear();

    // on_exit
    attr = PyObject_GetAttrString(pyObj, "on_exit");
    callback_cache.has_on_exit = (attr && PyCallable_Check(attr) && attr != Py_None);
    Py_XDECREF(attr);
    PyErr_Clear();

    // on_move
    attr = PyObject_GetAttrString(pyObj, "on_move");
    callback_cache.has_on_move = (attr && PyCallable_Check(attr) && attr != Py_None);
    Py_XDECREF(attr);
    PyErr_Clear();
}

// ============================================================================
// Alignment System Implementation
// ============================================================================

void UIDrawable::applyAlignment() {
    if (align_type == AlignmentType::NONE) return;

    float pw, ph;  // Parent width/height
    auto p = parent.lock();

    if (p) {
        // Parent is another UIDrawable (Frame, Grid, etc.)
        sf::FloatRect parent_bounds = p->get_bounds();
        pw = parent_bounds.width;
        ph = parent_bounds.height;
    } else if (!parent_scene.empty()) {
        // Parent is a Scene - use window's game resolution
        GameEngine* game = McRFPy_API::game;
        if (!game) return;
        sf::Vector2u resolution = game->getGameResolution();
        pw = static_cast<float>(resolution.x);
        ph = static_cast<float>(resolution.y);
    } else {
        return;  // No parent at all = can't align
    }

    sf::FloatRect self_bounds = get_bounds();
    float cw = self_bounds.width, ch = self_bounds.height;

    // Use specific margins if set (>= 0), otherwise inherit from general margin
    // -1.0 means "inherit", any value >= 0 is an explicit override
    float mx = (align_horiz_margin >= 0.0f) ? align_horiz_margin : align_margin;
    float my = (align_vert_margin >= 0.0f) ? align_vert_margin : align_margin;

    float x = 0, y = 0;
    switch (align_type) {
        case AlignmentType::TOP_LEFT:
            x = mx;
            y = my;
            break;
        case AlignmentType::TOP_CENTER:
            x = (pw - cw) / 2.0f;
            y = my;
            break;
        case AlignmentType::TOP_RIGHT:
            x = pw - cw - mx;
            y = my;
            break;
        case AlignmentType::CENTER_LEFT:
            x = mx;
            y = (ph - ch) / 2.0f;
            break;
        case AlignmentType::CENTER:
            x = (pw - cw) / 2.0f;
            y = (ph - ch) / 2.0f;
            break;
        case AlignmentType::CENTER_RIGHT:
            x = pw - cw - mx;
            y = (ph - ch) / 2.0f;
            break;
        case AlignmentType::BOTTOM_LEFT:
            x = mx;
            y = ph - ch - my;
            break;
        case AlignmentType::BOTTOM_CENTER:
            x = (pw - cw) / 2.0f;
            y = ph - ch - my;
            break;
        case AlignmentType::BOTTOM_RIGHT:
            x = pw - cw - mx;
            y = ph - ch - my;
            break;
        default:
            return;
    }

    // For most drawables, position IS the bounding box top-left corner
    // But for Circle and Arc, position is the center, and for Line the midpoint
    // (#426), so we need to adjust
    float offset_x = 0.0f;
    float offset_y = 0.0f;

    auto dtype = derived_type();
    if (dtype == PyObjectsEnum::UICIRCLE || dtype == PyObjectsEnum::UIARC ||
        dtype == PyObjectsEnum::UILINE) {
        // offset = position - bounds.topLeft
        offset_x = position.x - self_bounds.left;
        offset_y = position.y - self_bounds.top;
    }

    assignPosition(sf::Vector2f(x + offset_x, y + offset_y));
}

void UIDrawable::setAlignment(AlignmentType align) {
    align_type = align;
    if (align != AlignmentType::NONE) {
        applyAlignment();
    }
}

void UIDrawable::realign() {
    // Reapply alignment - useful for responsive layouts
    if (align_type != AlignmentType::NONE) {
        applyAlignment();
    }
}

PyObject* UIDrawable::py_realign(PyObject* self, PyObject* args) {
    PyObjectsEnum objtype = PyObjectsEnum::UIFRAME;  // Default, will be set by type check

    // Determine the type from the Python object
    if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUIFrameType)) objtype = PyObjectsEnum::UIFRAME;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUICaptionType)) objtype = PyObjectsEnum::UICAPTION;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUISpriteType)) objtype = PyObjectsEnum::UISPRITE;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUIGridViewType)) objtype = PyObjectsEnum::UIGRIDVIEW;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUILineType)) objtype = PyObjectsEnum::UILINE;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUICircleType)) objtype = PyObjectsEnum::UICIRCLE;
    else if (PyObject_IsInstance(self, (PyObject*)&mcrfpydef::PyUIArcType)) objtype = PyObjectsEnum::UIARC;

    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    drawable->realign();
    Py_RETURN_NONE;
}

bool UIDrawable::validateMargins(AlignmentType align, float margin, float horiz_margin, float vert_margin, bool set_error) {
    // Calculate effective margins (-1 means inherit from general margin)
    float eff_horiz = (horiz_margin >= 0.0f) ? horiz_margin : margin;
    float eff_vert = (vert_margin >= 0.0f) ? vert_margin : margin;

    // CENTER alignment doesn't support any margins
    if (align == AlignmentType::CENTER) {
        if (margin != 0.0f || eff_horiz != 0.0f || eff_vert != 0.0f) {
            if (set_error) {
                PyErr_SetString(PyExc_ValueError,
                    "CENTER alignment does not support margins");
            }
            return false;
        }
    }

    // Horizontally centered alignments don't support horiz_margin override
    // (margin is applied vertically only)
    if (align == AlignmentType::TOP_CENTER || align == AlignmentType::BOTTOM_CENTER) {
        // If horiz_margin is explicitly set (not -1), it must be 0 or error
        if (horiz_margin >= 0.0f && horiz_margin != 0.0f) {
            if (set_error) {
                PyErr_SetString(PyExc_ValueError,
                    "TOP_CENTER and BOTTOM_CENTER alignments do not support horiz_margin");
            }
            return false;
        }
    }

    // Vertically centered alignments don't support vert_margin override
    // (margin is applied horizontally only)
    if (align == AlignmentType::CENTER_LEFT || align == AlignmentType::CENTER_RIGHT) {
        // If vert_margin is explicitly set (not -1), it must be 0 or error
        if (vert_margin >= 0.0f && vert_margin != 0.0f) {
            if (set_error) {
                PyErr_SetString(PyExc_ValueError,
                    "CENTER_LEFT and CENTER_RIGHT alignments do not support vert_margin");
            }
            return false;
        }
    }

    return true;
}

// Python API: get align property
PyObject* UIDrawable::get_align(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    if (drawable->align_type == AlignmentType::NONE) {
        Py_RETURN_NONE;
    }

    // Return Alignment enum member
    if (!PyAlignment::alignment_enum_class) {
        PyErr_SetString(PyExc_RuntimeError, "Alignment enum not initialized");
        return NULL;
    }

    PyObject* value = PyLong_FromLong(static_cast<int>(drawable->align_type));
    if (!value) return NULL;

    PyObject* result = PyObject_CallFunctionObjArgs(PyAlignment::alignment_enum_class, value, NULL);
    Py_DECREF(value);
    return result;
}

// Python API: set align property
int UIDrawable::set_align(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    if (value == Py_None) {
        drawable->align_type = AlignmentType::NONE;
        return 0;
    }

    AlignmentType align;
    if (!PyAlignment::from_arg(value, &align)) {
        return -1;
    }

    // Validate margins for new alignment
    if (!validateMargins(align, drawable->align_margin, drawable->align_horiz_margin, drawable->align_vert_margin)) {
        return -1;
    }

    drawable->setAlignment(align);
    return 0;
}

// Python API: get margin property
PyObject* UIDrawable::get_margin(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyFloat_FromDouble(drawable->align_margin);
}

// Python API: set margin property
int UIDrawable::set_margin(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    float margin = 0.0f;
    if (PyFloat_Check(value)) {
        margin = static_cast<float>(PyFloat_AsDouble(value));
    } else if (PyLong_Check(value)) {
        margin = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "margin must be a number");
        return -1;
    }

    // Validate margins for current alignment
    if (drawable->align_type != AlignmentType::NONE) {
        if (!validateMargins(drawable->align_type, margin, drawable->align_horiz_margin, drawable->align_vert_margin)) {
            return -1;
        }
    }

    drawable->align_margin = margin;
    if (drawable->align_type != AlignmentType::NONE) {
        drawable->applyAlignment();
    }
    return 0;
}

// Python API: get horiz_margin property
PyObject* UIDrawable::get_horiz_margin(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyFloat_FromDouble(drawable->align_horiz_margin);
}

// Python API: set horiz_margin property
int UIDrawable::set_horiz_margin(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    float horiz_margin = 0.0f;
    if (PyFloat_Check(value)) {
        horiz_margin = static_cast<float>(PyFloat_AsDouble(value));
    } else if (PyLong_Check(value)) {
        horiz_margin = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "horiz_margin must be a number");
        return -1;
    }

    // Validate margins for current alignment
    if (drawable->align_type != AlignmentType::NONE) {
        if (!validateMargins(drawable->align_type, drawable->align_margin, horiz_margin, drawable->align_vert_margin)) {
            return -1;
        }
    }

    drawable->align_horiz_margin = horiz_margin;
    if (drawable->align_type != AlignmentType::NONE) {
        drawable->applyAlignment();
    }
    return 0;
}

// Python API: get vert_margin property
PyObject* UIDrawable::get_vert_margin(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return NULL;

    return PyFloat_FromDouble(drawable->align_vert_margin);
}

// Python API: set vert_margin property
int UIDrawable::set_vert_margin(PyObject* self, PyObject* value, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<intptr_t>(closure));
    UIDrawable* drawable = extractDrawable(self, objtype);
    if (!drawable) return -1;

    float vert_margin = 0.0f;
    if (PyFloat_Check(value)) {
        vert_margin = static_cast<float>(PyFloat_AsDouble(value));
    } else if (PyLong_Check(value)) {
        vert_margin = static_cast<float>(PyLong_AsLong(value));
    } else {
        PyErr_SetString(PyExc_TypeError, "vert_margin must be a number");
        return -1;
    }

    // Validate margins for current alignment
    if (drawable->align_type != AlignmentType::NONE) {
        if (!validateMargins(drawable->align_type, drawable->align_margin, drawable->align_horiz_margin, vert_margin)) {
            return -1;
        }
    }

    drawable->align_vert_margin = vert_margin;
    if (drawable->align_type != AlignmentType::NONE) {
        drawable->applyAlignment();
    }
    return 0;
}
