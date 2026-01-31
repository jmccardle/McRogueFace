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
    // Use headless type stubs instead of SFML
    #include "platform/HeadlessTypes.h"
    #define MCRF_GRAPHICS_BACKEND "headless"
#else
    // Use SFML for graphics and audio
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

