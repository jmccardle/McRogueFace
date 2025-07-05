#include "UIFrame.h"
#include "UICollection.h"
#include "GameEngine.h"

UIDrawable* UIFrame::click_at(sf::Vector2f point)
{
    for (auto e: *children)
    {
        auto p = e->click_at(point + box.getPosition());
        if (p)
            return p;
    }
    if (click_callable)
    {
        float x = box.getPosition().x, y = box.getPosition().y, w = box.getSize().x, h = box.getSize().y;
        if (point.x > x && point.y > y && point.x < x+w && point.y < y+h) return this;
    }
    return NULL;
}

UIFrame::UIFrame()
: outline(0)
{
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
    box.setPosition(0, 0);
    box.setSize(sf::Vector2f(0, 0));
}

UIFrame::UIFrame(float _x, float _y, float _w, float _h)
: outline(0)
{
    box.setPosition(_x, _y);
    box.setSize(sf::Vector2f(_w, _h));
    children = std::make_shared<std::vector<std::shared_ptr<UIDrawable>>>();
}

UIFrame::~UIFrame()
{
    children.reset();
}

PyObjectsEnum UIFrame::derived_type()
{
    return PyObjectsEnum::UIFRAME;
}

void UIFrame::render(sf::Vector2f offset, sf::RenderTarget& target)
{
    box.move(offset);
    //Resources::game->getWindow().draw(box);
    target.draw(box);
    box.move(-offset);

    // Sort children by z_index if needed
    if (children_need_sort && !children->empty()) {
        std::sort(children->begin(), children->end(),
            [](const std::shared_ptr<UIDrawable>& a, const std::shared_ptr<UIDrawable>& b) {
                return a->z_index < b->z_index;
            });
        children_need_sort = false;
    }

    for (auto drawable : *children) {
        drawable->render(offset + box.getPosition(), target);
    }
}

PyObject* UIFrame::get_children(PyUIFrameObject* self, void* closure)
{
    // create PyUICollection instance pointing to self->data->children
    //PyUICollectionObject* o = (PyUICollectionObject*)mcrfpydef::PyUICollectionType.tp_alloc(&mcrfpydef::PyUICollectionType, 0);
    auto type = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "UICollection");
    auto o = (PyUICollectionObject*)type->tp_alloc(type, 0);
    if (o)
        o->data = self->data->children;
    return (PyObject*)o;
}


PyObject* UIFrame::get_float_member(PyUIFrameObject* self, void* closure)
{
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr == 0)
        return PyFloat_FromDouble(self->data->box.getPosition().x);
    else if (member_ptr == 1)
        return PyFloat_FromDouble(self->data->box.getPosition().y);
    else if (member_ptr == 2)
        return PyFloat_FromDouble(self->data->box.getSize().x);
    else if (member_ptr == 3)
        return PyFloat_FromDouble(self->data->box.getSize().y);
    else if (member_ptr == 4)
        return PyFloat_FromDouble(self->data->box.getOutlineThickness());
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
}

int UIFrame::set_float_member(PyUIFrameObject* self, PyObject* value, void* closure)
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
        PyErr_SetString(PyExc_TypeError, "Value must be an integer.");
        return -1;
    }
    if (member_ptr == 0) //x
        self->data->box.setPosition(val, self->data->box.getPosition().y);
    else if (member_ptr == 1) //y
        self->data->box.setPosition(self->data->box.getPosition().x, val);
    else if (member_ptr == 2) //w
        self->data->box.setSize(sf::Vector2f(val, self->data->box.getSize().y));
    else if (member_ptr == 3) //h
        self->data->box.setSize(sf::Vector2f(self->data->box.getSize().x, val));
    else if (member_ptr == 4) //outline
        self->data->box.setOutlineThickness(val);
    return 0;
}

PyObject* UIFrame::get_color_member(PyUIFrameObject* self, void* closure)
{
    // validate closure (should be impossible to be wrong, but it's thorough)
    auto member_ptr = reinterpret_cast<long>(closure);
    if (member_ptr != 0 && member_ptr != 1)
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return nullptr;
    }
    //PyTypeObject* colorType = &PyColorType;
    auto colorType = (PyTypeObject*)PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color");
    PyObject* pyColor = colorType->tp_alloc(colorType, 0);
    if (pyColor == NULL)
    {
        std::cout << "failure to allocate mcrfpy.Color / PyColorType" << std::endl;
        return NULL;
    }
    PyColorObject* pyColorObj = reinterpret_cast<PyColorObject*>(pyColor);

    // fetch correct member data
    sf::Color color;
    if (member_ptr == 0)
    {
        color = self->data->box.getFillColor();
        //return Py_BuildValue("(iii)", color.r, color.g, color.b);
    }
    else if (member_ptr == 1)
    {
        color = self->data->box.getOutlineColor();
        //return Py_BuildValue("(iii)", color.r, color.g, color.b);
    }
    
    return PyColor(color).pyObject();
}

int UIFrame::set_color_member(PyUIFrameObject* self, PyObject* value, void* closure)
{
    //TODO: this logic of (PyColor instance OR tuple -> sf::color) should be encapsulated for reuse
    auto member_ptr = reinterpret_cast<long>(closure);
    int r, g, b, a;
    if (PyObject_IsInstance(value, PyObject_GetAttrString(McRFPy_API::mcrf_module, "Color")))
    {
        sf::Color c = ((PyColorObject*)value)->data;
        r = c.r; g = c.g; b = c.b; a = c.a;
    }
    else if (!PyTuple_Check(value) || PyTuple_Size(value) < 3 || PyTuple_Size(value) > 4)
    {
        // reject non-Color, non-tuple value
        PyErr_SetString(PyExc_TypeError, "Value must be a tuple of 3 or 4 integers or an mcrfpy.Color object.");
        return -1;
    }
    else // get value from tuples
    {
        r = PyLong_AsLong(PyTuple_GetItem(value, 0));
        g = PyLong_AsLong(PyTuple_GetItem(value, 1));
        b = PyLong_AsLong(PyTuple_GetItem(value, 2));
        a = 255;

        if (PyTuple_Size(value) == 4)
        {
            a = PyLong_AsLong(PyTuple_GetItem(value, 3));
        }
    }

    if (r < 0 || r > 255 || g < 0 || g > 255 || b < 0 || b > 255 || a < 0 || a > 255)
    {
        PyErr_SetString(PyExc_ValueError, "Color values must be between 0 and 255.");
        return -1;
    }

    if (member_ptr == 0)
    {
        self->data->box.setFillColor(sf::Color(r, g, b, a));
    }
    else if (member_ptr == 1)
    {
        self->data->box.setOutlineColor(sf::Color(r, g, b, a));
    }
    else
    {
        PyErr_SetString(PyExc_AttributeError, "Invalid attribute");
        return -1;
    }

    return 0;
}

PyGetSetDef UIFrame::getsetters[] = {
    {"x", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "X coordinate of top-left corner",   (void*)0},
    {"y", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "Y coordinate of top-left corner",   (void*)1},
    {"w", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "width of the rectangle",   (void*)2},
    {"h", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "height of the rectangle",   (void*)3},
    {"outline", (getter)UIFrame::get_float_member, (setter)UIFrame::set_float_member, "Thickness of the border",   (void*)4},
    {"fill_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member, "Fill color of the rectangle", (void*)0},
    {"outline_color", (getter)UIFrame::get_color_member, (setter)UIFrame::set_color_member, "Outline color of the rectangle", (void*)1},
    {"children", (getter)UIFrame::get_children, NULL, "UICollection of objects on top of this one", NULL},
    {"click", (getter)UIDrawable::get_click, (setter)UIDrawable::set_click, "Object called with (x, y, button) when clicked", (void*)PyObjectsEnum::UIFRAME},
    {"z_index", (getter)UIDrawable::get_int, (setter)UIDrawable::set_int, "Z-order for rendering (lower values rendered first)", (void*)PyObjectsEnum::UIFRAME},
    {NULL}
};

PyObject* UIFrame::repr(PyUIFrameObject* self)
{
    std::ostringstream ss;
    if (!self->data) ss << "<Frame (invalid internal object)>";
    else {
        auto box = self->data->box;
        auto fc = box.getFillColor();
        auto oc = box.getOutlineColor();
        ss << "<Frame (x=" << box.getPosition().x << ", y=" << box.getPosition().y << ", w=" << 
            box.getSize().x << ", w=" << box.getSize().y << ", " <<
            "outline=" << box.getOutlineThickness() << ", " << 
            "fill_color=(" << (int)fc.r << ", " << (int)fc.g << ", " << (int)fc.b << ", " << (int)fc.a <<"), " <<
            "outline_color=(" << (int)oc.r << ", " << (int)oc.g << ", " << (int)oc.b << ", " << (int)oc.a <<"), " <<
            self->data->children->size() << " child objects" <<
            ")>";
    }
    std::string repr_str = ss.str();
    return PyUnicode_DecodeUTF8(repr_str.c_str(), repr_str.size(), "replace");
}

int UIFrame::init(PyUIFrameObject* self, PyObject* args, PyObject* kwds)
{
    //std::cout << "Init called\n";
    const char* keywords[] = { "x", "y", "w", "h", "fill_color", "outline_color", "outline", nullptr }; 
    float x = 0.0f, y = 0.0f, w = 0.0f, h=0.0f, outline=0.0f;
    PyObject* fill_color = 0;
    PyObject* outline_color = 0;

    if (!PyArg_ParseTupleAndKeywords(args, kwds, "ffff|OOf", const_cast<char**>(keywords), &x, &y, &w, &h, &fill_color, &outline_color, &outline))
    {
        return -1;
    }

    self->data->box.setPosition(sf::Vector2f(x, y));
    self->data->box.setSize(sf::Vector2f(w, h));
    self->data->box.setOutlineThickness(outline);
    // getsetter abuse because I haven't standardized Color object parsing (TODO)
    int err_val = 0;
    if (fill_color && fill_color != Py_None) err_val = UIFrame::set_color_member(self, fill_color, (void*)0);
    else self->data->box.setFillColor(sf::Color(0,0,0,255));
    if (err_val) return err_val;
    if (outline_color && outline_color != Py_None) err_val = UIFrame::set_color_member(self, outline_color, (void*)1);
    else self->data->box.setOutlineColor(sf::Color(128,128,128,255));
    if (err_val) return err_val;
    return 0;
}

// Animation property system implementation
bool UIFrame::setProperty(const std::string& name, float value) {
    if (name == "x") {
        box.setPosition(sf::Vector2f(value, box.getPosition().y));
        return true;
    } else if (name == "y") {
        box.setPosition(sf::Vector2f(box.getPosition().x, value));
        return true;
    } else if (name == "w") {
        box.setSize(sf::Vector2f(value, box.getSize().y));
        return true;
    } else if (name == "h") {
        box.setSize(sf::Vector2f(box.getSize().x, value));
        return true;
    } else if (name == "outline") {
        box.setOutlineThickness(value);
        return true;
    } else if (name == "fill_color.r") {
        auto color = box.getFillColor();
        color.r = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        return true;
    } else if (name == "fill_color.g") {
        auto color = box.getFillColor();
        color.g = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        return true;
    } else if (name == "fill_color.b") {
        auto color = box.getFillColor();
        color.b = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        return true;
    } else if (name == "fill_color.a") {
        auto color = box.getFillColor();
        color.a = std::clamp(static_cast<int>(value), 0, 255);
        box.setFillColor(color);
        return true;
    } else if (name == "outline_color.r") {
        auto color = box.getOutlineColor();
        color.r = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        return true;
    } else if (name == "outline_color.g") {
        auto color = box.getOutlineColor();
        color.g = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        return true;
    } else if (name == "outline_color.b") {
        auto color = box.getOutlineColor();
        color.b = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        return true;
    } else if (name == "outline_color.a") {
        auto color = box.getOutlineColor();
        color.a = std::clamp(static_cast<int>(value), 0, 255);
        box.setOutlineColor(color);
        return true;
    }
    return false;
}

bool UIFrame::setProperty(const std::string& name, const sf::Color& value) {
    if (name == "fill_color") {
        box.setFillColor(value);
        return true;
    } else if (name == "outline_color") {
        box.setOutlineColor(value);
        return true;
    }
    return false;
}

bool UIFrame::setProperty(const std::string& name, const sf::Vector2f& value) {
    if (name == "position") {
        box.setPosition(value);
        return true;
    } else if (name == "size") {
        box.setSize(value);
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, float& value) const {
    if (name == "x") {
        value = box.getPosition().x;
        return true;
    } else if (name == "y") {
        value = box.getPosition().y;
        return true;
    } else if (name == "w") {
        value = box.getSize().x;
        return true;
    } else if (name == "h") {
        value = box.getSize().y;
        return true;
    } else if (name == "outline") {
        value = box.getOutlineThickness();
        return true;
    } else if (name == "fill_color.r") {
        value = box.getFillColor().r;
        return true;
    } else if (name == "fill_color.g") {
        value = box.getFillColor().g;
        return true;
    } else if (name == "fill_color.b") {
        value = box.getFillColor().b;
        return true;
    } else if (name == "fill_color.a") {
        value = box.getFillColor().a;
        return true;
    } else if (name == "outline_color.r") {
        value = box.getOutlineColor().r;
        return true;
    } else if (name == "outline_color.g") {
        value = box.getOutlineColor().g;
        return true;
    } else if (name == "outline_color.b") {
        value = box.getOutlineColor().b;
        return true;
    } else if (name == "outline_color.a") {
        value = box.getOutlineColor().a;
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, sf::Color& value) const {
    if (name == "fill_color") {
        value = box.getFillColor();
        return true;
    } else if (name == "outline_color") {
        value = box.getOutlineColor();
        return true;
    }
    return false;
}

bool UIFrame::getProperty(const std::string& name, sf::Vector2f& value) const {
    if (name == "position") {
        value = box.getPosition();
        return true;
    } else if (name == "size") {
        value = box.getSize();
        return true;
    }
    return false;
}
