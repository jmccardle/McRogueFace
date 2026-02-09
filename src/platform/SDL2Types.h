// SDL2Types.h - SFML type stubs for SDL2 + OpenGL ES 2 backend
// This file provides type definitions that compile against SDL2 instead of SFML,
// enabling cross-platform builds for Web (Emscripten/WebGL), Android, and desktop.
//
// Part of the renderer abstraction layer (issue #158 continuation)
//
// Architecture:
// - Game code uses sf:: namespace types (unchanged from SFML builds)
// - This header provides sf:: types implemented using SDL2 + OpenGL ES 2
// - Compile-time selection via MCRF_SDL2 define
//
// Phases:
// - Phase 1: Skeleton (stubs matching HeadlessTypes.h)
// - Phase 2: Window + GL context
// - Phase 3: Shape rendering (rectangles, circles)
// - Phase 4: Texture + Sprites
// - Phase 5: Text rendering
// - Phase 6: RenderTexture (FBO)
// - Phase 7: Custom shaders

#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <chrono>
#include <algorithm>

// SDL2 headers - conditionally included when actually implementing
// For now, forward declare what we need
#ifdef MCRF_SDL2_IMPL
#include <SDL2/SDL.h>
#include <GLES2/gl2.h>
#endif

// SDL2_mixer for audio (always needed in SDL2 builds for SoundBuffer/Sound/Music types)
#ifdef __EMSCRIPTEN__
#include <SDL_mixer.h>
#else
#include <SDL2/SDL_mixer.h>
#endif

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

// Static color definitions
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
// Transform
// =============================================================================
// SDL2 backend will implement actual matrix math for transforms
// For now, stub implementation matching headless

class Transform {
    // 3x3 matrix stored as column-major for OpenGL
    // [ a c tx ]     [ m[0] m[3] m[6] ]
    // [ b d ty ] ->  [ m[1] m[4] m[7] ]
    // [ 0 0 1  ]     [ m[2] m[5] m[8] ]
    float m[9] = {1,0,0, 0,1,0, 0,0,1};

public:
    Transform() = default;

    Transform& translate(float x, float y) {
        // Combine with translation matrix
        m[6] += m[0] * x + m[3] * y;
        m[7] += m[1] * x + m[4] * y;
        return *this;
    }
    Transform& translate(const Vector2f& offset) { return translate(offset.x, offset.y); }

    Transform& rotate(float angle) {
        float rad = angle * 3.14159265f / 180.0f;
        float cos_a = std::cos(rad);
        float sin_a = std::sin(rad);

        float new_m0 = m[0] * cos_a + m[3] * sin_a;
        float new_m1 = m[1] * cos_a + m[4] * sin_a;
        float new_m3 = m[0] * -sin_a + m[3] * cos_a;
        float new_m4 = m[1] * -sin_a + m[4] * cos_a;

        m[0] = new_m0; m[1] = new_m1;
        m[3] = new_m3; m[4] = new_m4;
        return *this;
    }
    Transform& rotate(float angle, const Vector2f& center) {
        translate(center.x, center.y);
        rotate(angle);
        translate(-center.x, -center.y);
        return *this;
    }

    Transform& scale(float factorX, float factorY) {
        m[0] *= factorX; m[1] *= factorX;
        m[3] *= factorY; m[4] *= factorY;
        return *this;
    }
    Transform& scale(const Vector2f& factors) { return scale(factors.x, factors.y); }

    Vector2f transformPoint(float x, float y) const {
        return Vector2f(m[0] * x + m[3] * y + m[6],
                        m[1] * x + m[4] * y + m[7]);
    }
    Vector2f transformPoint(const Vector2f& point) const {
        return transformPoint(point.x, point.y);
    }

    FloatRect transformRect(const FloatRect& rect) const {
        // Transform all four corners and compute bounding box
        Vector2f p1 = transformPoint(rect.left, rect.top);
        Vector2f p2 = transformPoint(rect.left + rect.width, rect.top);
        Vector2f p3 = transformPoint(rect.left, rect.top + rect.height);
        Vector2f p4 = transformPoint(rect.left + rect.width, rect.top + rect.height);

        float minX = std::min({p1.x, p2.x, p3.x, p4.x});
        float maxX = std::max({p1.x, p2.x, p3.x, p4.x});
        float minY = std::min({p1.y, p2.y, p3.y, p4.y});
        float maxY = std::max({p1.y, p2.y, p3.y, p4.y});

        return FloatRect(minX, minY, maxX - minX, maxY - minY);
    }

    Transform getInverse() const {
        // Compute inverse of 3x3 affine matrix
        float det = m[0] * m[4] - m[1] * m[3];
        if (std::abs(det) < 1e-7f) return Transform();

        float invDet = 1.0f / det;
        Transform inv;
        inv.m[0] = m[4] * invDet;
        inv.m[1] = -m[1] * invDet;
        inv.m[3] = -m[3] * invDet;
        inv.m[4] = m[0] * invDet;
        inv.m[6] = (m[3] * m[7] - m[4] * m[6]) * invDet;
        inv.m[7] = (m[1] * m[6] - m[0] * m[7]) * invDet;
        return inv;
    }

    Transform operator*(const Transform& rhs) const {
        Transform result;
        result.m[0] = m[0] * rhs.m[0] + m[3] * rhs.m[1];
        result.m[1] = m[1] * rhs.m[0] + m[4] * rhs.m[1];
        result.m[3] = m[0] * rhs.m[3] + m[3] * rhs.m[4];
        result.m[4] = m[1] * rhs.m[3] + m[4] * rhs.m[4];
        result.m[6] = m[0] * rhs.m[6] + m[3] * rhs.m[7] + m[6];
        result.m[7] = m[1] * rhs.m[6] + m[4] * rhs.m[7] + m[7];
        return result;
    }
    Vector2f operator*(const Vector2f& point) const { return transformPoint(point); }

    static const Transform Identity;

    // SDL2-specific: Get raw matrix for OpenGL
    const float* getMatrix() const { return m; }
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

    Transform getTransform() const {
        // View transform: translates world coords to view coords (NDC)
        // Order: Scale to NDC, then Rotate, then Translate center to origin
        Transform t;
        t.translate(-center_.x, -center_.y);  // Move center to origin
        t.rotate(-rotation_);                  // Rotate around origin (negative for view)
        t.scale(2.0f / size_.x, 2.0f / size_.y);  // Scale to NDC [-1,1]
        return t;
    }

    Transform getInverseTransform() const {
        return getTransform().getInverse();
    }
};

// =============================================================================
// Rendering Types
// =============================================================================

enum PrimitiveType {
    Points,
    Lines,
    LineStrip,
    Triangles,
    TriangleStrip,
    TriangleFan,
    Quads  // Deprecated in SFML 3.0, but we'll support it via triangulation
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
    Transform transform;
    BlendMode blendMode;
    const Shader* shader = nullptr;

    RenderStates() = default;
    RenderStates(const Transform& t) : transform(t) {}
    RenderStates(const BlendMode& mode) : blendMode(mode) {}
    RenderStates(const Shader* s) : shader(s) {}
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

// Drawable base class
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

    Transform getTransform() const {
        Transform transform;
        // Apply transformations: translate to position, rotate, scale, translate by -origin
        transform.translate(position_.x, position_.y);
        transform.rotate(rotation_);
        transform.scale(scale_.x, scale_.y);
        transform.translate(-origin_.x, -origin_.y);
        return transform;
    }
    Transform getInverseTransform() const {
        return getTransform().getInverse();
    }
};

// =============================================================================
// Shape Classes
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

    // Virtual methods for shape points (implemented by derived classes)
    virtual size_t getPointCount() const = 0;
    virtual Vector2f getPoint(size_t index) const = 0;

protected:
    void draw(RenderTarget& target, RenderStates states) const override;  // Implemented in SDL2Renderer.cpp
};

class RectangleShape : public Shape {
    Vector2f size_;
public:
    RectangleShape(const Vector2f& size = Vector2f(0, 0)) : size_(size) {}
    void setSize(const Vector2f& size) { size_ = size; }
    const Vector2f& getSize() const { return size_; }
    FloatRect getLocalBounds() const override { return FloatRect(0, 0, size_.x, size_.y); }
    FloatRect getGlobalBounds() const override { return FloatRect(position_.x, position_.y, size_.x, size_.y); }

    size_t getPointCount() const override { return 4; }
    Vector2f getPoint(size_t index) const override {
        switch (index) {
            case 0: return Vector2f(0, 0);
            case 1: return Vector2f(size_.x, 0);
            case 2: return Vector2f(size_.x, size_.y);
            case 3: return Vector2f(0, size_.y);
            default: return Vector2f();
        }
    }
};

class CircleShape : public Shape {
    float radius_ = 0.0f;
    size_t pointCount_ = 30;
public:
    CircleShape(float radius = 0, size_t pointCount = 30) : radius_(radius), pointCount_(pointCount) {}
    void setRadius(float radius) { radius_ = radius; }
    float getRadius() const { return radius_; }
    void setPointCount(size_t count) { pointCount_ = count; }
    size_t getPointCount() const override { return pointCount_; }
    FloatRect getLocalBounds() const override { return FloatRect(0, 0, radius_ * 2, radius_ * 2); }

    Vector2f getPoint(size_t index) const override {
        float angle = static_cast<float>(index) / pointCount_ * 2.0f * 3.14159265f;
        return Vector2f(radius_ + radius_ * std::cos(angle), radius_ + radius_ * std::sin(angle));
    }
};

class ConvexShape : public Shape {
    std::vector<Vector2f> points_;
public:
    ConvexShape(size_t pointCount = 0) : points_(pointCount) {}
    void setPointCount(size_t count) { points_.resize(count); }
    size_t getPointCount() const override { return points_.size(); }
    void setPoint(size_t index, const Vector2f& point) { if (index < points_.size()) points_[index] = point; }
    Vector2f getPoint(size_t index) const override { return index < points_.size() ? points_[index] : Vector2f(); }
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

    FloatRect getBounds() const { return FloatRect(); }  // TODO: Implement

protected:
    void draw(RenderTarget& target, RenderStates states) const override;  // Implemented in SDL2Renderer.cpp
};

// =============================================================================
// Image
// =============================================================================

class Image {
    Vector2u size_;
    std::vector<Uint8> pixels_;
public:
    Image() = default;

    void create(unsigned int width, unsigned int height, const Color& color = Color::Black) {
        size_ = Vector2u(width, height);
        pixels_.resize(width * height * 4, 0);
        // Fill with color
        for (unsigned int y = 0; y < height; ++y) {
            for (unsigned int x = 0; x < width; ++x) {
                setPixel(x, y, color);
            }
        }
    }

    bool loadFromFile(const std::string& filename);  // Implemented in SDL2Renderer.cpp (uses stb_image)
    bool saveToFile(const std::string& filename) const;  // Implemented in SDL2Renderer.cpp (uses stb_image_write)

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

    // SDL2-specific: Allow direct pixel access for texture upload
    Uint8* getPixelsPtr() { return pixels_.data(); }
    void setSize(unsigned int w, unsigned int h) { size_ = Vector2u(w, h); pixels_.resize(w * h * 4); }
};

// =============================================================================
// Texture
// =============================================================================

// Forward declare RenderWindow for Texture::update
class RenderWindow;

class Texture {
    Vector2u size_;
    // SDL2-specific: OpenGL texture handle (0 = not created)
    unsigned int textureId_ = 0;
    bool smooth_ = false;
    bool repeated_ = false;
    bool flippedY_ = false;  // True for RenderTexture (FBO) textures

public:
    Texture() = default;
    ~Texture();  // Implemented in SDL2Renderer.cpp (deletes GL texture)

    // Copy constructor/assignment - needed for proper GL resource management
    Texture(const Texture& other);
    Texture& operator=(const Texture& other);

    bool create(unsigned int width, unsigned int height);  // Implemented in SDL2Renderer.cpp
    bool loadFromFile(const std::string& filename);  // Implemented in SDL2Renderer.cpp
    bool loadFromMemory(const void* data, size_t size);  // Implemented in SDL2Renderer.cpp
    bool loadFromImage(const Image& image);  // Implemented in SDL2Renderer.cpp

    Vector2u getSize() const { return size_; }
    void setSize(unsigned int width, unsigned int height) { size_ = Vector2u(width, height); }
    void setFlippedY(bool flipped) { flippedY_ = flipped; }
    bool isFlippedY() const { return flippedY_; }
    void setSmooth(bool smooth);  // Implemented in SDL2Renderer.cpp
    bool isSmooth() const { return smooth_; }
    void setRepeated(bool repeated);  // Implemented in SDL2Renderer.cpp
    bool isRepeated() const { return repeated_; }

    Image copyToImage() const;  // Implemented in SDL2Renderer.cpp
    void update(const RenderWindow& window);  // Implemented in SDL2Renderer.cpp
    void update(const Uint8* pixels);  // Implemented in SDL2Renderer.cpp
    void update(const Uint8* pixels, unsigned int width, unsigned int height, unsigned int x, unsigned int y);

    // SDL2-specific: Get GL texture handle
    unsigned int getNativeHandle() const { return textureId_; }
    void setNativeHandle(unsigned int id) { textureId_ = id; }
};

// =============================================================================
// Sprite
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
    void draw(RenderTarget& target, RenderStates states) const override;  // Implemented in SDL2Renderer.cpp
};

// =============================================================================
// Text and Font
// =============================================================================

class Font {
    // SDL2-specific: font data for FreeType
    std::vector<unsigned char> fontData_;
    bool loaded_ = false;

    // FreeType handles (void* to avoid header dependency in .h)
    void* ftLibrary_ = nullptr;   // FT_Library
    void* ftFace_ = nullptr;      // FT_Face
    void* ftStroker_ = nullptr;   // FT_Stroker

public:
    struct Info {
        std::string family;
    };

    Font() = default;
    ~Font();  // Destructor for FreeType cleanup - implemented in SDL2Renderer.cpp
    bool loadFromFile(const std::string& filename);  // Implemented in SDL2Renderer.cpp
    bool loadFromMemory(const void* data, size_t sizeInBytes);  // Implemented in SDL2Renderer.cpp
    const Info& getInfo() const { static Info info; return info; }

    // SDL2-specific: Access font data
    const unsigned char* getData() const { return fontData_.data(); }
    size_t getDataSize() const { return fontData_.size(); }
    bool isLoaded() const { return loaded_; }

    // FreeType accessors
    void* getFTFace() const { return ftFace_; }
    void* getFTStroker() const { return ftStroker_; }
    void* getFTLibrary() const { return ftLibrary_; }
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

    FloatRect getLocalBounds() const;  // Implemented in SDL2Renderer.cpp
    FloatRect getGlobalBounds() const;  // Implemented in SDL2Renderer.cpp

protected:
    void draw(RenderTarget& target, RenderStates states) const override;  // Implemented in SDL2Renderer.cpp
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
    virtual void clear(const Color& color = Color::Black);  // Implemented in SDL2Renderer.cpp

    void draw(const Drawable& drawable, const RenderStates& states = RenderStates::Default) {
        drawable.draw(*this, states);
    }
    void draw(const Vertex* vertices, size_t vertexCount, PrimitiveType type, const RenderStates& states = RenderStates::Default);
    void draw(const VertexArray& vertices, const RenderStates& states = RenderStates::Default);

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
// RenderTexture (Framebuffer Object)
// =============================================================================

class RenderTexture : public RenderTarget {
    Texture texture_;
    unsigned int fboId_ = 0;  // OpenGL FBO handle
public:
    RenderTexture() = default;
    ~RenderTexture();  // Implemented in SDL2Renderer.cpp

    bool create(unsigned int width, unsigned int height);  // Implemented in SDL2Renderer.cpp

    void clear(const Color& color = Color::Black) override;  // Implemented in SDL2Renderer.cpp
    void display();  // Implemented in SDL2Renderer.cpp

    const Texture& getTexture() const { return texture_; }
    void setSmooth(bool smooth) { texture_.setSmooth(smooth); }
    bool isSmooth() const { return texture_.isSmooth(); }

    // SDL2-specific: Get FBO handle
    unsigned int getNativeHandle() const { return fboId_; }
};

// =============================================================================
// RenderWindow
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

    static VideoMode getDesktopMode();  // Implemented in SDL2Renderer.cpp
    static const std::vector<VideoMode>& getFullscreenModes();  // Implemented in SDL2Renderer.cpp
};

class RenderWindow : public RenderTarget {
    bool open_ = false;
    std::string title_;

    // SDL2-specific handles (void* to avoid SDL header dependency)
    void* sdlWindow_ = nullptr;
    void* glContext_ = nullptr;

public:
    RenderWindow() = default;
    RenderWindow(VideoMode mode, const std::string& title, uint32_t style = Style::Default) {
        create(mode, title, style);
    }
    ~RenderWindow();  // Implemented in SDL2Renderer.cpp

    void create(VideoMode mode, const std::string& title, uint32_t style = Style::Default);  // Implemented in SDL2Renderer.cpp

    void close();  // Implemented in SDL2Renderer.cpp
    bool isOpen() const { return open_; }

    void clear(const Color& color = Color::Black) override;  // Implemented in SDL2Renderer.cpp
    void display();  // Implemented in SDL2Renderer.cpp

    void setTitle(const std::string& title);  // Implemented in SDL2Renderer.cpp
    void setFramerateLimit(unsigned int limit);  // Implemented in SDL2Renderer.cpp
    void setVerticalSyncEnabled(bool enabled);  // Implemented in SDL2Renderer.cpp
    void setVisible(bool visible);  // Implemented in SDL2Renderer.cpp
    void setMouseCursorVisible(bool visible);  // Implemented in SDL2Renderer.cpp
    void setMouseCursorGrabbed(bool grabbed);  // Implemented in SDL2Renderer.cpp
    void setKeyRepeatEnabled(bool enabled) {}  // No-op for now

    Vector2i getPosition() const;  // Implemented in SDL2Renderer.cpp
    void setPosition(const Vector2i& position);  // Implemented in SDL2Renderer.cpp
    Vector2u getSize() const override { return size_; }
    void setSize(const Vector2u& size);  // Implemented in SDL2Renderer.cpp

    bool pollEvent(Event& event);  // Implemented in SDL2Renderer.cpp
    bool waitEvent(Event& event);  // Implemented in SDL2Renderer.cpp

    // SDL2-specific: Access native handles
    void* getNativeWindowHandle() const { return sdlWindow_; }
    void* getGLContext() const { return glContext_; }
};

// =============================================================================
// Audio (SDL2_mixer backed)
// =============================================================================

class SoundBuffer {
    Mix_Chunk* chunk_ = nullptr;
    Time duration_;

public:
    SoundBuffer() = default;
    ~SoundBuffer() {
        if (chunk_) {
            Mix_FreeChunk(chunk_);
            chunk_ = nullptr;
        }
    }

    // No copy (Mix_Chunk ownership)
    SoundBuffer(const SoundBuffer&) = delete;
    SoundBuffer& operator=(const SoundBuffer&) = delete;

    // Move
    SoundBuffer(SoundBuffer&& other) noexcept
        : chunk_(other.chunk_), duration_(other.duration_) {
        other.chunk_ = nullptr;
    }
    SoundBuffer& operator=(SoundBuffer&& other) noexcept {
        if (this != &other) {
            if (chunk_) Mix_FreeChunk(chunk_);
            chunk_ = other.chunk_;
            duration_ = other.duration_;
            other.chunk_ = nullptr;
        }
        return *this;
    }

    bool loadFromFile(const std::string& filename) {
        if (chunk_) { Mix_FreeChunk(chunk_); chunk_ = nullptr; }
        chunk_ = Mix_LoadWAV(filename.c_str());
        if (!chunk_) return false;
        computeDuration();
        return true;
    }

    bool loadFromMemory(const void* data, size_t sizeInBytes) {
        if (chunk_) { Mix_FreeChunk(chunk_); chunk_ = nullptr; }
        SDL_RWops* rw = SDL_RWFromConstMem(data, static_cast<int>(sizeInBytes));
        if (!rw) return false;
        chunk_ = Mix_LoadWAV_RW(rw, 1);  // 1 = free RWops after load
        if (!chunk_) return false;
        computeDuration();
        return true;
    }

    Time getDuration() const { return duration_; }
    Mix_Chunk* getChunk() const { return chunk_; }

private:
    void computeDuration() {
        if (!chunk_) { duration_ = Time(); return; }
        int freq = 0, channels = 0;
        Uint16 format = 0;
        Mix_QuerySpec(&freq, &format, &channels);
        if (freq == 0 || channels == 0) { duration_ = Time(); return; }
        // Compute bytes per sample based on format
        int bytesPerSample = 2;  // Default 16-bit
        if (format == AUDIO_U8 || format == AUDIO_S8) bytesPerSample = 1;
        else if (format == AUDIO_S32LSB || format == AUDIO_S32MSB) bytesPerSample = 4;
        else if (format == AUDIO_F32LSB || format == AUDIO_F32MSB) bytesPerSample = 4;
        int totalSamples = chunk_->alen / (bytesPerSample * channels);
        float secs = static_cast<float>(totalSamples) / static_cast<float>(freq);
        duration_ = seconds(secs);
    }
};

// Forward declare Sound for channel tracking
class Sound;

// Channel tracking: maps SDL_mixer channel indices to Sound* owners
// Defined as inline to keep header-only and avoid multiple definition issues
inline Sound* g_channelOwners[16] = {};

class Sound {
public:
    enum Status { Stopped, Paused, Playing };

    Sound() = default;
    Sound(const SoundBuffer& buffer) : chunk_(buffer.getChunk()) {}

    ~Sound() {
        // Release our channel claim
        if (channel_ >= 0 && channel_ < 16) {
            if (g_channelOwners[channel_] == this) {
                Mix_HaltChannel(channel_);
                g_channelOwners[channel_] = nullptr;
            }
            channel_ = -1;
        }
    }

    // No copy (channel ownership)
    Sound(const Sound&) = delete;
    Sound& operator=(const Sound&) = delete;

    // Move
    Sound(Sound&& other) noexcept
        : chunk_(other.chunk_), channel_(other.channel_),
          volume_(other.volume_), loop_(other.loop_) {
        if (channel_ >= 0 && channel_ < 16) {
            g_channelOwners[channel_] = this;
        }
        other.channel_ = -1;
        other.chunk_ = nullptr;
    }
    Sound& operator=(Sound&& other) noexcept {
        if (this != &other) {
            stop();
            chunk_ = other.chunk_;
            channel_ = other.channel_;
            volume_ = other.volume_;
            loop_ = other.loop_;
            if (channel_ >= 0 && channel_ < 16) {
                g_channelOwners[channel_] = this;
            }
            other.channel_ = -1;
            other.chunk_ = nullptr;
        }
        return *this;
    }

    void setBuffer(const SoundBuffer& buffer) { chunk_ = buffer.getChunk(); }

    void play() {
        if (!chunk_) return;
        channel_ = Mix_PlayChannel(-1, chunk_, loop_ ? -1 : 0);
        if (channel_ >= 0 && channel_ < 16) {
            // Clear any previous owner on this channel
            if (g_channelOwners[channel_] && g_channelOwners[channel_] != this) {
                g_channelOwners[channel_]->channel_ = -1;
            }
            g_channelOwners[channel_] = this;
            Mix_Volume(channel_, static_cast<int>(volume_ * 128.f / 100.f));
        }
    }

    void pause() {
        if (channel_ >= 0) Mix_Pause(channel_);
    }

    void stop() {
        if (channel_ >= 0) {
            Mix_HaltChannel(channel_);
            if (channel_ < 16 && g_channelOwners[channel_] == this) {
                g_channelOwners[channel_] = nullptr;
            }
            channel_ = -1;
        }
    }

    Status getStatus() const {
        if (channel_ < 0) return Stopped;
        if (Mix_Paused(channel_)) return Paused;
        if (Mix_Playing(channel_)) return Playing;
        return Stopped;
    }

    void setVolume(float vol) {
        volume_ = std::clamp(vol, 0.f, 100.f);
        if (channel_ >= 0) {
            Mix_Volume(channel_, static_cast<int>(volume_ * 128.f / 100.f));
        }
    }
    float getVolume() const { return volume_; }

    void setLoop(bool loop) { loop_ = loop; }
    bool getLoop() const { return loop_; }

    // Called by Mix_ChannelFinished callback
    static void onChannelFinished(int channel) {
        if (channel >= 0 && channel < 16 && g_channelOwners[channel]) {
            g_channelOwners[channel]->channel_ = -1;
            g_channelOwners[channel] = nullptr;
        }
    }

private:
    Mix_Chunk* chunk_ = nullptr;  // Borrowed from SoundBuffer
    int channel_ = -1;
    float volume_ = 100.f;
    bool loop_ = false;
};

class Music {
public:
    enum Status { Stopped, Paused, Playing };

    Music() = default;
    ~Music() {
        if (music_) {
            Mix_FreeMusic(music_);
            music_ = nullptr;
        }
    }

    // No copy (global music channel)
    Music(const Music&) = delete;
    Music& operator=(const Music&) = delete;

    // Move
    Music(Music&& other) noexcept
        : music_(other.music_), volume_(other.volume_), loop_(other.loop_) {
        other.music_ = nullptr;
    }
    Music& operator=(Music&& other) noexcept {
        if (this != &other) {
            if (music_) Mix_FreeMusic(music_);
            music_ = other.music_;
            volume_ = other.volume_;
            loop_ = other.loop_;
            other.music_ = nullptr;
        }
        return *this;
    }

    bool openFromFile(const std::string& filename) {
        if (music_) { Mix_FreeMusic(music_); music_ = nullptr; }
        music_ = Mix_LoadMUS(filename.c_str());
        return music_ != nullptr;
    }

    void play() {
        if (!music_) return;
        Mix_PlayMusic(music_, loop_ ? -1 : 0);
        Mix_VolumeMusic(static_cast<int>(volume_ * 128.f / 100.f));
    }

    void pause() {
        Mix_PauseMusic();
    }

    void stop() {
        Mix_HaltMusic();
    }

    Status getStatus() const {
        if (Mix_PausedMusic()) return Paused;
        if (Mix_PlayingMusic()) return Playing;
        return Stopped;
    }

    void setVolume(float vol) {
        volume_ = std::clamp(vol, 0.f, 100.f);
        Mix_VolumeMusic(static_cast<int>(volume_ * 128.f / 100.f));
    }
    float getVolume() const { return volume_; }

    void setLoop(bool loop) { loop_ = loop; }
    bool getLoop() const { return loop_; }

    // Duration not available in Emscripten's SDL_mixer 2.0.2
    Time getDuration() const { return Time(); }

    // Playing offset getter not available in Emscripten's SDL_mixer 2.0.2
    Time getPlayingOffset() const { return Time(); }

    // Setter works for OGG via Mix_SetMusicPosition
    void setPlayingOffset(Time offset) {
        if (music_) Mix_SetMusicPosition(static_cast<double>(offset.asSeconds()));
    }

private:
    Mix_Music* music_ = nullptr;
    float volume_ = 100.f;
    bool loop_ = false;
};

// =============================================================================
// Input (Keyboard and Mouse)
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

    static bool isKeyPressed(Key key);  // Implemented in SDL2Renderer.cpp
};

class Mouse {
public:
    enum Button { Left, Right, Middle, XButton1, XButton2, ButtonCount };
    enum Wheel { VerticalWheel, HorizontalWheel };

    static bool isButtonPressed(Button button);  // Implemented in SDL2Renderer.cpp
    static Vector2i getPosition();  // Implemented in SDL2Renderer.cpp
    static Vector2i getPosition(const RenderWindow& relativeTo);  // Implemented in SDL2Renderer.cpp
    static void setPosition(const Vector2i& position);  // Implemented in SDL2Renderer.cpp
    static void setPosition(const Vector2i& position, const RenderWindow& relativeTo);  // Implemented in SDL2Renderer.cpp
};

// =============================================================================
// Event System
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
// GLSL Types (for shader uniforms)
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

// =============================================================================
// Shader
// =============================================================================

class Shader {
    unsigned int programId_ = 0;  // OpenGL shader program handle
    bool loaded_ = false;

public:
    enum Type { Vertex, Geometry, Fragment };
    static const CurrentTextureType CurrentTexture;

    Shader() = default;
    ~Shader();  // Implemented in SDL2Renderer.cpp

    bool loadFromFile(const std::string& filename, Type type);  // Implemented in SDL2Renderer.cpp
    bool loadFromFile(const std::string& vertexFile, const std::string& fragmentFile);  // Implemented in SDL2Renderer.cpp
    bool loadFromMemory(const std::string& shader, Type type);  // Implemented in SDL2Renderer.cpp

    void setUniform(const std::string& name, float x);  // Implemented in SDL2Renderer.cpp
    void setUniform(const std::string& name, const Vector2f& v);
    void setUniform(const std::string& name, const Color& color);
    void setUniform(const std::string& name, const Texture& texture);
    void setUniform(const std::string& name, const Glsl::Vec3& v);
    void setUniform(const std::string& name, const Glsl::Vec4& v);
    void setUniform(const std::string& name, CurrentTextureType);

    static bool isAvailable();  // Implemented in SDL2Renderer.cpp

    // SDL2-specific: Get program handle
    unsigned int getNativeHandle() const { return programId_; }
    bool isLoaded() const { return loaded_; }
};

inline const CurrentTextureType Shader::CurrentTexture{};

// =============================================================================
// Error stream
// =============================================================================

#include <ostream>
#include <sstream>

inline std::ostream& err() {
    static std::stringstream dummy;
    return dummy;
}

} // namespace sf
