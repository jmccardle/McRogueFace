#pragma once
#include "Common.h"
#include "Python.h"

class PySound;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<PySound> data;
} PySoundObject;

class PySound : public std::enable_shared_from_this<PySound>
{
private:
    sf::SoundBuffer buffer;
    sf::Sound sound;
    std::string source;
    bool loaded;

public:
    PySound(const std::string& filename);

    // Playback control
    void play();
    void pause();
    void stop();

    // Properties
    float getVolume() const;
    void setVolume(float vol);
    bool getLoop() const;
    void setLoop(bool loop);
    bool isPlaying() const;
    float getDuration() const;

    // Python interface
    PyObject* pyObject();
    static PyObject* repr(PyObject* obj);
    static Py_hash_t hash(PyObject* obj);
    static int init(PySoundObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);

    // Python methods
    static PyObject* py_play(PySoundObject* self, PyObject* args);
    static PyObject* py_pause(PySoundObject* self, PyObject* args);
    static PyObject* py_stop(PySoundObject* self, PyObject* args);

    // Python getters/setters
    static PyObject* get_volume(PySoundObject* self, void* closure);
    static int set_volume(PySoundObject* self, PyObject* value, void* closure);
    static PyObject* get_loop(PySoundObject* self, void* closure);
    static int set_loop(PySoundObject* self, PyObject* value, void* closure);
    static PyObject* get_playing(PySoundObject* self, void* closure);
    static PyObject* get_duration(PySoundObject* self, void* closure);
    static PyObject* get_source(PySoundObject* self, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PySoundType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Sound",
        .tp_basicsize = sizeof(PySoundObject),
        .tp_itemsize = 0,
        .tp_repr = PySound::repr,
        .tp_hash = PySound::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Sound effect object for short audio clips"),
        .tp_methods = PySound::methods,
        .tp_getset = PySound::getsetters,
        .tp_init = (initproc)PySound::init,
        .tp_new = PyType_GenericNew,
    };
}
