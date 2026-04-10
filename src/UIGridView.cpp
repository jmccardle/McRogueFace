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

    // Render layers below entities (z_index <= 0)
    grid_data->sortLayers();
    for (auto& layer : grid_data->layers) {
        if (layer->z_index > 0) break;  // #257: z_index=0 is ground level (below entities)
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

    // Render layers above entities (z_index > 0)
    for (auto& layer : grid_data->layers) {
        if (layer->z_index <= 0) continue;  // #257: skip ground-level and below
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
    if (setShaderProperty(name, value)) return true;
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::setProperty(const std::string& name, const sf::Vector2f& value)
{
    if (name == "center") {
        center_x = value.x;
        center_y = value.y;
        return true;
    }
    return UIDrawable::setProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, float& value) const
{
    if (name == "center_x") { value = center_x; return true; }
    if (name == "center_y") { value = center_y; return true; }
    if (name == "zoom") { value = zoom; return true; }
    if (name == "camera_rotation") { value = camera_rotation; return true; }
    if (getShaderProperty(name, value)) return true;
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::getProperty(const std::string& name, sf::Vector2f& value) const
{
    if (name == "center") {
        value = sf::Vector2f(center_x, center_y);
        return true;
    }
    return UIDrawable::getProperty(name, value);
}

bool UIGridView::hasProperty(const std::string& name) const
{
    if (name == "center_x" || name == "center_y" || name == "zoom" || name == "camera_rotation" || name == "center")
        return true;
    // #106: Shader uniform properties
    if (hasShaderProperty(name))
        return true;
    return UIDrawable::hasProperty(name);
}

// =========================================================================
// Python API
// =========================================================================

// #252: Grid/GridView API Unification
// Two construction modes:
//   Mode 1 (view): Grid(grid=existing_grid, pos=..., size=...)
//   Mode 2 (factory): Grid(grid_size=..., pos=..., texture=..., ...)
//
// Mode 2 creates a UIGrid internally and copies rendering state to GridView.
// Attribute access delegates to the underlying UIGrid for data operations.

int UIGridView::init(PyUIGridViewObject* self, PyObject* args, PyObject* kwds)
{
    // Determine mode by checking for 'grid' kwarg
    PyObject* grid_kwarg = nullptr;
    if (kwds) {
        grid_kwarg = PyDict_GetItemString(kwds, "grid");  // borrowed ref
    }

    bool explicit_view = (grid_kwarg && grid_kwarg != Py_None);

    if (explicit_view) {
        // Mode 1: View of existing grid data
        static const char* kwlist[] = {"grid", "pos", "size", "zoom", "fill_color", "name", nullptr};
        PyObject* grid_obj = nullptr;
        PyObject* pos_obj = nullptr;
        PyObject* size_obj = nullptr;
        float zoom_val = 1.0f;
        PyObject* fill_obj = nullptr;
        const char* name_str = nullptr;

        if (!PyArg_ParseTupleAndKeywords(args, kwds, "|OOOfOz", const_cast<char**>(kwlist),
                                         &grid_obj, &pos_obj, &size_obj, &zoom_val, &fill_obj, &name_str)) {
            return -1;
        }

        self->data->zoom = zoom_val;
        if (name_str) self->data->UIDrawable::name = std::string(name_str);

        // Accept both internal _GridData and GridView (unified Grid) as grid source
        if (grid_obj && grid_obj != Py_None) {
            if (PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyUIGridType)) {
                // Internal _GridData object
                PyUIGridObject* pygrid = (PyUIGridObject*)grid_obj;
                self->data->grid_data = std::shared_ptr<GridData>(
                    pygrid->data, static_cast<GridData*>(pygrid->data.get()));
                self->data->ptex = pygrid->data->getTexture();
            } else if (PyObject_IsInstance(grid_obj, (PyObject*)&mcrfpydef::PyUIGridViewType)) {
                // Another GridView (unified Grid) - share its grid_data
                PyUIGridViewObject* pyview = (PyUIGridViewObject*)grid_obj;
                if (pyview->data->grid_data) {
                    self->data->grid_data = pyview->data->grid_data;
                    self->data->ptex = pyview->data->ptex;
                }
            } else {
                PyErr_SetString(PyExc_TypeError, "grid must be a Grid object");
                return -1;
            }
        }

        if (pos_obj && pos_obj != Py_None) {
            sf::Vector2f pos = PyObject_to_sfVector2f(pos_obj);
            if (PyErr_Occurred()) return -1;
            self->data->position = pos;
            self->data->box.setPosition(pos);
        }
        if (size_obj && size_obj != Py_None) {
            sf::Vector2f size = PyObject_to_sfVector2f(size_obj);
            if (PyErr_Occurred()) return -1;
            self->data->box.setSize(size);
        }
        if (fill_obj && fill_obj != Py_None) {
            self->data->fill_color = PyColor::fromPy(fill_obj);
            if (PyErr_Occurred()) return -1;
        }

        if (self->data->grid_data) {
            self->data->center_camera();
            self->data->ensureRenderTextureSize();
        }

        self->weakreflist = NULL;

        // Register in Python object cache
        if (self->data->serial_number == 0) {
            self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
            PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
            if (weakref) {
                PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
                Py_DECREF(weakref);
            }
        }
        self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUIGridViewType;

        return 0;
    } else {
        // Mode 2: Factory mode - create UIGrid internally
        return init_with_data(self, args, kwds);
    }
}

int UIGridView::init_with_data(PyUIGridViewObject* self, PyObject* args, PyObject* kwds)
{
    // Create a temporary UIGrid using the user's kwargs.
    // This reuses UIGrid::init's complex parsing for grid_size, texture, layers, etc.

    // Remove 'grid' key from kwds if present (e.g. grid=None)
    PyObject* filtered_kwds = kwds ? PyDict_Copy(kwds) : PyDict_New();
    if (!filtered_kwds) return -1;
    if (PyDict_DelItemString(filtered_kwds, "grid") < 0) {
        PyErr_Clear();  // OK if "grid" wasn't in dict
    }

    // Create UIGrid via Python type system, forwarding positional args
    PyObject* grid_type = (PyObject*)&mcrfpydef::PyUIGridType;
    PyObject* grid_py = PyObject_Call(grid_type, args, filtered_kwds);
    Py_DECREF(filtered_kwds);

    if (!grid_py) return -1;

    PyUIGridObject* pygrid = (PyUIGridObject*)grid_py;

    // Take UIGrid data via aliasing shared_ptr
    self->data->grid_data = std::shared_ptr<GridData>(
        pygrid->data, static_cast<GridData*>(pygrid->data.get()));
    self->data->ptex = pygrid->data->getTexture();

    // Copy rendering state from UIGrid to GridView
    self->data->position = pygrid->data->position;
    self->data->box.setPosition(pygrid->data->box.getPosition());
    self->data->box.setSize(pygrid->data->box.getSize());
    self->data->zoom = pygrid->data->zoom;
    self->data->center_x = pygrid->data->center_x;
    self->data->center_y = pygrid->data->center_y;
    self->data->fill_color = sf::Color(pygrid->data->box.getFillColor());
    self->data->visible = pygrid->data->visible;
    self->data->opacity = pygrid->data->opacity;
    self->data->z_index = pygrid->data->z_index;
    self->data->name = pygrid->data->name;
    self->data->camera_rotation = pygrid->data->camera_rotation;

    // Copy alignment
    self->data->align_type = pygrid->data->align_type;
    self->data->align_margin = pygrid->data->align_margin;
    self->data->align_horiz_margin = pygrid->data->align_horiz_margin;
    self->data->align_vert_margin = pygrid->data->align_vert_margin;

    // Copy click callback if set
    if (pygrid->data->click_callable) {
        PyObject* cb = pygrid->data->click_callable->borrow();
        if (cb && cb != Py_None) {
            self->data->click_register(cb);
        }
    }

    // Set owning_view back-reference on the GridData
    self->data->grid_data->owning_view = self->data;

    self->data->ensureRenderTextureSize();

    Py_DECREF(grid_py);
    self->weakreflist = NULL;

    // Register in Python object cache
    if (self->data->serial_number == 0) {
        self->data->serial_number = PythonObjectCache::getInstance().assignSerial();
        PyObject* weakref = PyWeakref_NewRef((PyObject*)self, NULL);
        if (weakref) {
            PythonObjectCache::getInstance().registerObject(self->data->serial_number, weakref);
            Py_DECREF(weakref);
        }
    }
    self->data->is_python_subclass = (PyObject*)Py_TYPE(self) != (PyObject*)&mcrfpydef::PyUIGridViewType;

    return 0;
}

PyObject* UIGridView::repr(PyUIGridViewObject* self)
{
    std::ostringstream ss;
    ss << "<Grid";
    if (self->data->grid_data) {
        ss << " (" << self->data->grid_data->grid_w << "x" << self->data->grid_data->grid_h << ")";
    } else {
        ss << " (no data)";
    }
    ss << " pos=(" << self->data->box.getPosition().x << ", " << self->data->box.getPosition().y << ")"
       << " size=(" << self->data->box.getSize().x << ", " << self->data->box.getSize().y << ")"
       << " zoom=" << self->data->zoom << ">";
    return PyUnicode_FromString(ss.str().c_str());
}

// =========================================================================
// #252: Attribute delegation to underlying Grid (UIGrid)
// =========================================================================

PyObject* UIGridView::get_grid_pyobj(PyUIGridViewObject* self)
{
    if (!self->data || !self->data->grid_data) {
        return nullptr;
    }
    return get_grid(self, nullptr);  // Returns new ref to internal UIGrid wrapper
}

PyObject* UIGridView::getattro(PyObject* self, PyObject* name)
{
    // First try normal attribute lookup on GridView (own getsetters + methods)
    PyObject* result = PyObject_GenericGetAttr(self, name);
    if (result) return result;

    // Only delegate on AttributeError, not other exceptions
    if (!PyErr_ExceptionMatches(PyExc_AttributeError)) return nullptr;

    PyUIGridViewObject* view = (PyUIGridViewObject*)self;
    if (!view->data || !view->data->grid_data) {
        // No grid data - can't delegate, return original AttributeError
        return nullptr;
    }

    // Clear error and try the internal Grid object
    PyErr_Clear();

    PyObject* grid = get_grid_pyobj(view);
    if (!grid) {
        PyErr_Format(PyExc_AttributeError,
            "'Grid' object has no attribute '%.200s'",
            PyUnicode_AsUTF8(name));
        return nullptr;
    }

    result = PyObject_GetAttr(grid, name);
    Py_DECREF(grid);
    return result;  // Returns result or propagates Grid's AttributeError
}

int UIGridView::setattro(PyObject* self, PyObject* name, PyObject* value)
{
    // First try normal attribute set on GridView (own getsetters)
    int result = PyObject_GenericSetAttr(self, name, value);
    if (result == 0) return 0;

    // Only delegate on AttributeError
    if (!PyErr_ExceptionMatches(PyExc_AttributeError)) return -1;

    PyUIGridViewObject* view = (PyUIGridViewObject*)self;
    if (!view->data || !view->data->grid_data) {
        return -1;  // No grid data, return original error
    }

    PyErr_Clear();

    PyObject* grid = get_grid_pyobj(view);
    if (!grid) {
        PyErr_Format(PyExc_AttributeError,
            "'Grid' object has no attribute '%.200s'",
            PyUnicode_AsUTF8(name));
        return -1;
    }

    result = PyObject_SetAttr(grid, name, value);
    Py_DECREF(grid);
    return result;
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
        if (self->data->grid_data) {
            self->data->grid_data->owning_view.reset();
        }
        self->data->grid_data = nullptr;
        return 0;
    }
    // Accept internal _GridData (UIGrid) objects
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridType)) {
        PyUIGridObject* pygrid = (PyUIGridObject*)value;
        if (self->data->grid_data) {
            self->data->grid_data->owning_view.reset();
        }
        self->data->grid_data = std::shared_ptr<GridData>(
            pygrid->data, static_cast<GridData*>(pygrid->data.get()));
        self->data->ptex = pygrid->data->getTexture();
        self->data->grid_data->owning_view = self->data;
        return 0;
    }
    // Accept GridView (unified Grid) objects - share their grid_data
    if (PyObject_IsInstance(value, (PyObject*)&mcrfpydef::PyUIGridViewType)) {
        PyUIGridViewObject* pyview = (PyUIGridViewObject*)value;
        if (pyview->data->grid_data) {
            if (self->data->grid_data) {
                self->data->grid_data->owning_view.reset();
            }
            self->data->grid_data = pyview->data->grid_data;
            self->data->ptex = pyview->data->ptex;
            // Don't override owning_view - original owner keeps it
            return 0;
        }
        self->data->grid_data = nullptr;
        return 0;
    }
    PyErr_SetString(PyExc_TypeError, "grid must be a Grid object or None");
    return -1;
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

// Float member getters/setters for GridView-specific float members (center_x, center_y, zoom, camera_rotation)
PyObject* UIGridView::get_float_member_gv(PyUIGridViewObject* self, void* closure)
{
    auto member_offset = (int)(intptr_t)closure;
    float value;
    switch (member_offset) {
        case 4: value = self->data->center_x; break;
        case 5: value = self->data->center_y; break;
        case 6: value = self->data->zoom; break;
        case 7: value = self->data->camera_rotation; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid member offset"); return NULL;
    }
    return PyFloat_FromDouble(value);
}

int UIGridView::set_float_member_gv(PyUIGridViewObject* self, PyObject* value, void* closure)
{
    float val;
    if (PyFloat_Check(value)) val = PyFloat_AsDouble(value);
    else if (PyLong_Check(value)) val = PyLong_AsLong(value);
    else { PyErr_SetString(PyExc_TypeError, "Value must be a number"); return -1; }

    auto member_offset = (int)(intptr_t)closure;
    switch (member_offset) {
        case 4: self->data->center_x = val; break;
        case 5: self->data->center_y = val; break;
        case 6: self->data->zoom = val; break;
        case 7: self->data->camera_rotation = val; break;
        default: PyErr_SetString(PyExc_RuntimeError, "Invalid member offset"); return -1;
    }
    self->data->markDirty();
    return 0;
}

// #252: PyObjectType typedef for UIDRAWABLE_* macros
typedef PyUIGridViewObject PyObjectType;

// Methods and getsetters arrays
PyMethodDef UIGridView_all_methods[] = {
    UIDRAWABLE_METHODS,
    {NULL}
};

// GridView getsetters for view-specific AND UIDrawable base properties.
// Data properties (entities, grid_size, layers, etc.) are accessed via getattro delegation.
PyGetSetDef UIGridView::getsetters[] = {
    {"grid_data", (getter)UIGridView::get_grid, (setter)UIGridView::set_grid,
     "The underlying grid data object (for multi-view scenarios).", NULL},
    {"center", (getter)UIGridView::get_center, (setter)UIGridView::set_center,
     "Camera center point in pixel coordinates.", NULL},
    {"zoom", (getter)UIGridView::get_zoom, (setter)UIGridView::set_zoom,
     "Zoom level for rendering.", NULL},
    {"fill_color", (getter)UIGridView::get_fill_color, (setter)UIGridView::set_fill_color,
     "Background fill color.", NULL},
    {"texture", (getter)UIGridView::get_texture, NULL,
     "Texture used for tile rendering (read-only).", NULL},
    // UIDrawable base properties - applied to GridView (the rendered object)
    {"pos", (getter)UIDrawable::get_pos, (setter)UIDrawable::set_pos,
     "Position of the grid as Vector", (void*)PyObjectsEnum::UIGRIDVIEW},
    {"x", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     "top-left corner X-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 0)},
    {"y", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     "top-left corner Y-coordinate", (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 1)},
    {"w", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     "visible widget width", (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 2)},
    {"h", (getter)UIDrawable::get_float_member, (setter)UIDrawable::set_float_member,
     "visible widget height", (void*)((intptr_t)PyObjectsEnum::UIGRIDVIEW << 8 | 3)},
    {"center_x", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     "center of the view X-coordinate", (void*)4},
    {"center_y", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     "center of the view Y-coordinate", (void*)5},
    {"camera_rotation", (getter)UIGridView::get_float_member_gv, (setter)UIGridView::set_float_member_gv,
     "Rotation of grid contents around camera center (degrees).", (void*)7},
    {"on_click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click,
     "Callable executed when object is clicked.", (void*)PyObjectsEnum::UIGRIDVIEW},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int,
     "Z-order for rendering (lower values rendered first).", (void*)PyObjectsEnum::UIGRIDVIEW},
    {"name", (getter)UIDrawable::get_name, (setter)UIDrawable::set_name,
     "Name for finding elements", (void*)PyObjectsEnum::UIGRIDVIEW},
    UIDRAWABLE_GETSETTERS,
    UIDRAWABLE_PARENT_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_ALIGNMENT_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_ROTATION_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    UIDRAWABLE_SHADER_GETSETTERS(PyObjectsEnum::UIGRIDVIEW),
    {NULL}
};
