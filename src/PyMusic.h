#pragma once
#include "Common.h"
#include "Python.h"
#include "Audio.h"

class PyMusic;

typedef struct {
    PyObject_HEAD
    std::shared_ptr<PyMusic> data;
} PyMusicObject;

// #440/#406: see PySound. `music` exists only while audio is enabled; the settings
// below are the object's own.
class PyMusic : public mcrf::audio::Source, public std::enable_shared_from_this<PyMusic>
{
private:
    std::unique_ptr<sf::Music> music;
    std::string source;
    bool loaded = false;
    float duration = 0.0f;
    float volume = 100.0f;
    bool loop = false;
    float position = 0.0f;  // the playing offset while there is no device

public:
    PyMusic(const std::string& filename);

    // mcrf::audio::Source
    bool active() const override;
    void releaseDevice() override;

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
    static PyObject* repr(PyObject* obj);
    static Py_hash_t hash(PyObject* obj);
    static int init(PyMusicObject* self, PyObject* args, PyObject* kwds);
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static void dealloc(PyMusicObject* self);

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
    inline PyTypeObject PyMusicType = {
        .ob_base = PyVarObject_HEAD_INIT(NULL, 0)
        .tp_name = "mcrfpy.Music",
        .tp_basicsize = sizeof(PyMusicObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyMusic::dealloc,
        .tp_repr = PyMusic::repr,
        .tp_hash = PyMusic::hash,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR("Streaming music object for longer audio tracks"),
        .tp_methods = PyMusic::methods,
        .tp_getset = PyMusic::getsetters,
        .tp_init = (initproc)PyMusic::init,
        .tp_new = PyMusic::pynew,
    };
}
