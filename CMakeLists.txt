# Minimum version of CMake required
cmake_minimum_required(VERSION 3.14)

# Project name
project(McRogueFace)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Detect cross-compilation for Windows (MinGW)
if(CMAKE_CROSSCOMPILING AND WIN32)
    set(MCRF_CROSS_WINDOWS TRUE)
    message(STATUS "Cross-compiling for Windows using MinGW")
endif()

# Add include directories
include_directories(${CMAKE_SOURCE_DIR}/deps)
include_directories(${CMAKE_SOURCE_DIR}/deps/libtcod)

# Python includes: use different paths for Windows vs Linux
if(MCRF_CROSS_WINDOWS)
    # Windows cross-compilation: use cpython headers with PC/pyconfig.h
    # Problem: Python.h uses #include "pyconfig.h" which finds Include/pyconfig.h (Linux) first
    # Solution: Use -include to force Windows pyconfig.h to be included first
    # This defines MS_WINDOWS before Python.h is processed, ensuring correct struct layouts
    add_compile_options(-include ${CMAKE_SOURCE_DIR}/deps/cpython/PC/pyconfig.h)
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython/Include)
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython/PC)  # For other Windows-specific headers
    # Also include SFML and libtcod Windows headers
    include_directories(${CMAKE_SOURCE_DIR}/__lib_windows/sfml/include)
    include_directories(${CMAKE_SOURCE_DIR}/__lib_windows/libtcod/include)
else()
    # Native builds (Linux/Windows): use existing Python setup
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython)
    include_directories(${CMAKE_SOURCE_DIR}/deps/Python)
endif()

# ImGui and ImGui-SFML include directories
include_directories(${CMAKE_SOURCE_DIR}/modules/imgui)
include_directories(${CMAKE_SOURCE_DIR}/modules/imgui-sfml)

# ImGui source files
set(IMGUI_SOURCES
    ${CMAKE_SOURCE_DIR}/modules/imgui/imgui.cpp
    ${CMAKE_SOURCE_DIR}/modules/imgui/imgui_draw.cpp
    ${CMAKE_SOURCE_DIR}/modules/imgui/imgui_tables.cpp
    ${CMAKE_SOURCE_DIR}/modules/imgui/imgui_widgets.cpp
    ${CMAKE_SOURCE_DIR}/modules/imgui-sfml/imgui-SFML.cpp
)

# Collect all the source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Add ImGui sources to the build
list(APPEND SOURCES ${IMGUI_SOURCES})

# Find OpenGL (required by ImGui-SFML)
if(MCRF_CROSS_WINDOWS)
    # For cross-compilation, OpenGL is provided by MinGW
    set(OPENGL_LIBRARIES opengl32)
else()
    find_package(OpenGL REQUIRED)
    set(OPENGL_LIBRARIES OpenGL::GL)
endif()

# Create a list of libraries to link against
if(MCRF_CROSS_WINDOWS)
    # MinGW cross-compilation: use full library names
    set(LINK_LIBS
        sfml-graphics
        sfml-window
        sfml-system
        sfml-audio
        libtcod
        python314
        ${OPENGL_LIBRARIES})

    # Add Windows system libraries needed by SFML and MinGW
    list(APPEND LINK_LIBS
        winmm      # Windows multimedia (for audio)
        gdi32      # Graphics Device Interface
        ws2_32     # Winsock (networking, used by some deps)
        ole32      # OLE support
        oleaut32   # OLE automation
        uuid       # UUID library
        comdlg32   # Common dialogs
        imm32      # Input Method Manager
        version    # Version info
    )

    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/windows)

    # Link directories for cross-compiled Windows libs
    link_directories(${CMAKE_SOURCE_DIR}/__lib_windows/sfml/lib)
    link_directories(${CMAKE_SOURCE_DIR}/__lib_windows/libtcod/lib)
    link_directories(${CMAKE_SOURCE_DIR}/__lib_windows)
elseif(WIN32)
    # Native Windows build (MSVC)
    set(LINK_LIBS
        sfml-graphics
        sfml-window
        sfml-system
        sfml-audio
        tcod
        python314
        ${OPENGL_LIBRARIES})
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/windows)
    link_directories(${CMAKE_SOURCE_DIR}/__lib)
else()
    # Unix/Linux build
    set(LINK_LIBS
        sfml-graphics
        sfml-window
        sfml-system
        sfml-audio
        tcod
        python3.14
        m dl util pthread
        ${OPENGL_LIBRARIES})
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/linux)
    link_directories(${CMAKE_SOURCE_DIR}/__lib)
endif()

# Define the executable target before linking libraries
add_executable(mcrogueface ${SOURCES})

# Define NO_SDL for libtcod-headless headers (excludes SDL-dependent code)
target_compile_definitions(mcrogueface PRIVATE NO_SDL)

# On Windows, define Py_ENABLE_SHARED for proper Python DLL imports
# Py_PYCONFIG_H prevents Include/pyconfig.h (Linux config) from being included
# (PC/pyconfig.h already defines HAVE_DECLSPEC_DLL and MS_WINDOWS)
if(WIN32 OR MCRF_CROSS_WINDOWS)
    target_compile_definitions(mcrogueface PRIVATE Py_ENABLE_SHARED Py_PYCONFIG_H)
endif()

# On Windows, set subsystem to WINDOWS to hide console
if(WIN32 AND NOT MCRF_CROSS_WINDOWS)
    # MSVC-specific flags
    set_target_properties(mcrogueface PROPERTIES
        WIN32_EXECUTABLE TRUE
        LINK_FLAGS "/SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup")
elseif(MCRF_CROSS_WINDOWS)
    # MinGW cross-compilation: use -mwindows to hide console
    set_target_properties(mcrogueface PROPERTIES
        WIN32_EXECUTABLE TRUE
        LINK_FLAGS "-mwindows")
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
if(MCRF_CROSS_WINDOWS)
    # Cross-compilation: copy DLLs from __lib_windows
    add_custom_command(TARGET mcrogueface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/__lib_windows/sfml/bin $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/__lib_windows/libtcod/bin $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_SOURCE_DIR}/__lib_windows/python314.dll $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_SOURCE_DIR}/__lib_windows/python3.dll $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_SOURCE_DIR}/__lib_windows/vcruntime140.dll $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_SOURCE_DIR}/__lib_windows/vcruntime140_1.dll $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E copy
        /usr/x86_64-w64-mingw32/lib/libwinpthread-1.dll $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E echo "Copied Windows DLLs to executable directory")

    # Copy Python standard library zip
    add_custom_command(TARGET mcrogueface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy
        ${CMAKE_SOURCE_DIR}/__lib_windows/python314.zip $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E echo "Copied Python stdlib")
elseif(WIN32)
    # Native Windows build: copy DLLs from __lib
    add_custom_command(TARGET mcrogueface POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_SOURCE_DIR}/__lib $<TARGET_FILE_DIR:mcrogueface>
        COMMAND ${CMAKE_COMMAND} -E echo "Copied DLLs to executable directory")
endif()

# rpath for including shared libraries (Linux/Unix only)
if(NOT WIN32)
    set_target_properties(mcrogueface PROPERTIES
                          INSTALL_RPATH "$ORIGIN/./lib")
endif()

