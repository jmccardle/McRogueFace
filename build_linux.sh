#!/bin/bash

#rm -R bin/linux
mkdir -p bin/linux/lib
mkdir -p obj
rm obj/*

# copy shared objects, squish "linux" subdirectory in bin/linux/lib
#cp -R lib/linux/* bin/linux/lib

# copy assets directory (font, sprites, etc)
cp -R assets bin/linux

# copy Python code
cp -R src/scripts bin/linux/scripts

# work from output directory and change every g++ path to relative D:<
cd bin/linux

# prepare object files of engine classes
abort_compile()
{
    echo "Compilation failed on $fn.cpp"
    exit 1
}

# Precompile engine classes. Get errors in their file, not where they're included
for fn in $(ls ../../src/*.cpp -1 | cut -d/ -f4 | cut -d. -f1)
do
    # Skip combined_poc.cpp, it has a duplicate main
    if [ "$fn" = "combined_poc" ]; then continue; fi

    echo "Compile $fn.cpp"
    g++ \
        -I../../deps_linux \
        -I../../deps_linux/Python-3.11.1 \
        -I../../platform/linux \
        --std=c++17 \
        -c ../../src/$fn.cpp \
        -o ../../obj/$fn.o \
        -lm \
        -ldl \
        -lutil \
        -lpthread \
        -lpython3.11 \
        -lsfml-graphics \
        -lsfml-window \
        -lsfml-system \
        -lsfml-audio \
        -ltcod \
        || abort_compile $fn
done

# Final executable
g++ \
    --std=c++17 \
    -I../../deps_linux \
    -I../../deps_linux/Python-3.11.1 \
    -I../../platform/linux \
    ../../obj/*.o \
    -o mcrogueface \
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
    -lsfml-audio \
    -ltcod \

