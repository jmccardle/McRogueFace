#include "UIDrawable.h"
#include "UIFrame.h"
#include "UICaption.h"
#include "UISprite.h"
#include "UIGrid.h"
#include "GameEngine.h"
#include "McRFPy_API.h"

UIDrawable::UIDrawable() { click_callable = NULL;  }

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
