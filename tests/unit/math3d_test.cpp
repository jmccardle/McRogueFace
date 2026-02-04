// math3d_test.cpp - Quick verification of Math3D library
// Compile: g++ -std=c++17 -I../../src math3d_test.cpp -o math3d_test && ./math3d_test

#include "3d/Math3D.h"
#include <iostream>
#include <cmath>

using namespace mcrf;

bool approx(float a, float b, float eps = 0.0001f) {
    return std::abs(a - b) < eps;
}

int main() {
    int passed = 0, failed = 0;

    // vec3 tests
    {
        vec3 a(1, 2, 3);
        vec3 b(4, 5, 6);

        vec3 sum = a + b;
        if (approx(sum.x, 5) && approx(sum.y, 7) && approx(sum.z, 9)) {
            std::cout << "[PASS] vec3 addition\n"; passed++;
        } else {
            std::cout << "[FAIL] vec3 addition\n"; failed++;
        }

        float dot = a.dot(b);
        if (approx(dot, 32)) { // 1*4 + 2*5 + 3*6 = 32
            std::cout << "[PASS] vec3 dot product\n"; passed++;
        } else {
            std::cout << "[FAIL] vec3 dot product: " << dot << "\n"; failed++;
        }

        vec3 c(1, 0, 0);
        vec3 d(0, 1, 0);
        vec3 cross = c.cross(d);
        if (approx(cross.x, 0) && approx(cross.y, 0) && approx(cross.z, 1)) {
            std::cout << "[PASS] vec3 cross product\n"; passed++;
        } else {
            std::cout << "[FAIL] vec3 cross product\n"; failed++;
        }

        vec3 n = vec3(3, 4, 0).normalized();
        if (approx(n.length(), 1.0f)) {
            std::cout << "[PASS] vec3 normalize\n"; passed++;
        } else {
            std::cout << "[FAIL] vec3 normalize\n"; failed++;
        }
    }

    // mat4 tests
    {
        mat4 id = mat4::identity();
        vec3 p(1, 2, 3);
        vec3 transformed = id.transformPoint(p);
        if (approx(transformed.x, 1) && approx(transformed.y, 2) && approx(transformed.z, 3)) {
            std::cout << "[PASS] mat4 identity transform\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 identity transform\n"; failed++;
        }

        mat4 trans = mat4::translate(10, 20, 30);
        vec3 moved = trans.transformPoint(p);
        if (approx(moved.x, 11) && approx(moved.y, 22) && approx(moved.z, 33)) {
            std::cout << "[PASS] mat4 translation\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 translation\n"; failed++;
        }

        mat4 scl = mat4::scale(2, 3, 4);
        vec3 scaled = scl.transformPoint(p);
        if (approx(scaled.x, 2) && approx(scaled.y, 6) && approx(scaled.z, 12)) {
            std::cout << "[PASS] mat4 scale\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 scale\n"; failed++;
        }

        // Test rotation: 90 degrees around Y should swap X and Z
        mat4 rotY = mat4::rotateY(HALF_PI);
        vec3 rotated = rotY.transformPoint(vec3(1, 0, 0));
        if (approx(rotated.x, 0) && approx(rotated.z, -1)) {
            std::cout << "[PASS] mat4 rotateY\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 rotateY: " << rotated.x << "," << rotated.y << "," << rotated.z << "\n"; failed++;
        }
    }

    // Projection matrix test
    {
        mat4 proj = mat4::perspective(radians(90.0f), 1.0f, 0.1f, 100.0f);
        // A point at z=-1 (in front of camera) should project to valid NDC
        vec4 p(0, 0, -1, 1);
        vec4 clip = proj * p;
        vec3 ndc = clip.perspectiveDivide();
        if (ndc.z > -1.0f && ndc.z < 1.0f) {
            std::cout << "[PASS] mat4 perspective\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 perspective\n"; failed++;
        }
    }

    // LookAt matrix test
    {
        mat4 view = mat4::lookAt(vec3(0, 0, 5), vec3(0, 0, 0), vec3(0, 1, 0));
        vec3 origin = view.transformPoint(vec3(0, 0, 0));
        // Origin should be at z=-5 in view space (5 units in front)
        if (approx(origin.x, 0) && approx(origin.y, 0) && approx(origin.z, -5)) {
            std::cout << "[PASS] mat4 lookAt\n"; passed++;
        } else {
            std::cout << "[FAIL] mat4 lookAt: " << origin.x << "," << origin.y << "," << origin.z << "\n"; failed++;
        }
    }

    // Quaternion tests
    {
        quat q = quat::fromAxisAngle(vec3(0, 1, 0), HALF_PI);
        vec3 rotated = q.rotate(vec3(1, 0, 0));
        if (approx(rotated.x, 0) && approx(rotated.z, -1)) {
            std::cout << "[PASS] quat rotation\n"; passed++;
        } else {
            std::cout << "[FAIL] quat rotation: " << rotated.x << "," << rotated.y << "," << rotated.z << "\n"; failed++;
        }

        quat a = quat::fromAxisAngle(vec3(0, 1, 0), 0);
        quat b = quat::fromAxisAngle(vec3(0, 1, 0), PI);
        quat mid = quat::slerp(a, b, 0.5f);
        vec3 half = mid.rotate(vec3(1, 0, 0));
        // At t=0.5 between 0 and PI rotation, we should get 90 degrees
        // Result should be perpendicular to input (x near 0, |z| near 1)
        if (approx(half.x, 0, 0.01f) && approx(std::abs(half.z), 1, 0.01f)) {
            std::cout << "[PASS] quat slerp\n"; passed++;
        } else {
            std::cout << "[FAIL] quat slerp: " << half.x << "," << half.y << "," << half.z << "\n"; failed++;
        }
    }

    std::cout << "\n=== Results: " << passed << " passed, " << failed << " failed ===\n";
    return failed > 0 ? 1 : 0;
}
