# pragma once

// =============================================================================
// Platform Selection
// =============================================================================
// Define MCRF_HEADLESS to build without SFML graphics/audio dependencies.
// This enables headless operation for servers, CI, and Emscripten builds.
//
// Build with: cmake -DMCRF_HEADLESS=ON ..
// =============================================================================

#ifdef MCRF_HEADLESS
    // Use headless type stubs instead of SFML (no graphics, for CI/testing)
    #include "platform/HeadlessTypes.h"
    #define MCRF_GRAPHICS_BACKEND "headless"
#elif defined(MCRF_SDL2)
    // Use SDL2 + OpenGL ES 2 backend (for Emscripten/WebGL, Android, cross-platform)
    #include "platform/SDL2Types.h"
    #define MCRF_GRAPHICS_BACKEND "sdl2"
#else
    // Use SFML for graphics and audio (default desktop build)
    #include <SFML/Graphics.hpp>
    #include <SFML/Audio.hpp>
    #define MCRF_GRAPHICS_BACKEND "sfml"
#endif

// Maximum dimension for grids, layers, and heightmaps (8192x8192 = 256MB of float data)
// Prevents integer overflow in size calculations and limits memory allocation
constexpr int GRID_MAX = 8192;

#include <vector>
#include <iostream>
#include <memory>
#include <fstream>
#include <sstream>
#include <algorithm>

// wstring<->string conversion
#include <locale>
#include <codecvt>
#include <filesystem>

