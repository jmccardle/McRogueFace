#include "GridLayers.h"
#include "UIGrid.h"
#include "PyColor.h"
#include "PyTexture.h"
#include <sstream>

// =============================================================================
// GridLayer base class
// =============================================================================

GridLayer::GridLayer(GridLayerType type, int z_index, int grid_x, int grid_y, UIGrid* parent)
    : type(type), z_index(z_index), grid_x(grid_x), grid_y(grid_y),
      parent_grid(parent), visible(true)
{}

// =============================================================================
// ColorLayer implementation
// =============================================================================

ColorLayer::ColorLayer(int z_index, int grid_x, int grid_y, UIGrid* parent)
    : GridLayer(GridLayerType::Color, z_index, grid_x, grid_y, parent),
      colors(grid_x * grid_y, sf::Color::Transparent)
{}

sf::Color& ColorLayer::at(int x, int y) {
    return colors[y * grid_x + x];
}

const sf::Color& ColorLayer::at(int x, int y) const {
    return colors[y * grid_x + x];
}

void ColorLayer::fill(const sf::Color& color) {
    std::fill(colors.begin(), colors.end(), color);
}

void ColorLayer::resize(int new_grid_x, int new_grid_y) {
    std::vector<sf::Color> new_colors(new_grid_x * new_grid_y, sf::Color::Transparent);

    // Copy existing data
    int copy_x = std::min(grid_x, new_grid_x);
    int copy_y = std::min(grid_y, new_grid_y);
    for (int y = 0; y < copy_y; ++y) {
        for (int x = 0; x < copy_x; ++x) {
            new_colors[y * new_grid_x + x] = colors[y * grid_x + x];
        }
    }

    colors = std::move(new_colors);
    grid_x = new_grid_x;
    grid_y = new_grid_y;
}

void ColorLayer::render(sf::RenderTarget& target,
                       float left_spritepixels, float top_spritepixels,
                       int left_edge, int top_edge, int x_limit, int y_limit,
                       float zoom, int cell_width, int cell_height) {
    if (!visible) return;

    sf::RectangleShape rect;
    rect.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));
    rect.setOutlineThickness(0);

    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0); x < x_limit; ++x) {
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0); y < y_limit; ++y) {
            if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) continue;

            const sf::Color& color = at(x, y);
            if (color.a == 0) continue;  // Skip fully transparent

            auto pixel_pos = sf::Vector2f(
                (x * cell_width - left_spritepixels) * zoom,
                (y * cell_height - top_spritepixels) * zoom
            );

            rect.setPosition(pixel_pos);
            rect.setFillColor(color);
            target.draw(rect);
        }
    }
}

// =============================================================================
// TileLayer implementation
// =============================================================================

TileLayer::TileLayer(int z_index, int grid_x, int grid_y, UIGrid* parent,
                     std::shared_ptr<PyTexture> texture)
    : GridLayer(GridLayerType::Tile, z_index, grid_x, grid_y, parent),
      tiles(grid_x * grid_y, -1),  // -1 = no tile
      texture(texture)
{}

int& TileLayer::at(int x, int y) {
    return tiles[y * grid_x + x];
}

int TileLayer::at(int x, int y) const {
    return tiles[y * grid_x + x];
}

void TileLayer::fill(int tile_index) {
    std::fill(tiles.begin(), tiles.end(), tile_index);
}

void TileLayer::resize(int new_grid_x, int new_grid_y) {
    std::vector<int> new_tiles(new_grid_x * new_grid_y, -1);

    // Copy existing data
    int copy_x = std::min(grid_x, new_grid_x);
    int copy_y = std::min(grid_y, new_grid_y);
    for (int y = 0; y < copy_y; ++y) {
        for (int x = 0; x < copy_x; ++x) {
            new_tiles[y * new_grid_x + x] = tiles[y * grid_x + x];
        }
    }

    tiles = std::move(new_tiles);
    grid_x = new_grid_x;
    grid_y = new_grid_y;
}

void TileLayer::render(sf::RenderTarget& target,
                      float left_spritepixels, float top_spritepixels,
                      int left_edge, int top_edge, int x_limit, int y_limit,
                      float zoom, int cell_width, int cell_height) {
    if (!visible || !texture) return;

    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0); x < x_limit; ++x) {
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0); y < y_limit; ++y) {
            if (x < 0 || x >= grid_x || y < 0 || y >= grid_y) continue;

            int tile_index = at(x, y);
            if (tile_index < 0) continue;  // No tile

            auto pixel_pos = sf::Vector2f(
                (x * cell_width - left_spritepixels) * zoom,
                (y * cell_height - top_spritepixels) * zoom
            );

            sf::Sprite sprite = texture->sprite(tile_index, pixel_pos, sf::Vector2f(zoom, zoom));
            target.draw(sprite);
        }
    }
}

// =============================================================================
// Python API - ColorLayer
// =============================================================================

PyMethodDef PyGridLayerAPI::ColorLayer_methods[] = {
    {"at", (PyCFunction)PyGridLayerAPI::ColorLayer_at, METH_VARARGS,
     "at(x, y) -> Color\n\nGet the color at cell position (x, y)."},
    {"set", (PyCFunction)PyGridLayerAPI::ColorLayer_set, METH_VARARGS,
     "set(x, y, color)\n\nSet the color at cell position (x, y)."},
    {"fill", (PyCFunction)PyGridLayerAPI::ColorLayer_fill, METH_VARARGS,
     "fill(color)\n\nFill the entire layer with the specified color."},
    {NULL}
};

PyGetSetDef PyGridLayerAPI::ColorLayer_getsetters[] = {
    {"z_index", (getter)PyGridLayerAPI::ColorLayer_get_z_index,
                (setter)PyGridLayerAPI::ColorLayer_set_z_index,
     "Layer z-order. Negative values render below entities.", NULL},
    {"visible", (getter)PyGridLayerAPI::ColorLayer_get_visible,
                (setter)PyGridLayerAPI::ColorLayer_set_visible,
     "Whether the layer is rendered.", NULL},
    {"grid_size", (getter)PyGridLayerAPI::ColorLayer_get_grid_size, NULL,
     "Layer dimensions as (width, height) tuple.", NULL},
    {NULL}
};

int PyGridLayerAPI::ColorLayer_init(PyColorLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"z_index", "grid_size", NULL};
    int z_index = -1;
    PyObject* grid_size_obj = nullptr;
    int grid_x = 0, grid_y = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iO", const_cast<char**>(kwlist),
                                     &z_index, &grid_size_obj)) {
        return -1;
    }

    // Parse grid_size if provided
    if (grid_size_obj && grid_size_obj != Py_None) {
        if (!PyTuple_Check(grid_size_obj) || PyTuple_Size(grid_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a (width, height) tuple");
            return -1;
        }
        grid_x = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 0));
        grid_y = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 1));
        if (PyErr_Occurred()) return -1;
    }

    // Create the layer (will be attached to grid via add_layer)
    self->data = std::make_shared<ColorLayer>(z_index, grid_x, grid_y, nullptr);
    self->grid.reset();

    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_at(PyColorLayerObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    const sf::Color& color = self->data->at(x, y);

    // Return as mcrfpy.Color
    auto* color_type = (PyTypeObject*)PyObject_GetAttrString(
        PyImport_ImportModule("mcrfpy"), "Color");
    if (!color_type) return NULL;

    PyColorObject* color_obj = (PyColorObject*)color_type->tp_alloc(color_type, 0);
    Py_DECREF(color_type);
    if (!color_obj) return NULL;

    color_obj->data = color;
    return (PyObject*)color_obj;
}

PyObject* PyGridLayerAPI::ColorLayer_set(PyColorLayerObject* self, PyObject* args) {
    int x, y;
    PyObject* color_obj;
    if (!PyArg_ParseTuple(args, "iiO", &x, &y, &color_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    // Parse color
    sf::Color color;
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return NULL;

    if (PyObject_IsInstance(color_obj, color_type)) {
        color = ((PyColorObject*)color_obj)->data;
    } else if (PyTuple_Check(color_obj)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(color_obj, "iii|i", &r, &g, &b, &a)) {
            Py_DECREF(color_type);
            return NULL;
        }
        color = sf::Color(r, g, b, a);
    } else {
        Py_DECREF(color_type);
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or (r, g, b[, a]) tuple");
        return NULL;
    }
    Py_DECREF(color_type);

    self->data->at(x, y) = color;
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_fill(PyColorLayerObject* self, PyObject* args) {
    PyObject* color_obj;
    if (!PyArg_ParseTuple(args, "O", &color_obj)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    // Parse color
    sf::Color color;
    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return NULL;

    auto* color_type = PyObject_GetAttrString(mcrfpy_module, "Color");
    Py_DECREF(mcrfpy_module);
    if (!color_type) return NULL;

    if (PyObject_IsInstance(color_obj, color_type)) {
        color = ((PyColorObject*)color_obj)->data;
    } else if (PyTuple_Check(color_obj)) {
        int r, g, b, a = 255;
        if (!PyArg_ParseTuple(color_obj, "iii|i", &r, &g, &b, &a)) {
            Py_DECREF(color_type);
            return NULL;
        }
        color = sf::Color(r, g, b, a);
    } else {
        Py_DECREF(color_type);
        PyErr_SetString(PyExc_TypeError, "color must be a Color object or (r, g, b[, a]) tuple");
        return NULL;
    }
    Py_DECREF(color_type);

    self->data->fill(color);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::ColorLayer_get_z_index(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyLong_FromLong(self->data->z_index);
}

int PyGridLayerAPI::ColorLayer_set_z_index(PyColorLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    long z = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;
    self->data->z_index = z;
    // TODO: Trigger re-sort in parent grid
    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_get_visible(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyBool_FromLong(self->data->visible);
}

int PyGridLayerAPI::ColorLayer_set_visible(PyColorLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    int v = PyObject_IsTrue(value);
    if (v < 0) return -1;
    self->data->visible = v;
    return 0;
}

PyObject* PyGridLayerAPI::ColorLayer_get_grid_size(PyColorLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* PyGridLayerAPI::ColorLayer_repr(PyColorLayerObject* self) {
    std::ostringstream ss;
    if (!self->data) {
        ss << "<ColorLayer (invalid)>";
    } else {
        ss << "<ColorLayer z_index=" << self->data->z_index
           << " size=(" << self->data->grid_x << "x" << self->data->grid_y << ")"
           << " visible=" << (self->data->visible ? "True" : "False") << ">";
    }
    return PyUnicode_FromString(ss.str().c_str());
}

// =============================================================================
// Python API - TileLayer
// =============================================================================

PyMethodDef PyGridLayerAPI::TileLayer_methods[] = {
    {"at", (PyCFunction)PyGridLayerAPI::TileLayer_at, METH_VARARGS,
     "at(x, y) -> int\n\nGet the tile index at cell position (x, y). Returns -1 if no tile."},
    {"set", (PyCFunction)PyGridLayerAPI::TileLayer_set, METH_VARARGS,
     "set(x, y, index)\n\nSet the tile index at cell position (x, y). Use -1 for no tile."},
    {"fill", (PyCFunction)PyGridLayerAPI::TileLayer_fill, METH_VARARGS,
     "fill(index)\n\nFill the entire layer with the specified tile index."},
    {NULL}
};

PyGetSetDef PyGridLayerAPI::TileLayer_getsetters[] = {
    {"z_index", (getter)PyGridLayerAPI::TileLayer_get_z_index,
                (setter)PyGridLayerAPI::TileLayer_set_z_index,
     "Layer z-order. Negative values render below entities.", NULL},
    {"visible", (getter)PyGridLayerAPI::TileLayer_get_visible,
                (setter)PyGridLayerAPI::TileLayer_set_visible,
     "Whether the layer is rendered.", NULL},
    {"texture", (getter)PyGridLayerAPI::TileLayer_get_texture,
                (setter)PyGridLayerAPI::TileLayer_set_texture,
     "Texture atlas for tile sprites.", NULL},
    {"grid_size", (getter)PyGridLayerAPI::TileLayer_get_grid_size, NULL,
     "Layer dimensions as (width, height) tuple.", NULL},
    {NULL}
};

int PyGridLayerAPI::TileLayer_init(PyTileLayerObject* self, PyObject* args, PyObject* kwds) {
    static const char* kwlist[] = {"z_index", "texture", "grid_size", NULL};
    int z_index = -1;
    PyObject* texture_obj = nullptr;
    PyObject* grid_size_obj = nullptr;
    int grid_x = 0, grid_y = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|iOO", const_cast<char**>(kwlist),
                                     &z_index, &texture_obj, &grid_size_obj)) {
        return -1;
    }

    // Parse texture
    std::shared_ptr<PyTexture> texture;
    if (texture_obj && texture_obj != Py_None) {
        // Check if it's a PyTexture
        auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
        if (!mcrfpy_module) return -1;

        auto* texture_type = PyObject_GetAttrString(mcrfpy_module, "Texture");
        Py_DECREF(mcrfpy_module);
        if (!texture_type) return -1;

        if (PyObject_IsInstance(texture_obj, texture_type)) {
            texture = ((PyTextureObject*)texture_obj)->data;
        } else {
            Py_DECREF(texture_type);
            PyErr_SetString(PyExc_TypeError, "texture must be a Texture object");
            return -1;
        }
        Py_DECREF(texture_type);
    }

    // Parse grid_size if provided
    if (grid_size_obj && grid_size_obj != Py_None) {
        if (!PyTuple_Check(grid_size_obj) || PyTuple_Size(grid_size_obj) != 2) {
            PyErr_SetString(PyExc_TypeError, "grid_size must be a (width, height) tuple");
            return -1;
        }
        grid_x = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 0));
        grid_y = PyLong_AsLong(PyTuple_GetItem(grid_size_obj, 1));
        if (PyErr_Occurred()) return -1;
    }

    // Create the layer
    self->data = std::make_shared<TileLayer>(z_index, grid_x, grid_y, nullptr, texture);
    self->grid.reset();

    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_at(PyTileLayerObject* self, PyObject* args) {
    int x, y;
    if (!PyArg_ParseTuple(args, "ii", &x, &y)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    return PyLong_FromLong(self->data->at(x, y));
}

PyObject* PyGridLayerAPI::TileLayer_set(PyTileLayerObject* self, PyObject* args) {
    int x, y, index;
    if (!PyArg_ParseTuple(args, "iii", &x, &y, &index)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (x < 0 || x >= self->data->grid_x || y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_IndexError, "Cell coordinates out of bounds");
        return NULL;
    }

    self->data->at(x, y) = index;
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::TileLayer_fill(PyTileLayerObject* self, PyObject* args) {
    int index;
    if (!PyArg_ParseTuple(args, "i", &index)) {
        return NULL;
    }

    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    self->data->fill(index);
    Py_RETURN_NONE;
}

PyObject* PyGridLayerAPI::TileLayer_get_z_index(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyLong_FromLong(self->data->z_index);
}

int PyGridLayerAPI::TileLayer_set_z_index(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    long z = PyLong_AsLong(value);
    if (PyErr_Occurred()) return -1;
    self->data->z_index = z;
    // TODO: Trigger re-sort in parent grid
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_visible(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return PyBool_FromLong(self->data->visible);
}

int PyGridLayerAPI::TileLayer_set_visible(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }
    int v = PyObject_IsTrue(value);
    if (v < 0) return -1;
    self->data->visible = v;
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_texture(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }

    if (!self->data->texture) {
        Py_RETURN_NONE;
    }

    auto* texture_type = (PyTypeObject*)PyObject_GetAttrString(
        PyImport_ImportModule("mcrfpy"), "Texture");
    if (!texture_type) return NULL;

    PyTextureObject* tex_obj = (PyTextureObject*)texture_type->tp_alloc(texture_type, 0);
    Py_DECREF(texture_type);
    if (!tex_obj) return NULL;

    tex_obj->data = self->data->texture;
    return (PyObject*)tex_obj;
}

int PyGridLayerAPI::TileLayer_set_texture(PyTileLayerObject* self, PyObject* value, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return -1;
    }

    if (value == Py_None) {
        self->data->texture.reset();
        return 0;
    }

    auto* mcrfpy_module = PyImport_ImportModule("mcrfpy");
    if (!mcrfpy_module) return -1;

    auto* texture_type = PyObject_GetAttrString(mcrfpy_module, "Texture");
    Py_DECREF(mcrfpy_module);
    if (!texture_type) return -1;

    if (!PyObject_IsInstance(value, texture_type)) {
        Py_DECREF(texture_type);
        PyErr_SetString(PyExc_TypeError, "texture must be a Texture object or None");
        return -1;
    }
    Py_DECREF(texture_type);

    self->data->texture = ((PyTextureObject*)value)->data;
    return 0;
}

PyObject* PyGridLayerAPI::TileLayer_get_grid_size(PyTileLayerObject* self, void* closure) {
    if (!self->data) {
        PyErr_SetString(PyExc_RuntimeError, "Layer has no data");
        return NULL;
    }
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* PyGridLayerAPI::TileLayer_repr(PyTileLayerObject* self) {
    std::ostringstream ss;
    if (!self->data) {
        ss << "<TileLayer (invalid)>";
    } else {
        ss << "<TileLayer z_index=" << self->data->z_index
           << " size=(" << self->data->grid_x << "x" << self->data->grid_y << ")"
           << " visible=" << (self->data->visible ? "True" : "False")
           << " texture=" << (self->data->texture ? "set" : "None") << ">";
    }
    return PyUnicode_FromString(ss.str().c_str());
}
