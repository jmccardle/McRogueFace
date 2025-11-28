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

#include "Resources.h"
#include "UIBase.h"
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

    // Mouse input handling - callable object, methods to find event's destination
    std::unique_ptr<PyClickCallable> click_callable;
    virtual UIDrawable* click_at(sf::Vector2f point) = 0;
    void click_register(PyObject*);
    void click_unregister();

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
    static PyObject* get_int(PyObject* self, void* closure);
    static int set_int(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_name(PyObject* self, void* closure);
    static int set_name(PyObject* self, PyObject* value, void* closure);
    
    // Common position getters/setters for Python API
    static PyObject* get_float_member(PyObject* self, void* closure);
    static int set_float_member(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_pos(PyObject* self, void* closure);
    static int set_pos(PyObject* self, PyObject* value, void* closure);
    
    // Z-order for rendering (lower values rendered first, higher values on top)
    int z_index = 0;
    
    // Notification for z_index changes
    void notifyZIndexChanged();
    
    // Name for finding elements
    std::string name;

    // Position in pixel coordinates (moved from derived classes)
    sf::Vector2f position;

    // Parent-child hierarchy (#122)
    std::weak_ptr<UIDrawable> parent;

    // Set the parent of this drawable (called by collections when adding)
    void setParent(std::shared_ptr<UIDrawable> new_parent);

    // Get the parent drawable (returns nullptr if no parent or expired)
    std::shared_ptr<UIDrawable> getParent() const;

    // Remove this drawable from its current parent's children
    void removeFromParent();

    // Get the global (screen) position by walking up the parent chain (#102)
    sf::Vector2f get_global_position() const;

    // Python API for parent/global_position
    static PyObject* get_parent(PyObject* self, void* closure);
    static int set_parent(PyObject* self, PyObject* value, void* closure);
    static PyObject* get_global_pos(PyObject* self, void* closure);
    
    // New properties for Phase 1
    bool visible = true;      // #87 - visibility flag
    float opacity = 1.0f;     // #88 - opacity (0.0 = transparent, 1.0 = opaque)
    
    // New virtual methods for Phase 1
    virtual sf::FloatRect get_bounds() const = 0;  // #89 - get bounding box
    virtual void move(float dx, float dy) = 0;     // #98 - move by offset
    virtual void resize(float w, float h) = 0;     // #98 - resize to dimensions
    
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
    
    // Python object cache support
    uint64_t serial_number = 0;
    
protected:
    // RenderTexture support (opt-in)
    std::unique_ptr<sf::RenderTexture> render_texture;
    sf::Sprite render_sprite;
    bool use_render_texture = false;
    bool render_dirty = true;
    
    // Enable RenderTexture for this drawable
    void enableRenderTexture(unsigned int width, unsigned int height);
    void updateRenderTexture();
    
public:
    // Mark this drawable as needing redraw (#116 - propagates up parent chain)
    void markDirty();

    // Check if this drawable needs redraw
    bool isDirty() const { return render_dirty; }

    // Clear dirty flag (called after rendering)
    void clearDirty() { render_dirty = false; }
};

typedef struct {
    PyObject_HEAD
    std::shared_ptr<std::vector<std::shared_ptr<UIDrawable>>> data;
    std::weak_ptr<UIDrawable> owner;  // #122: Parent drawable (for Frame.children, Grid.children)
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
