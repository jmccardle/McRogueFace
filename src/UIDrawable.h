#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <list>
#include <memory>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyVector.h"
#include "PyFont.h"
#include "PyAlignment.h"

#include "Resources.h"
#include "UIBase.h"

// Forward declarations for shader support (#106)
class UniformCollection;
// PyShaderObject is a typedef, forward declare as a struct with explicit typedef
typedef struct PyShaderObjectStruct PyShaderObject;

class UIFrame; class UICaption; class UISprite; class UIEntity; class UIGrid;

enum PyObjectsEnum : int
{
    UIFRAME = 1,
    UICAPTION,
    UISPRITE,
    UIGRID,
    UILINE,
    UICIRCLE,
    UIARC
};

class UIDrawable
{
public:
    void render();
    //virtual void render(sf::Vector2f) = 0;
    virtual void render(sf::Vector2f, sf::RenderTarget&) = 0;
    virtual PyObjectsEnum derived_type() = 0;

    // Mouse input handling - callable objects for click, enter, exit, move events
    std::unique_ptr<PyClickCallable> click_callable;
    std::unique_ptr<PyClickCallable> on_enter_callable;   // #140
    std::unique_ptr<PyClickCallable> on_exit_callable;    // #140
    std::unique_ptr<PyClickCallable> on_move_callable;    // #141

    virtual UIDrawable* click_at(sf::Vector2f point) = 0;
    void click_register(PyObject*);
    void click_unregister();

    // #140 - Mouse enter/exit callbacks
    void on_enter_register(PyObject*);
    void on_enter_unregister();
    void on_exit_register(PyObject*);
    void on_exit_unregister();

    // #141 - Mouse move callback
    void on_move_register(PyObject*);
    void on_move_unregister();

    // #140 - Hovered state (set by GameEngine)
    bool hovered = false;

    UIDrawable();
    virtual ~UIDrawable();
    
    // Copy constructor and assignment operator
    UIDrawable(const UIDrawable& other);
    UIDrawable& operator=(const UIDrawable& other);
    
    // Move constructor and assignment operator
    UIDrawable(UIDrawable&& other) noexcept;
    UIDrawable& operator=(UIDrawable&& other) noexcept;

    static PyObject* get_click(PyObject* self, void* closure);
    static int set_click(PyObject* self, PyObject* value, void* closure);
    // #140 - Python API for on_enter/on_exit callbacks
    static PyObject* get_on_enter(PyObject* self, void* closure);
    static int set_on_enter(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_on_exit(PyObject* self, void* closure);
    static int set_on_exit(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_hovered(PyObject* self, void* closure);
    // #141 - Python API for on_move callback
    static PyObject* get_on_move(PyObject* self, void* closure);
    static int set_on_move(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_int(PyObject* self, void* closure);
    static int set_int(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_name(PyObject* self, void* closure);
    static int set_name(PyObject* self, PyObject* value, void* closure);
    
    // Common position getters/setters for Python API
    static PyObject* get_float_member(PyObject* self, void* closure);
    static int set_float_member(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_pos(PyObject* self, void* closure);
    static int set_pos(PyObject* self, PyObject* value, void* closure);

    // Rotation getters/setters for Python API
    static PyObject* get_rotation(PyObject* self, void* closure);
    static int set_rotation(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_origin(PyObject* self, void* closure);
    static int set_origin(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_rotate_with_camera(PyObject* self, void* closure);
    static int set_rotate_with_camera(PyObject* self, PyObject* value, void* closure);

    // #221 - Grid coordinate properties (only valid when parent is UIGrid)
    static PyObject* get_grid_pos(PyObject* self, void* closure);
    static int set_grid_pos(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_grid_size(PyObject* self, void* closure);
    static int set_grid_size(PyObject* self, PyObject* value, void* closure);
    
    // Z-order for rendering (lower values rendered first, higher values on top)
    int z_index = 0;
    
    // Notification for z_index changes
    void notifyZIndexChanged();
    
    // Name for finding elements
    std::string name;

    // Position in pixel coordinates (moved from derived classes)
    sf::Vector2f position;

    // Rotation in degrees (clockwise around origin)
    float rotation = 0.0f;

    // Transform origin point (relative to position, pivot for rotation/scale)
    sf::Vector2f origin;

    // Whether to rotate visually with parent Grid's camera_rotation
    // Only affects children of UIGrid; ignored for other parents
    bool rotate_with_camera = false;

    // Parent-child hierarchy (#122)
    std::weak_ptr<UIDrawable> parent;

    // Scene parent tracking (#183) - name of scene if this is a top-level element
    std::string parent_scene;

    // Set the parent of this drawable (called by collections when adding)
    void setParent(std::shared_ptr<UIDrawable> new_parent);

    // Set the parent scene name (called by UICollection when adding to scene)
    void setParentScene(const std::string& scene_name);

    // Get the parent drawable (returns nullptr if no parent or expired)
    std::shared_ptr<UIDrawable> getParent() const;

    // Remove this drawable from its current parent's children (or scene)
    void removeFromParent();

    // Get the global (screen) position by walking up the parent chain (#102)
    sf::Vector2f get_global_position() const;

    // Python API for parent/global_position
    static PyObject* get_parent(PyObject* self, void* closure);
    static int set_parent(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_global_pos(PyObject* self, void* closure);

    // Python API for hit testing (#138)
    static PyObject* get_bounds_py(PyObject* self, void* closure);
    static PyObject* get_global_bounds_py(PyObject* self, void* closure);

    // Alignment system - position children relative to parent bounds
    AlignmentType align_type = AlignmentType::NONE;
    float align_margin = 0.0f;         // General margin for all edges
    float align_horiz_margin = -1.0f;  // Horizontal margin override (-1 = use align_margin)
    float align_vert_margin = -1.0f;   // Vertical margin override (-1 = use align_margin)

    // Apply alignment: recalculate position from parent bounds
    void applyAlignment();

    // User-callable realignment: reapply alignment to self (useful for responsive layouts)
    void realign();

    // Python API: realign method
    static PyObject* py_realign(PyObject* self, PyObject* args);

    // Setters that trigger realignment
    void setAlignment(AlignmentType align);
    AlignmentType getAlignment() const { return align_type; }

    // Python API for alignment properties
    static PyObject* get_align(PyObject* self, void* closure);
    static int set_align(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_margin(PyObject* self, void* closure);
    static int set_margin(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_horiz_margin(PyObject* self, void* closure);
    static int set_horiz_margin(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_vert_margin(PyObject* self, void* closure);
    static int set_vert_margin(PyObject* self, PyObject* value, void* closure);

    // Validate margin settings (raises ValueError for invalid combinations)
    static bool validateMargins(AlignmentType align, float margin, float horiz_margin, float vert_margin, bool set_error = true);

    // New properties for Phase 1
    bool visible = true;      // #87 - visibility flag
    float opacity = 1.0f;     // #88 - opacity (0.0 = transparent, 1.0 = opaque)
    
    // New virtual methods for Phase 1
    virtual sf::FloatRect get_bounds() const = 0;  // #89 - get bounding box
    virtual void move(float dx, float dy) = 0;     // #98 - move by offset
    virtual void resize(float w, float h) = 0;     // #98 - resize to dimensions

    // Hit testing (#138)
    sf::FloatRect get_global_bounds() const;       // Bounds in screen coordinates
    bool contains_point(float x, float y) const;   // Hit test using global bounds
    
    // Called when position changes to allow derived classes to sync
    virtual void onPositionChanged() {}
    
    // Animation support
    virtual bool setProperty(const std::string& name, float value) { return false; }
    virtual bool setProperty(const std::string& name, int value) { return false; }
    virtual bool setProperty(const std::string& name, const sf::Color& value) { return false; }
    virtual bool setProperty(const std::string& name, const sf::Vector2f& value) { return false; }
    virtual bool setProperty(const std::string& name, const std::string& value) { return false; }
    
    virtual bool getProperty(const std::string& name, float& value) const { return false; }
    virtual bool getProperty(const std::string& name, int& value) const { return false; }
    virtual bool getProperty(const std::string& name, sf::Color& value) const { return false; }
    virtual bool getProperty(const std::string& name, sf::Vector2f& value) const { return false; }
    virtual bool getProperty(const std::string& name, std::string& value) const { return false; }

    // Check if a property name is valid for animation on this drawable type
    virtual bool hasProperty(const std::string& name) const { return false; }

    // #106: Shader uniform property helpers for animation support
    // These methods handle "shader.uniform_name" property paths
    bool setShaderProperty(const std::string& name, float value);
    bool getShaderProperty(const std::string& name, float& value) const;
    bool hasShaderProperty(const std::string& name) const;

    // Note: animate_helper is now a free function (UIDrawable_animate_impl) declared in UIBase.h
    // to avoid incomplete type issues with template instantiation.

    // Python object cache support
    uint64_t serial_number = 0;

    // Python subclass callback support (#184)
    // Enables subclass method overrides like: class MyFrame(Frame): def on_click(self, ...): ...
    bool is_python_subclass = false;

    // Callback method cache - avoids repeated Python lookups
    struct CallbackCache {
        uint32_t generation = 0;          // Class generation when cache was populated
        bool valid = false;               // Whether cache has been populated
        bool has_on_click = false;
        bool has_on_enter = false;
        bool has_on_exit = false;
        bool has_on_move = false;
    };
    CallbackCache callback_cache;

    // Check if callback cache is still valid (compares against class generation)
    bool isCallbackCacheValid(PyObject* type) const;

    // Refresh the callback cache by checking for methods on the Python object
    void refreshCallbackCache(PyObject* pyObj);

    // Get the current callback generation for a type
    static uint32_t getCallbackGeneration(PyObject* type);

    // Increment callback generation for a type (called when on_* attributes change)
    static void incrementCallbackGeneration(PyObject* type);

protected:
    // RenderTexture support (opt-in)
    std::unique_ptr<sf::RenderTexture> render_texture;
    sf::Sprite render_sprite;
    bool use_render_texture = false;
    bool render_dirty = true;
    
    // Enable RenderTexture for this drawable
    void enableRenderTexture(unsigned int width, unsigned int height);
    void updateRenderTexture();

    // Disable RenderTexture for this drawable (public for property setters)
public:
    void disableRenderTexture();

    // Shader support (#106)
    std::shared_ptr<PyShaderObject> shader;
    std::unique_ptr<UniformCollection> uniforms;
    bool shader_dynamic = false;  // True if shader uses time-varying effects

    // Mark this drawable as having dynamic shader effects
    // Propagates up to parent to invalidate caches
    void markShaderDynamic();

    // Python API for shader properties
    static PyObject* get_shader(PyObject* self, void* closure);
    static int set_shader(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_uniforms(PyObject* self, void* closure);

protected:

public:
    // #144: Dirty flag system - content vs composite
    // content_dirty: THIS drawable's texture needs rebuild (color/text/sprite changed)
    // composite_dirty: Parent needs to re-composite children (position changed)

    // Mark content as dirty - texture needs rebuild, propagates up
    void markDirty();  // Legacy method - calls markContentDirty
    void markContentDirty();

    // Mark only composite as dirty - position changed, texture still valid
    // Only notifies parent, doesn't set own render_dirty
    void markCompositeDirty();

    // Check if this drawable needs redraw
    bool isDirty() const { return render_dirty; }
    bool isCompositeDirty() const { return composite_dirty; }

    // Clear dirty flags (called after rendering)
    void clearDirty() { render_dirty = false; composite_dirty = false; }

protected:
    bool composite_dirty = true;  // #144: Needs re-composite (child positions changed)
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
    std::weak_ptr<UIDrawable> owner;  // #122: Parent drawable (for Frame.children, Grid.children)
    std::string scene_name;           // #183: Scene name (for Scene.children) - empty if not scene-level
} PyUICollectionObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
    int index;
    int start_size;
} PyUICollectionIterObject;

namespace mcrfpydef {
    // DEPRECATED: RET_PY_INSTANCE macro has been replaced with template functions in PyObjectUtils.h
    // The macro was difficult to debug and used static type references that could cause initialization order issues.
    // Use PyObjectUtils::convertDrawableToPython() or PyObjectUtils::createPyObject<T>() instead.

//TODO: add this method to class scope; move implementation to .cpp file
/*
static PyObject* PyUIDrawable_get_click(PyObject* self, void* closure) {
    PyObjectsEnum objtype = static_cast<PyObjectsEnum>(reinterpret_cast<long>(closure)); // trust me bro, it's an Enum
    PyObject* ptr;

    switch (objtype)
    {
        case PyObjectsEnum::UIFRAME:
            ptr = ((PyUIFrameObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UICAPTION:
            ptr = ((PyUICaptionObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UISPRITE:
            ptr = ((PyUISpriteObject*)self)->data->click_callable->borrow();
            break;
        case PyObjectsEnum::UIGRID:
            ptr = ((PyUIGridObject*)self)->data->click_callable->borrow();
            break;
        default:
            PyErr_SetString(PyExc_TypeError, "no idea how you did that; invalid UIDrawable derived instance for _get_click");
            return NULL;
    }
    if (ptr && ptr != Py_None)
        return ptr;
    else
        return Py_None;
}*/

//TODO: add this method to class scope; move implementation to .cpp file
/*
static int PyUIDrawable_set_click(PyObject* self, PyObject* value, void* closure) {
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
*/
}
