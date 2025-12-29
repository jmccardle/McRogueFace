#pragma once
#include "Common.h"
#include "Python.h"

class PyMusic;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyMusic> data;
} PyMusicObject;

class PyMusic : public std::enable_shared_from_this<PyMusic>
{
private:
    sf::Music music;
    std::string source;
    bool loaded;

public:
    PyMusic(const std::string& filename);

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
    float getPosition() const;
    void setPosition(float pos);

    // Python interface
    PyObject* pyObject();
    static PyObject* repr(PyObject* obj);
    static Py_hash_t hash(PyObject* obj);
    static int init(PyMusicObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);

    // Python methods
    static PyObject* py_play(PyMusicObject* self, PyObject* args);
    static PyObject* py_pause(PyMusicObject* self, PyObject* args);
    static PyObject* py_stop(PyMusicObject* self, PyObject* args);

    // Python getters/setters
    static PyObject* get_volume(PyMusicObject* self, void* closure);
    static int set_volume(PyMusicObject* self, PyObject* value, void* closure);
    static PyObject* get_loop(PyMusicObject* self, void* closure);
    static int set_loop(PyMusicObject* self, PyObject* value, void* closure);
    static PyObject* get_playing(PyMusicObject* self, void* closure);
    static PyObject* get_duration(PyMusicObject* self, void* closure);
    static PyObject* get_position(PyMusicObject* self, void* closure);
    static int set_position(PyMusicObject* self, PyObject* value, void* closure);
    static PyObject* get_source(PyMusicObject* self, void* closure);

    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    static PyTypeObject PyMusicType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.Music",
        .tp_basicsize = sizeof(PyMusicObject),
        .tp_itemsize = 0,
        .tp_repr = PyMusic::repr,
        .tp_hash = PyMusic::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Streaming music object for longer audio tracks"),
        .tp_methods = PyMusic::methods,
        .tp_getset = PyMusic::getsetters,
        .tp_init = (initproc)PyMusic::init,
        .tp_new = PyType_GenericNew,
    };
}
