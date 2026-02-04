// Camera3D.cpp - 3D camera implementation

#include "Camera3D.h"

namespace mcrf {

Camera3D::Camera3D()
    : position_(0.0f, 0.0f, 5.0f)
    , target_(0.0f, 0.0f, 0.0f)
    , up_(0.0f, 1.0f, 0.0f)
{
}

Camera3D::Camera3D(const vec3& position, const vec3& target)
    : position_(position)
    , target_(target)
    , up_(0.0f, 1.0f, 0.0f)
{
}

void Camera3D::setPosition(const vec3& pos) {
    position_ = pos;
}

void Camera3D::setTarget(const vec3& target) {
    target_ = target;
}

void Camera3D::setUp(const vec3& up) {
    up_ = up.normalized();
}

vec3 Camera3D::getForward() const {
    return (target_ - position_).normalized();
}

vec3 Camera3D::getRight() const {
    return getForward().cross(up_).normalized();
}

void Camera3D::setFOV(float fovDegrees) {
    fov_ = fovDegrees;
}

void Camera3D::setAspect(float aspect) {
    aspect_ = aspect;
}

void Camera3D::setClipPlanes(float near, float far) {
    nearClip_ = near;
    farClip_ = far;
}

mat4 Camera3D::getViewMatrix() const {
    return mat4::lookAt(position_, target_, up_);
}

mat4 Camera3D::getProjectionMatrix() const {
    return mat4::perspective(radians(fov_), aspect_, nearClip_, farClip_);
}

mat4 Camera3D::getViewProjectionMatrix() const {
    return getProjectionMatrix() * getViewMatrix();
}

void Camera3D::moveForward(float distance) {
    vec3 forward = getForward();
    position_ += forward * distance;
    target_ += forward * distance;
}

void Camera3D::moveRight(float distance) {
    vec3 right = getRight();
    position_ += right * distance;
    target_ += right * distance;
}

void Camera3D::moveUp(float distance) {
    position_ += up_ * distance;
    target_ += up_ * distance;
}

void Camera3D::orbit(float yawDelta, float pitchDelta) {
    // Get current offset from target
    vec3 offset = position_ - target_;
    float distance = offset.length();

    // Convert to spherical coordinates
    float yaw = std::atan2(offset.x, offset.z);
    float pitch = std::asin(clamp(offset.y / distance, -1.0f, 1.0f));

    // Apply deltas (in radians)
    yaw += yawDelta;
    pitch += pitchDelta;

    // Clamp pitch to avoid gimbal lock
    pitch = clamp(pitch, -HALF_PI + 0.01f, HALF_PI - 0.01f);

    // Convert back to Cartesian
    position_.x = target_.x + distance * std::cos(pitch) * std::sin(yaw);
    position_.y = target_.y + distance * std::sin(pitch);
    position_.z = target_.z + distance * std::cos(pitch) * std::cos(yaw);
}

void Camera3D::lookAt(const vec3& point) {
    target_ = point;
}

} // namespace mcrf
