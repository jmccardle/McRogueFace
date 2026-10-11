#include "UIFrame.h"
#include "PyWrap.h"
#include "UICollection.h"
#include "GameEngine.h"
#include "PyVector.h"
#include "UICaption.h"
#include "UISprite.h"
#include "PyGridData.h"
#include "PySceneObject.h"  // parent= kwarg: Scene parent type
#include "McRFPy_API.h"
#include "PythonObjectCache.h"
#include "PyAlignment.h"
#include "PyShader.h"  // #106: Shader support
#include "PyUniformCollection.h"  // #106: Uniform collection
#include <iostream>  // #106: for shader error output
#include "McRFPy_Doc.h"
// UIDrawable methods now in UIBase.h

UIDrawable* UIFrame::click_at(sf::Vector2f point)
{
    float w = box.getSize().x, h = box.getSize().y;

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
    if (localPoint.x < 0 || localPoint.y < 0 || localPoint.x >= w || localPoint.y >= h) {
        return nullptr;
    }

    // Check children in reverse order (top to bottom, highest z-index first)
    for (auto it = children->rbegin(); it != children->rend(); ++it) {
        auto& child = *it;
        if (!child->visible) continue;

        if (auto target = child->click_at(localPoint)) {
            return target;
        }
    }

    // No child handled it, check if we have a handler
    // #184: Also check for Python subclass (might have on_click method)
    if (click_callable || is_python_subclass) {
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
    UIDrawable::releaseChildPins(children);  // #373
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
    // The cached/clipping texture must match the new size (this ran only for animated
    // w/h before #426, so assigning frame.w left a clipping frame at its old size).
    if (use_render_texture && w > 0 && h > 0) {
        enableRenderTexture(static_cast<unsigned int>(w), static_cast<unsigned int>(h));
    }

    // Notify aligned children to recalculate their positions
    if (children) {
        for (auto& child : *children) {
            if (child->getAlignment() != AlignmentType::NONE) {
                child->applyAlignment();
            }
        }
    }
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

    // Apply opacity (multiply with fill/outline color alpha)
    auto fill_color = box.getFillColor();
    auto outline_color = box.getOutlineColor();
    sf::Uint8 original_fill_alpha = fill_color.a;
    sf::Uint8 original_outline_alpha = outline_color.a;
    fill_color.a = static_cast<sf::Uint8>(original_fill_alpha * opacity);
    outline_color.a = static_cast<sf::Uint8>(original_outline_alpha * opacity);
    box.setFillColor(fill_color);
    box.setOutlineColor(outline_color);

    // #144: Use RenderTexture for clipping OR texture caching OR shaders (#106)
    // clip_children: requires texture for clipping effect (only when has children)
    // cache_subtree: uses texture for performance (always, even without children)
    // shader: requires texture for shader post-processing
    bool use_texture = (clip_children && !children->empty()) || cache_subtree || (shader && shader->shader);

    if (use_texture) {
        // Enable RenderTexture if not already enabled
        if (!use_render_texture) {
            auto size = box.getSize();
            if (size.x > 0 && size.y > 0) {
                enableRenderTexture(static_cast<unsigned int>(size.x),
                                  static_cast<unsigned int>(size.y));
            }
        }

        // Fall back to standard rendering if texture not available (e.g., zero size)
        if (!realizeRenderTexture()) {
            use_texture = false;  // Force standard path for this render call
        }
    }

    if (use_texture) {
        // Update RenderTexture if dirty
        if (use_render_texture && render_dirty) {
            // Clear the RenderTexture
            render_texture->clear(sf::Color::Transparent);

            // Draw the frame box to RenderTexture (without rotation - that's applied to the final sprite)
            box.setPosition(0, 0);  // Render at origin in texture
            box.setOrigin(0, 0);    // No origin offset in texture
            box.setRotation(0);     // No rotation in texture
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

        // Draw the RenderTexture sprite (single blit!)
        if (use_render_texture) {
            // Use `position` instead of box.getPosition() - box was set to (0,0) for texture rendering
            render_sprite.setPosition(offset + position);

            // Apply rotation to the rendered sprite (children rotate with parent)
            render_sprite.setOrigin(origin);
            render_sprite.setRotation(rotation);

            // Apply opacity to render_sprite
            auto sprite_color = render_sprite.getColor();
            sprite_color.a = static_cast<sf::Uint8>(255 * opacity);
            render_sprite.setColor(sprite_color);

            // #106: Apply shader if set
            if (shader && shader->shader) {
                // Apply engine uniforms (time, resolution, mouse, texture)
                sf::Vector2f resolution(render_sprite.getLocalBounds().width,
                                        render_sprite.getLocalBounds().height);
                PyShader::applyEngineUniforms(*shader->shader, resolution);

                // Apply user-defined uniforms
                if (uniforms) {
                    uniforms->applyTo(*shader->shader);
                }

                target.draw(render_sprite, shader->shader.get());
            } else {
                target.draw(render_sprite);
            }
        }
    } else {
        // Standard rendering without caching
        // Restore box position from `position` - may have been set to (0,0) by previous texture render
        box.setPosition(offset + position);
        box.setOrigin(origin);
        box.setRotation(rotation);
        target.draw(box);
        box.setPosition(position);  // Restore to canonical position

        // Sort children by z_index if needed
        if (children_need_sort && !children->empty()) {
            std::sort(children->begin(), children->end(),
                [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                    return a->z_index < b->z_index;
                });
            children_need_sort = false;
        }

        // Render children - note: in non-texture mode, children don't automatically
        // rotate with parent. Use clip_children=True or cache_subtree=True if you need
        // children to rotate with the frame.
        for (auto drawable : *children) {
            drawable->render(offset + position, target);  // Use `position` as source of truth
        }
    }

    // Restore original colors
    fill_color.a = original_fill_alpha;
    outline_color.a = original_outline_alpha;
    box.setFillColor(fill_color);
    box.setOutlineColor(outline_color);
}

PyObject* UIFrame::get_children(PyUIFrameObject* self, void* closure)
{
    return UICollection::pyobject_for(self->data->children_serial, self->data->children,
                                      self->data, {});
}


PyObject* UIFrame::get_float_member(PyUIFrameObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    if (member_ptr != 0 && member_ptr != 1)
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
    auto colorType = &mcrfpydef::PyColorType;

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
    auto member_ptr = reinterpret_cast<intptr_t>(closure);
    sf::Color color;
    if (!PyColor::to_color(value, color)) return -1;  // #450

    if (member_ptr == 0)
    {
        self->data->box.setFillColor(color);
        self->data->markDirty();
    }
    else if (member_ptr == 1)
    {
        self->data->box.setOutlineColor(color);
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
    auto type = &mcrfpydef::PyVectorType;
    auto obj = (PyVectorObject*)type->tp_alloc(type, 0);
    if (obj) {
        auto pos = self->data->box.getPosition();
        obj->data = sf::Vector2f(pos.x, pos.y);
    }
    return (PyObject*)obj;
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

        // Disable texture if no longer needed (and cache_subtree isn't using it)
        if (!new_clip && !self->data->cache_subtree) {
            self->data->disableRenderTexture();
        }

        self->data->markDirty();  // Mark as needing redraw
    }

    return 0;
}

// #144 - cache_subtree property for texture caching
PyObject* UIFrame::get_cache_subtree(PyUIFrameObject* self, void* closure)
{
    return PyBool_FromLong(self->data->cache_subtree);
}

int UIFrame::set_cache_subtree(PyUIFrameObject* self, PyObject* value, void* closure)
{
    if (!PyBool_Check(value)) {
        PyErr_SetString(PyExc_TypeError, "cache_subtree must be a boolean");
        return -1;
    }

    bool new_cache = PyObject_IsTrue(value);
    if (new_cache != self->data->cache_subtree) {
        self->data->cache_subtree = new_cache;

        // Enable or disable the render texture
        if (new_cache) {
            auto size = self->data->box.getSize();
            if (size.x > 0 && size.y > 0) {
                self->data->enableRenderTexture(static_cast<unsigned int>(size.x),
                                                static_cast<unsigned int>(size.y));
            }
        } else if (!self->data->clip_children) {
            // Disable texture if clip_children also doesn't need it
            self->data->disableRenderTexture();
        }

        self->data->markDirty();  // Mark as needing redraw
    }

    return 0;
}

// #106 - Shader POC: shader_enabled property
// Define the PyObjectType alias for the macros
typedef PyUIFrameObject PyObjectType;

// Method definitions
PyMethodDef UIFrame_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}  // Sentinel
};

PyGetSetDef UIFrame::getsetters[] = {
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(x, "X coordinate of the top-left corner (float)."),
     (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(y, "Y coordinate of the top-left corner (float)."),
     (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(w, "Width of the rectangle (float)."),
     (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     MCRF_PROPERTY(h, "Height of the rectangle (float)."),
     (void*)((intptr_t)PyObjectsEnum::UIFRAME << 8 | 3)},
    {"size", (getter)UIDrawable::get_size_vec, (setter)UIDrawable::set_size_vec,
     MCRF_PROPERTY(size, "Size of the rectangle as a Vector (w, h)."),
     (void*)PyObjectsEnum::UIFRAME},
    {"outline", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member,
     MCRF_PROPERTY(outline, "Thickness of the border in pixels (float)."),
     (void*)4},
    {"fill_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member,
     MCRF_PROPERTY(fill_color,
         "Fill color of the rectangle (Color). "
         "Returns a copy; modifying components requires reassignment. "
         "For animation, use 'fill_color.r', 'fill_color.g', etc."
     ), (void*)0},
    {"outline_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member,
     MCRF_PROPERTY(outline_color,
         "Outline color of the rectangle (Color). "
         "Returns a copy; modifying components requires reassignment. "
         "For animation, use 'outline_color.r', 'outline_color.g', etc."
     ), (void*)1},
    {"children", (getter)UIFrame::get_children, NULL,
     MCRF_PROPERTY(children,
         "UICollection of child drawable objects rendered on top of this frame (UICollection, "
         "read-only)."
         MCRF_NOTE(
             "Child positions are frame-local (relative to this Frame's top-left corner). A "
             "Frame has no camera, so it cannot pan its content -- frame-local is effectively "
             "screen space. Contrast with Grid.children, which are positioned in the grid's "
             "pixel-world coordinates and pan/zoom with the grid camera."
         )
     ),
     NULL},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     MCRF_PROPERTY(on_click,
         "Callable executed when object is clicked. "
         "Function receives (pos: Vector, button: MouseButton, action: InputState)."
     ), (void*)PyObjectsEnum::UIFRAME},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     MCRF_PROPERTY(z_index,
         "Z-order for rendering (lower values rendered first). "
         "Automatically triggers scene resort when changed."
     ), (void*)PyObjectsEnum::UIFRAME},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     MCRF_PROPERTY(name, "Name for finding elements (str)."),
     (void*)PyObjectsEnum::UIFRAME},
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     MCRF_PROPERTY(pos, "Position as a Vector (Vector)."),
     (void*)PyObjectsEnum::UIFRAME},
    {"grid_pos", (getter)UIDrawable::get_grid_pos, (setter)UIDrawable::set_grid_pos,
     MCRF_PROPERTY(grid_pos, "Position in grid tile coordinates (Vector). Only meaningful when this element's parent is a Grid."),
     (void*)PyObjectsEnum::UIFRAME},
    {"grid_size", (getter)UIDrawable::get_grid_size, (setter)UIDrawable::set_grid_size,
     MCRF_PROPERTY(grid_size, "Size in grid tile coordinates (Vector). Only meaningful when this element's parent is a Grid."),
     (void*)PyObjectsEnum::UIFRAME},
    {"clip_children", (getter)UIFrame::get_clip_children, (setter)UIFrame::set_clip_children,
     MCRF_PROPERTY(clip_children, "Whether to clip child elements to the frame's bounds (bool). Enables render-texture mode when True."),
     NULL},
    {"cache_subtree", (getter)UIFrame::get_cache_subtree, (setter)UIFrame::set_cache_subtree,
     MCRF_PROPERTY(cache_subtree, "Cache the frame and all children to a render texture for performance (bool). Useful for complex static subtrees."),
     NULL},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIFRAME),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UIFRAME),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UIFRAME),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UIFRAME),
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
            box.getSize().x << ", h=" << box.getSize().y << ", " <<
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
    // Initialize children first. A re-run __init__ replaces the vector, so the cached
    // `children` wrapper (which views the old vector) must stop answering for it (#430).
    if (self->data->children_serial != 0) {
        mcrf::unregister_wrapper(self->data->children_serial);
        self->data->children_serial = 0;
    }
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
    int cache_subtree = 0;  // #144: texture caching
    PyObject* align_obj = nullptr;  // Alignment enum or None
    float margin = 0.0f;
    float horiz_margin = -1.0f;
    float vert_margin = -1.0f;
    PyObject* parent_obj = nullptr;  // Auto-attach parent (Frame, Scene, or Grid)

    // Keywords list matches the new spec: positional args first, then all keyword args
    static const char* kwlist[] = {
        "pos", "size",  // Positional args (as per spec)
        // Keyword-only args
        "fill_color", "outline_color", "outline", "children", "on_click",
        "visible", "opacity", "z_index", "name", "x", "y", "w", "h", "clip_children", "cache_subtree",
        "align", "margin", "horiz_margin", "vert_margin",
        "parent",
        nullptr
    };

    // Parse arguments with | for optional positional args
    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOOfOOifizffffiiOfffO", const_cast<char**>(kwlist),
                                     &pos_obj, &size_obj,  // Positional
                                     &fill_color, &outline_color, &outline, &children_arg, &click_handler,
                                     &visible, &opacity, &z_index, &name, &x, &y, &w, &h, &clip_children, &cache_subtree,
                                     &align_obj, &margin, &horiz_margin, &vert_margin,
                                     &parent_obj)) {
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
        sf::Color color;
        if (!PyColor::to_color(fill_color, color)) return -1;  // #450
        self->data->box.setFillColor(color);
    } else {
        self->data->box.setFillColor(sf::Color(0, 0, 0, 128));  // Default: semi-transparent black
    }
    
    // Handle outline_color
    if (outline_color && outline_color != Py_None) {
        sf::Color color;
        if (!PyColor::to_color(outline_color, color)) return -1;  // #450
        self->data->box.setOutlineColor(color);
    } else {
        self->data->box.setOutlineColor(sf::Color(255, 255, 255, 255));  // Default: white
    }
    
    // Set other properties
    self->data->visible = visible;
    self->data->opacity = opacity;
    self->data->z_index = z_index;
    self->data->clip_children = clip_children;
    self->data->cache_subtree = cache_subtree;  // #144: texture caching

    // #144: Enable render texture if cache_subtree requested
    if (cache_subtree && w > 0 && h > 0) {
        self->data->enableRenderTexture(static_cast<unsigned int>(w), static_cast<unsigned int>(h));
    }

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
    
    // Process children argument if provided. #442: through children.extend(), the
    // same path as frame.children.extend(): every child is type- and cycle-checked
    // before any is added, and each is detached from its old parent first.
    if (children_arg && children_arg != Py_None) {
        PyObject* children = PyObject_GetAttrString((PyObject*)self, "children");
        if (!children) return -1;
        PyObject* result = PyObject_CallMethod(children, "extend", "O", children_arg);
        Py_DECREF(children);
        if (!result) return -1;
        Py_DECREF(result);
    }
    
    // Process click handler if provided
    if (click_handler && click_handler != Py_None) {
        if (!PyCallable_Check(click_handler)) {
            PyErr_SetString(PyExc_TypeError, "click must be callable");
            return -1;
        }
        self->data->click_register(click_handler);
    }
    
    if (mcrf::register_wrapper(self->data->serial_number, (PyObject*)self) < 0) return -1;

    // #184: Check if this is a Python subclass (for callback method support)
    self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUIFrameType;

    // Auto-attach to parent's children collection if parent= was supplied
    UIDRAWABLE_ATTACH_TO_PARENT(parent_obj, self);

    return 0;
}

// Animation property system implementation. The shared names (x, y, pos, w, h, size,
// rotation, origin, opacity, z_index) are handled by UIDrawable (#426).
bool UIFrame::setProperty(const std::string& name, float value) {
    if (name == "outline") {
        box.setOutlineThickness(value);
        markDirty();
        return true;
    }
    int channel;
    if (colorChannelName(name, "fill_color", channel)) {
        auto color = box.getFillColor();
        colorChannel(color, channel) = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        box.setFillColor(color);
        markDirty();
        return true;
    }
    if (colorChannelName(name, "outline_color", channel)) {
        auto color = box.getOutlineColor();
        colorChannel(color, channel) = static_cast<sf::Uint8>(std::clamp(value, 0.0f, 255.0f));
        box.setOutlineColor(color);
        markDirty();
        return true;
    }
    // #106: Check for shader uniform properties
    if (setShaderProperty(name, value)) {
        return true;
    }
    return UIDrawable::setProperty(name, value);
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
    return UIDrawable::setProperty(name, value);
}

bool UIFrame::setProperty(const std::string& name, const sf::Vector2f& value) {
    return UIDrawable::setProperty(name, value);
}

bool UIFrame::getProperty(const std::string& name, float& value) const {
    if (name == "outline") {
        value = box.getOutlineThickness();
        return true;
    }
    int channel;
    if (colorChannelName(name, "fill_color", channel)) {
        auto color = box.getFillColor();
        value = colorChannel(color, channel);
        return true;
    }
    if (colorChannelName(name, "outline_color", channel)) {
        auto color = box.getOutlineColor();
        value = colorChannel(color, channel);
        return true;
    }
    // #106: Check for shader uniform properties
    if (getShaderProperty(name, value)) {
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UIFrame::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = box.getFillColor();
        return true;
    } else if (name == "outline_color") {
        value = box.getOutlineColor();
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UIFrame::getProperty(const std::string& name, sf::Vector2f& value) const {
    return UIDrawable::getProperty(name, value);
}

bool UIFrame::hasProperty(const std::string& name) const {
    int channel;
    if (name == "outline" || name == "fill_color" || name == "outline_color" ||
        colorChannelName(name, "fill_color", channel) || colorChannelName(name, "outline_color", channel)) {
        return true;
    }
    // #106: Check for shader uniform properties
    if (hasShaderProperty(name)) {
        return true;
    }
    return UIDrawable::hasProperty(name);
}

// #441: a Frame also speaks for what its children own.
int UIFrame::traverseOwned(visitproc visit, void* arg)
{
    MCRF_VISIT(UIDrawable::traverseOwned(visit, arg));
    return traverseChildren(children, this, nullptr, visit, arg);
}

void UIFrame::clearOwned()
{
    UIDrawable::clearOwned();
    clearChildren(children, this, nullptr);
}
