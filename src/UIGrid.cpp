#include "UIGrid.h"
#include "GameEngine.h"
#include "McRFPy_API.h"

UIGrid::UIGrid() {}

UIGrid::UIGrid(int gx, int gy, std::shared_ptr<PyTexture> _ptex, sf::Vector2f _xy, sf::Vector2f _wh)
: grid_x(gx), grid_y(gy),
  zoom(1.0f), center_x((gx/2) * _ptex->sprite_width), center_y((gy/2) * _ptex->sprite_height),
  ptex(_ptex), points(gx * gy)
{
    entities = std::make_shared<std::list<std::shared_ptr<UIEntity>>>();

    box.setSize(_wh);
    box.setPosition(_xy); 

    box.setFillColor(sf::Color(0,0,0,0));
    // create renderTexture with maximum theoretical size; sprite can resize to show whatever amount needs to be rendered
    renderTexture.create(1920, 1080); // TODO - renderTexture should be window size; above 1080p this will cause rendering errors
    
    sprite = ptex->sprite(0);

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
    // sprites that are visible according to zoom, center_x, center_y, and box width
    float center_x_sq = center_x / ptex->sprite_width;
    float center_y_sq = center_y / ptex->sprite_height;

    float width_sq = box.getSize().x / (ptex->sprite_width * zoom);
    float height_sq = box.getSize().y / (ptex->sprite_height * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);

    int left_spritepixels = center_x - (box.getSize().x / 2.0 / zoom);
    int top_spritepixels = center_y - (box.getSize().y / 2.0 / zoom);

    //sprite.setScale(sf::Vector2f(zoom, zoom));
    sf::RectangleShape r; // for colors and overlays
    r.setSize(sf::Vector2f(ptex->sprite_width * zoom, ptex->sprite_height * zoom));
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
                    (x*ptex->sprite_width - left_spritepixels) * zoom,
                    (y*ptex->sprite_height - top_spritepixels) * zoom );

            auto gridpoint = at(std::floor(x), std::floor(y));

            //sprite.setPosition(pixel_pos);

            r.setPosition(pixel_pos);
            r.setFillColor(gridpoint.color);
            renderTexture.draw(r);

            // tilesprite
            // if discovered but not visible, set opacity to 90%
            // if not discovered... just don't draw it?
            if (gridpoint.tilesprite != -1) {
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
            (e->position.x*ptex->sprite_width - left_spritepixels) * zoom,
            (e->position.y*ptex->sprite_height - top_spritepixels) * zoom );
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
    PyObject* textureObj;
    //float box_x, box_y, box_w, box_h;
    PyObject* pos, *size;

    //if (!PyArg_ParseTuple(args, "iiOffff", &grid_x, &grid_y, &textureObj, &box_x, &box_y, &box_w, &box_h)) {
    if (!PyArg_ParseTuple(args, "iiOOO", &grid_x, &grid_y, &textureObj, &pos, &size)) {
        return -1; // If parsing fails, return an error
    }

    PyVectorObject* pos_result = PyVector::from_arg(pos);
    if (!pos_result)
    {
        PyErr_SetString(PyExc_TypeError, "pos must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
        return -1;
    }

    PyVectorObject* size_result = PyVector::from_arg(size);
    if (!size_result)
    {
        PyErr_SetString(PyExc_TypeError, "pos must be a mcrfpy.Vector instance or arguments to mcrfpy.Vector.__init__");
        return -1;
    }

    // Convert PyObject texture to IndexTexture*
    // This requires the texture object to have been initialized similar to UISprite's texture handling

    //if (!PyObject_IsInstance(textureObj, (PyObject*)&PyTextureType)) {
    if (!PyObject_IsInstance(textureObj, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture"))) {
        PyErr_SetString(PyExc_TypeError, "texture must be a mcrfpy.Texture instance");
        return -1;
    }
    PyTextureObject* pyTexture = reinterpret_cast<PyTextureObject*>(textureObj);
    // TODO (7DRL day 2, item 4.) use shared_ptr / PyTextureObject on UIGrid
    //IndexTexture* texture = pyTexture->data.get();
    
    // Initialize UIGrid
    //self->data = new UIGrid(grid_x, grid_y, texture, sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    //self->data = std::make_shared<UIGrid>(grid_x, grid_y, pyTexture->data, 
    //        sf::Vector2f(box_x, box_y), sf::Vector2f(box_w, box_h));
    self->data = std::make_shared<UIGrid>(grid_x, grid_y, pyTexture->data, pos_result->data, size_result->data);
    return 0; // Success
}

PyObject* UIGrid::get_grid_size(PyUIGridObject* self, void* closure) {
    return Py_BuildValue("(ii)", self->data->grid_x, self->data->grid_y);
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
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
    else if (member_ptr == 3) // h
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
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
        auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Texture");
        auto obj = (PyTextureObject*)type->tp_alloc(type, 0);
        obj->data = self->data->getTexture();
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
        PyErr_SetString(PyExc_ValueError, "x value out of range (0, Grid.grid_y)");
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
    {"at", (PyCFunction)UIGrid::py_at, METH_O},
    {NULL, NULL, 0, NULL}
};


PyGetSetDef UIGrid::getsetters[] = {

    // TODO - refactor into get_vector_member with field identifier values `(void*)n`
    {"grid_size", (getter)UIGrid::get_grid_size, NULL, "Grid dimensions (grid_x, grid_y)", NULL},
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
    // Advance list iterator since Entities are not stored in a vector (if this code even worked)
    // vectors only: //auto target = (*vec)[self->index-1];
    //auto l_front = (*vec).begin();
    //std::advance(l_front, self->index-1);

    // TODO build PyObject* of the correct UIDrawable subclass to return
    //return py_instance(target);
    return NULL;
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
    //RET_PY_INSTANCE(target);
    // construct and return an entity object that points directly into the UIGrid's entity vector
    //PyUIEntityObject* o = (PyUIEntityObject*)((&PyUIEntityType)->tp_alloc(&PyUIEntityType, 0));
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Entity");
    auto o = (PyUIEntityObject*)type->tp_alloc(type, 0);
    auto p = std::static_pointer_cast<UIEntity>(target);
    o->data = p;
    return (PyObject*)o;
return NULL;


}

PySequenceMethods UIEntityCollection::sqmethods = {
    .sq_length = (lenfunc)UIEntityCollection::len,
    .sq_item = (ssizeargfunc)UIEntityCollection::getitem,
    //.sq_item_by_index = UIEntityCollection::getitem
    //.sq_slice - return a subset of the iterable
    //.sq_ass_item - called when `o[x] = y` is executed (x is any object type)
    //.sq_ass_slice - cool; no thanks, for now
    //.sq_contains - called when `x in o` is executed
    //.sq_ass_item_by_index - called when `o[x] = y` is executed (x is explictly an integer)
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
        PyErr_SetString(PyExc_TypeError, "UICollection.remove requires an integer index to remove");
        return NULL;
    }
    long index = PyLong_AsLong(o);
    if (index >= self->data->size())
    {
        PyErr_SetString(PyExc_ValueError, "Index out of range");
        return NULL;
    }
    else if (index < 0)
    {
        PyErr_SetString(PyExc_NotImplementedError, "reverse indexing is not implemented.");
        return NULL;
    }

    // release the shared pointer at correct part of the list
    self->data->erase(std::next(self->data->begin(), index));
    Py_INCREF(Py_None);
    return Py_None;
}

PyMethodDef UIEntityCollection::methods[] = {
    {"append", (PyCFunction)UIEntityCollection::append, METH_O},
    //{"extend", (PyCFunction)UIEntityCollection::extend, METH_O}, // TODO
    {"remove", (PyCFunction)UIEntityCollection::remove, METH_O},
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
    //PyUIEntityCollectionIterObject* iterObj;
    //iterObj = (PyUIEntityCollectionIterObject*)PyUIEntityCollectionIterType.tp_alloc(&PyUIEntityCollectionIterType, 0);
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "EntityCollectionIter");
    auto iterObj = (PyUIEntityCollectionIterObject*)type->tp_alloc(type, 0);
    if (iterObj == NULL) {
        return NULL;  // Failed to allocate memory for the iterator object
    }

    iterObj->data = self->data;
    iterObj->index = 0;
    iterObj->start_size = self->data->size();

    return (PyObject*)iterObj;
}
