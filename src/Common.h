# pragma once
#include <SFML/Graphics.hpp>
#include <SFML/Audio.hpp>

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

