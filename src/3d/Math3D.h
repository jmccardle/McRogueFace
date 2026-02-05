// Math3D.h - Minimal 3D math library for McRogueFace
// Header-only implementation of vec3, mat4, and quat
// Column-major matrices for OpenGL compatibility

#pragma once

#include <cmath>
#include <algorithm>

namespace mcrf {

// =============================================================================
// vec2 - 2D vector
// =============================================================================

struct vec2 {
    float x, y;

    vec2() : x(0), y(0) {}
    vec2(float x_, float y_) : x(x_), y(y_) {}
    explicit vec2(float v) : x(v), y(v) {}

    vec2 operator+(const vec2& other) const { return vec2(x + other.x, y + other.y); }
    vec2 operator-(const vec2& other) const { return vec2(x - other.x, y - other.y); }
    vec2 operator*(float s) const { return vec2(x * s, y * s); }
    vec2 operator/(float s) const { return vec2(x / s, y / s); }

    float dot(const vec2& other) const { return x * other.x + y * other.y; }
    float length() const { return std::sqrt(x * x + y * y); }
    float lengthSquared() const { return x * x + y * y; }

    vec2 normalized() const {
        float len = length();
        if (len > 0.0001f) return vec2(x / len, y / len);
        return vec2(0, 0);
    }
};

// =============================================================================
// vec3 - 3D vector
// =============================================================================

struct vec3 {
    float x, y, z;

    vec3() : x(0), y(0), z(0) {}
    vec3(float x_, float y_, float z_) : x(x_), y(y_), z(z_) {}
    explicit vec3(float v) : x(v), y(v), z(v) {}

    vec3 operator+(const vec3& other) const {
        return vec3(x + other.x, y + other.y, z + other.z);
    }

    vec3 operator-(const vec3& other) const {
        return vec3(x - other.x, y - other.y, z - other.z);
    }

    vec3 operator*(float s) const {
        return vec3(x * s, y * s, z * s);
    }

    vec3 operator/(float s) const {
        return vec3(x / s, y / s, z / s);
    }

    vec3 operator-() const {
        return vec3(-x, -y, -z);
    }

    vec3& operator+=(const vec3& other) {
        x += other.x; y += other.y; z += other.z;
        return *this;
    }

    vec3& operator-=(const vec3& other) {
        x -= other.x; y -= other.y; z -= other.z;
        return *this;
    }

    vec3& operator*=(float s) {
        x *= s; y *= s; z *= s;
        return *this;
    }

    float dot(const vec3& other) const {
        return x * other.x + y * other.y + z * other.z;
    }

    vec3 cross(const vec3& other) const {
        return vec3(
            y * other.z - z * other.y,
            z * other.x - x * other.z,
            x * other.y - y * other.x
        );
    }

    float lengthSquared() const {
        return x * x + y * y + z * z;
    }

    float length() const {
        return std::sqrt(lengthSquared());
    }

    vec3 normalized() const {
        float len = length();
        if (len > 0.0001f) {
            return *this / len;
        }
        return vec3(0, 0, 0);
    }

    // Component-wise operations
    vec3 hadamard(const vec3& other) const {
        return vec3(x * other.x, y * other.y, z * other.z);
    }

    // Linear interpolation
    static vec3 lerp(const vec3& a, const vec3& b, float t) {
        return a + (b - a) * t;
    }
};

// Left-hand scalar multiplication
inline vec3 operator*(float s, const vec3& v) {
    return v * s;
}

// =============================================================================
// vec4 - 4D vector (for homogeneous coordinates)
// =============================================================================

struct vec4 {
    float x, y, z, w;

    vec4() : x(0), y(0), z(0), w(0) {}
    vec4(float x_, float y_, float z_, float w_) : x(x_), y(y_), z(z_), w(w_) {}
    vec4(const vec3& v, float w_) : x(v.x), y(v.y), z(v.z), w(w_) {}

    vec3 xyz() const { return vec3(x, y, z); }

    // Perspective divide
    vec3 perspectiveDivide() const {
        if (std::abs(w) > 0.0001f) {
            return vec3(x / w, y / w, z / w);
        }
        return vec3(x, y, z);
    }
};

// =============================================================================
// mat4 - 4x4 matrix (column-major for OpenGL)
// =============================================================================

struct mat4 {
    // Column-major storage: m[col][row] but stored as m[col*4 + row]
    // This matches OpenGL's expected layout
    float m[16];

    mat4() {
        for (int i = 0; i < 16; i++) m[i] = 0;
    }

    // Access element at column c, row r
    float& at(int c, int r) { return m[c * 4 + r]; }
    const float& at(int c, int r) const { return m[c * 4 + r]; }

    // Get column as vec4
    vec4 col(int c) const {
        return vec4(m[c*4], m[c*4+1], m[c*4+2], m[c*4+3]);
    }

    // Get raw data pointer (for OpenGL uniforms)
    const float* data() const { return m; }
    float* data() { return m; }

    static mat4 identity() {
        mat4 result;
        result.at(0, 0) = 1.0f;
        result.at(1, 1) = 1.0f;
        result.at(2, 2) = 1.0f;
        result.at(3, 3) = 1.0f;
        return result;
    }

    static mat4 translate(const vec3& v) {
        mat4 result = identity();
        result.at(3, 0) = v.x;
        result.at(3, 1) = v.y;
        result.at(3, 2) = v.z;
        return result;
    }

    static mat4 translate(float x, float y, float z) {
        return translate(vec3(x, y, z));
    }

    static mat4 scale(const vec3& v) {
        mat4 result = identity();
        result.at(0, 0) = v.x;
        result.at(1, 1) = v.y;
        result.at(2, 2) = v.z;
        return result;
    }

    static mat4 scale(float x, float y, float z) {
        return scale(vec3(x, y, z));
    }

    static mat4 scale(float s) {
        return scale(vec3(s, s, s));
    }

    static mat4 rotateX(float radians) {
        mat4 result = identity();
        float c = std::cos(radians);
        float s = std::sin(radians);
        result.at(1, 1) = c;
        result.at(2, 1) = -s;
        result.at(1, 2) = s;
        result.at(2, 2) = c;
        return result;
    }

    static mat4 rotateY(float radians) {
        mat4 result = identity();
        float c = std::cos(radians);
        float s = std::sin(radians);
        result.at(0, 0) = c;
        result.at(2, 0) = s;
        result.at(0, 2) = -s;
        result.at(2, 2) = c;
        return result;
    }

    static mat4 rotateZ(float radians) {
        mat4 result = identity();
        float c = std::cos(radians);
        float s = std::sin(radians);
        result.at(0, 0) = c;
        result.at(1, 0) = -s;
        result.at(0, 1) = s;
        result.at(1, 1) = c;
        return result;
    }

    // Perspective projection matrix
    // fov: vertical field of view in radians
    // aspect: width / height
    // near, far: clipping planes
    static mat4 perspective(float fov, float aspect, float near, float far) {
        mat4 result;
        float tanHalfFov = std::tan(fov / 2.0f);

        result.at(0, 0) = 1.0f / (aspect * tanHalfFov);
        result.at(1, 1) = 1.0f / tanHalfFov;
        result.at(2, 2) = -(far + near) / (far - near);
        result.at(2, 3) = -1.0f;
        result.at(3, 2) = -(2.0f * far * near) / (far - near);

        return result;
    }

    // Orthographic projection matrix
    static mat4 ortho(float left, float right, float bottom, float top, float near, float far) {
        mat4 result = identity();

        result.at(0, 0) = 2.0f / (right - left);
        result.at(1, 1) = 2.0f / (top - bottom);
        result.at(2, 2) = -2.0f / (far - near);
        result.at(3, 0) = -(right + left) / (right - left);
        result.at(3, 1) = -(top + bottom) / (top - bottom);
        result.at(3, 2) = -(far + near) / (far - near);

        return result;
    }

    // View matrix (camera transformation)
    static mat4 lookAt(const vec3& eye, const vec3& target, const vec3& up) {
        vec3 zaxis = (eye - target).normalized();  // Forward (camera looks down -Z)
        vec3 xaxis = up.cross(zaxis).normalized(); // Right
        vec3 yaxis = zaxis.cross(xaxis);           // Up

        mat4 result;

        // Rotation part (transposed because we need the inverse)
        result.at(0, 0) = xaxis.x;
        result.at(1, 0) = xaxis.y;
        result.at(2, 0) = xaxis.z;

        result.at(0, 1) = yaxis.x;
        result.at(1, 1) = yaxis.y;
        result.at(2, 1) = yaxis.z;

        result.at(0, 2) = zaxis.x;
        result.at(1, 2) = zaxis.y;
        result.at(2, 2) = zaxis.z;

        // Translation part
        result.at(3, 0) = -xaxis.dot(eye);
        result.at(3, 1) = -yaxis.dot(eye);
        result.at(3, 2) = -zaxis.dot(eye);
        result.at(3, 3) = 1.0f;

        return result;
    }

    // Matrix multiplication
    mat4 operator*(const mat4& other) const {
        mat4 result;
        for (int c = 0; c < 4; c++) {
            for (int r = 0; r < 4; r++) {
                float sum = 0.0f;
                for (int k = 0; k < 4; k++) {
                    sum += at(k, r) * other.at(c, k);
                }
                result.at(c, r) = sum;
            }
        }
        return result;
    }

    // Transform a point (assumes w=1, returns xyz)
    vec3 transformPoint(const vec3& p) const {
        vec4 v(p, 1.0f);
        vec4 result(
            at(0, 0) * v.x + at(1, 0) * v.y + at(2, 0) * v.z + at(3, 0) * v.w,
            at(0, 1) * v.x + at(1, 1) * v.y + at(2, 1) * v.z + at(3, 1) * v.w,
            at(0, 2) * v.x + at(1, 2) * v.y + at(2, 2) * v.z + at(3, 2) * v.w,
            at(0, 3) * v.x + at(1, 3) * v.y + at(2, 3) * v.z + at(3, 3) * v.w
        );
        return result.perspectiveDivide();
    }

    // Transform a direction (assumes w=0)
    vec3 transformDirection(const vec3& d) const {
        return vec3(
            at(0, 0) * d.x + at(1, 0) * d.y + at(2, 0) * d.z,
            at(0, 1) * d.x + at(1, 1) * d.y + at(2, 1) * d.z,
            at(0, 2) * d.x + at(1, 2) * d.y + at(2, 2) * d.z
        );
    }

    // Transform a vec4
    vec4 operator*(const vec4& v) const {
        return vec4(
            at(0, 0) * v.x + at(1, 0) * v.y + at(2, 0) * v.z + at(3, 0) * v.w,
            at(0, 1) * v.x + at(1, 1) * v.y + at(2, 1) * v.z + at(3, 1) * v.w,
            at(0, 2) * v.x + at(1, 2) * v.y + at(2, 2) * v.z + at(3, 2) * v.w,
            at(0, 3) * v.x + at(1, 3) * v.y + at(2, 3) * v.z + at(3, 3) * v.w
        );
    }

    // Transpose
    mat4 transposed() const {
        mat4 result;
        for (int c = 0; c < 4; c++) {
            for (int r = 0; r < 4; r++) {
                result.at(r, c) = at(c, r);
            }
        }
        return result;
    }

    // Inverse (for general 4x4 matrix - used for camera)
    // Returns identity if matrix is singular
    mat4 inverse() const {
        mat4 inv;
        const float* m = this->m;
        float* out = inv.m;

        out[0] = m[5]  * m[10] * m[15] - m[5]  * m[11] * m[14] -
                 m[9]  * m[6]  * m[15] + m[9]  * m[7]  * m[14] +
                 m[13] * m[6]  * m[11] - m[13] * m[7]  * m[10];
        out[4] = -m[4] * m[10] * m[15] + m[4]  * m[11] * m[14] +
                  m[8] * m[6]  * m[15] - m[8]  * m[7]  * m[14] -
                 m[12] * m[6]  * m[11] + m[12] * m[7]  * m[10];
        out[8] = m[4]  * m[9]  * m[15] - m[4]  * m[11] * m[13] -
                 m[8]  * m[5]  * m[15] + m[8]  * m[7]  * m[13] +
                 m[12] * m[5]  * m[11] - m[12] * m[7]  * m[9];
        out[12] = -m[4] * m[9]  * m[14] + m[4]  * m[10] * m[13] +
                   m[8] * m[5]  * m[14] - m[8]  * m[6]  * m[13] -
                  m[12] * m[5]  * m[10] + m[12] * m[6]  * m[9];
        out[1] = -m[1] * m[10] * m[15] + m[1]  * m[11] * m[14] +
                  m[9] * m[2]  * m[15] - m[9]  * m[3]  * m[14] -
                 m[13] * m[2]  * m[11] + m[13] * m[3]  * m[10];
        out[5] = m[0]  * m[10] * m[15] - m[0]  * m[11] * m[14] -
                 m[8]  * m[2]  * m[15] + m[8]  * m[3]  * m[14] +
                 m[12] * m[2]  * m[11] - m[12] * m[3]  * m[10];
        out[9] = -m[0] * m[9]  * m[15] + m[0]  * m[11] * m[13] +
                  m[8] * m[1]  * m[15] - m[8]  * m[3]  * m[13] -
                 m[12] * m[1]  * m[11] + m[12] * m[3]  * m[9];
        out[13] = m[0]  * m[9]  * m[14] - m[0]  * m[10] * m[13] -
                  m[8]  * m[1]  * m[14] + m[8]  * m[2]  * m[13] +
                  m[12] * m[1]  * m[10] - m[12] * m[2]  * m[9];
        out[2] = m[1]  * m[6] * m[15] - m[1]  * m[7] * m[14] -
                 m[5]  * m[2] * m[15] + m[5]  * m[3] * m[14] +
                 m[13] * m[2] * m[7]  - m[13] * m[3] * m[6];
        out[6] = -m[0] * m[6] * m[15] + m[0]  * m[7] * m[14] +
                  m[4] * m[2] * m[15] - m[4]  * m[3] * m[14] -
                 m[12] * m[2] * m[7]  + m[12] * m[3] * m[6];
        out[10] = m[0]  * m[5] * m[15] - m[0]  * m[7] * m[13] -
                  m[4]  * m[1] * m[15] + m[4]  * m[3] * m[13] +
                  m[12] * m[1] * m[7]  - m[12] * m[3] * m[5];
        out[14] = -m[0] * m[5] * m[14] + m[0]  * m[6] * m[13] +
                   m[4] * m[1] * m[14] - m[4]  * m[2] * m[13] -
                  m[12] * m[1] * m[6]  + m[12] * m[2] * m[5];
        out[3] = -m[1] * m[6] * m[11] + m[1] * m[7] * m[10] +
                  m[5] * m[2] * m[11] - m[5] * m[3] * m[10] -
                  m[9] * m[2] * m[7]  + m[9] * m[3] * m[6];
        out[7] = m[0] * m[6] * m[11] - m[0] * m[7] * m[10] -
                 m[4] * m[2] * m[11] + m[4] * m[3] * m[10] +
                 m[8] * m[2] * m[7]  - m[8] * m[3] * m[6];
        out[11] = -m[0] * m[5] * m[11] + m[0] * m[7] * m[9] +
                   m[4] * m[1] * m[11] - m[4] * m[3] * m[9] -
                   m[8] * m[1] * m[7]  + m[8] * m[3] * m[5];
        out[15] = m[0] * m[5] * m[10] - m[0] * m[6] * m[9] -
                  m[4] * m[1] * m[10] + m[4] * m[2] * m[9] +
                  m[8] * m[1] * m[6]  - m[8] * m[2] * m[5];

        float det = m[0] * out[0] + m[1] * out[4] + m[2] * out[8] + m[3] * out[12];

        if (std::abs(det) < 0.0001f) {
            return identity();
        }

        det = 1.0f / det;
        for (int i = 0; i < 16; i++) {
            out[i] *= det;
        }

        return inv;
    }
};

// =============================================================================
// quat - Quaternion for rotations
// =============================================================================

struct quat {
    float x, y, z, w;  // w is the scalar part

    quat() : x(0), y(0), z(0), w(1) {}  // Identity quaternion
    quat(float x_, float y_, float z_, float w_) : x(x_), y(y_), z(z_), w(w_) {}

    // Create from axis and angle (angle in radians)
    static quat fromAxisAngle(const vec3& axis, float angle) {
        float halfAngle = angle * 0.5f;
        float s = std::sin(halfAngle);
        vec3 n = axis.normalized();
        return quat(n.x * s, n.y * s, n.z * s, std::cos(halfAngle));
    }

    // Create from Euler angles (in radians, applied as yaw-pitch-roll / Y-X-Z)
    static quat fromEuler(float pitch, float yaw, float roll) {
        float cy = std::cos(yaw * 0.5f);
        float sy = std::sin(yaw * 0.5f);
        float cp = std::cos(pitch * 0.5f);
        float sp = std::sin(pitch * 0.5f);
        float cr = std::cos(roll * 0.5f);
        float sr = std::sin(roll * 0.5f);

        return quat(
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
            cr * cp * cy + sr * sp * sy
        );
    }

    float lengthSquared() const {
        return x * x + y * y + z * z + w * w;
    }

    float length() const {
        return std::sqrt(lengthSquared());
    }

    quat normalized() const {
        float len = length();
        if (len > 0.0001f) {
            float invLen = 1.0f / len;
            return quat(x * invLen, y * invLen, z * invLen, w * invLen);
        }
        return quat();
    }

    quat conjugate() const {
        return quat(-x, -y, -z, w);
    }

    quat inverse() const {
        float lenSq = lengthSquared();
        if (lenSq > 0.0001f) {
            float invLenSq = 1.0f / lenSq;
            return quat(-x * invLenSq, -y * invLenSq, -z * invLenSq, w * invLenSq);
        }
        return quat();
    }

    // Quaternion multiplication
    quat operator*(const quat& other) const {
        return quat(
            w * other.x + x * other.w + y * other.z - z * other.y,
            w * other.y - x * other.z + y * other.w + z * other.x,
            w * other.z + x * other.y - y * other.x + z * other.w,
            w * other.w - x * other.x - y * other.y - z * other.z
        );
    }

    // Rotate a vector by this quaternion
    vec3 rotate(const vec3& v) const {
        // q * v * q^-1
        quat vq(v.x, v.y, v.z, 0);
        quat result = (*this) * vq * conjugate();
        return vec3(result.x, result.y, result.z);
    }

    // Convert to rotation matrix
    mat4 toMatrix() const {
        mat4 result = mat4::identity();

        float xx = x * x;
        float yy = y * y;
        float zz = z * z;
        float xy = x * y;
        float xz = x * z;
        float yz = y * z;
        float wx = w * x;
        float wy = w * y;
        float wz = w * z;

        result.at(0, 0) = 1.0f - 2.0f * (yy + zz);
        result.at(0, 1) = 2.0f * (xy + wz);
        result.at(0, 2) = 2.0f * (xz - wy);

        result.at(1, 0) = 2.0f * (xy - wz);
        result.at(1, 1) = 1.0f - 2.0f * (xx + zz);
        result.at(1, 2) = 2.0f * (yz + wx);

        result.at(2, 0) = 2.0f * (xz + wy);
        result.at(2, 1) = 2.0f * (yz - wx);
        result.at(2, 2) = 1.0f - 2.0f * (xx + yy);

        return result;
    }

    // Spherical linear interpolation
    static quat slerp(const quat& a, const quat& b, float t) {
        float dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;

        quat b2 = b;
        if (dot < 0.0f) {
            // Take the shorter path
            b2.x = -b.x;
            b2.y = -b.y;
            b2.z = -b.z;
            b2.w = -b.w;
            dot = -dot;
        }

        const float DOT_THRESHOLD = 0.9995f;
        if (dot > DOT_THRESHOLD) {
            // Linear interpolation for very similar quaternions
            return quat(
                a.x + (b2.x - a.x) * t,
                a.y + (b2.y - a.y) * t,
                a.z + (b2.z - a.z) * t,
                a.w + (b2.w - a.w) * t
            ).normalized();
        }

        float theta_0 = std::acos(dot);
        float theta = theta_0 * t;
        float sin_theta = std::sin(theta);
        float sin_theta_0 = std::sin(theta_0);

        float s0 = std::cos(theta) - dot * sin_theta / sin_theta_0;
        float s1 = sin_theta / sin_theta_0;

        return quat(
            a.x * s0 + b2.x * s1,
            a.y * s0 + b2.y * s1,
            a.z * s0 + b2.z * s1,
            a.w * s0 + b2.w * s1
        );
    }

    // Linear interpolation (faster but less accurate for large angles)
    static quat lerp(const quat& a, const quat& b, float t) {
        float dot = a.x * b.x + a.y * b.y + a.z * b.z + a.w * b.w;

        quat result;
        if (dot < 0.0f) {
            result = quat(
                a.x - (b.x + a.x) * t,
                a.y - (b.y + a.y) * t,
                a.z - (b.z + a.z) * t,
                a.w - (b.w + a.w) * t
            );
        } else {
            result = quat(
                a.x + (b.x - a.x) * t,
                a.y + (b.y - a.y) * t,
                a.z + (b.z - a.z) * t,
                a.w + (b.w - a.w) * t
            );
        }
        return result.normalized();
    }
};

// =============================================================================
// Frustum - View frustum for culling
// =============================================================================

struct Plane {
    vec3 normal;
    float distance;

    Plane() : normal(0, 1, 0), distance(0) {}
    Plane(const vec3& n, float d) : normal(n), distance(d) {}

    // Distance from plane to point (positive = in front, negative = behind)
    float distanceToPoint(const vec3& point) const {
        return normal.dot(point) + distance;
    }
};

struct Frustum {
    // Six planes: left, right, bottom, top, near, far
    Plane planes[6];

    // Extract frustum planes from view-projection matrix
    // Uses Gribb/Hartmann method
    void extractFromMatrix(const mat4& viewProj) {
        const float* m = viewProj.m;

        // Left plane
        planes[0].normal.x = m[3] + m[0];
        planes[0].normal.y = m[7] + m[4];
        planes[0].normal.z = m[11] + m[8];
        planes[0].distance = m[15] + m[12];

        // Right plane
        planes[1].normal.x = m[3] - m[0];
        planes[1].normal.y = m[7] - m[4];
        planes[1].normal.z = m[11] - m[8];
        planes[1].distance = m[15] - m[12];

        // Bottom plane
        planes[2].normal.x = m[3] + m[1];
        planes[2].normal.y = m[7] + m[5];
        planes[2].normal.z = m[11] + m[9];
        planes[2].distance = m[15] + m[13];

        // Top plane
        planes[3].normal.x = m[3] - m[1];
        planes[3].normal.y = m[7] - m[5];
        planes[3].normal.z = m[11] - m[9];
        planes[3].distance = m[15] - m[13];

        // Near plane
        planes[4].normal.x = m[3] + m[2];
        planes[4].normal.y = m[7] + m[6];
        planes[4].normal.z = m[11] + m[10];
        planes[4].distance = m[15] + m[14];

        // Far plane
        planes[5].normal.x = m[3] - m[2];
        planes[5].normal.y = m[7] - m[6];
        planes[5].normal.z = m[11] - m[10];
        planes[5].distance = m[15] - m[14];

        // Normalize all planes
        for (int i = 0; i < 6; i++) {
            float len = planes[i].normal.length();
            if (len > 0.0001f) {
                planes[i].normal = planes[i].normal / len;
                planes[i].distance /= len;
            }
        }
    }

    // Test if a point is inside the frustum
    bool containsPoint(const vec3& point) const {
        for (int i = 0; i < 6; i++) {
            if (planes[i].distanceToPoint(point) < 0) {
                return false;
            }
        }
        return true;
    }

    // Test if a sphere intersects or is inside the frustum
    bool containsSphere(const vec3& center, float radius) const {
        for (int i = 0; i < 6; i++) {
            if (planes[i].distanceToPoint(center) < -radius) {
                return false;  // Sphere is completely behind this plane
            }
        }
        return true;
    }

    // Test if an axis-aligned bounding box intersects the frustum
    bool containsAABB(const vec3& min, const vec3& max) const {
        for (int i = 0; i < 6; i++) {
            // Find the positive vertex (furthest along plane normal)
            vec3 pVertex;
            pVertex.x = (planes[i].normal.x >= 0) ? max.x : min.x;
            pVertex.y = (planes[i].normal.y >= 0) ? max.y : min.y;
            pVertex.z = (planes[i].normal.z >= 0) ? max.z : min.z;

            // If positive vertex is behind plane, box is outside
            if (planes[i].distanceToPoint(pVertex) < 0) {
                return false;
            }
        }
        return true;
    }
};

// =============================================================================
// Utility constants and functions
// =============================================================================

constexpr float PI = 3.14159265358979323846f;
constexpr float TWO_PI = PI * 2.0f;
constexpr float HALF_PI = PI * 0.5f;
constexpr float DEG_TO_RAD = PI / 180.0f;
constexpr float RAD_TO_DEG = 180.0f / PI;

inline float radians(float degrees) { return degrees * DEG_TO_RAD; }
inline float degrees(float radians) { return radians * RAD_TO_DEG; }

inline float clamp(float v, float min, float max) {
    return std::min(std::max(v, min), max);
}

} // namespace mcrf
