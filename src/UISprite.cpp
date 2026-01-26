#include "UISprite.h"
#include "GameEngine.h"
#include "PyVector.h"
#include "PythonObjectCache.h"
#include "UIFrame.h"  // #144: For snapshot= parameter
#include "PyAlignment.h"
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection support
// UIDrawable methods now in UIBase.h

UIDrawable* UISprite::click_at(sf::Vector2f point)
{
    // #184: Also check for Python subclass (might have on_click method)
    if (!click_callable && !is_python_subclass) return nullptr;

    // Get sprite dimensions from local bounds
    sf::FloatRect localBounds = sprite.getLocalBounds();
    float w = localBounds.width * sprite.getScale().x;
    float h = localBounds.height * sprite.getScale().y;

    // Transform click point to local coordinates accounting for rotation
    sf::Vector2f localPoint;
    if (rotation != 0.0f) {
        // Build transform: translate to position, then rotate around origin
        sf::Transform transform;
        transform.translate(position);
        transform.translate(origin);
        transform.rotate(rotation);
        transform.translate(-origin);

        // Apply inverse transform to get local coordinates
        sf::Transform inverse = transform.getInverse();
        localPoint = inverse.transformPoint(point);
    } else {
        // No rotation - simple subtraction
        localPoint = point - position;
    }

    // Check if local point is within bounds (0,0 to w,h in local space)
    if (localPoint.x >= 0 && localPoint.y >= 0 && localPoint.x < w && localPoint.y < h) {
        return this;
    }
    return nullptr;
}

UISprite::UISprite() 
: sprite_index(0), ptex(nullptr)
{
    // Initialize sprite to safe defaults
    position = sf::Vector2f(0.0f, 0.0f);  // Set base class position
    sprite.setPosition(position);         // Sync sprite position
    sprite.setScale(1.0f, 1.0f);
}

UISprite::UISprite(std::shared_ptr<PyTexture> _ptex, int _sprite_index, sf::Vector2f _pos, float _scale)
: ptex(_ptex), sprite_index(_sprite_index)
{
    position = _pos;  // Set base class position
    sprite = ptex->sprite(sprite_index, position, sf::Vector2f(_scale, _scale));
}

UISprite::UISprite(const UISprite& other) 
    : UIDrawable(other),
      sprite_index(other.sprite_index),
      sprite(other.sprite),
      ptex(other.ptex)
{
}

UISprite& UISprite::operator=(const UISprite& other) {
    if (this != &other) {
        UIDrawable::operator=(other);
        sprite_index = other.sprite_index;
        sprite = other.sprite;
        ptex = other.ptex;
    }
    return *this;
}

UISprite::UISprite(UISprite&& other) noexcept
    : UIDrawable(std::move(other)),
      sprite_index(other.sprite_index),
      sprite(std::move(other.sprite)),
      ptex(std::move(other.ptex))
{
}

UISprite& UISprite::operator=(UISprite&& other) noexcept {
    if (this != &other) {
        UIDrawable::operator=(std::move(other));
        sprite_index = other.sprite_index;
        sprite = std::move(other.sprite);
        ptex = std::move(other.ptex);
    }
    return *this;
}

/*
void UISprite::render(sf::Vector2f offset)
{
    sprite.move(offset);
    Resources::game->getWindow().draw(sprite);
    sprite.move(-offset);
}
*/

void UISprite::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    // Check visibility
    if (!visible) return;

    // Apply opacity
    auto color = sprite.getColor();
    color.a = static_cast<sf::Uint8>(255 * opacity);
    sprite.setColor(color);

    // Apply rotation and origin
    sprite.setOrigin(origin);
    sprite.setRotation(rotation);

    // #106: Shader rendering path
    if (shader && shader->shader) {
        // Get the sprite bounds for rendering
        auto bounds = sprite.getGlobalBounds();
        sf::Vector2f screen_pos = offset + position;

        // Get or create intermediate texture
        auto& intermediate = GameEngine::getShaderIntermediate();
        intermediate.clear(sf::Color::Transparent);

        // Render sprite at origin in intermediate texture
        sf::Sprite temp_sprite = sprite;
        temp_sprite.setPosition(0, 0);  // Render at origin of intermediate texture
        intermediate.draw(temp_sprite);
        intermediate.display();

        // Create result sprite from intermediate texture
        sf::Sprite result_sprite(intermediate.getTexture());
        result_sprite.setPosition(screen_pos);

        // Apply engine uniforms
        sf::Vector2f resolution(bounds.width, bounds.height);
        PyShader::applyEngineUniforms(*shader->shader, resolution);

        // Apply user uniforms
        if (uniforms) {
            uniforms->applyTo(*shader->shader);
        }

        // Draw with shader
        target.draw(result_sprite, shader->shader.get());
    } else {
        // Standard rendering path (no shader)
        sprite.move(offset);
        target.draw(sprite);
        sprite.move(-offset);
    }

    // Restore original alpha
    color.a = 255;
    sprite.setColor(color);
}

void UISprite::setPosition(sf::Vector2f pos)
{
    position = pos;  // Update base class position
    sprite.setPosition(position);  // Sync sprite position
}

void UISprite::setScale(sf::Vector2f s)
{
    sprite.setScale(s);
}

void UISprite::setTexture(std::shared_ptr<PyTexture> _ptex, int _sprite_index)
{
    ptex = _ptex;
    if (_sprite_index != -1) // if you are changing textures, there's a good chance you need a new index too
        sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, position, sprite.getScale());  // Use base class position
}

void UISprite::setSpriteIndex(int _sprite_index)
{
    sprite_index = _sprite_index;
    sprite = ptex->sprite(sprite_index, position, sprite.getScale());  // Use base class position
}

sf::Vector2f UISprite::getScale() const
{
    return sprite.getScale();
}

sf::Vector2f UISprite::getPosition()
{
    return position;  // Return base class position
}

std::shared_ptr<PyTexture> UISprite::getTexture()
{
    return ptex;
}

int UISprite::getSpriteIndex()
{
    return sprite_index;
}

PyObjectsEnum UISprite::derived_type()
{
    return PyObjectsEnum::UISPRITE;
}

// Phase 1 implementations
sf::FloatRect UISprite::get_bounds() const
{
    return sprite.getGlobalBounds();
}

void UISprite::move(float dx, float dy)
{
    position.x += dx;
    position.y += dy;
    sprite.setPosition(position);  // Keep sprite in sync
}

void UISprite::resize(float w, float h)
{
    // Calculate scale factors to achieve target size while preserving aspect ratio
    auto bounds = sprite.getLocalBounds();
    if (bounds.width > 0 && bounds.height > 0) {
        float scaleX = w / bounds.width;
        float scaleY = h / bounds.height;
        
        // Use the smaller scale factor to maintain aspect ratio
        // This ensures the sprite fits within the given bounds
        float scale = std::min(scaleX, scaleY);
        
        // Apply uniform scaling to preserve aspect ratio
        sprite.setScale(scale, scale);
    }
}

void UISprite::onPositionChanged()
{
    // Sync sprite position with base class position
    sprite.setPosition(position);
}

PyObject* UISprite::get_float_member(PyUISpriteObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->getPosition().x);
    else if (member_ptr == 1)
        return PyFloat_FromDouble(self->data->getPosition().y);
    else if (member_ptr == 2)
        return PyFloat_FromDouble(self->data->getScale().x); // scale X and Y are identical, presently
    else if (member_ptr == 3)
        return PyFloat_FromDouble(self->data->getScale().x); // scale_x
    else if (member_ptr == 4)
        return PyFloat_FromDouble(self->data->getScale().y); // scale_y
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UISprite::set_float_member(PyUISpriteObject* self, PyObject* value, void* closure)
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
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    if (member_ptr == 0) //x
        self->data->setPosition(sf::Vector2f(val, self->data->getPosition().y));
    else if (member_ptr == 1) //y
        self->data->setPosition(sf::Vector2f(self->data->getPosition().x, val));
    else if (member_ptr == 2) // scale (uniform)
        self->data->setScale(sf::Vector2f(val, val));
    else if (member_ptr == 3) // scale_x
        self->data->setScale(sf::Vector2f(val, self->data->getScale().y));
    else if (member_ptr == 4) // scale_y
        self->data->setScale(sf::Vector2f(self->data->getScale().x, val));
    return 0;
}

PyObject* UISprite::get_int_member(PyUISpriteObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (true) {}
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
    
    return PyLong_FromDouble(self->data->getSpriteIndex());
}

int UISprite::set_int_member(PyUISpriteObject* self, PyObject* value, void* closure)
{
    int val;
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "sprite_index must be an integer");
        return -1;
    }
    
    // Validate sprite index is within texture bounds
    auto texture = self->data->getTexture();
    if (texture) {
        int sprite_count = texture->getSpriteCount();
        
        if (val < 0 || val >= sprite_count) {
            PyErr_Format(PyExc_ValueError, 
                "Sprite index %d out of range. Texture has %d sprites (0-%d)", 
                val, sprite_count, sprite_count - 1);
            return -1;
        }
    }
    
    self->data->setSpriteIndex(val);
    return 0;
}

PyObject* UISprite::get_texture(PyUISpriteObject* self, void* closure)
{
    return self->data->getTexture()->pyObject();
}

int UISprite::set_texture(PyUISpriteObject* self, PyObject* value, void* closure)
{
    // Check if value is a Texture instance
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    }
    
    // Get the texture from the Python object
    auto pytexture = (PyTextureObject*)value;
    if (!pytexture->data) {
        PyErr_SetString(PyExc_ValueError, "Invalid texture object");
        return -1;
    }
    
    // Update the sprite's texture
    self->data->setTexture(pytexture->data);
    
    return 0;
}

PyObject* UISprite::get_pos(PyUISpriteObject* self, void* closure)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        auto pos = self->data->getPosition();
        obj->data = sf::Vector2f(pos.x, pos.y);
    }
    return (PyObject*)obj;
}

int UISprite::set_pos(PyUISpriteObject* self, PyObject* value, void* closure)
{
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "pos must be a Vector or convertible to Vector");
        return -1;
    }
    self->data->setPosition(vec->data);
    return 0;
}

// Define the PyObjectType alias for the macros
typedef PyUISpriteObject PyObjectType;

// Method definitions
PyMethodDef UISprite_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}  // Sentinel
};

PyGetSetDef UISprite::getsetters[] = {
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "X coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UISPRITE << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "Y coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UISPRITE << 8 | 1)},
    {"scale", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Uniform size factor",                   (void*)2},
    {"scale_x", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Horizontal scale factor",         (void*)3},
    {"scale_y", (getter)UISprite::get_float_member, (setter)UISprite::set_float_member, "Vertical scale factor",           (void*)4},
    {"sprite_index", (getter)UISprite::get_int_member, (setter)UISprite::set_int_member, "Which sprite on the texture is shown", NULL},
    {"sprite_number", (getter)UISprite::get_int_member, (setter)UISprite::set_int_member, "Sprite index (DEPRECATED: use sprite_index instead)", NULL},
    {"texture", (getter)UISprite::get_texture, (setter)UISprite::set_texture,     "Texture object",                    NULL},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: str, action: str)."
     ), (void*)PyObjectsEnum::UISPRITE},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UISPRITE},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name, "Name for finding elements", (void*)PyObjectsEnum::UISPRITE},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos, "Position as a Vector", (void*)PyObjectsEnum::UISPRITE},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos, "Position in grid tile coordinates (only when parent is Grid)", (void*)PyObjectsEnum::UISPRITE},
    {"grid_size", (getter)UIDrawable::get_grid_size, (setter)UIDrawable::set_grid_size, "Size in grid tile coordinates (only when parent is Grid)", (void*)PyObjectsEnum::UISPRITE},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UISPRITE),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UISPRITE),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UISPRITE),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UISPRITE),
    {NULL}
};

PyObject* UISprite::repr(PyUISpriteObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Sprite (invalid internal object)>";
    else {
        //auto sprite = self->data->sprite;
        ss << "<Sprite (x=" << self->data->getPosition().x << ", y=" << self->data->getPosition().y << ", " <<
            "scale=" << self->data->getScale().x << ", " <<
            "sprite_index=" << self->data->getSpriteIndex() << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UISprite::init(PyUISpriteObject* self, PyObject* args, PyObject* kwds)
{
    // Define all parameters with defaults
    PyObject* pos_obj = nullptr;
    PyObject* texture = nullptr;
    int sprite_index = 0;
    float scale = 1.0f;
    float scale_x = 1.0f;
    float scale_y = 1.0f;
    PyObject* click_handler = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f;
    PyObject* snapshot = nullptr;  // #144: snapshot parameter
    PyObject* align_obj = nullptr;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;

    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "pos", "texture", "sprite_index",  // Positional args (as per spec)
        // Keyword-only args
        "scale", "scale_x", "scale_y", "on_click",
        "visible", "opacity", "z_index", "name", "x", "y", "snapshot",
        "align", "margin", "horiz_margin", "vert_margin",
        nullptr
    };

    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOifffOifizffOOfff", const_cast<char**>(kwlist),
                                     &pos_obj, &texture, &sprite_index,  // Positional
                                     &scale, &scale_x, &scale_y, &click_handler,
                                     &visible, &opacity, &z_index, &name, &x, &y, &snapshot,
                                     &align_obj, &margin, &horiz_margin, &vert_margin)) {
        return -1;
    }
    
    // Handle position argument (can be tuple, Vector, or use x/y keywords)
    if (pos_obj) {
        PyVectorObject* vec = PyVector::from_arg(pos_obj);
        if (vec) {
            x = vec->data.x;
            y = vec->data.y;
            Py_DECREF(vec);
        } else {
            PyErr_Clear();
            if (PyTuple_Check(pos_obj) && PyTuple_Size(pos_obj) == 2) {
                PyObject* x_val = PyTuple_GetItem(pos_obj, 0);
                PyObject* y_val = PyTuple_GetItem(pos_obj, 1);
                if ((PyFloat_Check(x_val) || PyLong_Check(x_val)) &&
                    (PyFloat_Check(y_val) || PyLong_Check(y_val))) {
                    x = PyFloat_Check(x_val) ? PyFloat_AsDouble(x_val) : PyLong_AsLong(x_val);
                    y = PyFloat_Check(y_val) ? PyFloat_AsDouble(y_val) : PyLong_AsLong(y_val);
                } else {
                    PyErr_SetString(PyExc_TypeError, "pos tuple must contain numbers");
                    return -1;
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "pos must be a tuple (x, y) or Vector");
                return -1;
            }
        }
    }

    // #144: Handle snapshot parameter - renders a UIDrawable to texture
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    if (snapshot && snapshot != Py_None) {
        // Check if snapshot is a Frame (most common case)
        PyObject* frame_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
        if (PyObject_IsInstance(snapshot, frame_type)) {
            Py_DECREF(frame_type);
            auto pyframe = (PyUIFrameObject*)snapshot;
            if (!pyframe->data) {
                PyErr_SetString(PyExc_ValueError, "Invalid Frame object for snapshot");
                return -1;
            }

            // Get bounds and create render texture
            auto bounds = pyframe->data->get_bounds();
            if (bounds.width <= 0 || bounds.height <= 0) {
                PyErr_SetString(PyExc_ValueError, "snapshot Frame must have positive size");
                return -1;
            }

            sf::RenderTexture render_tex;
            if (!render_tex.create(static_cast<unsigned int>(bounds.width),
                                   static_cast<unsigned int>(bounds.height))) {
                PyErr_SetString(PyExc_RuntimeError, "Failed to create RenderTexture for snapshot");
                return -1;
            }

            // Render the frame to the texture
            render_tex.clear(sf::Color::Transparent);
            pyframe->data->render(sf::Vector2f(0, 0), render_tex);
            render_tex.display();

            // Create PyTexture from the rendered content
            texture_ptr = PyTexture::from_rendered(render_tex);
            sprite_index = 0;  // Snapshot is always sprite index 0
        } else {
            Py_DECREF(frame_type);
            PyErr_SetString(PyExc_TypeError, "snapshot must be a Frame instance");
            return -1;
        }
    }
    // Handle texture - allow None or use default (only if no snapshot)
    else if (texture && texture != Py_None) {
        if (!PyObject_IsInstance(texture, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
            return -1;
        }
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
    
    // Create the sprite
    self->data = std::make_shared<UISprite>(texture_ptr, sprite_index, sf::Vector2f(x, y), scale);
    
    // Set scale properties
    if (scale_x != 1.0f || scale_y != 1.0f) {
        // If scale_x or scale_y were explicitly set, use them
        self->data->setScale(sf::Vector2f(scale_x, scale_y));
    } else if (scale != 1.0f) {
        // Otherwise use uniform scale
        self->data->setScale(sf::Vector2f(scale, scale));
    }
    
    // Set other properties
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    if (name) {
        self->data->name = std::string(name);
    }

    // Process alignment arguments
    UIDRAWABLE_PROCESS_ALIGNMENT(self->data, align_obj, margin, horiz_margin, vert_margin);

    // Handle click handler
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }

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

    // #184: Check if this is a Python subclass (for callback method support)
    PyObject* sprite_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
    if (sprite_type) {
        self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != sprite_type;
        Py_DECREF(sprite_type);
    }

    return 0;
}

// Property system implementation for animations
bool UISprite::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        sprite.setPosition(position);  // Keep sprite in sync
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "y") {
        position.y = value;
        sprite.setPosition(position);  // Keep sprite in sync
        markCompositeDirty();  // #144 - Position change, texture still valid
        return true;
    }
    else if (name == "scale") {
        sprite.setScale(sf::Vector2f(value, value));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "scale_x") {
        sprite.setScale(sf::Vector2f(value, sprite.getScale().y));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "scale_y") {
        sprite.setScale(sf::Vector2f(sprite.getScale().x, value));
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        markDirty();  // #144 - Z-order change affects parent
        return true;
    }
    else if (name == "rotation") {
        rotation = value;
        sprite.setRotation(rotation);
        markDirty();
        return true;
    }
    else if (name == "origin_x") {
        origin.x = value;
        sprite.setOrigin(origin);
        markDirty();
        return true;
    }
    else if (name == "origin_y") {
        origin.y = value;
        sprite.setOrigin(origin);
        markDirty();
        return true;
    }
    // #106: Check for shader uniform properties
    if (setShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UISprite::setProperty(const std::string& name, int value) {
    if (name == "sprite_index" || name == "sprite_number") {
        setSpriteIndex(value);
        markDirty();  // #144 - Content change
        return true;
    }
    else if (name == "z_index") {
        z_index = value;
        markDirty();  // #144 - Z-order change affects parent
        return true;
    }
    return false;
}

bool UISprite::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = position.x;
        return true;
    }
    else if (name == "y") {
        value = position.y;
        return true;
    }
    else if (name == "scale") {
        value = sprite.getScale().x;  // Assuming uniform scale
        return true;
    }
    else if (name == "scale_x") {
        value = sprite.getScale().x;
        return true;
    }
    else if (name == "scale_y") {
        value = sprite.getScale().y;
        return true;
    }
    else if (name == "z_index") {
        value = static_cast<float>(z_index);
        return true;
    }
    else if (name == "rotation") {
        value = rotation;
        return true;
    }
    else if (name == "origin_x") {
        value = origin.x;
        return true;
    }
    else if (name == "origin_y") {
        value = origin.y;
        return true;
    }
    // #106: Check for shader uniform properties
    if (getShaderProperty(name, value)) {
        return true;
    }
    return false;
}

bool UISprite::getProperty(const std::string& name, int& value) const {
    if (name == "sprite_index" || name == "sprite_number") {
        value = sprite_index;
        return true;
    }
    else if (name == "z_index") {
        value = z_index;
        return true;
    }
    return false;
}

bool UISprite::hasProperty(const std::string& name) const {
    // Float properties
    if (name == "x" || name == "y" ||
        name == "scale" || name == "scale_x" || name == "scale_y" ||
        name == "z_index" ||
        name == "rotation" || name == "origin_x" || name == "origin_y") {
        return true;
    }
    // Int properties
    if (name == "sprite_index" || name == "sprite_number") {
        return true;
    }
    // Vector2f properties
    if (name == "origin") {
        return true;
    }
    // #106: Check for shader uniform properties
    if (hasShaderProperty(name)) {
        return true;
    }
    return false;
}
