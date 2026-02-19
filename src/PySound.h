#pragma once
#include "Common.h"
#include "Python.h"

class PySound;
class SoundBufferData;

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

    // SoundBuffer support: if created from a SoundBuffer, store reference
    std::shared_ptr<SoundBufferData> bufferData;

public:
    PySound(const std::string& filename);
    PySound(std::shared_ptr<SoundBufferData> bufData);

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

    // Pitch
    float getPitch() const;
    void setPitch(float pitch);

    // Buffer data access
    std::shared_ptr<SoundBufferData> getBufferData() const { return bufferData; }

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
    static PyObject* py_play_varied(PySoundObject* self, PyObject* args, PyObject* kwds);

    // Python getters/setters
    static PyObject* get_volume(PySoundObject* self, void* closure);
    static int set_volume(PySoundObject* self, PyObject* value, void* closure);
    static PyObject* get_loop(PySoundObject* self, void* closure);
    static int set_loop(PySoundObject* self, PyObject* value, void* closure);
    static PyObject* get_playing(PySoundObject* self, void* closure);
    static PyObject* get_duration(PySoundObject* self, void* closure);
    static PyObject* get_source(PySoundObject* self, void* closure);
    static PyObject* get_pitch(PySoundObject* self, void* closure);
    static int set_pitch(PySoundObject* self, PyObject* value, void* closure);
    static PyObject* get_buffer(PySoundObject* self, void* closure);

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
        .tp_doc = PyDoc_STR(
            "Sound(source)\n\n"
            "Sound effect object for short audio clips.\n\n"
            "Args:\n"
            "    source: Filename string or SoundBuffer object.\n\n"
            "Properties:\n"
            "    volume (float): Volume 0-100.\n"
            "    loop (bool): Whether to loop.\n"
            "    playing (bool, read-only): True if playing.\n"
            "    duration (float, read-only): Duration in seconds.\n"
            "    source (str, read-only): Source filename.\n"
            "    pitch (float): Playback pitch (1.0 = normal).\n"
            "    buffer (SoundBuffer, read-only): The SoundBuffer, if created from one.\n"
        ),
        .tp_methods = PySound::methods,
        .tp_getset = PySound::getsetters,
        .tp_init = (initproc)PySound::init,
        .tp_new = PyType_GenericNew,
    };
}
