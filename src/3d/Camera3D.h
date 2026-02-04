// Camera3D.h - 3D camera for McRogueFace
// Provides view and projection matrices for 3D rendering

#pragma once

#include "Math3D.h"

namespace mcrf {

// =============================================================================
// Camera3D - First-person style camera with position, target, up vector
// =============================================================================

class Camera3D {
public:
    Camera3D();
    Camera3D(const vec3& position, const vec3& target);

    // Position and orientation
    void setPosition(const vec3& pos);
    void setTarget(const vec3& target);
    void setUp(const vec3& up);

    vec3 getPosition() const { return position_; }
    vec3 getTarget() const { return target_; }
    vec3 getUp() const { return up_; }

    // Direction vectors
    vec3 getForward() const;
    vec3 getRight() const;

    // Projection settings
    void setFOV(float fovDegrees);
    void setAspect(float aspect);
    void setClipPlanes(float near, float far);

    float getFOV() const { return fov_; }
    float getAspect() const { return aspect_; }
    float getNearClip() const { return nearClip_; }
    float getFarClip() const { return farClip_; }

    // Matrix computation
    mat4 getViewMatrix() const;
    mat4 getProjectionMatrix() const;
    mat4 getViewProjectionMatrix() const;

    // Convenience methods for camera movement
    void moveForward(float distance);
    void moveRight(float distance);
    void moveUp(float distance);

    // Orbit around target
    void orbit(float yawDelta, float pitchDelta);

    // Look at a specific point (updates target)
    void lookAt(const vec3& point);

private:
    vec3 position_;
    vec3 target_;
    vec3 up_;

    float fov_ = 60.0f;      // Vertical FOV in degrees
    float aspect_ = 1.0f;    // Width / height
    float nearClip_ = 0.1f;
    float farClip_ = 100.0f;
};

} // namespace mcrf
