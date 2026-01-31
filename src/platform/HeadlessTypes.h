// HeadlessTypes.h - SFML type stubs for headless/no-graphics builds
// This file provides minimal type definitions that allow McRogueFace
// to compile without linking against SFML.
//
// Part of the Emscripten research branch (emscripten-mcrogueface)

#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <chrono>

namespace sf {

// Forward declarations (needed for RenderWindow)
struct Event;
class Keyboard;
class Mouse;

// =============================================================================
// Type Aliases (SFML compatibility)
// =============================================================================

using Uint8 = uint8_t;
using Uint16 = uint16_t;
using Uint32 = uint32_t;
using Uint64 = uint64_t;
using Int8 = int8_t;
using Int16 = int16_t;
using Int32 = int32_t;
using Int64 = int64_t;

// =============================================================================
// Vector Types
// =============================================================================

template<typename T>
struct Vector2 {
    T x = 0;
    T y = 0;

    Vector2() = default;
    Vector2(T x_, T y_) : x(x_), y(y_) {}

    template<typename U>
    explicit Vector2(const Vector2<U>& other) : x(static_cast<T>(other.x)), y(static_cast<T>(other.y)) {}

    Vector2 operator+(const Vector2& rhs) const { return Vector2(x + rhs.x, y + rhs.y); }
    Vector2 operator-(const Vector2& rhs) const { return Vector2(x - rhs.x, y - rhs.y); }
    Vector2 operator*(T scalar) const { return Vector2(x * scalar, y * scalar); }
    Vector2 operator/(T scalar) const { return Vector2(x / scalar, y / scalar); }
    Vector2& operator+=(const Vector2& rhs) { x += rhs.x; y += rhs.y; return *this; }
    Vector2& operator-=(const Vector2& rhs) { x -= rhs.x; y -= rhs.y; return *this; }
    Vector2& operator*=(T scalar) { x *= scalar; y *= scalar; return *this; }
    Vector2& operator/=(T scalar) { x /= scalar; y /= scalar; return *this; }
    bool operator==(const Vector2& rhs) const { return x == rhs.x && y == rhs.y; }
    bool operator!=(const Vector2& rhs) const { return !(*this == rhs); }
    Vector2 operator-() const { return Vector2(-x, -y); }
};

using Vector2f = Vector2<float>;
using Vector2i = Vector2<int>;
using Vector2u = Vector2<unsigned int>;

template<typename T>
Vector2<T> operator*(T scalar, const Vector2<T>& vec) { return vec * scalar; }

// =============================================================================
// Color Type
// =============================================================================

struct Color {
    uint8_t r = 0;
    uint8_t g = 0;
    uint8_t b = 0;
    uint8_t a = 255;

    Color() = default;
    Color(uint8_t r_, uint8_t g_, uint8_t b_, uint8_t a_ = 255) : r(r_), g(g_), b(b_), a(a_) {}

    bool operator==(const Color& rhs) const { return r == rhs.r && g == rhs.g && b == rhs.b && a == rhs.a; }
    bool operator!=(const Color& rhs) const { return !(*this == rhs); }

    // Standard colors
    static const Color Black;
    static const Color White;
    static const Color Red;
    static const Color Green;
    static const Color Blue;
    static const Color Yellow;
    static const Color Magenta;
    static const Color Cyan;
    static const Color Transparent;
};

// Static color definitions (need to be in a .cpp file for real builds)
inline const Color Color::Black(0, 0, 0);
inline const Color Color::White(255, 255, 255);
inline const Color Color::Red(255, 0, 0);
inline const Color Color::Green(0, 255, 0);
inline const Color Color::Blue(0, 0, 255);
inline const Color Color::Yellow(255, 255, 0);
inline const Color Color::Magenta(255, 0, 255);
inline const Color Color::Cyan(0, 255, 255);
inline const Color Color::Transparent(0, 0, 0, 0);

// =============================================================================
// Rectangle Types
// =============================================================================

template<typename T>
struct Rect {
    T left = 0;
    T top = 0;
    T width = 0;
    T height = 0;

    Rect() = default;
    Rect(T left_, T top_, T width_, T height_) : left(left_), top(top_), width(width_), height(height_) {}
    Rect(const Vector2<T>& position, const Vector2<T>& size)
        : left(position.x), top(position.y), width(size.x), height(size.y) {}

    bool contains(T x, T y) const {
        return x >= left && x < left + width && y >= top && y < top + height;
    }
    bool contains(const Vector2<T>& point) const { return contains(point.x, point.y); }

    bool intersects(const Rect& other) const {
        return left < other.left + other.width && left + width > other.left &&
               top < other.top + other.height && top + height > other.top;
    }

    Vector2<T> getPosition() const { return Vector2<T>(left, top); }
    Vector2<T> getSize() const { return Vector2<T>(width, height); }
};

using FloatRect = Rect<float>;
using IntRect = Rect<int>;

// =============================================================================
// Time Types
// =============================================================================

class Time {
    int64_t microseconds_ = 0;
public:
    Time() = default;
    float asSeconds() const { return microseconds_ / 1000000.0f; }
    int32_t asMilliseconds() const { return static_cast<int32_t>(microseconds_ / 1000); }
    int64_t asMicroseconds() const { return microseconds_; }

    static Time Zero;

    friend Time seconds(float amount);
    friend Time milliseconds(int32_t amount);
    friend Time microseconds(int64_t amount);
};

inline Time Time::Zero;

inline Time seconds(float amount) { Time t; t.microseconds_ = static_cast<int64_t>(amount * 1000000); return t; }
inline Time milliseconds(int32_t amount) { Time t; t.microseconds_ = amount * 1000; return t; }
inline Time microseconds(int64_t amount) { Time t; t.microseconds_ = amount; return t; }

class Clock {
    int64_t start_time_ = 0;

    static int64_t now_microseconds() {
        // Use C++11 chrono for portable timing
        auto now = std::chrono::high_resolution_clock::now();
        auto duration = now.time_since_epoch();
        return std::chrono::duration_cast<std::chrono::microseconds>(duration).count();
    }
public:
    Clock() : start_time_(now_microseconds()) {}

    Time getElapsedTime() const {
        return microseconds(now_microseconds() - start_time_);
    }

    Time restart() {
        int64_t now = now_microseconds();
        int64_t elapsed = now - start_time_;
        start_time_ = now;
        return microseconds(elapsed);
    }
};

// =============================================================================
// Transform (minimal stub)
// =============================================================================

class Transform {
public:
    Transform() = default;
    Transform& translate(float x, float y) { return *this; }
    Transform& translate(const Vector2f& offset) { return translate(offset.x, offset.y); }
    Transform& rotate(float angle) { return *this; }
    Transform& rotate(float angle, const Vector2f& center) { return *this; }
    Transform& scale(float factorX, float factorY) { return *this; }
    Transform& scale(const Vector2f& factors) { return scale(factors.x, factors.y); }

    Vector2f transformPoint(float x, float y) const { return Vector2f(x, y); }
    Vector2f transformPoint(const Vector2f& point) const { return point; }
    FloatRect transformRect(const FloatRect& rect) const { return rect; }

    Transform getInverse() const { return Transform(); }

    Transform operator*(const Transform& rhs) const { return Transform(); }
    Vector2f operator*(const Vector2f& point) const { return point; }

    static const Transform Identity;
};

inline const Transform Transform::Identity;

// =============================================================================
// Vertex (for custom geometry)
// =============================================================================

struct Vertex {
    Vector2f position;
    Color color;
    Vector2f texCoords;

    Vertex() = default;
    Vertex(const Vector2f& pos) : position(pos), color(Color::White) {}
    Vertex(const Vector2f& pos, const Color& col) : position(pos), color(col) {}
    Vertex(const Vector2f& pos, const Vector2f& tex) : position(pos), color(Color::White), texCoords(tex) {}
    Vertex(const Vector2f& pos, const Color& col, const Vector2f& tex) : position(pos), color(col), texCoords(tex) {}
};

// =============================================================================
// View (camera)
// =============================================================================

class View {
    Vector2f center_;
    Vector2f size_;
    float rotation_ = 0.0f;
    FloatRect viewport_{0, 0, 1, 1};
public:
    View() : center_(0, 0), size_(1000, 1000) {}
    View(const FloatRect& rect) : center_(rect.left + rect.width/2, rect.top + rect.height/2), size_(rect.width, rect.height) {}
    View(const Vector2f& center, const Vector2f& size) : center_(center), size_(size) {}

    void setCenter(float x, float y) { center_ = Vector2f(x, y); }
    void setCenter(const Vector2f& center) { center_ = center; }
    void setSize(float width, float height) { size_ = Vector2f(width, height); }
    void setSize(const Vector2f& size) { size_ = size; }
    void setRotation(float angle) { rotation_ = angle; }
    void setViewport(const FloatRect& viewport) { viewport_ = viewport; }

    const Vector2f& getCenter() const { return center_; }
    const Vector2f& getSize() const { return size_; }
    float getRotation() const { return rotation_; }
    const FloatRect& getViewport() const { return viewport_; }

    void move(float offsetX, float offsetY) { center_.x += offsetX; center_.y += offsetY; }
    void move(const Vector2f& offset) { center_ += offset; }
    void rotate(float angle) { rotation_ += angle; }
    void zoom(float factor) { size_ *= factor; }

    Transform getTransform() const { return Transform::Identity; }
    Transform getInverseTransform() const { return Transform::Identity; }
};

// =============================================================================
// Rendering Stubs (no-op implementations)
// =============================================================================

enum PrimitiveType {
    Points,
    Lines,
    LineStrip,
    Triangles,
    TriangleStrip,
    TriangleFan,
    Quads  // Deprecated in SFML 3.0
};

// BlendMode stub
struct BlendMode {
    BlendMode() = default;
    static const BlendMode Alpha;
    static const BlendMode Add;
    static const BlendMode Multiply;
    static const BlendMode None;
};
inline const BlendMode BlendMode::Alpha{};
inline const BlendMode BlendMode::Add{};
inline const BlendMode BlendMode::Multiply{};
inline const BlendMode BlendMode::None{};

// Forward declare Shader for RenderStates
class Shader;

class RenderStates {
public:
    RenderStates() = default;
    RenderStates(const Transform& transform) {}  // Implicit conversion from Transform
    RenderStates(const BlendMode& mode) {}
    RenderStates(const Shader* shader) {}  // Implicit conversion from Shader pointer
    static const RenderStates Default;
};

inline const RenderStates RenderStates::Default;

// Forward declarations for rendering types
class RenderTarget;
class RenderTexture;
class RenderWindow;
class Texture;
class Font;
class Shader;

// Drawable base class (no-op)
class Drawable {
public:
    virtual ~Drawable() = default;
protected:
    friend class RenderTarget;
    virtual void draw(RenderTarget& target, RenderStates states) const = 0;
};

// Transformable base class
class Transformable {
protected:
    Vector2f position_;
    float rotation_ = 0.0f;
    Vector2f scale_{1.0f, 1.0f};
    Vector2f origin_;
public:
    virtual ~Transformable() = default;

    void setPosition(float x, float y) { position_ = Vector2f(x, y); }
    void setPosition(const Vector2f& position) { position_ = position; }
    void setRotation(float angle) { rotation_ = angle; }
    void setScale(float factorX, float factorY) { scale_ = Vector2f(factorX, factorY); }
    void setScale(const Vector2f& factors) { scale_ = factors; }
    void setOrigin(float x, float y) { origin_ = Vector2f(x, y); }
    void setOrigin(const Vector2f& origin) { origin_ = origin; }

    const Vector2f& getPosition() const { return position_; }
    float getRotation() const { return rotation_; }
    const Vector2f& getScale() const { return scale_; }
    const Vector2f& getOrigin() const { return origin_; }

    void move(float offsetX, float offsetY) { position_.x += offsetX; position_.y += offsetY; }
    void move(const Vector2f& offset) { position_ += offset; }
    void rotate(float angle) { rotation_ += angle; }
    void scale(float factorX, float factorY) { scale_.x *= factorX; scale_.y *= factorY; }
    void scale(const Vector2f& factor) { scale_.x *= factor.x; scale_.y *= factor.y; }

    Transform getTransform() const { return Transform::Identity; }
    Transform getInverseTransform() const { return Transform::Identity; }
};

// =============================================================================
// Shape Classes (stubs)
// =============================================================================

class Shape : public Drawable, public Transformable {
protected:
    Color fillColor_ = Color::White;
    Color outlineColor_ = Color::White;
    float outlineThickness_ = 0.0f;
public:
    void setFillColor(const Color& color) { fillColor_ = color; }
    void setOutlineColor(const Color& color) { outlineColor_ = color; }
    void setOutlineThickness(float thickness) { outlineThickness_ = thickness; }

    const Color& getFillColor() const { return fillColor_; }
    const Color& getOutlineColor() const { return outlineColor_; }
    float getOutlineThickness() const { return outlineThickness_; }

    virtual FloatRect getLocalBounds() const { return FloatRect(); }
    virtual FloatRect getGlobalBounds() const { return FloatRect(); }

protected:
    void draw(RenderTarget& target, RenderStates states) const override {}
};

class RectangleShape : public Shape {
    Vector2f size_;
public:
    RectangleShape(const Vector2f& size = Vector2f(0, 0)) : size_(size) {}
    void setSize(const Vector2f& size) { size_ = size; }
    const Vector2f& getSize() const { return size_; }
    FloatRect getLocalBounds() const override { return FloatRect(0, 0, size_.x, size_.y); }
    FloatRect getGlobalBounds() const override { return FloatRect(position_.x, position_.y, size_.x, size_.y); }
};

class CircleShape : public Shape {
    float radius_ = 0.0f;
    size_t pointCount_ = 30;
public:
    CircleShape(float radius = 0, size_t pointCount = 30) : radius_(radius), pointCount_(pointCount) {}
    void setRadius(float radius) { radius_ = radius; }
    float getRadius() const { return radius_; }
    void setPointCount(size_t count) { pointCount_ = count; }
    size_t getPointCount() const { return pointCount_; }
    FloatRect getLocalBounds() const override { return FloatRect(0, 0, radius_ * 2, radius_ * 2); }
};

class ConvexShape : public Shape {
    std::vector<Vector2f> points_;
public:
    ConvexShape(size_t pointCount = 0) : points_(pointCount) {}
    void setPointCount(size_t count) { points_.resize(count); }
    size_t getPointCount() const { return points_.size(); }
    void setPoint(size_t index, const Vector2f& point) { if (index < points_.size()) points_[index] = point; }
    Vector2f getPoint(size_t index) const { return index < points_.size() ? points_[index] : Vector2f(); }
};

// =============================================================================
// VertexArray
// =============================================================================

class VertexArray : public Drawable {
    std::vector<Vertex> vertices_;
    PrimitiveType primitiveType_ = Points;
public:
    VertexArray() = default;
    VertexArray(PrimitiveType type, size_t vertexCount = 0) : vertices_(vertexCount), primitiveType_(type) {}

    size_t getVertexCount() const { return vertices_.size(); }
    Vertex& operator[](size_t index) { return vertices_[index]; }
    const Vertex& operator[](size_t index) const { return vertices_[index]; }

    void clear() { vertices_.clear(); }
    void resize(size_t vertexCount) { vertices_.resize(vertexCount); }
    void append(const Vertex& vertex) { vertices_.push_back(vertex); }

    void setPrimitiveType(PrimitiveType type) { primitiveType_ = type; }
    PrimitiveType getPrimitiveType() const { return primitiveType_; }

    FloatRect getBounds() const { return FloatRect(); }

protected:
    void draw(RenderTarget& target, RenderStates states) const override {}
};

// =============================================================================
// Texture (stub)
// =============================================================================

// Image (stub) - defined before Texture since Texture::copyToImage returns it
class Image {
    Vector2u size_;
    std::vector<Uint8> pixels_;
public:
    Image() = default;

    void create(unsigned int width, unsigned int height, const Color& color = Color::Black) {
        size_ = Vector2u(width, height);
        pixels_.resize(width * height * 4, 0);
    }

    bool loadFromFile(const std::string& filename) { return false; }
    bool saveToFile(const std::string& filename) const { return false; }

    Vector2u getSize() const { return size_; }

    void setPixel(unsigned int x, unsigned int y, const Color& color) {
        if (x < size_.x && y < size_.y) {
            size_t idx = (y * size_.x + x) * 4;
            pixels_[idx] = color.r;
            pixels_[idx + 1] = color.g;
            pixels_[idx + 2] = color.b;
            pixels_[idx + 3] = color.a;
        }
    }

    Color getPixel(unsigned int x, unsigned int y) const {
        if (x < size_.x && y < size_.y) {
            size_t idx = (y * size_.x + x) * 4;
            return Color(pixels_[idx], pixels_[idx + 1], pixels_[idx + 2], pixels_[idx + 3]);
        }
        return Color::Black;
    }

    const Uint8* getPixelsPtr() const { return pixels_.data(); }
};

// Forward declare RenderWindow for Texture::update
class RenderWindow;

class Texture {
    Vector2u size_;
public:
    Texture() = default;
    bool create(unsigned int width, unsigned int height) { size_ = Vector2u(width, height); return true; }
    // In headless mode, pretend texture loading succeeded with dummy dimensions
    // This allows game scripts to run without actual graphics
    bool loadFromFile(const std::string& filename) {
        size_ = Vector2u(256, 256);  // Default size for headless textures
        return true;
    }
    bool loadFromMemory(const void* data, size_t size) {
        size_ = Vector2u(256, 256);
        return true;
    }
    Vector2u getSize() const { return size_; }
    void setSmooth(bool smooth) {}
    bool isSmooth() const { return false; }
    void setRepeated(bool repeated) {}
    bool isRepeated() const { return false; }
    Image copyToImage() const { Image img; img.create(size_.x, size_.y); return img; }
    void update(const RenderWindow& window) {}
    void update(const Uint8* pixels) {}
    void update(const Uint8* pixels, unsigned int width, unsigned int height, unsigned int x, unsigned int y) {}
};

// =============================================================================
// Sprite (stub)
// =============================================================================

class Sprite : public Drawable, public Transformable {
    const Texture* texture_ = nullptr;
    IntRect textureRect_;
    Color color_ = Color::White;
public:
    Sprite() = default;
    Sprite(const Texture& texture) : texture_(&texture) {}
    Sprite(const Texture& texture, const IntRect& rectangle) : texture_(&texture), textureRect_(rectangle) {}

    void setTexture(const Texture& texture, bool resetRect = false) { texture_ = &texture; }
    void setTextureRect(const IntRect& rectangle) { textureRect_ = rectangle; }
    void setColor(const Color& color) { color_ = color; }

    const Texture* getTexture() const { return texture_; }
    const IntRect& getTextureRect() const { return textureRect_; }
    const Color& getColor() const { return color_; }

    FloatRect getLocalBounds() const { return FloatRect(0, 0, static_cast<float>(textureRect_.width), static_cast<float>(textureRect_.height)); }
    FloatRect getGlobalBounds() const { return FloatRect(position_.x, position_.y, static_cast<float>(textureRect_.width), static_cast<float>(textureRect_.height)); }

protected:
    void draw(RenderTarget& target, RenderStates states) const override {}
};

// =============================================================================
// Text and Font (stubs)
// =============================================================================

class Font {
public:
    struct Info {
        std::string family;
    };

    Font() = default;
    // In headless mode, pretend font loading succeeded
    bool loadFromFile(const std::string& filename) { return true; }
    bool loadFromMemory(const void* data, size_t sizeInBytes) { return true; }
    const Info& getInfo() const { static Info info; return info; }
};

class Text : public Drawable, public Transformable {
    std::string string_;
    const Font* font_ = nullptr;
    unsigned int characterSize_ = 30;
    Color fillColor_ = Color::White;
    Color outlineColor_ = Color::Black;
    float outlineThickness_ = 0.0f;
    uint32_t style_ = 0;
public:
    enum Style { Regular = 0, Bold = 1, Italic = 2, Underlined = 4, StrikeThrough = 8 };

    Text() = default;
    Text(const std::string& string, const Font& font, unsigned int characterSize = 30)
        : string_(string), font_(&font), characterSize_(characterSize) {}

    void setString(const std::string& string) { string_ = string; }
    void setFont(const Font& font) { font_ = &font; }
    void setCharacterSize(unsigned int size) { characterSize_ = size; }
    void setStyle(uint32_t style) { style_ = style; }
    void setFillColor(const Color& color) { fillColor_ = color; }
    void setOutlineColor(const Color& color) { outlineColor_ = color; }
    void setOutlineThickness(float thickness) { outlineThickness_ = thickness; }

    const std::string& getString() const { return string_; }
    const Font* getFont() const { return font_; }
    unsigned int getCharacterSize() const { return characterSize_; }
    uint32_t getStyle() const { return style_; }
    const Color& getFillColor() const { return fillColor_; }
    const Color& getOutlineColor() const { return outlineColor_; }
    float getOutlineThickness() const { return outlineThickness_; }

    FloatRect getLocalBounds() const { return FloatRect(); }
    FloatRect getGlobalBounds() const { return FloatRect(); }

protected:
    void draw(RenderTarget& target, RenderStates states) const override {}
};

// =============================================================================
// RenderTarget (base class for rendering)
// =============================================================================

class RenderTarget {
protected:
    Vector2u size_;
    View view_;
    View defaultView_;
public:
    virtual ~RenderTarget() = default;

    virtual Vector2u getSize() const { return size_; }
    virtual void clear(const Color& color = Color::Black) {}

    void draw(const Drawable& drawable, const RenderStates& states = RenderStates::Default) {
        drawable.draw(*this, states);
    }
    void draw(const Vertex* vertices, size_t vertexCount, PrimitiveType type, const RenderStates& states = RenderStates::Default) {}
    void draw(const VertexArray& vertices, const RenderStates& states = RenderStates::Default) {}

    void setView(const View& view) { view_ = view; }
    const View& getView() const { return view_; }
    const View& getDefaultView() const { return defaultView_; }

    IntRect getViewport(const View& view) const { return IntRect(0, 0, size_.x, size_.y); }

    Vector2f mapPixelToCoords(const Vector2i& point) const { return Vector2f(static_cast<float>(point.x), static_cast<float>(point.y)); }
    Vector2f mapPixelToCoords(const Vector2i& point, const View& view) const { return Vector2f(static_cast<float>(point.x), static_cast<float>(point.y)); }
    Vector2i mapCoordsToPixel(const Vector2f& point) const { return Vector2i(static_cast<int>(point.x), static_cast<int>(point.y)); }
    Vector2i mapCoordsToPixel(const Vector2f& point, const View& view) const { return Vector2i(static_cast<int>(point.x), static_cast<int>(point.y)); }
};

// =============================================================================
// RenderTexture
// =============================================================================

class RenderTexture : public RenderTarget {
    Texture texture_;
public:
    RenderTexture() = default;
    bool create(unsigned int width, unsigned int height) {
        size_ = Vector2u(width, height);
        texture_.create(width, height);
        view_ = View(FloatRect(0, 0, static_cast<float>(width), static_cast<float>(height)));
        defaultView_ = view_;
        return true;
    }

    void clear(const Color& color = Color::Black) override {}
    void display() {}

    const Texture& getTexture() const { return texture_; }
    void setSmooth(bool smooth) {}
    bool isSmooth() const { return false; }
};

// =============================================================================
// RenderWindow (stub - window operations are no-ops)
// =============================================================================

namespace Style {
    enum {
        None = 0,
        Titlebar = 1 << 0,
        Resize = 1 << 1,
        Close = 1 << 2,
        Fullscreen = 1 << 3,
        Default = Titlebar | Resize | Close
    };
}

class VideoMode {
public:
    unsigned int width = 0;
    unsigned int height = 0;
    unsigned int bitsPerPixel = 32;

    VideoMode() = default;
    VideoMode(unsigned int w, unsigned int h, unsigned int bpp = 32) : width(w), height(h), bitsPerPixel(bpp) {}

    static VideoMode getDesktopMode() { return VideoMode(1920, 1080, 32); }
    static const std::vector<VideoMode>& getFullscreenModes() {
        static std::vector<VideoMode> modes = {VideoMode(1920, 1080), VideoMode(1280, 720)};
        return modes;
    }
};

class RenderWindow : public RenderTarget {
    bool open_ = false;
    std::string title_;
public:
    RenderWindow() = default;
    RenderWindow(VideoMode mode, const std::string& title, uint32_t style = Style::Default) {
        create(mode, title, style);
    }

    void create(VideoMode mode, const std::string& title, uint32_t style = Style::Default) {
        size_ = Vector2u(mode.width, mode.height);
        title_ = title;
        open_ = true;
        view_ = View(FloatRect(0, 0, static_cast<float>(mode.width), static_cast<float>(mode.height)));
        defaultView_ = view_;
    }

    void close() { open_ = false; }
    bool isOpen() const { return open_; }

    void clear(const Color& color = Color::Black) override {}
    void display() {}

    void setTitle(const std::string& title) { title_ = title; }
    void setFramerateLimit(unsigned int limit) {}
    void setVerticalSyncEnabled(bool enabled) {}
    void setVisible(bool visible) {}
    void setMouseCursorVisible(bool visible) {}
    void setMouseCursorGrabbed(bool grabbed) {}
    void setKeyRepeatEnabled(bool enabled) {}

    Vector2i getPosition() const { return Vector2i(0, 0); }
    void setPosition(const Vector2i& position) {}
    Vector2u getSize() const override { return size_; }
    void setSize(const Vector2u& size) { size_ = size; }

    bool pollEvent(Event& event) { return false; }
    bool waitEvent(Event& event) { return false; }
};

// =============================================================================
// Audio Stubs
// =============================================================================

class SoundBuffer {
public:
    SoundBuffer() = default;
    // In headless mode, pretend sound loading succeeded
    bool loadFromFile(const std::string& filename) { return true; }
    bool loadFromMemory(const void* data, size_t sizeInBytes) { return true; }
    Time getDuration() const { return Time(); }
};

class Sound {
public:
    enum Status { Stopped, Paused, Playing };

    Sound() = default;
    Sound(const SoundBuffer& buffer) {}

    void setBuffer(const SoundBuffer& buffer) {}
    void play() {}
    void pause() {}
    void stop() {}

    Status getStatus() const { return Stopped; }
    void setVolume(float volume) {}
    float getVolume() const { return 100.0f; }
    void setLoop(bool loop) {}
    bool getLoop() const { return false; }
};

class Music {
public:
    enum Status { Stopped, Paused, Playing };

    Music() = default;
    // In headless mode, pretend music loading succeeded
    bool openFromFile(const std::string& filename) { return true; }

    void play() {}
    void pause() {}
    void stop() {}

    Status getStatus() const { return Stopped; }
    void setVolume(float volume) {}
    float getVolume() const { return 100.0f; }
    void setLoop(bool loop) {}
    bool getLoop() const { return false; }
    Time getDuration() const { return Time(); }
    Time getPlayingOffset() const { return Time(); }
    void setPlayingOffset(Time offset) {}
};

// =============================================================================
// Input Stubs (Keyboard and Mouse)
// =============================================================================

class Keyboard {
public:
    enum Key {
        Unknown = -1,
        A = 0, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P, Q, R, S, T, U, V, W, X, Y, Z,
        Num0, Num1, Num2, Num3, Num4, Num5, Num6, Num7, Num8, Num9,
        Escape, LControl, LShift, LAlt, LSystem, RControl, RShift, RAlt, RSystem,
        Menu, LBracket, RBracket, Semicolon, Comma, Period, Apostrophe, Slash, Backslash,
        Grave, Equal, Hyphen, Space, Enter, Backspace, Tab, PageUp, PageDown, End, Home,
        Insert, Delete, Add, Subtract, Multiply, Divide,
        Left, Right, Up, Down,
        Numpad0, Numpad1, Numpad2, Numpad3, Numpad4, Numpad5, Numpad6, Numpad7, Numpad8, Numpad9,
        F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, F11, F12, F13, F14, F15,
        Pause,
        KeyCount,
        // Deprecated aliases (SFML 2.x compatibility)
        Tilde = Grave,
        Quote = Apostrophe,
        BackSpace = Backspace,
        BackSlash = Backslash,
        SemiColon = Semicolon,
        Dash = Hyphen
    };

    static bool isKeyPressed(Key key) { return false; }
};

class Mouse {
public:
    enum Button { Left, Right, Middle, XButton1, XButton2, ButtonCount };
    enum Wheel { VerticalWheel, HorizontalWheel };

    static bool isButtonPressed(Button button) { return false; }
    static Vector2i getPosition() { return Vector2i(0, 0); }
    static Vector2i getPosition(const RenderWindow& relativeTo) { return Vector2i(0, 0); }
    static void setPosition(const Vector2i& position) {}
    static void setPosition(const Vector2i& position, const RenderWindow& relativeTo) {}
};

// =============================================================================
// Event System (stub)
// =============================================================================

struct Event {
    enum EventType {
        Closed,
        Resized,
        LostFocus,
        GainedFocus,
        TextEntered,
        KeyPressed,
        KeyReleased,
        MouseWheelMoved,      // Deprecated
        MouseWheelScrolled,
        MouseButtonPressed,
        MouseButtonReleased,
        MouseMoved,
        MouseEntered,
        MouseLeft,
        Count
    };

    struct SizeEvent { unsigned int width, height; };
    struct KeyEvent { Keyboard::Key code; bool alt, control, shift, system; };
    struct TextEvent { uint32_t unicode; };
    struct MouseMoveEvent { int x, y; };
    struct MouseButtonEvent { Mouse::Button button; int x, y; };
    struct MouseWheelScrollEvent { Mouse::Wheel wheel; float delta; int x, y; };

    EventType type;
    union {
        SizeEvent size;
        KeyEvent key;
        TextEvent text;
        MouseMoveEvent mouseMove;
        MouseButtonEvent mouseButton;
        MouseWheelScrollEvent mouseWheelScroll;
    };
};

// =============================================================================
// Shader (minimal stub)
// =============================================================================

// =============================================================================
// GLSL Types (for shader uniforms) - must be before Shader
// =============================================================================

namespace Glsl {
    using Vec2 = Vector2f;

    struct Vec3 {
        float x = 0, y = 0, z = 0;
        Vec3() = default;
        Vec3(float x_, float y_, float z_) : x(x_), y(y_), z(z_) {}
    };

    struct Vec4 {
        float x = 0, y = 0, z = 0, w = 0;
        Vec4() = default;
        Vec4(float x_, float y_, float z_, float w_) : x(x_), y(y_), z(z_), w(w_) {}
        Vec4(const Color& c) : x(c.r/255.f), y(c.g/255.f), z(c.b/255.f), w(c.a/255.f) {}
    };
} // namespace Glsl

// Forward declaration for CurrentTexture
struct CurrentTextureType {};

class Shader {
public:
    enum Type { Vertex, Geometry, Fragment };
    static const CurrentTextureType CurrentTexture;

    Shader() = default;
    bool loadFromFile(const std::string& filename, Type type) { return false; }
    bool loadFromFile(const std::string& vertexFile, const std::string& fragmentFile) { return false; }
    bool loadFromMemory(const std::string& shader, Type type) { return false; }

    void setUniform(const std::string& name, float x) {}
    void setUniform(const std::string& name, const Vector2f& v) {}
    void setUniform(const std::string& name, const Color& color) {}
    void setUniform(const std::string& name, const Texture& texture) {}
    void setUniform(const std::string& name, const Glsl::Vec3& v) {}
    void setUniform(const std::string& name, const Glsl::Vec4& v) {}
    void setUniform(const std::string& name, CurrentTextureType) {}

    static bool isAvailable() { return false; }
};

inline const CurrentTextureType Shader::CurrentTexture{};

// =============================================================================
// Error stream (stub)
// =============================================================================

#include <ostream>

inline std::ostream& err() {
    static std::stringstream dummy;
    return dummy;
}

} // namespace sf
