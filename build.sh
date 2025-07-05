#!/bin/bash
# Build script for McRogueFace - compiles everything into ./build directory

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}McRogueFace Build Script${NC}"
echo "========================="

# Create build directory if it doesn't exist
if [ ! -d "build" ]; then
    echo -e "${YELLOW}Creating build directory...${NC}"
    mkdir build
fi

# Change to build directory
cd build

# Run CMake to generate build files
echo -e "${YELLOW}Running CMake...${NC}"
cmake .. -DCMAKE_BUILD_TYPE=Release

# Check if CMake succeeded
if [ $? -ne 0 ]; then
    echo -e "${RED}CMake configuration failed!${NC}"
    exit 1
fi

# Run make with parallel jobs
echo -e "${YELLOW}Building with make...${NC}"
make -j$(nproc)

# Check if make succeeded
if [ $? -ne 0 ]; then
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

echo -e "${GREEN}Build completed successfully!${NC}"
echo ""
echo "The build directory contains:"
ls -la

echo ""
echo -e "${GREEN}To run McRogueFace:${NC}"
echo "  cd build"
echo "  ./mcrogueface"
echo ""
echo -e "${GREEN}To create a distribution archive:${NC}"
echo "  cd build"
echo "  zip -r ../McRogueFace-$(date +%Y%m%d).zip ."