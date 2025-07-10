# Minimum version of CMake required
cmake_minimum_required(VERSION 3.14)

# Project name
project(McRogueFace)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Add include directories
#include_directories(${CMAKE_SOURCE_DIR}/deps_linux)
include_directories(${CMAKE_SOURCE_DIR}/deps)
#include_directories(${CMAKE_SOURCE_DIR}/deps_linux/Python-3.11.1)
include_directories(${CMAKE_SOURCE_DIR}/deps/libtcod)

include_directories(${CMAKE_SOURCE_DIR}/deps/cpython)
include_directories(${CMAKE_SOURCE_DIR}/deps/Python)

# Collect all the source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Create a list of libraries to link against
set(LINK_LIBS 
    sfml-graphics 
    sfml-window 
    sfml-system 
    sfml-audio 
    tcod)

# On Windows, add any additional libs and include directories
if(WIN32)
    # Windows-specific Python library name (no dots)
    list(APPEND LINK_LIBS python312)
    # Add the necessary Windows-specific libraries and include directories
    # include_directories(path_to_additional_includes)
    # link_directories(path_to_additional_libs)
    # list(APPEND LINK_LIBS additional_windows_libs)
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/windows)
else()
    # Unix/Linux specific libraries
    list(APPEND LINK_LIBS python3.12 m dl util pthread)
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/linux)
endif()

# Add the directory where the linker should look for the libraries
#link_directories(${CMAKE_SOURCE_DIR}/deps_linux)
link_directories(${CMAKE_SOURCE_DIR}/__lib)

# Define the executable target before linking libraries
add_executable(mcrogueface ${SOURCES})

# On Windows, set subsystem to WINDOWS to hide console
if(WIN32)
    set_target_properties(mcrogueface PROPERTIES
        WIN32_EXECUTABLE TRUE
        LINK_FLAGS "/SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup")
endif()

# Now the linker will find the libraries in the specified directory
target_link_libraries(mcrogueface ${LINK_LIBS})

# Copy assets to build directory post-build
add_custom_command(TARGET mcrogueface POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/assets $<TARGET_FILE_DIR:mcrogueface>/assets)

# Copy Python scripts to build directory post-build
add_custom_command(TARGET mcrogueface POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/src/scripts $<TARGET_FILE_DIR:mcrogueface>/scripts)

# Copy Python standard library to build directory
add_custom_command(TARGET mcrogueface POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_SOURCE_DIR}/__lib $<TARGET_FILE_DIR:mcrogueface>/lib)

# On Windows, copy DLLs to executable directory
if(WIN32)
    # Copy all DLL files from lib to the executable directory
    add_custom_command(TARGET mcrogueface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/__lib $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E echo "Copied DLLs to executable directory")
        
    # Alternative: Copy specific DLLs if you want more control
    # file(GLOB DLLS "${CMAKE_SOURCE_DIR}/__lib/*.dll")
    # foreach(DLL ${DLLS})
    #     add_custom_command(TARGET mcrogueface POST_BUILD
    #         COMMAND ${CMAKE_COMMAND} -E copy_if_different
    #         ${DLL} $<TARGET_FILE_DIR:mcrogueface>)
    # endforeach()
endif()

# rpath for including shared libraries (Linux/Unix only)
if(NOT WIN32)
    set_target_properties(mcrogueface PROPERTIES
                          INSTALL_RPATH "$ORIGIN/./lib")
endif()

