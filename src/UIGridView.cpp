// UIGridView.cpp - Rendering view for GridData (#252)
#include "UIGridView.h"
#include "UIGrid.h"
#include "UIEntity.h"
#include "GameEngine.h"
#include "McRFPy_API.h"
#include "Resources.h"
#include "Profiler.h"
#include "PyShader.h"
#include "PyUniformCollection.h"
#include "PyPositionHelper.h"
#include "PyVector.h"
#include "PythonObjectCache.h"
#include <cmath>
#include <algorithm>

UIGridView::UIGridView()
{
    renderTexture.create(1, 1);
    renderTextureSize = {1, 1};
    output.setTextureRect(sf::IntRect(0, 0, 0, 0));
    output.setPosition(0, 0);
    output.setTexture(renderTexture.getTexture());
    box.setSize(sf::Vector2f(256, 256));
    box.setFillColor(sf::Color(0, 0, 0, 0));
}

UIGridView::~UIGridView() {}

PyObjectsEnum UIGridView::derived_type()
{
    return PyObjectsEnum::UIGRIDVIEW;
}

void UIGridView::ensureRenderTextureSize()
{
    sf::Vector2u resolution{1920, 1080};
    if (Resources::game) {
        resolution = Resources::game->getGameResolution();
    }
    unsigned int required_w = std::min(resolution.x, 4096u);
    unsigned int required_h = std::min(resolution.y, 4096u);

    if (renderTextureSize.x != required_w || renderTextureSize.y != required_h) {
        renderTexture.create(required_w, required_h);
        renderTextureSize = {required_w, required_h};
        output.setTexture(renderTexture.getTexture());
    }
}

sf::FloatRect UIGridView::get_bounds() const
{
    return sf::FloatRect(box.getPosition(), box.getSize());
}

void UIGridView::move(float dx, float dy)
{
    box.move(dx, dy);
    position += sf::Vector2f(dx, dy);
}

void UIGridView::resize(float w, float h)
{
    box.setSize(sf::Vector2f(w, h));
}

sf::Vector2f UIGridView::getEffectiveCellSize() const
{
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    return sf::Vector2f(cw * zoom, ch * zoom);
}

std::optional<sf::Vector2i> UIGridView::screenToCell(sf::Vector2f screen_pos) const
{
    if (!grid_data) return std::nullopt;
    if (!box.getGlobalBounds().contains(screen_pos)) return std::nullopt;

    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    sf::Vector2f local = screen_pos - box.getPosition();
    int left_sp = center_x - (box.getSize().x / 2.0 / zoom);
    int top_sp = center_y - (box.getSize().y / 2.0 / zoom);

    float gx = (local.x / zoom + left_sp) / cw;
    float gy = (local.y / zoom + top_sp) / ch;

    int cx = static_cast<int>(std::floor(gx));
    int cy = static_cast<int>(std::floor(gy));

    if (cx < 0 || cx >= grid_data->grid_w || cy < 0 || cy >= grid_data->grid_h)
        return std::nullopt;
    return sf::Vector2i(cx, cy);
}

void UIGridView::center_camera()
{
    if (!grid_data) return;
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    center_x = (grid_data->grid_w / 2.0f) * cw;
    center_y = (grid_data->grid_h / 2.0f) * ch;
}

void UIGridView::center_camera(float tile_x, float tile_y)
{
    int cw = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int ch = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;
    center_x = tile_x * cw;
    center_y = tile_y * ch;
}

// =========================================================================
// Render — adapted from UIGrid::render()
// =========================================================================
void UIGridView::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    if (!visible || !grid_data) return;

    ensureRenderTextureSize();

    int cell_width = ptex ? ptex->sprite_width : DEFAULT_CELL_WIDTH;
    int cell_height = ptex ? ptex->sprite_height : DEFAULT_CELL_HEIGHT;

    bool has_camera_rotation = (camera_rotation != 0.0f);
    float grid_w_px = box.getSize().x;
    float grid_h_px = box.getSize().y;

    float rad = camera_rotation * (M_PI / 180.0f);
    float cos_r = std::cos(rad);
    float sin_r = std::sin(rad);
    float abs_cos = std::abs(cos_r);
    float abs_sin = std::abs(sin_r);
    float aabb_w = grid_w_px * abs_cos + grid_h_px * abs_sin;
    float aabb_h = grid_w_px * abs_sin + grid_h_px * abs_cos;

    sf::RenderTexture* activeTexture = &renderTexture;

    if (has_camera_rotation) {
        unsigned int needed_size = static_cast<unsigned int>(std::max(aabb_w, aabb_h) + 1);
        if (rotationTextureSize < needed_size) {
            rotationTexture.create(needed_size, needed_size);
            rotationTextureSize = needed_size;
        }
        activeTexture = &rotationTexture;
        activeTexture->clear(fill_color);
    } else {
        output.setPosition(box.getPosition() + offset);
        output.setTextureRect(sf::IntRect(0, 0, grid_w_px, grid_h_px));
        renderTexture.clear(fill_color);
    }

    float render_w = has_camera_rotation ? aabb_w : grid_w_px;
    float render_h = has_camera_rotation ? aabb_h : grid_h_px;

    float center_x_sq = center_x / cell_width;
    float center_y_sq = center_y / cell_height;
    float width_sq = render_w / (cell_width * zoom);
    float height_sq = render_h / (cell_height * zoom);
    float left_edge = center_x_sq - (width_sq / 2.0);
    float top_edge = center_y_sq - (height_sq / 2.0);
    int left_spritepixels = center_x - (render_w / 2.0 / zoom);
    int top_spritepixels = center_y - (render_h / 2.0 / zoom);
    int x_limit = left_edge + width_sq + 2;
    if (x_limit > grid_data->grid_w) x_limit = grid_data->grid_w;
    int y_limit = top_edge + height_sq + 2;
    if (y_limit > grid_data->grid_h) y_limit = grid_data->grid_h;

    // Render layers below entities (z_index < 0)
    grid_data->sortLayers();
    for (auto& layer : grid_data->layers) {
        if (layer->z_index >= 0) break;
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
    }

    // Render entities
    if (grid_data->entities) {
        for (auto& e : *grid_data->entities) {
            if (e->position.x < left_edge - 2 || e->position.x >= left_edge + width_sq + 2 ||
                e->position.y < top_edge - 2 || e->position.y >= top_edge + height_sq + 2) {
                continue;
            }
            auto& drawent = e->sprite;
            drawent.setScale(sf::Vector2f(zoom, zoom));
            auto pixel_pos = sf::Vector2f(
                (e->position.x*cell_width - left_spritepixels + e->sprite_offset.x) * zoom,
                (e->position.y*cell_height - top_spritepixels + e->sprite_offset.y) * zoom);
            drawent.render(pixel_pos, *activeTexture);
        }
    }

    // Render layers above entities (z_index >= 0)
    for (auto& layer : grid_data->layers) {
        if (layer->z_index < 0) continue;
        layer->render(*activeTexture, left_spritepixels, top_spritepixels,
                     left_edge, top_edge, x_limit, y_limit, zoom, cell_width, cell_height);
    }

    // Children (grid-world pixel coordinates)
    if (grid_data->children && !grid_data->children->empty()) {
        if (grid_data->children_need_sort) {
            std::sort(grid_data->children->begin(), grid_data->children->end(),
                [](const auto& a, const auto& b) { return a->z_index < b->z_index; });
            grid_data->children_need_sort = false;
        }
        for (auto& child : *grid_data->children) {
            if (!child->visible) continue;
            float child_grid_x = child->position.x / cell_width;
            float child_grid_y = child->position.y / cell_height;
            if (child_grid_x < left_edge - 2 || child_grid_x >= left_edge + width_sq + 2 ||
                child_grid_y < top_edge - 2 || child_grid_y >= top_edge + height_sq + 2)
                continue;
            auto pixel_pos = sf::Vector2f(
                (child->position.x - left_spritepixels) * zoom,
                (child->position.y - top_spritepixels) * zoom);
            child->render(pixel_pos, *activeTexture);
        }
    }

    // Perspective overlay
    if (perspective_enabled) {
        auto entity = perspective_entity.lock();
        sf::RectangleShape overlay;
        overlay.setSize(sf::Vector2f(cell_width * zoom, cell_height * zoom));

        if (entity) {
            for (int x = std::max(0, (int)(left_edge - 1)); x < x_limit; x++) {
                for (int y = std::max(0, (int)(top_edge - 1)); y < y_limit; y++) {
                    if (x < 0 || x >= grid_data->grid_w || y < 0 || y >= grid_data->grid_h) continue;
                    auto pixel_pos = sf::Vector2f(
                        (x*cell_width - left_spritepixels) * zoom,
                        (y*cell_height - top_spritepixels) * zoom);
                    int idx = y * grid_data->grid_w + x;
                    if (idx >= 0 && idx < static_cast<int>(entity->gridstate.size())) {
                        const auto& state = entity->gridstate[idx];
                        overlay.setPosition(pixel_pos);
                        if (!state.discovered) {
                            overlay.setFillColor(sf::Color(0, 0, 0, 255));
                            activeTexture->draw(overlay);
                        } else if (!state.visible) {
                            overlay.setFillColor(sf::Color(32, 32, 40, 192));
                            activeTexture->draw(overlay);
                        }
                    }
                }
            }
        } else {
            for (int x = std::max(0, (int)(left_edge - 1)); x < x_limit; x++) {
                for (int y = std::max(0, (int)(top_edge - 1)); y < y_limit; y++) {
                    if (x < 0 || x >= grid_data->grid_w || y < 0 || y >= grid_data->grid_h) continue;
                    auto pixel_pos = sf::Vector2f(
                        (x*cell_width - left_spritepixels) * zoom,
                        (y*cell_height - top_spritepixels) * zoom);
                    overlay.setPosition(pixel_pos);
                    overlay.setFillColor(sf::Color(0, 0, 0, 255));
                    activeTexture->draw(overlay);
                }
            }
        }
    }

    activeTexture->display();

    // Camera rotation compositing
    if (has_camera_rotation) {
        renderTexture.clear(fill_color);
        sf::Sprite rotatedSprite(rotationTexture.getTexture());
        float tex_center_x = aabb_w / 2.0f;
        float tex_center_y = aabb_h / 2.0f;
        rotatedSprite.setOrigin(tex_center_x, tex_center_y);
        rotatedSprite.setRotation(camera_rotation);
        rotatedSprite.setPosition(grid_w_px / 2.0f, grid_h_px / 2.0f);
        rotatedSprite.setTextureRect(sf::IntRect(0, 0, (int)aabb_w, (int)aabb_h));
        renderTexture.draw(rotatedSprite);
        renderTexture.display();
        output.setPosition(box.getPosition() + offset);
        output.setTextureRect(sf::IntRect(0, 0, grid_w_px, grid_h_px));
    }

    if (rotation != 0.0f) {
        output.setOrigin(origin);
        output.setRotation(rotation);
        output.setPosition(box.getPosition() + offset + origin);
    } else {
        output.setOrigin(0, 0);
        output.setRotation(0);
    }

    if (shader && shader->shader) {
        sf::Vector2f resolution(box.getSize().x, box.getSize().y);
        PyShader::applyEngineUniforms(*shader->shader, resolution);
        if (uniforms) uniforms->applyTo(*shader->shader);
        target.draw(output, shader->shader.get());
    } else {
        target.draw(output);
    }
}

UIDrawable* UIGridView::click_at(sf::Vector2f point)
{
    if (!box.getGlobalBounds().contains(point)) return nullptr;
    return this;  // GridView consumes clicks within its bounds
}

// Property system
bool UIGridView::setProperty(const std::string& name, float value)
{
    if (name == "center_x") { center_x = value; return true; }
    if (name == "center_y") { center_y = value; return true; }
    if (name == "zoom") { zoom = value; return true; }
    if (name == "camera_rotation") { camera_rotation = value; return true; }
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::setProperty(const std::string& name, const sf::Vector2f& value)
{
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, float& value) const
{
    if (name == "center_x") { value = center_x; return true; }
    if (name == "center_y") { value = center_y; return true; }
    if (name == "zoom") { value = zoom; return true; }
    if (name == "camera_rotation") { value = camera_rotation; return true; }
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, sf::Vector2f& value) const
{
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::hasProperty(const std::string& name) const
{
    if (name == "center_x" || name == "center_y" || name == "zoom" || name == "camera_rotation")
        return true;
    return UIDrawable::hasProperty(name);
}

// =========================================================================
// Python API
// =========================================================================

int UIGridView::init(PyUIGridViewObject* self, PyObject* args, PyObject* kwds)
{
    static const char* kwlist[] = {"grid", "pos", "size", "zoom", "fill_color", "name", nullptr};
    PyObject* grid_obj = nullptr;
    PyObject* pos_obj = nullptr;
    PyObject* size_obj = nullptr;
    float zoom_val = 1.0f;
    PyObject* fill_obj = nullptr;
    const char* name = nullptr;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOfOz", const_cast<char**>(kwlist),
                                     &grid_obj, &pos_obj, &size_obj, &zoom_val, &fill_obj, &name)) {
        return -1;
    }

    self->data->zoom = zoom_val;
    if (name) self->data->UIDrawable::name = std::string(name);

    // Parse grid
    if (grid_obj && grid_obj != Py_None) {
        if (PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyUIGridType)) {
            PyUIGridObject* pygrid = (PyUIGridObject*)grid_obj;
            // Create aliasing shared_ptr: shares ownership with UIGrid, points to GridData base
            self->data->grid_data = std::shared_ptr<GridData>(
                pygrid->data, static_cast<GridData*>(pygrid->data.get()));
            self->data->ptex = pygrid->data->getTexture();
        } else {
            PyErr_SetString(PyExc_TypeError, "grid must be a Grid object");
            return -1;
        }
    }

    // Parse pos
    if (pos_obj && pos_obj != Py_None) {
        sf::Vector2f pos = PyObject_to_sfVector2f(pos_obj);
        if (PyErr_Occurred()) return -1;
        self->data->position = pos;
        self->data->box.setPosition(pos);
    }

    // Parse size
    if (size_obj && size_obj != Py_None) {
        sf::Vector2f size = PyObject_to_sfVector2f(size_obj);
        if (PyErr_Occurred()) return -1;
        self->data->box.setSize(size);
    }

    // Parse fill_color
    if (fill_obj && fill_obj != Py_None) {
        self->data->fill_color = PyColor::fromPy(fill_obj);
        if (PyErr_Occurred()) return -1;
    }

    // Center camera on grid if we have one
    if (self->data->grid_data) {
        self->data->center_camera();
        self->data->ensureRenderTextureSize();
    }

    self->weakreflist = NULL;
    return 0;
}

PyObject* UIGridView::repr(PyUIGridViewObject* self)
{
    std::ostringstream ss;
    ss << "<GridView";
    if (self->data->grid_data) {
        ss << " grid=(" << self->data->grid_data->grid_w << "x" << self->data->grid_data->grid_h << ")";
    } else {
        ss << " grid=None";
    }
    ss << " pos=(" << self->data->box.getPosition().x << ", " << self->data->box.getPosition().y << ")"
       << " size=(" << self->data->box.getSize().x << ", " << self->data->box.getSize().y << ")"
       << " zoom=" << self->data->zoom << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

// Property getters/setters
PyObject* UIGridView::get_grid(PyUIGridViewObject* self, void* closure)
{
    if (!self->data->grid_data) Py_RETURN_NONE;

    // grid_data is an aliasing shared_ptr into a UIGrid (GridData is a base of UIGrid).
    // Reconstruct shared_ptr<UIGrid> to return the proper Python wrapper.
    auto grid_ptr = static_cast<UIGrid*>(self->data->grid_data.get());
    auto grid_as_uigrid = std::shared_ptr<UIGrid>(
        self->data->grid_data, grid_ptr);

    // Check cache via UIDrawable::serial_number
    if (grid_ptr->serial_number != 0) {
        PyObject* cached = PythonObjectCache::getInstance().lookup(grid_ptr->serial_number);
        if (cached) return cached;
    }

    auto grid_type = &mcrfpydef::PyUIGridType;
    auto pyGrid = (PyUIGridObject*)grid_type->tp_alloc(grid_type, 0);
    if (!pyGrid) return PyErr_NoMemory();

    pyGrid->data = grid_as_uigrid;
    pyGrid->weakreflist = NULL;

    if (grid_ptr->serial_number == 0) {
        grid_ptr->serial_number = PythonObjectCache::getInstance().assignSerial();
    }
    PyObject* weakref = PyWeakref_NewRef((PyObject*)pyGrid, NULL);
    if (weakref) {
        PythonObjectCache::getInstance().registerObject(grid_ptr->serial_number, weakref);
        Py_DECREF(weakref);
    }
    return (PyObject*)pyGrid;
}

int UIGridView::set_grid(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    if (value == Py_None) {
        self->data->grid_data = nullptr;
        return 0;
    }
    if (!PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridType)) {
        PyErr_SetString(PyExc_TypeError, "grid must be a Grid object or None");
        return -1;
    }
    PyUIGridObject* pygrid = (PyUIGridObject*)value;
    self->data->grid_data = std::shared_ptr<GridData>(
        pygrid->data, static_cast<GridData*>(pygrid->data.get()));
    self->data->ptex = pygrid->data->getTexture();
    return 0;
}

PyObject* UIGridView::get_center(PyUIGridViewObject* self, void* closure)
{
    return sfVector2f_to_PyObject(sf::Vector2f(self->data->center_x, self->data->center_y));
}

int UIGridView::set_center(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    sf::Vector2f vec = PyObject_to_sfVector2f(value);
    if (PyErr_Occurred()) return -1;
    self->data->center_x = vec.x;
    self->data->center_y = vec.y;
    return 0;
}

PyObject* UIGridView::get_zoom(PyUIGridViewObject* self, void* closure)
{
    return PyFloat_FromDouble(self->data->zoom);
}

int UIGridView::set_zoom(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    double val = PyFloat_AsDouble(value);
    if (val == -1.0 && PyErr_Occurred()) return -1;
    self->data->zoom = static_cast<float>(val);
    return 0;
}

PyObject* UIGridView::get_fill_color(PyUIGridViewObject* self, void* closure)
{
    auto type = &mcrfpydef::PyColorType;
    auto obj = (PyColorObject*)type->tp_alloc(type, 0);
    if (obj) obj->data = self->data->fill_color;
    return (PyObject*)obj;
}

int UIGridView::set_fill_color(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    self->data->fill_color = PyColor::fromPy(value);
    if (PyErr_Occurred()) return -1;
    return 0;
}

PyObject* UIGridView::get_texture(PyUIGridViewObject* self, void* closure)
{
    if (!self->data->ptex) Py_RETURN_NONE;
    // TODO: return texture wrapper
    Py_RETURN_NONE;
}

// Methods and getsetters arrays
PyMethodDef UIGridView_all_methods[] = {
    {NULL}
};

PyGetSetDef UIGridView::getsetters[] = {
    {"grid", (getter)UIGridView::get_grid, (setter)UIGridView::set_grid,
     "The Grid data this view renders.", NULL},
    {"center", (getter)UIGridView::get_center, (setter)UIGridView::set_center,
     "Camera center point in pixel coordinates.", NULL},
    {"zoom", (getter)UIGridView::get_zoom, (setter)UIGridView::set_zoom,
     "Zoom level for rendering.", NULL},
    {"fill_color", (getter)UIGridView::get_fill_color, (setter)UIGridView::set_fill_color,
     "Background fill color.", NULL},
    {"texture", (getter)UIGridView::get_texture, NULL,
     "Texture used for tile rendering (read-only).", NULL},
    {NULL}
};
