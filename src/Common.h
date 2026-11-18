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


// #562: blend modes for the render-texture-cache-then-composite pattern (layer chunks, Frame
// clip_children/cache_subtree). Content is painted into a transparent RenderTexture with
// kCachePaintBlend (the stored colour is premultiplied; stored alpha accumulates as
// a + (1-a)*dst_a), then the texture is composited with kPremultipliedBlend so alpha is not
// applied a second time. A sprite drawn this way scales its opacity with a colour of
// (o, o, o, o), not (255, 255, 255, o).
inline const sf::BlendMode kCachePaintBlend(
    sf::BlendMode::SrcAlpha, sf::BlendMode::OneMinusSrcAlpha, sf::BlendMode::Add,
    sf::BlendMode::One, sf::BlendMode::OneMinusSrcAlpha, sf::BlendMode::Add);
inline const sf::BlendMode kPremultipliedBlend(
    sf::BlendMode::One, sf::BlendMode::OneMinusSrcAlpha, sf::BlendMode::Add);
