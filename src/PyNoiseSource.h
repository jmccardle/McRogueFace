#pragma once
#include "Common.h"
#include "Python.h"
#include <libtcod.h>
#include <cstdint>

// Forward declaration
class PyNoiseSource;

// Python object structure for NoiseSource
typedef struct {
    PyObject_HEAD
    TCOD_Noise* noise;          // libtcod noise object (owned)
    int dimensions;             // 1-4
    TCOD_noise_type_t algorithm; // PERLIN, SIMPLEX, or WAVELET
    float hurst;                // Hurst exponent for fbm/turbulence
    float lacunarity;           // Frequency multiplier between octaves
    uint32_t seed;              // Random seed (stored even if auto-generated)
} PyNoiseSourceObject;

class PyNoiseSource
{
public:
    // Python type interface
    static PyObject* pynew(PyTypeObject* type, PyObject* args, PyObject* kwds);
    static int init(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds);
    static void dealloc(PyNoiseSourceObject* self);
    static PyObject* repr(PyObject* obj);

    // Properties (all read-only)
    static PyObject* get_dimensions(PyNoiseSourceObject* self, void* closure);
    static PyObject* get_algorithm(PyNoiseSourceObject* self, void* closure);
    static PyObject* get_hurst(PyNoiseSourceObject* self, void* closure);
    static PyObject* get_lacunarity(PyNoiseSourceObject* self, void* closure);
    static PyObject* get_seed(PyNoiseSourceObject* self, void* closure);

    // Point query methods (#207)
    static PyObject* get(PyNoiseSourceObject* self, PyObject* args);
    static PyObject* fbm(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds);
    static PyObject* turbulence(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds);

    // Batch sampling method (#208) - returns HeightMap
    static PyObject* sample(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds);

    // Method and property definitions
    static PyMethodDef methods[];
    static PyGetSetDef getsetters[];
};

namespace mcrfpydef {
    inline PyTypeObject PyNoiseSourceType = {
        .ob_base = {.ob_base = {.ob_refcnt = 1, .ob_type = NULL}, .ob_size = 0},
        .tp_name = "mcrfpy.NoiseSource",
        .tp_basicsize = sizeof(PyNoiseSourceObject),
        .tp_itemsize = 0,
        .tp_dealloc = (destructor)PyNoiseSource::dealloc,
        .tp_repr = PyNoiseSource::repr,
        .tp_flags = Py_TPFLAGS_DEFAULT,
        .tp_doc = PyDoc_STR(
            "NoiseSource(dimensions: int = 2, algorithm: str = 'simplex', hurst: float = 0.5, lacunarity: float = 2.0, seed: int = None)\n\n"
            "A configured noise generator for procedural generation.\n\n"
            "NoiseSource wraps libtcod's noise generator, providing coherent noise values "
            "that can be used for terrain generation, textures, and other procedural content. "
            "The same coordinates always produce the same value (deterministic).\n\n"
            "Args:\n"
            "    dimensions: Number of input dimensions (1-4). Default: 2.\n"
            "    algorithm: Noise algorithm - 'simplex', 'perlin', or 'wavelet'. Default: 'simplex'.\n"
            "    hurst: Fractal Hurst exponent for fbm/turbulence (0.0-1.0). Default: 0.5.\n"
            "    lacunarity: Frequency multiplier between octaves. Default: 2.0.\n"
            "    seed: Random seed for reproducibility. None for random seed.\n\n"
            "Properties:\n"
            "    dimensions (int): Read-only. Number of input dimensions.\n"
            "    algorithm (str): Read-only. Noise algorithm name.\n"
            "    hurst (float): Read-only. Hurst exponent.\n"
            "    lacunarity (float): Read-only. Lacunarity value.\n"
            "    seed (int): Read-only. Seed used (even if originally None).\n\n"
            "Example:\n"
            "    noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)\n"
            "    value = noise.get((10.5, 20.3))  # Returns -1.0 to 1.0\n"
            "    fbm_val = noise.fbm((10.5, 20.3), octaves=6)\n"
        ),
        .tp_methods = nullptr,  // Set in McRFPy_API.cpp
        .tp_getset = nullptr,   // Set in McRFPy_API.cpp
        .tp_init = (initproc)PyNoiseSource::init,
        .tp_new = PyNoiseSource::pynew,
    };
}
