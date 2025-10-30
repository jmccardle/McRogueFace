#include "UIFrame.h"
#include "UICollection.h"
#include "GameEngine.h"
#include "PyVector.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
// UIDrawable methods now in UIBase.h

UIDrawable* UIFrame::click_at(sf::Vector2f point)
{
    // Check bounds first (optimization)
    float x = position.x, y = position.y, w = box.getSize().x, h = box.getSize().y;
    if (point.x < x || point.y < y || point.x >= x+w || point.y >= y+h) {
        return nullptr;
    }
    
    // Transform to local coordinates for children
    sf::Vector2f localPoint = point - position;
    
    // Check children in reverse order (top to bottom, highest z-index first)
    for (auto it = children->rbegin(); it != children->rend(); ++it) {
        auto& child = *it;
        if (!child->visible) continue;
        
        if (auto target = child->click_at(localPoint)) {
            return target;
        }
    }
    
    // No child handled it, check if we have a handler
    if (click_callable) {
        return this;
    }
    
    return nullptr;
}

UIFrame::UIFrame()
: outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    position = sf::Vector2f(0, 0);  // Set base class position
    box.setPosition(position);      // Sync box position
    box.setSize(sf::Vector2f(0, 0));
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h)
: outline(0)
{
    position = sf::Vector2f(_x, _y);  // Set base class position
    box.setPosition(position);        // Sync box position
    box.setSize(sf::Vector2f(_w, _h));
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}

UIFrame::~UIFrame()
{
    children.reset();
}

PyObjectsEnum UIFrame::derived_type()
{
    return PyObjectsEnum::UIFRAME;
}

// Phase 1 implementations
sf::FloatRect UIFrame::get_bounds() const
{
    auto size = box.getSize();
    return sf::FloatRect(position.x, position.y, size.x, size.y);
}

void UIFrame::move(float dx, float dy)
{
    position.x += dx;
    position.y += dy;
    box.setPosition(position);  // Keep box in sync
}

void UIFrame::resize(float w, float h)
{
    box.setSize(sf::Vector2f(w, h));
}

void UIFrame::onPositionChanged()
{
    // Sync box position with base class position
    box.setPosition(position);
}

void UIFrame::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    // Check visibility
    if (!visible) return;
    
    // TODO: Apply opacity when SFML supports it on shapes
    
    // Check if we need to use RenderTexture for clipping
    if (clip_children && !children->empty()) {
        // Enable RenderTexture if not already enabled
        if (!use_render_texture) {
            auto size = box.getSize();
            enableRenderTexture(static_cast<unsigned int>(size.x), 
                              static_cast<unsigned int>(size.y));
        }
        
        // Update RenderTexture if dirty
        if (use_render_texture && render_dirty) {
            // Clear the RenderTexture
            render_texture->clear(sf::Color::Transparent);
            
            // Draw the frame box to RenderTexture
            box.setPosition(0, 0);  // Render at origin in texture
            render_texture->draw(box);
            
            // Sort children by z_index if needed
            if (children_need_sort && !children->empty()) {
                std::sort(children->begin(), children->end(),
                    [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                        return a->z_index < b->z_index;
                    });
                children_need_sort = false;
            }
            
            // Render children to RenderTexture at local coordinates
            for (auto drawable : *children) {
                drawable->render(sf::Vector2f(0, 0), *render_texture);
            }
            
            // Finalize the RenderTexture
            render_texture->display();
            
            // Update sprite
            render_sprite.setTexture(render_texture->getTexture());
            
            render_dirty = false;
        }
        
        // Draw the RenderTexture sprite
        if (use_render_texture) {
            render_sprite.setPosition(offset + box.getPosition());
            target.draw(render_sprite);
        }
    } else {
        // Standard rendering without clipping
        box.move(offset);
        target.draw(box);
        box.move(-offset);

        // Sort children by z_index if needed
        if (children_need_sort && !children->empty()) {
            std::sort(children->begin(), children->end(),
                [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                    return a->z_index < b->z_index;
                });
            children_need_sort = false;
        }

        for (auto drawable : *children) {
            drawable->render(offset + box.getPosition(), target);
        }
    }
}

PyObject* UIFrame::get_children(PyUIFrameObject* self, void* closure)
{
    // create PyUICollection instance pointing to self->data->children
    //PyUICollectionObject* o = (PyUICollectionObject*)mcrfpydef::PyUICollectionType.tp_alloc(&mcrfpydef::PyUICollectionType, 0);
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UICollection");
    auto o = (PyUICollectionObject*)type->tp_alloc(type, 0);
    if (o)
        o->data = self->data->children;
    return (PyObject*)o;
}


PyObject* UIFrame::get_float_member(PyUIFrameObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1)
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2)
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3)
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4)
        return PyFloat_FromDouble(self->data->box.getOutlineThickness());
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIFrame::set_float_member(PyUIFrameObject* self, PyObject* value, void* closure)
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
        PyErr_SetString(PyExc_TypeError, "Value must be a number (int or float)");
        return -1;
    }
    if (member_ptr == 0) { //x
        self->data->box.setPosition(val, self->data->box.getPosition().y);
        self->data->markDirty();
    }
    else if (member_ptr == 1) { //y
        self->data->box.setPosition(self->data->box.getPosition().x, val);
        self->data->markDirty();
    }
    else if (member_ptr == 2) { //w
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
        if (self->data->use_render_texture) {
            // Need to recreate RenderTexture with new size
            self->data->enableRenderTexture(static_cast<unsigned int>(self->data->box.getSize().x), 
                                           static_cast<unsigned int>(self->data->box.getSize().y));
        }
        self->data->markDirty();
    }
    else if (member_ptr == 3) { //h
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
        if (self->data->use_render_texture) {
            // Need to recreate RenderTexture with new size
            self->data->enableRenderTexture(static_cast<unsigned int>(self->data->box.getSize().x), 
                                           static_cast<unsigned int>(self->data->box.getSize().y));
        }
        self->data->markDirty();
    }
    else if (member_ptr == 4) { //outline
        self->data->box.setOutlineThickness(val);
        self->data->markDirty();
    }
    return 0;
}

PyObject* UIFrame::get_color_member(PyUIFrameObject* self, void* closure)
{
    // validate closure (should be impossible to be wrong, but it's thorough)
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr != 0 && member_ptr != 1)
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
    //PyTypeObject* colorType = &PyColorType;
    auto colorType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    PyObject* pyColor = colorType->tp_alloc(colorType, 0);
    if (pyColor == NULL)
    {
        std::cout << "failure to allocate mcrfpy.Color / PyColorType" << std::endl;
        return NULL;
    }
    PyColorObject* pyColorObj = reinterpret_cast<PyColorObject*>(pyColor);

    // fetch correct member data
    sf::Color color;
    if (member_ptr == 0)
    {
        color = self->data->box.getFillColor();
        //return Py_BuildValue("(iii)", color.r, color.g, color.b);
    }
    else if (member_ptr == 1)
    {
        color = self->data->box.getOutlineColor();
        //return Py_BuildValue("(iii)", color.r, color.g, color.b);
    }
    
    return PyColor(color).pyObject();
}

int UIFrame::set_color_member(PyUIFrameObject* self, PyObject* value, void* closure)
{
    //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
    auto member_ptr = reinterpret_cast<long>(closure);
    int r, g, b, a;
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color")))
    {
        sf::Color c = ((PyColorObject*)value)->data;
        r = c.r; g = c.g; b = c.b; a = c.a;
    }
    else if (!PyTuple_Check(value) || PyTuple_Size(value) < 3 || PyTuple_Size(value) > 4)
    {
        // reject non-Color, non-tuple value
        PyErr_SetString(PyExc_TypeError, "Value must be a tuple of 3 or 4 integers or an mcrfpy.Color object.");
        return -1;
    }
    else // get value from tuples
    {
        r = PyLong_AsLong(PyTuple_GetItem(value, 0));
        g = PyLong_AsLong(PyTuple_GetItem(value, 1));
        b = PyLong_AsLong(PyTuple_GetItem(value, 2));
        a = 255;

        if (PyTuple_Size(value) == 4)
        {
            a = PyLong_AsLong(PyTuple_GetItem(value, 3));
        }
    }

    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255)
    {
        PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255.");
        return -1;
    }

    if (member_ptr == 0)
    {
        self->data->box.setFillColor(sf::Color(r, g, b, a));
        self->data->markDirty();
    }
    else if (member_ptr == 1)
    {
        self->data->box.setOutlineColor(sf::Color(r, g, b, a));
        self->data->markDirty();
    }
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return -1;
    }

    return 0;
}

PyObject* UIFrame::get_pos(PyUIFrameObject* self, void* closure)
{
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        auto pos = self->data->box.getPosition();
        obj->data = sf::Vector2f(pos.x, pos.y);
    }
    return (PyObject*)obj;
}

int UIFrame::set_pos(PyUIFrameObject* self, PyObject* value, void* closure)
{
    PyVectorObject* vec = PyVector::from_arg(value);
    if (!vec) {
        PyErr_SetString(PyExc_TypeError, "pos must be a Vector or convertible to Vector");
        return -1;
    }
    self->data->box.setPosition(vec->data);
    self->data->markDirty();
    return 0;
}

PyObject* UIFrame::get_clip_children(PyUIFrameObject* self, void* closure)
{
    return PyBool_FromLong(self->data->clip_children);
}

int UIFrame::set_clip_children(PyUIFrameObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "clip_children must be a boolean");
        return -1;
    }
    
    bool new_clip = PyObject_IsTrue(value);
    if (new_clip != self->data->clip_children) {
        self->data->clip_children = new_clip;
        self->data->markDirty();  // Mark as needing redraw
    }
    
    return 0;
}

// Define the PyObjectType alias for the macros
typedef PyUIFrameObject PyObjectType;

// Method definitions
PyMethodDef UIFrame_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}  // Sentinel
};

PyGetSetDef UIFrame::getsetters[] = {
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "X coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "Y coordinate of top-left corner", (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "width of the rectangle", (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member, "height of the rectangle", (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 3)},
    {"outline", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "Thickness of the border",   (void*)4},
    {"fill_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member, "Fill color of the rectangle", (void*)0},
    {"outline_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member, "Outline color of the rectangle", (void*)1},
    {"children", (getter)UIFrame::get_children, NULL, "UICollection of objects on top of this one", NULL},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(click,
         "Callable executed when object is clicked. "
         "Function receives (x, y) coordinates of click."
     ), (void*)PyObjectsEnum::UIFRAME},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UIFRAME},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name, "Name for finding elements", (void*)PyObjectsEnum::UIFRAME},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos, "Position as a Vector", (void*)PyObjectsEnum::UIFRAME},
    {"clip_children", (getter)UIFrame::get_clip_children, (setter)UIFrame::set_clip_children, "Whether to clip children to frame bounds", NULL},
    UIDRAWABLE_GETSETTERS,
    {NULL}
};

PyObject* UIFrame::repr(PyUIFrameObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Frame (invalid internal object)>";
    else {
        auto box = self->data->box;
        auto fc = box.getFillColor();
        auto oc = box.getOutlineColor();
        ss << "<Frame (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", w=" << 
            box.getSize().x << ", w=" << box.getSize().y << ", " <<
            "outline=" << box.getOutlineThickness() << ", " << 
            "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", " << (int)fc.b << ", " << (int)fc.a <<"), " <<
            "outline_color=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
            self->data->children->size() << " child objects" <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIFrame::init(PyUIFrameObject* self, PyObject* args, PyObject* kwds)
{
    // Initialize children first
    self->data->children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    
    // Initialize weak reference list
    self->weakreflist = NULL;
    
    // Define all parameters with defaults
    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;
    PyObject* fill_color = nullptr;
    PyObject* outline_color = nullptr;
    float outline = 0.0f;
    PyObject* children_arg = nullptr;
    PyObject* click_handler = nullptr;
    int visible = 1;
    float opacity = 1.0f;
    int z_index = 0;
    const char* name = nullptr;
    float x = 0.0f, y = 0.0f, w = 0.0f, h = 0.0f;
    int clip_children = 0;
    
    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "pos", "size",  // Positional args (as per spec)
        // Keyword-only args
        "fill_color", "outline_color", "outline", "children", "click",
        "visible", "opacity", "z_index", "name", "x", "y", "w", "h", "clip_children",
        nullptr
    };
    
    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOfOOifizffffi", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj,  // Positional
                                     &fill_color, &outline_color, &outline, &children_arg, &click_handler,
                                     &visible, &opacity, &z_index, &name, &x, &y, &w, &h, &clip_children)) {
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
    // If no pos_obj but x/y keywords were provided, they're already in x, y variables
    
    // Handle size argument (can be tuple or use w/h keywords)
    if (size_obj) {
        if (PyTuple_Check(size_obj) && PyTuple_Size(size_obj) == 2) {
            PyObject* w_val = PyTuple_GetItem(size_obj, 0);
            PyObject* h_val = PyTuple_GetItem(size_obj, 1);
            if ((PyFloat_Check(w_val) || PyLong_Check(w_val)) &&
                (PyFloat_Check(h_val) || PyLong_Check(h_val))) {
                w = PyFloat_Check(w_val) ? PyFloat_AsDouble(w_val) : PyLong_AsLong(w_val);
                h = PyFloat_Check(h_val) ? PyFloat_AsDouble(h_val) : PyLong_AsLong(h_val);
            } else {
                PyErr_SetString(PyExc_TypeError, "size tuple must contain numbers");
                return -1;
            }
        } else {
            PyErr_SetString(PyExc_TypeError, "size must be a tuple (w, h)");
            return -1;
        }
    }
    // If no size_obj but w/h keywords were provided, they're already in w, h variables

    // Set the position and size
    self->data->position = sf::Vector2f(x, y);
    self->data->box.setPosition(self->data->position);
    self->data->box.setSize(sf::Vector2f(w, h));
    self->data->box.setOutlineThickness(outline);
    
    // Handle fill_color
    if (fill_color && fill_color != Py_None) {
        PyColorObject* color_obj = PyColor::from_arg(fill_color);
        if (!color_obj) {
            PyErr_SetString(PyExc_TypeError, "fill_color must be a Color or color tuple");
            return -1;
        }
        self->data->box.setFillColor(color_obj->data);
        Py_DECREF(color_obj);
    } else {
        self->data->box.setFillColor(sf::Color(0, 0, 0, 128));  // Default: semi-transparent black
    }
    
    // Handle outline_color
    if (outline_color && outline_color != Py_None) {
        PyColorObject* color_obj = PyColor::from_arg(outline_color);
        if (!color_obj) {
            PyErr_SetString(PyExc_TypeError, "outline_color must be a Color or color tuple");
            return -1;
        }
        self->data->box.setOutlineColor(color_obj->data);
        Py_DECREF(color_obj);
    } else {
        self->data->box.setOutlineColor(sf::Color(255, 255, 255, 255));  // Default: white
    }
    
    // Set other properties
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    self->data->clip_children = clip_children;
    if (name) {
        self->data->name = std::string(name);
    }
    
    // Handle click handler
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }
    
    // Process children argument if provided
    if (children_arg && children_arg != Py_None) {
        if (!PySequence_Check(children_arg)) {
            PyErr_SetString(PyExc_TypeError, "children must be a sequence");
            return -1;
        }
        
        Py_ssize_t len = PySequence_Length(children_arg);
        for (Py_ssize_t i = 0; i < len; i++) {
            PyObject* child = PySequence_GetItem(children_arg, i);
            if (!child) return -1;
            
            // Check if it's a UIDrawable (Frame, Caption, Sprite, or Grid)
            PyObject* frame_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Frame");
            PyObject* caption_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Caption");
            PyObject* sprite_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Sprite");
            PyObject* grid_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Grid");
            
            if (!PyObject_IsInstance(child, frame_type) &&
                !PyObject_IsInstance(child, caption_type) &&
                !PyObject_IsInstance(child, sprite_type) &&
                !PyObject_IsInstance(child, grid_type)) {
                Py_DECREF(child);
                PyErr_SetString(PyExc_TypeError, "children must contain only Frame, Caption, Sprite, or Grid objects");
                return -1;
            }
            
            // Get the shared_ptr and add to children
            std::shared_ptr<UIDrawable> drawable = nullptr;
            if (PyObject_IsInstance(child, frame_type)) {
                drawable = ((PyUIFrameObject*)child)->data;
            } else if (PyObject_IsInstance(child, caption_type)) {
                drawable = ((PyUICaptionObject*)child)->data;
            } else if (PyObject_IsInstance(child, sprite_type)) {
                drawable = ((PyUISpriteObject*)child)->data;
            } else if (PyObject_IsInstance(child, grid_type)) {
                drawable = ((PyUIGridObject*)child)->data;
            }
            
            // Clean up type references
            Py_DECREF(frame_type);
            Py_DECREF(caption_type);
            Py_DECREF(sprite_type);
            Py_DECREF(grid_type);
            
            if (drawable) {
                self->data->children->push_back(drawable);
                self->data->children_need_sort = true;
            }
            
            Py_DECREF(child);
        }
    }
    
    // Process click handler if provided
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }
    
    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);  // Cache owns the reference now
        }
    }
    
    return 0;
}

// Animation property system implementation
bool UIFrame::setProperty(const std::string& name, float value) {
    if (name == "x") {
        position.x = value;
        box.setPosition(position);  // Keep box in sync
        markDirty();
        return true;
    } else if (name == "y") {
        position.y = value;
        box.setPosition(position);  // Keep box in sync
        markDirty();
        return true;
    } else if (name == "w") {
        box.setSize(sf::Vector2f(value, box.getSize().y));
        if (use_render_texture) {
            // Need to recreate RenderTexture with new size
            enableRenderTexture(static_cast<unsigned int>(box.getSize().x), 
                              static_cast<unsigned int>(box.getSize().y));
        }
        markDirty();
        return true;
    } else if (name == "h") {
        box.setSize(sf::Vector2f(box.getSize().x, value));
        if (use_render_texture) {
            // Need to recreate RenderTexture with new size
            enableRenderTexture(static_cast<unsigned int>(box.getSize().x), 
                              static_cast<unsigned int>(box.getSize().y));
        }
        markDirty();
        return true;
    } else if (name == "outline") {
        box.setOutlineThickness(value);
        markDirty();
        return true;
    } else if (name == "fill_color.r") {
        auto color = box.getFillColor();
        color.r = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        markDirty();
        return true;
    } else if (name == "fill_color.g") {
        auto color = box.getFillColor();
        color.g = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        markDirty();
        return true;
    } else if (name == "fill_color.b") {
        auto color = box.getFillColor();
        color.b = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        markDirty();
        return true;
    } else if (name == "fill_color.a") {
        auto color = box.getFillColor();
        color.a = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        markDirty();
        return true;
    } else if (name == "outline_color.r") {
        auto color = box.getOutlineColor();
        color.r = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        markDirty();
        return true;
    } else if (name == "outline_color.g") {
        auto color = box.getOutlineColor();
        color.g = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        markDirty();
        return true;
    } else if (name == "outline_color.b") {
        auto color = box.getOutlineColor();
        color.b = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        markDirty();
        return true;
    } else if (name == "outline_color.a") {
        auto color = box.getOutlineColor();
        color.a = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        markDirty();
        return true;
    }
    return false;
}

bool UIFrame::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        box.setFillColor(value);
        markDirty();
        return true;
    } else if (name == "outline_color") {
        box.setOutlineColor(value);
        markDirty();
        return true;
    }
    return false;
}

bool UIFrame::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "position") {
        position = value;
        box.setPosition(position);  // Keep box in sync
        markDirty();
        return true;
    } else if (name == "size") {
        box.setSize(value);
        if (use_render_texture) {
            // Need to recreate RenderTexture with new size
            enableRenderTexture(static_cast<unsigned int>(value.x), 
                              static_cast<unsigned int>(value.y));
        }
        markDirty();
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = position.x;
        return true;
    } else if (name == "y") {
        value = position.y;
        return true;
    } else if (name == "w") {
        value = box.getSize().x;
        return true;
    } else if (name == "h") {
        value = box.getSize().y;
        return true;
    } else if (name == "outline") {
        value = box.getOutlineThickness();
        return true;
    } else if (name == "fill_color.r") {
        value = box.getFillColor().r;
        return true;
    } else if (name == "fill_color.g") {
        value = box.getFillColor().g;
        return true;
    } else if (name == "fill_color.b") {
        value = box.getFillColor().b;
        return true;
    } else if (name == "fill_color.a") {
        value = box.getFillColor().a;
        return true;
    } else if (name == "outline_color.r") {
        value = box.getOutlineColor().r;
        return true;
    } else if (name == "outline_color.g") {
        value = box.getOutlineColor().g;
        return true;
    } else if (name == "outline_color.b") {
        value = box.getOutlineColor().b;
        return true;
    } else if (name == "outline_color.a") {
        value = box.getOutlineColor().a;
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = box.getFillColor();
        return true;
    } else if (name == "outline_color") {
        value = box.getOutlineColor();
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "position") {
        value = position;
        return true;
    } else if (name == "size") {
        value = box.getSize();
        return true;
    }
    return false;
}
