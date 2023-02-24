#!/bin/bash

#rm -R bin/linux
mkdir -p bin/linux/lib

# copy shared objects, squish "linux" subdirectory in bin/linux/lib
#cp -R lib/linux/* bin/linux/lib

# copy assets directory (font, sprites, etc)
cp -R assets bin/linux

# copy Python code
cp -R src/scripts bin/linux/scripts

# work from output directory and change every g++ path to relative D:<
cd bin/linux

g++ \
    --std=c++17 \
    -I../../deps_linux \
    -I../../deps_linux/Python-3.11.1 \
    -I../../platform/linux \
    ../../src/combined_poc.cpp \
    -o poc \
    -Wl,-rpath lib \
    -L../../deps_linux \
    -lm \
    -ldl \
    -lutil \
    -lpthread \
    -lpython3.11 \
    -lsfml-graphics \
    -lsfml-window \
    -lsfml-system \
    -ltcod

