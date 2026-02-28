#pragma once

#include "Common.h"
#include "Python.h"
#include "structmember.h"
#include "Animation.h"
#include <memory>

typedef struct {
    PyObject_HEAD
    std::shared_ptr<Animation> data;
} PyAnimationObject;

class PyAnimation {
public:
    static PyObject* create(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyAnimationObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyAnimationObject* self);
    static PyObject* repr(PyAnimationObject* self);
    
    // Properties
    static PyObject* get_property(PyAnimationObject* self, void* closure);
    static PyObject* get_duration(PyAnimationObject* self, void* closure);
    static PyObject* get_elapsed(PyAnimationObject* self, void* closure);
    static PyObject* get_is_complete(PyAnimationObject* self, void* closure);
    static PyObject* get_is_delta(PyAnimationObject* self, void* closure);
    static PyObject* get_is_looping(PyAnimationObject* self, void* closure);
    
    // Methods
    static PyObject* start(PyAnimationObject* self, PyObject* args, PyObject* kwds);
    static PyObject* update(PyAnimationObject* self, PyObject* args);
    static PyObject* get_current_value(PyAnimationObject* self, PyObject* args);
    static PyObject* complete(PyAnimationObject* self, PyObject* args);
    static PyObject* stop(PyAnimationObject* self, PyObject* args);
    static PyObject* has_valid_target(PyAnimationObject* self, PyObject* args);
    
    static PyGetSetDef getsetters[];
    static PyMethodDef methods[];
};

namespace mcrfpydef {
    inline PyTypeObject PyAnimationType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Animation",
        .tp_basicsize = sizeof(PyAnimationObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyAnimation::dealloc,
        .tp_repr = (reprfunc)PyAnimation::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "Animation(property: str, target: Any, duration: float, easing: str = 'linear', delta: bool = False, loop: bool = False, callback: Callable = None)\n"
            "\n"
            "Create an animation that interpolates a property value over time.\n"
            "\n"
            "Args:\n"
            "    property: Property name to animate. Valid properties depend on target type:\n"
            "        - Position/Size: 'x', 'y', 'w', 'h', 'pos', 'size'\n"
            "        - Appearance: 'fill_color', 'outline_color', 'outline', 'opacity'\n"
            "        - Sprite: 'sprite_index', 'sprite_number', 'scale'\n"
            "        - Grid: 'center', 'zoom'\n"
            "        - Caption: 'text'\n"
            "        - Sub-properties: 'fill_color.r', 'fill_color.g', 'fill_color.b', 'fill_color.a'\n"
            "    target: Target value for the animation. Type depends on property:\n"
            "        - float: For numeric properties (x, y, w, h, scale, opacity, zoom)\n"
            "        - int: For integer properties (sprite_index)\n"
            "        - tuple (r, g, b[, a]): For color properties\n"
            "        - tuple (x, y): For vector properties (pos, size, center)\n"
            "        - list[int]: For sprite animation sequences\n"
            "        - str: For text animation\n"
            "    duration: Animation duration in seconds.\n"
            "    easing: Easing function name. Options:\n"
            "        - 'linear' (default)\n"
            "        - 'easeIn', 'easeOut', 'easeInOut'\n"
            "        - 'easeInQuad', 'easeOutQuad', 'easeInOutQuad'\n"
            "        - 'easeInCubic', 'easeOutCubic', 'easeInOutCubic'\n"
            "        - 'easeInQuart', 'easeOutQuart', 'easeInOutQuart'\n"
            "        - 'easeInSine', 'easeOutSine', 'easeInOutSine'\n"
            "        - 'easeInExpo', 'easeOutExpo', 'easeInOutExpo'\n"
            "        - 'easeInCirc', 'easeOutCirc', 'easeInOutCirc'\n"
            "        - 'easeInElastic', 'easeOutElastic', 'easeInOutElastic'\n"
            "        - 'easeInBack', 'easeOutBack', 'easeInOutBack'\n"
            "        - 'easeInBounce', 'easeOutBounce', 'easeInOutBounce'\n"
            "    delta: If True, target is relative to start value (additive). Default False.\n"
            "    loop: If True, animation repeats from start when it reaches the end. Default False.\n"
            "    callback: Function(target, property, value) called when animation completes.\n"
            "        Not called for looping animations (since they never complete).\n"
            "\n"
            "Example:\n"
            "    # Move a frame from current position to x=500 over 2 seconds\n"
            "    anim = mcrfpy.Animation('x', 500.0, 2.0, 'easeInOut')\n"
            "    anim.start(my_frame)\n"
            "\n"
            "    # Looping sprite animation\n"
            "    walk = mcrfpy.Animation('sprite_index', [0,1,2,3,2,1], 0.6, loop=True)\n"
            "    walk.start(my_sprite)\n"
        ),
        .tp_methods = PyAnimation::methods,
        .tp_getset = PyAnimation::getsetters,
        .tp_init = (initproc)PyAnimation::init,
        .tp_new = PyAnimation::create,
    };
}