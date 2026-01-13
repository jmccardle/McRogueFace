#include "PyNoiseSource.h"
#include "PyHeightMap.h"
#include "McRFPy_API.h"
#include "McRFPy_Doc.h"
#include <sstream>
#include <cstdlib>
#include <ctime>
#include <random>

// Property definitions
PyGetSetDef PyNoiseSource::getsetters[] = {
    {"dimensions", (getter)PyNoiseSource::get_dimensions, NULL,
     MCRF_PROPERTY(dimensions, "Number of input dimensions (1-4). Read-only."), NULL},
    {"algorithm", (getter)PyNoiseSource::get_algorithm, NULL,
     MCRF_PROPERTY(algorithm, "Noise algorithm name ('simplex', 'perlin', or 'wavelet'). Read-only."), NULL},
    {"hurst", (getter)PyNoiseSource::get_hurst, NULL,
     MCRF_PROPERTY(hurst, "Hurst exponent for fbm/turbulence. Read-only."), NULL},
    {"lacunarity", (getter)PyNoiseSource::get_lacunarity, NULL,
     MCRF_PROPERTY(lacunarity, "Frequency multiplier between octaves. Read-only."), NULL},
    {"seed", (getter)PyNoiseSource::get_seed, NULL,
     MCRF_PROPERTY(seed, "Random seed used (even if originally None). Read-only."), NULL},
    {NULL}
};

// Method definitions
PyMethodDef PyNoiseSource::methods[] = {
    {"get", (PyCFunction)PyNoiseSource::get, METH_VARARGS,
     MCRF_METHOD(NoiseSource, get,
         MCRF_SIG("(pos: tuple[float, ...])", "float"),
         MCRF_DESC("Get flat noise value at coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position tuple with length matching dimensions")
         MCRF_RETURNS("float: Noise value in range [-1.0, 1.0]")
         MCRF_RAISES("ValueError", "Position tuple length doesn't match dimensions")
     )},
    {"fbm", (PyCFunction)PyNoiseSource::fbm, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(NoiseSource, fbm,
         MCRF_SIG("(pos: tuple[float, ...], octaves: int = 4)", "float"),
         MCRF_DESC("Get fractal brownian motion value at coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position tuple with length matching dimensions")
         MCRF_ARG("octaves", "Number of noise octaves to combine (default: 4)")
         MCRF_RETURNS("float: FBM noise value in range [-1.0, 1.0]")
         MCRF_RAISES("ValueError", "Position tuple length doesn't match dimensions")
     )},
    {"turbulence", (PyCFunction)PyNoiseSource::turbulence, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(NoiseSource, turbulence,
         MCRF_SIG("(pos: tuple[float, ...], octaves: int = 4)", "float"),
         MCRF_DESC("Get turbulence (absolute fbm) value at coordinates."),
         MCRF_ARGS_START
         MCRF_ARG("pos", "Position tuple with length matching dimensions")
         MCRF_ARG("octaves", "Number of noise octaves to combine (default: 4)")
         MCRF_RETURNS("float: Turbulence noise value in range [-1.0, 1.0]")
         MCRF_RAISES("ValueError", "Position tuple length doesn't match dimensions")
     )},
    {"sample", (PyCFunction)PyNoiseSource::sample, METH_VARARGS | METH_KEYWORDS,
     MCRF_METHOD(NoiseSource, sample,
         MCRF_SIG("(size: tuple[int, int], world_origin: tuple[float, float] = (0.0, 0.0), "
                  "world_size: tuple[float, float] = None, mode: str = 'fbm', octaves: int = 4)", "HeightMap"),
         MCRF_DESC("Sample noise into a HeightMap for batch processing."),
         MCRF_ARGS_START
         MCRF_ARG("size", "Output dimensions in cells as (width, height)")
         MCRF_ARG("world_origin", "World coordinates of top-left corner (default: (0, 0))")
         MCRF_ARG("world_size", "World area to sample (default: same as size)")
         MCRF_ARG("mode", "Sampling mode: 'flat', 'fbm', or 'turbulence' (default: 'fbm')")
         MCRF_ARG("octaves", "Octaves for fbm/turbulence modes (default: 4)")
         MCRF_RETURNS("HeightMap: New HeightMap filled with sampled noise values")
         MCRF_NOTE("Requires dimensions=2. Values are in range [-1.0, 1.0].")
     )},
    {NULL}
};

// Helper: Convert algorithm enum to string
static const char* algorithm_to_string(TCOD_noise_type_t alg) {
    switch (alg) {
        case TCOD_NOISE_PERLIN: return "perlin";
        case TCOD_NOISE_SIMPLEX: return "simplex";
        case TCOD_NOISE_WAVELET: return "wavelet";
        default: return "unknown";
    }
}

// Helper: Convert string to algorithm enum
static bool string_to_algorithm(const char* str, TCOD_noise_type_t* out) {
    if (strcmp(str, "simplex") == 0) {
        *out = TCOD_NOISE_SIMPLEX;
        return true;
    } else if (strcmp(str, "perlin") == 0) {
        *out = TCOD_NOISE_PERLIN;
        return true;
    } else if (strcmp(str, "wavelet") == 0) {
        *out = TCOD_NOISE_WAVELET;
        return true;
    }
    return false;
}

// Helper: Parse position tuple and validate dimensions
static bool parse_position(PyObject* pos_obj, int expected_dims, float* coords) {
    if (!PyTuple_Check(pos_obj) && !PyList_Check(pos_obj)) {
        PyErr_SetString(PyExc_TypeError, "pos must be a tuple or list");
        return false;
    }

    Py_ssize_t size = PyTuple_Check(pos_obj) ? PyTuple_Size(pos_obj) : PyList_Size(pos_obj);
    if (size != expected_dims) {
        PyErr_Format(PyExc_ValueError,
            "Position has %zd coordinates, but NoiseSource has %d dimensions",
            size, expected_dims);
        return false;
    }

    for (Py_ssize_t i = 0; i < size; i++) {
        PyObject* item = PyTuple_Check(pos_obj) ? PyTuple_GetItem(pos_obj, i) : PyList_GetItem(pos_obj, i);
        if (PyFloat_Check(item)) {
            coords[i] = (float)PyFloat_AsDouble(item);
        } else if (PyLong_Check(item)) {
            coords[i] = (float)PyLong_AsLong(item);
        } else {
            PyErr_Format(PyExc_TypeError, "Coordinate %zd must be a number", i);
            return false;
        }
    }

    return true;
}

// Constructor
PyObject* PyNoiseSource::pynew(PyTypeObject* type, PyObject* args, PyObject* kwds)
{
    PyNoiseSourceObject* self = (PyNoiseSourceObject*)type->tp_alloc(type, 0);
    if (self) {
        self->noise = nullptr;
        self->dimensions = 2;
        self->algorithm = TCOD_NOISE_SIMPLEX;
        self->hurst = TCOD_NOISE_DEFAULT_HURST;
        self->lacunarity = TCOD_NOISE_DEFAULT_LACUNARITY;
        self->seed = 0;
    }
    return (PyObject*)self;
}

int PyNoiseSource::init(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds)
{
    static const char* keywords[] = {"dimensions", "algorithm", "hurst", "lacunarity", "seed", nullptr};
    int dimensions = 2;
    const char* algorithm_str = "simplex";
    float hurst = TCOD_NOISE_DEFAULT_HURST;
    float lacunarity = TCOD_NOISE_DEFAULT_LACUNARITY;
    PyObject* seed_obj = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|isffO", const_cast<char**>(keywords),
                                     &dimensions, &algorithm_str, &hurst, &lacunarity, &seed_obj)) {
        return -1;
    }

    // Validate dimensions
    if (dimensions < 1 || dimensions > TCOD_NOISE_MAX_DIMENSIONS) {
        PyErr_Format(PyExc_ValueError,
            "dimensions must be between 1 and %d, got %d",
            TCOD_NOISE_MAX_DIMENSIONS, dimensions);
        return -1;
    }

    // Parse algorithm
    TCOD_noise_type_t algorithm;
    if (!string_to_algorithm(algorithm_str, &algorithm)) {
        PyErr_Format(PyExc_ValueError,
            "algorithm must be 'simplex', 'perlin', or 'wavelet', got '%s'",
            algorithm_str);
        return -1;
    }

    // Handle seed - generate random if None
    uint32_t seed;
    if (seed_obj == nullptr || seed_obj == Py_None) {
        // Generate random seed using C++ random facilities
        std::random_device rd;
        seed = rd();
    } else if (PyLong_Check(seed_obj)) {
        seed = (uint32_t)PyLong_AsUnsignedLong(seed_obj);
        if (PyErr_Occurred()) {
            return -1;
        }
    } else {
        PyErr_SetString(PyExc_TypeError, "seed must be an integer or None");
        return -1;
    }

    // Clean up any existing noise object
    if (self->noise) {
        TCOD_noise_delete(self->noise);
    }

    // Create TCOD random generator with the seed
    TCOD_Random* rng = TCOD_random_new_from_seed(TCOD_RNG_MT, seed);
    if (!rng) {
        PyErr_SetString(PyExc_MemoryError, "Failed to create random generator");
        return -1;
    }

    // Create noise object
    self->noise = TCOD_noise_new(dimensions, hurst, lacunarity, rng);
    if (!self->noise) {
        TCOD_random_delete(rng);
        PyErr_SetString(PyExc_MemoryError, "Failed to create noise object");
        return -1;
    }

    // Set the algorithm
    TCOD_noise_set_type(self->noise, algorithm);

    // Store configuration
    self->dimensions = dimensions;
    self->algorithm = algorithm;
    self->hurst = hurst;
    self->lacunarity = lacunarity;
    self->seed = seed;

    return 0;
}

void PyNoiseSource::dealloc(PyNoiseSourceObject* self)
{
    if (self->noise) {
        // The TCOD_Noise owns its random generator, so deleting noise also deletes rng
        TCOD_noise_delete(self->noise);
        self->noise = nullptr;
    }
    Py_TYPE(self)->tp_free((PyObject*)self);
}

PyObject* PyNoiseSource::repr(PyObject* obj)
{
    PyNoiseSourceObject* self = (PyNoiseSourceObject*)obj;
    std::ostringstream ss;

    if (self->noise) {
        ss << "<NoiseSource " << self->dimensions << "D "
           << algorithm_to_string(self->algorithm)
           << " seed=" << self->seed << ">";
    } else {
        ss << "<NoiseSource (uninitialized)>";
    }

    return PyUnicode_FromString(ss.str().c_str());
}

// Properties

PyObject* PyNoiseSource::get_dimensions(PyNoiseSourceObject* self, void* closure)
{
    return PyLong_FromLong(self->dimensions);
}

PyObject* PyNoiseSource::get_algorithm(PyNoiseSourceObject* self, void* closure)
{
    return PyUnicode_FromString(algorithm_to_string(self->algorithm));
}

PyObject* PyNoiseSource::get_hurst(PyNoiseSourceObject* self, void* closure)
{
    return PyFloat_FromDouble(self->hurst);
}

PyObject* PyNoiseSource::get_lacunarity(PyNoiseSourceObject* self, void* closure)
{
    return PyFloat_FromDouble(self->lacunarity);
}

PyObject* PyNoiseSource::get_seed(PyNoiseSourceObject* self, void* closure)
{
    return PyLong_FromUnsignedLong(self->seed);
}

// Point query methods

PyObject* PyNoiseSource::get(PyNoiseSourceObject* self, PyObject* args)
{
    if (!self->noise) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource not initialized");
        return nullptr;
    }

    PyObject* pos_obj;
    if (!PyArg_ParseTuple(args, "O", &pos_obj)) {
        return nullptr;
    }

    float coords[TCOD_NOISE_MAX_DIMENSIONS];
    if (!parse_position(pos_obj, self->dimensions, coords)) {
        return nullptr;
    }

    float value = TCOD_noise_get(self->noise, coords);
    return PyFloat_FromDouble(value);
}

PyObject* PyNoiseSource::fbm(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->noise) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource not initialized");
        return nullptr;
    }

    static const char* keywords[] = {"pos", "octaves", nullptr};
    PyObject* pos_obj;
    int octaves = 4;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char**>(keywords),
                                     &pos_obj, &octaves)) {
        return nullptr;
    }

    if (octaves < 1 || octaves > TCOD_NOISE_MAX_OCTAVES) {
        PyErr_Format(PyExc_ValueError,
            "octaves must be between 1 and %d, got %d",
            TCOD_NOISE_MAX_OCTAVES, octaves);
        return nullptr;
    }

    float coords[TCOD_NOISE_MAX_DIMENSIONS];
    if (!parse_position(pos_obj, self->dimensions, coords)) {
        return nullptr;
    }

    float value = TCOD_noise_get_fbm(self->noise, coords, (float)octaves);
    return PyFloat_FromDouble(value);
}

PyObject* PyNoiseSource::turbulence(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->noise) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource not initialized");
        return nullptr;
    }

    static const char* keywords[] = {"pos", "octaves", nullptr};
    PyObject* pos_obj;
    int octaves = 4;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|i", const_cast<char**>(keywords),
                                     &pos_obj, &octaves)) {
        return nullptr;
    }

    if (octaves < 1 || octaves > TCOD_NOISE_MAX_OCTAVES) {
        PyErr_Format(PyExc_ValueError,
            "octaves must be between 1 and %d, got %d",
            TCOD_NOISE_MAX_OCTAVES, octaves);
        return nullptr;
    }

    float coords[TCOD_NOISE_MAX_DIMENSIONS];
    if (!parse_position(pos_obj, self->dimensions, coords)) {
        return nullptr;
    }

    float value = TCOD_noise_get_turbulence(self->noise, coords, (float)octaves);
    return PyFloat_FromDouble(value);
}

// Batch sampling method - returns HeightMap

PyObject* PyNoiseSource::sample(PyNoiseSourceObject* self, PyObject* args, PyObject* kwds)
{
    if (!self->noise) {
        PyErr_SetString(PyExc_RuntimeError, "NoiseSource not initialized");
        return nullptr;
    }

    // sample() only works for 2D noise
    if (self->dimensions != 2) {
        PyErr_Format(PyExc_ValueError,
            "sample() requires 2D NoiseSource, but this NoiseSource has %d dimensions",
            self->dimensions);
        return nullptr;
    }

    static const char* keywords[] = {"size", "world_origin", "world_size", "mode", "octaves", nullptr};
    PyObject* size_obj = nullptr;
    PyObject* origin_obj = nullptr;
    PyObject* world_size_obj = nullptr;
    const char* mode_str = "fbm";
    int octaves = 4;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "O|OOsi", const_cast<char**>(keywords),
                                     &size_obj, &origin_obj, &world_size_obj, &mode_str, &octaves)) {
        return nullptr;
    }

    // Parse size
    int width, height;
    if (!PyTuple_Check(size_obj) || PyTuple_Size(size_obj) != 2) {
        PyErr_SetString(PyExc_TypeError, "size must be a tuple of (width, height)");
        return nullptr;
    }
    width = (int)PyLong_AsLong(PyTuple_GetItem(size_obj, 0));
    height = (int)PyLong_AsLong(PyTuple_GetItem(size_obj, 1));
    if (PyErr_Occurred()) {
        return nullptr;
    }
    if (width <= 0 || height <= 0) {
        PyErr_SetString(PyExc_ValueError, "size dimensions must be positive");
        return nullptr;
    }

    // Parse world_origin (default: (0, 0))
    float origin_x = 0.0f, origin_y = 0.0f;
    if (origin_obj && origin_obj != Py_None) {
        if (!PyTuple_Check(origin_obj) || PyTuple_Size(origin_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "world_origin must be a tuple of (x, y)");
            return nullptr;
        }
        PyObject* ox = PyTuple_GetItem(origin_obj, 0);
        PyObject* oy = PyTuple_GetItem(origin_obj, 1);
        if (PyFloat_Check(ox)) origin_x = (float)PyFloat_AsDouble(ox);
        else if (PyLong_Check(ox)) origin_x = (float)PyLong_AsLong(ox);
        else { PyErr_SetString(PyExc_TypeError, "world_origin values must be numeric"); return nullptr; }
        if (PyFloat_Check(oy)) origin_y = (float)PyFloat_AsDouble(oy);
        else if (PyLong_Check(oy)) origin_y = (float)PyLong_AsLong(oy);
        else { PyErr_SetString(PyExc_TypeError, "world_origin values must be numeric"); return nullptr; }
    }

    // Parse world_size (default: same as size)
    float world_w = (float)width, world_h = (float)height;
    if (world_size_obj && world_size_obj != Py_None) {
        if (!PyTuple_Check(world_size_obj) || PyTuple_Size(world_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "world_size must be a tuple of (width, height)");
            return nullptr;
        }
        PyObject* ww = PyTuple_GetItem(world_size_obj, 0);
        PyObject* wh = PyTuple_GetItem(world_size_obj, 1);
        if (PyFloat_Check(ww)) world_w = (float)PyFloat_AsDouble(ww);
        else if (PyLong_Check(ww)) world_w = (float)PyLong_AsLong(ww);
        else { PyErr_SetString(PyExc_TypeError, "world_size values must be numeric"); return nullptr; }
        if (PyFloat_Check(wh)) world_h = (float)PyFloat_AsDouble(wh);
        else if (PyLong_Check(wh)) world_h = (float)PyLong_AsLong(wh);
        else { PyErr_SetString(PyExc_TypeError, "world_size values must be numeric"); return nullptr; }
    }

    // Parse mode
    enum class SampleMode { FLAT, FBM, TURBULENCE };
    SampleMode mode;
    if (strcmp(mode_str, "flat") == 0) {
        mode = SampleMode::FLAT;
    } else if (strcmp(mode_str, "fbm") == 0) {
        mode = SampleMode::FBM;
    } else if (strcmp(mode_str, "turbulence") == 0) {
        mode = SampleMode::TURBULENCE;
    } else {
        PyErr_Format(PyExc_ValueError,
            "mode must be 'flat', 'fbm', or 'turbulence', got '%s'",
            mode_str);
        return nullptr;
    }

    // Validate octaves
    if (octaves < 1 || octaves > TCOD_NOISE_MAX_OCTAVES) {
        PyErr_Format(PyExc_ValueError,
            "octaves must be between 1 and %d, got %d",
            TCOD_NOISE_MAX_OCTAVES, octaves);
        return nullptr;
    }

    // Create HeightMap
    PyObject* heightmap_type = PyObject_GetAttrString(McRFPy_API::mcrf_module, "HeightMap");
    if (!heightmap_type) {
        PyErr_SetString(PyExc_RuntimeError, "HeightMap type not found in module");
        return nullptr;
    }

    PyObject* size_tuple = Py_BuildValue("(ii)", width, height);
    if (!size_tuple) {
        Py_DECREF(heightmap_type);
        return nullptr;
    }

    PyObject* hmap_args = PyTuple_Pack(1, size_tuple);
    Py_DECREF(size_tuple);
    if (!hmap_args) {
        Py_DECREF(heightmap_type);
        return nullptr;
    }

    PyHeightMapObject* hmap = (PyHeightMapObject*)PyObject_Call(heightmap_type, hmap_args, nullptr);
    Py_DECREF(hmap_args);
    Py_DECREF(heightmap_type);

    if (!hmap) {
        return nullptr;
    }

    // Sample noise into the heightmap
    // Formula: For output cell (x, y), sample world coordinate:
    //   wx = world_origin[0] + (x / size[0]) * world_size[0]
    //   wy = world_origin[1] + (y / size[1]) * world_size[1]
    float coords[2];
    for (int y = 0; y < height; y++) {
        for (int x = 0; x < width; x++) {
            coords[0] = origin_x + ((float)x / (float)width) * world_w;
            coords[1] = origin_y + ((float)y / (float)height) * world_h;

            float value;
            switch (mode) {
                case SampleMode::FLAT:
                    value = TCOD_noise_get(self->noise, coords);
                    break;
                case SampleMode::FBM:
                    value = TCOD_noise_get_fbm(self->noise, coords, (float)octaves);
                    break;
                case SampleMode::TURBULENCE:
                    value = TCOD_noise_get_turbulence(self->noise, coords, (float)octaves);
                    break;
            }

            TCOD_heightmap_set_value(hmap->heightmap, x, y, value);
        }
    }

    return (PyObject*)hmap;
}
