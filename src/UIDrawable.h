#pragma once
#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "IndexTexture.h"
#include "Resources.h"
#include <cstring>
#include <list>
#include <memory>

#include "PyCallable.h"
#include "PyTexture.h"
#include "PyColor.h"
#include "PyWrap.h"
#include "PyVector.h"
#include "PyFont.h"
#include "PyAlignment.h"

#include "Resources.h"
#include "UIBase.h"

// Forward declarations for shader support (#106)
class UniformCollection;
// PyShaderObject is a typedef, forward declare as a struct with explicit typedef
typedef struct PyShaderObjectStruct PyShaderObject;

class UIFrame; class UICaption; class UISprite; class UIEntity; class GridData; class Scene;

enum PyObjectsEnum : int
{
    UIFRAME = 1,
    UICAPTION,
    UISPRITE,
    // #361: no UIGRID. GridData is not a UIDrawable, so it has no derived_type()
    // and can never appear in a scene graph. Every grid node IS a UIGRIDVIEW.
    UILINE,
    UICIRCLE,
    UIARC,
    UIVIEWPORT3D,
    UIGRIDVIEW  // #252: rendering view for GridData
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
    std::unique_ptr<PyHoverCallable> on_enter_callable;   // #140, #230 - position-only
    std::unique_ptr<PyHoverCallable> on_exit_callable;    // #140, #230 - position-only
    std::unique_ptr<PyHoverCallable> on_move_callable;    // #141, #230 - position-only

    virtual UIDrawable* click_at(sf::Vector2f point) = 0;
    void click_register(PyObject*);
    void click_unregister();

    // #355 - Grid cell input. Defaults are inert: no caller may switch on grid-ness.
    //
    // dispatchCellClick: called by PyScene after click_at() resolved this drawable as
    // the click target. Takes no point: click_at() already resolved the cell in the
    // coordinate space of the hit (parent-local), which PyScene does not have.
    // Returns true if a cell callback consumed the click.
    virtual bool dispatchCellClick(const std::string& button, const std::string& action)
    { (void)button; (void)action; return false; }

    // updateHover: called by PyScene::do_mouse_hover for every drawable, with the
    // mouse position in this drawable's PARENT-local coordinate space (the same
    // convention click_at() uses; at the top level that is global space).
    // hit_allowed is false when an ancestor already determined the mouse cannot be
    // over this subtree -- such a call may only clear hover state, never set it.
    virtual void updateHover(sf::Vector2f point, bool hit_allowed)
    { (void)point; (void)hit_allowed; }

    // asGridData: non-null only for drawables that own or view grid data.
    // (#357 find/findAll and #358 ImGuiSceneExplorer will use this same primitive.)
    virtual GridData* asGridData() { return nullptr; }

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
    static PyObject* get_size_vec(PyObject* self, void* closure);
    static int set_size_vec(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_rotation(PyObject* self, void* closure);
    static int set_rotation(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_origin(PyObject* self, void* closure);
    static int set_origin(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_rotate_with_camera(PyObject* self, void* closure);
    static int set_rotate_with_camera(PyObject* self, PyObject* value, void* closure);

    // #221 - Grid coordinate properties (only valid when the parent is a Grid/UIGridView)
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
    // Only affects children of a Grid (UIGridView); ignored for other parents
    bool rotate_with_camera = false;

    // Parent-child hierarchy (#122)
    std::weak_ptr<UIDrawable> parent;

    // Scene parent tracking (#183): the scene whose children this is, if top-level.
    // The scene itself, not its name (#464): a name can be given to another scene,
    // and the old scene's children must stay with the old scene.
    std::weak_ptr<Scene> parent_scene;

    // Set the parent of this drawable (called by collections when adding)
    void setParent(std::shared_ptr<UIDrawable> new_parent);

    // #442: may `child` become a child of `new_parent`? False, with ValueError set,
    // when `new_parent` is `child` or one of its descendants: the parent chain would
    // loop and every upward walk (markContentDirty, global position, alignment)
    // would recurse forever. Every path that links a child calls this BEFORE it
    // mutates anything; a null parent (scene collection) always may.
    static bool canAdopt(const std::shared_ptr<UIDrawable>& new_parent, const UIDrawable* child);

    // Set the parent scene (called by UICollection when adding to scene)
    void setParentScene(const std::weak_ptr<Scene>& scene);

    // Get the parent drawable (returns nullptr if no parent or expired)
    std::shared_ptr<UIDrawable> getParent() const;

    // Remove this drawable from its current parent's children (or scene)
    void removeFromParent();

    // #373: strong ref to this drawable's Python wrapper, held for exactly as long as
    // the drawable is a member of a children collection (a Frame's, a GridView's, or a
    // Scene's). PythonObjectCache holds only weakrefs, so without this a subclass
    // wrapper that Python stops referencing is collected while C++ still owns the
    // object -- and the next .parent / find() / indexing lookup misses the cache and
    // hands back a freshly allocated BASE-type wrapper, silently dropping the subclass
    // and every attribute the user set on it.
    //
    // Membership is the boundary, exactly as grid membership is for UIEntity (#266).
    // It is represented by the parent link, so the pin is re-evaluated in setParent()
    // and setParentScene() -- the two choke points every collection mutator goes
    // through -- and by pyobject_for() when it makes a wrapper for a contained object.
    // #443: plain wrappers are pinned too. Otherwise a contained object with a live
    // wrapper has two owners (its collection and that wrapper), neither of which can
    // report its callbacks to the cycle collector (#441), so a cycle through it leaks.
    //
    // The pin is a reference cycle (wrapper -> shared_ptr -> drawable -> wrapper) that
    // Python's GC cannot see through the C++ side, so it MUST be released on the way
    // out. Every exit is covered: unlinking calls setParent(nullptr), and an owner
    // destroyed while still holding children releases its children's pins first.
    mcrf::PyIdentityPin py_identity;

    // Acquire or drop py_identity to match the current parent link. Idempotent.
    void updatePyIdentityPin();

    // Unconditionally drop the pin. Called by an owner tearing down its children vector.
    void releasePyIdentity();

    // #373: an owner (Frame, GridView, Scene) destroyed while it still holds children
    // must drop their pins. Nothing calls setParent(nullptr) on that path -- the vector
    // simply dies -- so without this the wrapper <-> drawable cycle would strand the
    // entire subtree in memory. Releasing a child's pin cannot free it here: the vector
    // still holds a strong ref. It dies with the vector, and its own destructor then
    // releases the next level down.
    static void releaseChildPins(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children);

    // #441: report to / drop for the cycle collector the Python objects this drawable
    // owns: its callbacks, plus whatever its children own. Only called once the caller
    // has established exclusive ownership (mcrf::owns_exclusively, PyWrap.h). Types
    // with more Python state (children, cell callbacks, a cached wrapper) extend these.
    virtual int traverseOwned(visitproc visit, void* arg);
    virtual void clearOwned();

    // tp_traverse / tp_clear for every drawable wrapper type. Templates so use_count()
    // is read on the wrapper's own shared_ptr: converting it to shared_ptr<UIDrawable>
    // would make a temporary copy and count one owner too many.
    template <typename T>
    static int traverseWrapper(PyObject* self, const std::shared_ptr<T>& data,
                               visitproc visit, void* arg) {
        if (!data || !mcrf::owns_exclusively(data.use_count(), data->py_identity.holds(self) ? 1 : 0))
            return 0;
        return data->traverseOwned(visit, arg);
    }
    template <typename T>
    static int clearWrapper(PyObject* self, const std::shared_ptr<T>& data) {
        if (data && mcrf::owns_exclusively(data.use_count(), data->py_identity.holds(self) ? 1 : 0))
            data->clearOwned();
        return 0;
    }

    // A children vector's share, for the Frame / GridView (owner) or Scene (scene) that
    // holds it. A pinned child is reported through its pin (its own wrapper reports what
    // it holds); an unwrapped child that only the vector owns is descended into.
    static int traverseChildren(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children,
                                const UIDrawable* owner, const Scene* scene,
                                visitproc visit, void* arg);
    static void clearChildren(const std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>>& children,
                              const UIDrawable* owner, const Scene* scene);

    // Get the global (screen) position by walking up the parent chain (#102)
    sf::Vector2f get_global_position() const;

    // #369: the single cache-aware C++ -> Python wrapper conversion for drawables.
    // Returns the live wrapper for this drawable if one exists (preserving object
    // identity and any Python subclass), otherwise allocates one and registers it.
    // Returns a new reference, or nullptr with an exception set.
    static PyObject* pyobject_for(std::shared_ptr<UIDrawable> drawable);

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
    
    // #426: the properties drawable types share. Attribute assignment and animation
    // both write them through these setters, so `d.x = v` and `d.animate("x", v, ...)`
    // cannot drift apart.
    void assignPosition(sf::Vector2f p);
    void assignSize(sf::Vector2f s);
    void assignRotation(float degrees);
    void assignOrigin(sf::Vector2f o);
    void assignOpacity(float o);
    void assignZIndex(int z);

    // Which shared groups a type exposes as Python attributes, and so as animation
    // targets. UIDrawable's setProperty/getProperty/hasProperty handle exactly these.
    enum SharedProperty : unsigned {
        SHARED_POSITION = 1u << 0,  // x, y, pos
        SHARED_SIZE     = 1u << 1,  // w, h, size (only where they are writable)
        SHARED_ROTATION = 1u << 2,  // rotation, origin
        SHARED_OPACITY  = 1u << 3,  // opacity
        SHARED_Z_INDEX  = 1u << 4,  // z_index
    };
    virtual unsigned sharedProperties() const {
        return SHARED_POSITION | SHARED_ROTATION | SHARED_OPACITY | SHARED_Z_INDEX;
    }

    // "<color>.r" / ".g" / ".b" / ".a": one channel of a Color attribute, animated as a
    // float. Returns the channel index (0-3) through `channel`.
    static bool colorChannelName(const std::string& name, const char* color, int& channel) {
        const size_t n = std::strlen(color);
        if (name.size() != n + 2 || name.compare(0, n, color) != 0 || name[n] != '.') return false;
        switch (name[n + 1]) {
            case 'r': channel = 0; return true;
            case 'g': channel = 1; return true;
            case 'b': channel = 2; return true;
            case 'a': channel = 3; return true;
        }
        return false;
    }
    static sf::Uint8& colorChannel(sf::Color& c, int channel) {
        return channel == 0 ? c.r : channel == 1 ? c.g : channel == 2 ? c.b : c.a;
    }

    // Animation support. Every animatable name is a readable attribute, animated in that
    // attribute's units and type (#423, #426). A subclass handles its own names and
    // passes the rest to these base versions, which handle the shared ones.
    virtual bool setProperty(const std::string& name, float value);
    virtual bool setProperty(const std::string& name, int value);
    virtual bool setProperty(const std::string& name, const sf::Color& value) { return false; }
    virtual bool setProperty(const std::string& name, const sf::Vector2f& value);
    virtual bool setProperty(const std::string& name, const std::string& value) { return false; }

    virtual bool getProperty(const std::string& name, float& value) const;
    virtual bool getProperty(const std::string& name, int& value) const;
    virtual bool getProperty(const std::string& name, sf::Color& value) const { return false; }
    virtual bool getProperty(const std::string& name, sf::Vector2f& value) const;
    virtual bool getProperty(const std::string& name, std::string& value) const { return false; }

    // Check if a property name is valid for animation on this drawable type
    virtual bool hasProperty(const std::string& name) const;

    // The value a float animation would end at, checked as assigning it is checked
    // (#463): false with a Python error set. Only properties with a range override it.
    virtual bool checkFloatTarget(const std::string& name, float final_value) const { return true; }

    // #106: Shader uniform property helpers for animation support
    // These methods handle "shader.uniform_name" property paths
    bool setShaderProperty(const std::string& name, float value);
    bool getShaderProperty(const std::string& name, float& value) const;
    bool hasShaderProperty(const std::string& name) const;

    // Note: animate_helper is now a free function (UIDrawable_animate_impl) declared in UIBase.h
    // to avoid incomplete type issues with template instantiation.

    // Python object cache support
    uint64_t serial_number = 0;
    // #430: cache key for this drawable's children-collection wrapper (Frame.children,
    // GridView.children). The collection has no C++ object of its own, so its
    // identity lives on the owner.
    uint64_t children_serial = 0;

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
    // #451: enableRenderTexture() records the size; the texture (a GL resource) is created
    // by realizeRenderTexture() when the drawable is first drawn.
    std::unique_ptr<sf::RenderTexture> render_texture;
    sf::Vector2u render_texture_size{0, 0};
    sf::Sprite render_sprite;
    bool use_render_texture = false;
    bool render_dirty = true;
    
    // Enable RenderTexture for this drawable
    void enableRenderTexture(unsigned int width, unsigned int height);
    // Creates the texture enableRenderTexture() asked for, if it doesn't exist yet. False
    // (and render textures off) when it can't be created.
    bool realizeRenderTexture();
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
    std::weak_ptr<Scene> scene;       // #183/#464: the scene (for Scene.children); empty if not scene-level
    PyObject* weakreflist;            // #430: cacheable, so `f.children is f.children`
} PyUICollectionObject;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
    int index;
    int start_size;
} PyUICollectionIterObject;

namespace mcrfpydef {

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
            ptr = ((PyGridDataObject*)self)->data->click_callable->borrow();
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
            target = (((PyGridDataObject*)self)->data.get());
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
