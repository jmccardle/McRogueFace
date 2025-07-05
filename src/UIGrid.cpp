#include "UIGrid.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include <algorithm>

UIGrid::UIGrid() {}

UIGrid::UIGrid(int gx, int gy, std::shared_ptr<PyTexture> _ptex, sf::Vector2f _xy, sf::Vector2f _wh)
: grid_x(gx), grid_y(gy),
  zoom(1.0f), 
  ptex(_ptex), points(gx * gy)
{
    // Use texture dimensions if available, otherwise use defaults
    int cell_width = _ptex ? _ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = _ptex ? _ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    
    center_x = (gx/2) * cell_width;
    center_y = (gy/2) * cell_height;
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    box.setSize(_wh);
    box.setPosition(_xy); 

    box.setFillColor(sf::Color(0,0,0,0));
    // create renderTexture with maximum theoretical size; sprite can resize to show whatever amount needs to be rendered
    renderTexture.create(1920, 1080); // TODO - renderTexture should be window size; above 1080p this will cause rendering errors
    
    // Only initialize sprite if texture is available
    if (ptex) {
        sprite = ptex->sprite(0);
    }

    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
     output.setPosition(box.getPosition());
     // textures are upside-down inside renderTexture
     output.setTexture(renderTexture.getTexture());

}

void UIGrid::update() {}


void UIGrid::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    output.setPosition(box.getPosition() + offset); // output sprite can move; update position when drawing
    // output size can change; update size when drawing
    output.setTextureRect(
         sf::IntRect(0, 0,
         box.getSize().x, box.getSize().y));
    renderTexture.clear(sf::Color(8, 8, 8, 255)); // TODO - UIGrid needs a "background color" field
    
    // Get cell dimensions - use texture if available, otherwise defaults
    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    
    // sprites that are visible according to zoom, center_x, center_y, and box width
    float center_x_sq = center_x / cell_width;
    float center_y_sq = center_y / cell_height;

    float width_sq = box.getSize().x / (cell_width * zoom);
    float height_sq = box.getSize().y / (cell_height * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    //sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));
    r.setOutlineThickness(0);

    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_x) x_limit = grid_x;

    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_y) y_limit = grid_y;

    // base layer - bottom color, tile sprite ("ground")
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width; 
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0); 
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {
            auto pixel_pos = sf::Vector2f(
                    (x*cell_width - left_spritepixels) * zoom,
                    (y*cell_height - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            //sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);
            r.setFillColor(gridpoint.color);
            renderTexture.draw(r);

            // tilesprite - only draw if texture is available
            // if discovered but not visible, set opacity to 90%
            // if not discovered... just don't draw it?
            if (ptex && gridpoint.tilesprite != -1) {
                sprite = ptex->sprite(gridpoint.tilesprite, pixel_pos, sf::Vector2f(zoom, zoom)); //setSprite(gridpoint.tilesprite);;
                renderTexture.draw(sprite);
            }
        }
    }

    // middle layer - entities
    // disabling entity rendering until I can render their UISprite inside the rendertexture (not directly to window)
    for (auto e : *entities) {
        // TODO skip out-of-bounds entities (grid square not visible at all, check for partially on visible grid squares / floating point grid position)
        //auto drawent = e->cGrid->indexsprite.drawable();
        auto& drawent = e->sprite;
        //drawent.setScale(zoom, zoom);
        drawent.setScale(sf::Vector2f(zoom, zoom));
        auto pixel_pos = sf::Vector2f(
            (e->position.x*cell_width - left_spritepixels) * zoom,
            (e->position.y*cell_height - top_spritepixels) * zoom );
        //drawent.setPosition(pixel_pos);
        //renderTexture.draw(drawent);
        drawent.render(pixel_pos, renderTexture);
    }
    

    // top layer - opacity for discovered / visible status (debug, basically)
    /* // Disabled until I attach a "perspective"
    for (int x = (left_edge - 1 >= 0 ? left_edge - 1 : 0);
        x < x_limit; //x < view_width; 
        x+=1)
    {
        //for (float y = (top_edge >= 0 ? top_edge : 0); 
        for (int y = (top_edge - 1 >= 0 ? top_edge - 1 : 0);
            y < y_limit; //y < view_height;
            y+=1)
        {

            auto pixel_pos = sf::Vector2f(
                    (x*itex->grid_size - left_spritepixels) * zoom,
                    (y*itex->grid_size - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);

            // visible & discovered layers for testing purposes
            if (!gridpoint.discovered) {
                r.setFillColor(sf::Color(16, 16, 20, 192)); // 255 opacity for actual blackout
                renderTexture.draw(r);
            } else if (!gridpoint.visible) {
                r.setFillColor(sf::Color(32, 32, 40, 128));
                renderTexture.draw(r);
            }

            // overlay

            // uisprite
        }
    }
    */

    // grid lines for testing & validation
    /*
    sf::Vertex line[] =
    {
        sf::Vertex(sf::Vector2f(0, 0), sf::Color::Red),
        sf::Vertex(box.getSize(), sf::Color::Red),

    };

    renderTexture.draw(line, 2, sf::Lines);
    sf::Vertex lineb[] =
    {
        sf::Vertex(sf::Vector2f(0, box.getSize().y), sf::Color::Blue),
        sf::Vertex(sf::Vector2f(box.getSize().x, 0), sf::Color::Blue),

    };

    renderTexture.draw(lineb, 2, sf::Lines);
    */

    // render to window
    renderTexture.display();
    //Resources::game->getWindow().draw(output);
    target.draw(output);

}

UIGridPoint& UIGrid::at(int x, int y)
{
    return points[y * grid_x + x];
}

PyObjectsEnum UIGrid::derived_type()
{
    return PyObjectsEnum::UIGRID;
}

std::shared_ptr<PyTexture> UIGrid::getTexture()
{
    return ptex;
}

UIDrawable* UIGrid::click_at(sf::Vector2f point)
{
    if (click_callable)
    {
        if(box.getGlobalBounds().contains(point)) return this;
    }
    return NULL;
}


int UIGrid::init(PyUIGridObject* self, PyObject* args, PyObject* kwds) {
    int grid_x, grid_y;
    PyObject* textureObj = Py_None;
    //float box_x, box_y, box_w, box_h;
    PyObject* pos = NULL;
    PyObject* size = NULL;

    //if (!PyArg_ParseTuple(args, "iiOffff", &grid_x, &grid_y, &textureObj, &box_x, &box_y, &box_w, &box_h)) {
    if (!PyArg_ParseTuple(args, "ii|OOO", &grid_x, &grid_y, &textureObj, &pos, &size)) {
        return -1; // If parsing fails, return an error
    }

    // Default position and size if not provided
    PyVectorObject* pos_result = NULL;
    PyVectorObject* size_result = NULL;
    
    if (pos) {
        pos_result = PyVector::from_arg(pos);
        if (!pos_result)
        {
            PyErr_SetString(PyExc_TypeError, "pos must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
            return -1;
        }
    } else {
        // Default position (0, 0)
        PyObject* vector_class = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
        if (vector_class) {
            PyObject* pos_obj = PyObject_CallFunction(vector_class, "ff", 0.0f, 0.0f);
            Py_DECREF(vector_class);
            if (pos_obj) {
                pos_result = (PyVectorObject*)pos_obj;
            }
        }
        if (!pos_result) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to create default position vector");
            return -1;
        }
    }

    if (size) {
        size_result = PyVector::from_arg(size);
        if (!size_result)
        {
            PyErr_SetString(PyExc_TypeError, "size must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
            return -1;
        }
    } else {
        // Default size based on grid dimensions
        float default_w = grid_x * 16.0f;  // Assuming 16 pixel tiles
        float default_h = grid_y * 16.0f;
        PyObject* vector_class = PyObject_GetAttrString(McRFPy_API::mcrf_module, "Vector");
        if (vector_class) {
            PyObject* size_obj = PyObject_CallFunction(vector_class, "ff", default_w, default_h);
            Py_DECREF(vector_class);
            if (size_obj) {
                size_result = (PyVectorObject*)size_obj;
            }
        }
        if (!size_result) {
            PyErr_SetString(PyExc_RuntimeError, "Failed to create default size vector");
            return -1;
        }
    }

    // Convert PyObject texture to IndexTexture*
    // This requires the texture object to have been initialized similar to UISprite's texture handling
    
    std::shared_ptr<PyTexture> texture_ptr = nullptr;
    
    // Allow None for texture - use default texture in that case
    if (textureObj != Py_None) {
        //if (!PyObject_IsInstance(textureObj, (PyObject*)&PyTextureType)) {
        if (!PyObject_IsInstance(textureObj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
            PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance or None");
            return -1;
        }
        PyTextureObject* pyTexture = reinterpret_cast<PyTextureObject*>(textureObj);
        texture_ptr = pyTexture->data;
    } else {
        // Use default texture when None is provided
        texture_ptr = McRFPy_API::default_texture;
    }
    
    // Initialize UIGrid - texture_ptr will be nullptr if texture was None
    //self->data = new UIGrid(grid_x, grid_y, texture, sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    //self->data = std::make_shared<UIGrid>(grid_x, grid_y, pyTexture->data, 
    //        sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    self->data = std::make_shared<UIGrid>(grid_x, grid_y, texture_ptr, pos_result->data, size_result->data);
    return 0; // Success
}

PyObject* UIGrid::get_grid_size(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
}

PyObject* UIGrid::get_grid_x(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_x);
}

PyObject* UIGrid::get_grid_y(PyUIGridObject* self, void* closure) {
    return PyLong_FromLong(self->data->grid_y);
}

PyObject* UIGrid::get_position(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getPosition().x, box.getPosition().y);
}

int UIGrid::set_position(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Position must be a tuple of two floats");
        return -1;
    }
    self->data->box.setPosition(x, y);
    return 0;
}

PyObject* UIGrid::get_size(PyUIGridObject* self, void* closure) {
    auto& box = self->data->box;
    return Py_BuildValue("(ff)", box.getSize().x, box.getSize().y);
}

int UIGrid::set_size(PyUIGridObject* self, PyObject* value, void* closure) {
    float w, h;
    if (!PyArg_ParseTuple(value, "ff", &w, &h)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->box.setSize(sf::Vector2f(w, h));
    
    // Recreate renderTexture with new size to avoid rendering issues
    // Add some padding to handle zoom and ensure we don't cut off content
    unsigned int tex_width = static_cast<unsigned int>(w * 1.5f);
    unsigned int tex_height = static_cast<unsigned int>(h * 1.5f);
    
    // Clamp to reasonable maximum to avoid GPU memory issues
    tex_width = std::min(tex_width, 4096u);
    tex_height = std::min(tex_height, 4096u);
    
    self->data->renderTexture.create(tex_width, tex_height);
    
    return 0;
}

PyObject* UIGrid::get_center(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ff)", self->data->center_x, self->data->center_y);
}

int UIGrid::set_center(PyUIGridObject* self, PyObject* value, void* closure) {
    float x, y;
    if (!PyArg_ParseTuple(value, "ff", &x, &y)) {
        PyErr_SetString(PyExc_ValueError, "Size must be a tuple of two floats");
        return -1;
    }
    self->data->center_x = x;
    self->data->center_y = y;
    return 0;
}

PyObject* UIGrid::get_float_member(PyUIGridObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0) // x
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1) // y
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2) // w
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3) // h
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4) // center_x
        return PyFloat_FromDouble(self->data->center_x);
    else if (member_ptr == 5) // center_y
        return PyFloat_FromDouble(self->data->center_y);
    else if (member_ptr == 6) // zoom
        return PyFloat_FromDouble(self->data->zoom);
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIGrid::set_float_member(PyUIGridObject* self, PyObject* value, void* closure)
{
    float val;
    auto member_ptr = reinterpret_cast<long>(closure);
    if (PyFloat_Check(value))
    {
        val = PyFloat_AsDouble(value);
    }
    else if (PyLong_Check(value))
    {
        val = PyLong_AsLong(value);
    }
    else
    {
        PyErr_SetString(PyExc_TypeError, "Value must be a floating point number.");
        return -1;
    }
    if (member_ptr == 0) // x
        self->data->box.setPosition(val, self->data->box.getPosition().y);
    else if (member_ptr == 1) // y
        self->data->box.setPosition(self->data->box.getPosition().x, val);
    else if (member_ptr == 2) // w
    {
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
        // Recreate renderTexture when width changes
        unsigned int tex_width = static_cast<unsigned int>(val * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(self->data->box.getSize().y * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 3) // h
    {
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
        // Recreate renderTexture when height changes
        unsigned int tex_width = static_cast<unsigned int>(self->data->box.getSize().x * 1.5f);
        unsigned int tex_height = static_cast<unsigned int>(val * 1.5f);
        tex_width = std::min(tex_width, 4096u);
        tex_height = std::min(tex_height, 4096u);
        self->data->renderTexture.create(tex_width, tex_height);
    }
    else if (member_ptr == 4) // center_x
        self->data->center_x = val;
    else if (member_ptr == 5) // center_y
        self->data->center_y = val;
    else if (member_ptr == 6) // zoom
        self->data->zoom = val;
    return 0;
}
// TODO (7DRL Day 2, item 5.) return Texture object
/*
PyObject* UIGrid::get_texture(PyUIGridObject* self, void* closure) {
    Py_INCREF(self->texture);
    return self->texture;
}
*/

PyObject* UIGrid::get_texture(PyUIGridObject* self, void* closure) {
        //return self->data->getTexture()->pyObject();
        // PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPointState")
        //PyTextureObject* obj = (PyTextureObject*)((&PyTextureType)->tp_alloc(&PyTextureType, 0));
        
        // Return None if no texture
        auto texture = self->data->getTexture();
        if (!texture) {
            Py_RETURN_NONE;
        }
        
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");
        auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
        obj->data = texture;
        return (PyObject*)obj;
}

PyObject* UIGrid::py_at(PyUIGridObject* self, PyObject* o)
{
    int x, y;
    if (!PyArg_ParseTuple(o, "ii", &x, &y)) {
        PyErr_SetString(PyExc_TypeError, "UIGrid.at requires two integer arguments: (x, y)");
        return NULL;
    }
    if (x < 0 || x >= self->data->grid_x) {
        PyErr_SetString(PyExc_ValueError, "x value out of range (0, Grid.grid_x)");
        return NULL;
    }
    if (y < 0 || y >= self->data->grid_y) {
        PyErr_SetString(PyExc_ValueError, "y value out of range (0, Grid.grid_y)");
        return NULL;
    }

    //PyUIGridPointObject* obj = (PyUIGridPointObject*)((&PyUIGridPointType)->tp_alloc(&PyUIGridPointType, 0));
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "GridPoint");
    auto obj = (PyUIGridPointObject*)type->tp_alloc(type, 0);
    //auto target = std::static_pointer_cast<UIEntity>(target);
    obj->data = &(self->data->points[x + self->data->grid_x * y]);
    obj->grid = self->data;
    return (PyObject*)obj;
}

PyMethodDef UIGrid::methods[] = {
    {"at", (PyCFunction)UIGrid::py_at, METH_VARARGS},
    {NULL, NULL, 0, NULL}
};


PyGetSetDef UIGrid::getsetters[] = {

    // TODO - refactor into get_vector_member with field identifier values `(void*)n`
    {"grid_size", (getter)UIGrid::get_grid_size, NULL, "Grid dimensions (grid_x, grid_y)", NULL},
    {"grid_x", (getter)UIGrid::get_grid_x, NULL, "Grid x dimension", NULL},
    {"grid_y", (getter)UIGrid::get_grid_y, NULL, "Grid y dimension", NULL},
    {"position", (getter)UIGrid::get_position, (setter)UIGrid::set_position, "Position of the grid (x, y)", NULL},
    {"size", (getter)UIGrid::get_size, (setter)UIGrid::set_size, "Size of the grid (width, height)", NULL},
    {"center", (getter)UIGrid::get_center, (setter)UIGrid::set_center, "Grid coordinate at the center of the Grid's view (pan)", NULL},

    {"entities", (getter)UIGrid::get_children, NULL, "EntityCollection of entities on this grid", NULL},

    {"x", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "top-left corner X-coordinate", (void*)0},
    {"y", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "top-left corner Y-coordinate", (void*)1},
    {"w", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "visible widget width", (void*)2},
    {"h", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "visible widget height", (void*)3},
    {"center_x", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view X-coordinate", (void*)4},
    {"center_y", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "center of the view Y-coordinate", (void*)5},
    {"zoom", (getter)UIGrid::get_float_member, (setter)UIGrid::set_float_member, "zoom factor for displaying the Grid", (void*)6},

    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UIGRID},

    {"texture", (getter)UIGrid::get_texture, NULL, "Texture of the grid", NULL}, //TODO 7DRL-day2-item5
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int, "Z-order for rendering (lower values rendered first)", (void*)PyObjectsEnum::UIGRID},
    {NULL}  /* Sentinel */
};

PyObject* UIGrid::get_children(PyUIGridObject* self, void* closure)
{
    // create PyUICollection instance pointing to self->data->children
    //PyUIEntityCollectionObject* o = (PyUIEntityCollectionObject*)PyUIEntityCollectionType.tp_alloc(&PyUIEntityCollectionType, 0);
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "EntityCollection");
    auto o = (PyUIEntityCollectionObject*)type->tp_alloc(type, 0);
    if (o) {
        o->data = self->data->entities; // todone. / BUGFIX - entities isn't a shared pointer on UIGrid, what to do? -- I made it a sp<list<sp<UIEntity>>>
        o->grid = self->data;
    }
    return (PyObject*)o;
}

PyObject* UIGrid::repr(PyUIGridObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Grid (invalid internal object)>";
    else {
        auto grid = self->data;
        auto box = grid->box;
        ss << "<Grid (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", w=" << box.getSize().x << ", h=" << box.getSize().y << ", " <<
            "center=(" << grid->center_x << ", " << grid->center_y << "), zoom=" << grid->zoom <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

/* // TODO standard pointer would need deleted, but I opted for a shared pointer. tp_dealloc currently not even defined in the PyTypeObject
void PyUIGrid_dealloc(PyUIGridObject* self) {
    delete self->data; // Clean up the allocated UIGrid object
    Py_TYPE(self)->tp_free((PyObject*)self);
}
*/

int UIEntityCollectionIter::init(PyUIEntityCollectionIterObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "UICollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UIEntityCollectionIter::next(PyUIEntityCollectionIterObject* self)
{
    if (self->data->size() != self->start_size)
    {
        PyErr_SetString(PyExc_RuntimeError, "collection changed size during iteration");
        return NULL;
    }

    if (self->index > self->start_size - 1)
    {
        PyErr_SetNone(PyExc_StopIteration);
        return NULL;
    }
    self->index++;
    auto vec = self->data.get();
    if (!vec)
    {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    // Advance list iterator since Entities are stored in a list, not a vector
    auto l_begin = (*vec).begin();
    std::advance(l_begin, self->index-1);
    auto target = *l_begin;
    
    // Return the stored Python object if it exists (preserves derived types)
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }
    
    // Otherwise create and return a new Python Entity object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    auto p = std::static_pointer_cast<UIEntity>(target);
    o->data = p;
    return (PyObject*)o;
}

PyObject* UIEntityCollectionIter::repr(PyUIEntityCollectionIterObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<UICollectionIter (invalid internal object)>";
    else {
        ss << "<UICollectionIter (" << self->data->size() << " child objects, @ index " << self->index  << ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

Py_ssize_t UIEntityCollection::len(PyUIEntityCollectionObject* self) {
    return self->data->size();
}

PyObject* UIEntityCollection::getitem(PyUIEntityCollectionObject* self, Py_ssize_t index) {
    // build a Python version of item at self->data[index]
    //  Copy pasted::
    auto vec = self->data.get();
    if (!vec)
    {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    while (index < 0) index += self->data->size();
    if (index > self->data->size() - 1)
    {
        PyErr_SetString(PyExc_IndexError, "EntityCollection index out of range");
        return NULL;
    }
    auto l_begin = (*vec).begin();
    std::advance(l_begin, index);
    auto target = *l_begin; //auto target = (*vec)[index];
    
    // If the entity has a stored Python object reference, return that to preserve derived class
    if (target->self != nullptr) {
        Py_INCREF(target->self);
        return target->self;
    }
    
    // Otherwise, create a new base Entity object
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    auto p = std::static_pointer_cast<UIEntity>(target);
    o->data = p;
    return (PyObject*)o;
}

int UIEntityCollection::setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Handle negative indexing
    while (index < 0) index += list->size();
    
    // Bounds check
    if (index >= list->size()) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection assignment index out of range");
        return -1;
    }
    
    // Get iterator to the target position
    auto it = list->begin();
    std::advance(it, index);
    
    // Handle deletion
    if (value == NULL) {
        // Clear grid reference from the entity being removed
        (*it)->grid = nullptr;
        list->erase(it);
        return 0;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection can only contain Entity objects");
        return -1;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return -1;
    }
    
    // Clear grid reference from the old entity
    (*it)->grid = nullptr;
    
    // Replace the element and set grid reference
    *it = entity->data;
    entity->data->grid = self->grid;
    
    return 0;
}

int UIEntityCollection::contains(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        // Not an Entity, so it can't be in the collection
        return 0;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return 0;
    }
    
    // Search for the object by comparing C++ pointers
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return 1;  // Found
        }
    }
    
    return 0;  // Not found
}

PyObject* UIEntityCollection::concat(PyUIEntityCollectionObject* self, PyObject* other) {
    // Create a new Python list containing elements from both collections
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    Py_ssize_t self_len = self->data->size();
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    PyObject* result_list = PyList_New(self_len + other_len);
    if (!result_list) {
        return NULL;
    }
    
    // Add all elements from self
    Py_ssize_t idx = 0;
    for (const auto& entity : *self->data) {
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
        auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
        if (obj) {
            obj->data = entity;
            PyList_SET_ITEM(result_list, idx, (PyObject*)obj);  // Steals reference
        } else {
            Py_DECREF(result_list);
            Py_DECREF(type);
            return NULL;
        }
        Py_DECREF(type);
        idx++;
    }
    
    // Add all elements from other
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, self_len + i, item);  // Steals reference
    }
    
    return result_list;
}

PyObject* UIEntityCollection::inplace_concat(PyUIEntityCollectionObject* self, PyObject* other) {
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    // First, validate ALL items in the sequence before modifying anything
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    // Validate all items first
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }
        
        // Type check
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError, 
                "EntityCollection can only contain Entity objects; "
                "got %s at index %zd", Py_TYPE(item)->tp_name, i);
            return NULL;
        }
        Py_DECREF(item);
    }
    
    // All items validated, now we can safely add them
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;  // Shouldn't happen, but be safe
        }
        
        // Use the existing append method which handles grid references
        PyObject* result = append(self, item);
        Py_DECREF(item);
        
        if (!result) {
            return NULL;  // append() failed
        }
        Py_DECREF(result);  // append returns Py_None
    }
    
    Py_INCREF(self);
    return (PyObject*)self;
}

int UIEntityCollection::setitem(PyUIEntityCollectionObject* self, Py_ssize_t index, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Handle negative indexing
    while (index < 0) index += list->size();
    
    // Bounds check
    if (index >= list->size()) {
        PyErr_SetString(PyExc_IndexError, "EntityCollection assignment index out of range");
        return -1;
    }
    
    // Get iterator to the target position
    auto it = list->begin();
    std::advance(it, index);
    
    // Handle deletion
    if (value == NULL) {
        // Clear grid reference from the entity being removed
        (*it)->grid = nullptr;
        list->erase(it);
        return 0;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection can only contain Entity objects");
        return -1;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return -1;
    }
    
    // Clear grid reference from the old entity
    (*it)->grid = nullptr;
    
    // Replace the element and set grid reference
    *it = entity->data;
    entity->data->grid = self->grid;
    
    return 0;
}

int UIEntityCollection::contains(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return -1;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        // Not an Entity, so it can't be in the collection
        return 0;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return 0;
    }
    
    // Search for the object by comparing C++ pointers
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return 1;  // Found
        }
    }
    
    return 0;  // Not found
}

PyObject* UIEntityCollection::concat(PyUIEntityCollectionObject* self, PyObject* other) {
    // Create a new Python list containing elements from both collections
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    Py_ssize_t self_len = self->data->size();
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    PyObject* result_list = PyList_New(self_len + other_len);
    if (!result_list) {
        return NULL;
    }
    
    // Add all elements from self
    Py_ssize_t idx = 0;
    for (const auto& entity : *self->data) {
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
        auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
        if (obj) {
            obj->data = entity;
            PyList_SET_ITEM(result_list, idx, (PyObject*)obj);  // Steals reference
        } else {
            Py_DECREF(result_list);
            Py_DECREF(type);
            return NULL;
        }
        Py_DECREF(type);
        idx++;
    }
    
    // Add all elements from other
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            Py_DECREF(result_list);
            return NULL;
        }
        PyList_SET_ITEM(result_list, self_len + i, item);  // Steals reference
    }
    
    return result_list;
}

PyObject* UIEntityCollection::inplace_concat(PyUIEntityCollectionObject* self, PyObject* other) {
    if (!PySequence_Check(other)) {
        PyErr_SetString(PyExc_TypeError, "can only concatenate sequence to EntityCollection");
        return NULL;
    }
    
    // First, validate ALL items in the sequence before modifying anything
    Py_ssize_t other_len = PySequence_Length(other);
    if (other_len == -1) {
        return NULL;  // Error already set
    }
    
    // Validate all items first
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;
        }
        
        // Type check
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
            Py_DECREF(item);
            PyErr_Format(PyExc_TypeError, 
                "EntityCollection can only contain Entity objects; "
                "got %s at index %zd", Py_TYPE(item)->tp_name, i);
            return NULL;
        }
        Py_DECREF(item);
    }
    
    // All items validated, now we can safely add them
    for (Py_ssize_t i = 0; i < other_len; i++) {
        PyObject* item = PySequence_GetItem(other, i);
        if (!item) {
            return NULL;  // Shouldn't happen, but be safe
        }
        
        // Use the existing append method which handles grid references
        PyObject* result = append(self, item);
        Py_DECREF(item);
        
        if (!result) {
            return NULL;  // append() failed
        }
        Py_DECREF(result);  // append returns Py_None
    }
    
    Py_INCREF(self);
    return (PyObject*)self;
}

PySequenceMethods UIEntityCollection::sqmethods = {
    .sq_length = (lenfunc)UIEntityCollection::len,
    .sq_concat = (binaryfunc)UIEntityCollection::concat,
    .sq_repeat = NULL,
    .sq_item = (ssizeargfunc)UIEntityCollection::getitem,
    .was_sq_slice = NULL,
    .sq_ass_item = (ssizeobjargproc)UIEntityCollection::setitem,
    .was_sq_ass_slice = NULL,
    .sq_contains = (objobjproc)UIEntityCollection::contains,
    .sq_inplace_concat = (binaryfunc)UIEntityCollection::inplace_concat,
    .sq_inplace_repeat = NULL
};

PyObject* UIEntityCollection::append(PyUIEntityCollectionObject* self, PyObject* o)
{
    // if not UIDrawable subclass, reject it
    // self->data->push_back( c++ object inside o );

    // this would be a great use case for .tp_base
    //if (!PyObject_IsInstance(o, (PyObject*)&PyUIEntityType))
    if (!PyObject_IsInstance(o, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity")))
    {
        PyErr_SetString(PyExc_TypeError, "Only Entity objects can be added to EntityCollection");
        return NULL;
    }
    PyUIEntityObject* entity = (PyUIEntityObject*)o;
    self->data->push_back(entity->data);
    entity->data->grid = self->grid;

    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UIEntityCollection::remove(PyUIEntityCollectionObject* self, PyObject* o)
{
    if (!PyLong_Check(o))
    {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.remove requires an integer index to remove");
        return NULL;
    }
    long index = PyLong_AsLong(o);
    
    // Handle negative indexing
    while (index < 0) index += self->data->size();
    
    if (index >= self->data->size())
    {
        PyErr_SetString(PyExc_ValueError, "Index out of range");
        return NULL;
    }

    // Get iterator to the entity to remove
    auto it = self->data->begin();
    std::advance(it, index);
    
    // Clear grid reference before removing
    (*it)->grid = nullptr;
    
    // release the shared pointer at correct part of the list
    self->data->erase(it);
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UIEntityCollection::extend(PyUIEntityCollectionObject* self, PyObject* o)
{
    // Accept any iterable of Entity objects
    PyObject* iterator = PyObject_GetIter(o);
    if (iterator == NULL) {
        PyErr_SetString(PyExc_TypeError, "UIEntityCollection.extend requires an iterable");
        return NULL;
    }
    
    PyObject* item;
    while ((item = PyIter_Next(iterator)) != NULL) {
        // Check if item is an Entity
        if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
            Py_DECREF(item);
            Py_DECREF(iterator);
            PyErr_SetString(PyExc_TypeError, "All items in iterable must be Entity objects");
            return NULL;
        }
        
        // Add the entity to the collection
        PyUIEntityObject* entity = (PyUIEntityObject*)item;
        self->data->push_back(entity->data);
        entity->data->grid = self->grid;
        
        Py_DECREF(item);
    }
    
    Py_DECREF(iterator);
    
    // Check if iteration ended due to an error
    if (PyErr_Occurred()) {
        return NULL;
    }
    
    Py_INCREF(Py_None);
    return Py_None;
}

PyObject* UIEntityCollection::index_method(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        PyErr_SetString(PyExc_TypeError, "EntityCollection.index requires an Entity object");
        return NULL;
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        PyErr_SetString(PyExc_RuntimeError, "Invalid Entity object");
        return NULL;
    }
    
    // Search for the object
    Py_ssize_t idx = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            return PyLong_FromSsize_t(idx);
        }
        idx++;
    }
    
    PyErr_SetString(PyExc_ValueError, "Entity not in EntityCollection");
    return NULL;
}

PyObject* UIEntityCollection::count(PyUIEntityCollectionObject* self, PyObject* value) {
    auto list = self->data.get();
    if (!list) {
        PyErr_SetString(PyExc_RuntimeError, "the collection store returned a null pointer");
        return NULL;
    }
    
    // Type checking - must be an Entity
    if (!PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
        // Not an Entity, so count is 0
        return PyLong_FromLong(0);
    }
    
    // Get the C++ object from the Python object
    PyUIEntityObject* entity = (PyUIEntityObject*)value;
    if (!entity->data) {
        return PyLong_FromLong(0);
    }
    
    // Count occurrences
    Py_ssize_t count = 0;
    for (const auto& ent : *list) {
        if (ent.get() == entity->data.get()) {
            count++;
        }
    }
    
    return PyLong_FromSsize_t(count);
}

PyObject* UIEntityCollection::subscript(PyUIEntityCollectionObject* self, PyObject* key) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return NULL;
        }
        return getitem(self, index);
    } else if (PySlice_Check(key)) {
        // Handle slice
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return NULL;
        }
        
        PyObject* result_list = PyList_New(slicelength);
        if (!result_list) {
            return NULL;
        }
        
        // Iterate through the list with slice parameters
        auto it = self->data->begin();
        for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
            auto cur_it = it;
            std::advance(cur_it, cur);
            
            auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
            auto obj = (PyUIEntityObject*)type->tp_alloc(type, 0);
            if (obj) {
                obj->data = *cur_it;
                PyList_SET_ITEM(result_list, i, (PyObject*)obj);  // Steals reference
            } else {
                Py_DECREF(result_list);
                Py_DECREF(type);
                return NULL;
            }
            Py_DECREF(type);
        }
        
        return result_list;
    } else {
        PyErr_Format(PyExc_TypeError, "EntityCollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return NULL;
    }
}

int UIEntityCollection::ass_subscript(PyUIEntityCollectionObject* self, PyObject* key, PyObject* value) {
    if (PyLong_Check(key)) {
        // Single index - delegate to sq_ass_item
        Py_ssize_t index = PyLong_AsSsize_t(key);
        if (index == -1 && PyErr_Occurred()) {
            return -1;
        }
        return setitem(self, index, value);
    } else if (PySlice_Check(key)) {
        // Handle slice assignment/deletion
        Py_ssize_t start, stop, step, slicelength;
        
        if (PySlice_GetIndicesEx(key, self->data->size(), &start, &stop, &step, &slicelength) < 0) {
            return -1;
        }
        
        if (value == NULL) {
            // Deletion
            if (step != 1) {
                // For non-contiguous slices, delete from highest to lowest to maintain indices
                std::vector<Py_ssize_t> indices;
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    indices.push_back(cur);
                }
                // Sort in descending order
                std::sort(indices.begin(), indices.end(), std::greater<Py_ssize_t>());
                
                // Delete each index
                for (Py_ssize_t idx : indices) {
                    auto it = self->data->begin();
                    std::advance(it, idx);
                    (*it)->grid = nullptr;  // Clear grid reference
                    self->data->erase(it);
                }
            } else {
                // Contiguous slice - delete range
                auto it_start = self->data->begin();
                auto it_stop = self->data->begin();
                std::advance(it_start, start);
                std::advance(it_stop, stop);
                
                // Clear grid references
                for (auto it = it_start; it != it_stop; ++it) {
                    (*it)->grid = nullptr;
                }
                
                self->data->erase(it_start, it_stop);
            }
            return 0;
        } else {
            // Assignment
            if (!PySequence_Check(value)) {
                PyErr_SetString(PyExc_TypeError, "can only assign sequence to slice");
                return -1;
            }
            
            Py_ssize_t value_len = PySequence_Length(value);
            if (value_len == -1) {
                return -1;
            }
            
            // Validate all items first
            std::vector<std::shared_ptr<UIEntity>> new_items;
            for (Py_ssize_t i = 0; i < value_len; i++) {
                PyObject* item = PySequence_GetItem(value, i);
                if (!item) {
                    return -1;
                }
                
                // Type check
                if (!PyObject_IsInstance(item, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity"))) {
                    Py_DECREF(item);
                    PyErr_Format(PyExc_TypeError, 
                        "EntityCollection can only contain Entity objects; "
                        "got %s at index %zd", Py_TYPE(item)->tp_name, i);
                    return -1;
                }
                
                PyUIEntityObject* entity = (PyUIEntityObject*)item;
                Py_DECREF(item);
                new_items.push_back(entity->data);
            }
            
            // Now perform the assignment
            if (step == 1) {
                // Contiguous slice
                if (slicelength != value_len) {
                    // Need to resize - remove old items and insert new ones
                    auto it_start = self->data->begin();
                    auto it_stop = self->data->begin();
                    std::advance(it_start, start);
                    std::advance(it_stop, stop);
                    
                    // Clear grid references from old items
                    for (auto it = it_start; it != it_stop; ++it) {
                        (*it)->grid = nullptr;
                    }
                    
                    // Erase old range
                    it_start = self->data->erase(it_start, it_stop);
                    
                    // Insert new items
                    for (const auto& entity : new_items) {
                        entity->grid = self->grid;
                        it_start = self->data->insert(it_start, entity);
                        ++it_start;
                    }
                } else {
                    // Same size, just replace
                    auto it = self->data->begin();
                    std::advance(it, start);
                    for (const auto& entity : new_items) {
                        (*it)->grid = nullptr;  // Clear old grid ref
                        *it = entity;
                        entity->grid = self->grid;  // Set new grid ref
                        ++it;
                    }
                }
            } else {
                // Extended slice
                if (slicelength != value_len) {
                    PyErr_Format(PyExc_ValueError,
                        "attempt to assign sequence of size %zd to extended slice of size %zd",
                        value_len, slicelength);
                    return -1;
                }
                
                auto list_it = self->data->begin();
                for (Py_ssize_t i = 0, cur = start; i < slicelength; i++, cur += step) {
                    auto cur_it = list_it;
                    std::advance(cur_it, cur);
                    (*cur_it)->grid = nullptr;  // Clear old grid ref
                    *cur_it = new_items[i];
                    new_items[i]->grid = self->grid;  // Set new grid ref
                }
            }
            
            return 0;
        }
    } else {
        PyErr_Format(PyExc_TypeError, "EntityCollection indices must be integers or slices, not %.200s",
                     Py_TYPE(key)->tp_name);
        return -1;
    }
}

PyMappingMethods UIEntityCollection::mpmethods = {
    .mp_length = (lenfunc)UIEntityCollection::len,
    .mp_subscript = (binaryfunc)UIEntityCollection::subscript,
    .mp_ass_subscript = (objobjargproc)UIEntityCollection::ass_subscript
};

PyMethodDef UIEntityCollection::methods[] = {
    {"append", (PyCFunction)UIEntityCollection::append, METH_O},
    {"extend", (PyCFunction)UIEntityCollection::extend, METH_O},
    {"remove", (PyCFunction)UIEntityCollection::remove, METH_O},
    {"index", (PyCFunction)UIEntityCollection::index_method, METH_O},
    {"count", (PyCFunction)UIEntityCollection::count, METH_O},
    {NULL, NULL, 0, NULL}
};

PyObject* UIEntityCollection::repr(PyUIEntityCollectionObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<UICollection (invalid internal object)>";
    else {
        ss << "<UICollection (" << self->data->size() << " child objects)>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIEntityCollection::init(PyUIEntityCollectionObject* self, PyObject* args, PyObject* kwds)
{
    PyErr_SetString(PyExc_TypeError, "EntityCollection cannot be instantiated: a C++ data source is required.");
    return -1;
}

PyObject* UIEntityCollection::iter(PyUIEntityCollectionObject* self)
{
    // Get the iterator type from the module to ensure we have the registered version
    PyTypeObject* iterType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UIEntityCollectionIter");
    if (!iterType) {
        PyErr_SetString(PyExc_RuntimeError, "Could not find UIEntityCollectionIter type in module");
        return NULL;
    }
    
    // Allocate new iterator instance
    PyUIEntityCollectionIterObject* iterObj = (PyUIEntityCollectionIterObject*)iterType->tp_alloc(iterType, 0);
    
    if (iterObj == NULL) {
        Py_DECREF(iterType);
        return NULL;  // Failed to allocate memory for the iterator object
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    Py_DECREF(iterType);
    return (PyObject*)iterObj;
}

// Property system implementation for animations
bool UIGrid::setProperty(const std::string& name, float value) {
    if (name == "x") {
        box.setPosition(sf::Vector2f(value, box.getPosition().y));
        output.setPosition(box.getPosition());
        return true;
    }
    else if (name == "y") {
        box.setPosition(sf::Vector2f(box.getPosition().x, value));
        output.setPosition(box.getPosition());
        return true;
    }
    else if (name == "w" || name == "width") {
        box.setSize(sf::Vector2f(value, box.getSize().y));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "h" || name == "height") {
        box.setSize(sf::Vector2f(box.getSize().x, value));
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "center_x") {
        center_x = value;
        return true;
    }
    else if (name == "center_y") {
        center_y = value;
        return true;
    }
    else if (name == "zoom") {
        zoom = value;
        return true;
    }
    else if (name == "z_index") {
        z_index = static_cast<int>(value);
        return true;
    }
    return false;
}

bool UIGrid::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "position") {
        box.setPosition(value);
        output.setPosition(box.getPosition());
        return true;
    }
    else if (name == "size") {
        box.setSize(value);
        output.setTextureRect(sf::IntRect(0, 0, box.getSize().x, box.getSize().y));
        return true;
    }
    else if (name == "center") {
        center_x = value.x;
        center_y = value.y;
        return true;
    }
    return false;
}

bool UIGrid::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = box.getPosition().x;
        return true;
    }
    else if (name == "y") {
        value = box.getPosition().y;
        return true;
    }
    else if (name == "w" || name == "width") {
        value = box.getSize().x;
        return true;
    }
    else if (name == "h" || name == "height") {
        value = box.getSize().y;
        return true;
    }
    else if (name == "center_x") {
        value = center_x;
        return true;
    }
    else if (name == "center_y") {
        value = center_y;
        return true;
    }
    else if (name == "zoom") {
        value = zoom;
        return true;
    }
    else if (name == "z_index") {
        value = static_cast<float>(z_index);
        return true;
    }
    return false;
}

bool UIGrid::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "position") {
        value = box.getPosition();
        return true;
    }
    else if (name == "size") {
        value = box.getSize();
        return true;
    }
    else if (name == "center") {
        value = sf::Vector2f(center_x, center_y);
        return true;
    }
    return false;
}
