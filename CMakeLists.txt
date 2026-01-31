# Minimum version of CMake required
cmake_minimum_required(VERSION 3.14)

# Project name
project(McRogueFace)

# Specify the C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Headless build option (no SFML, no graphics - for server/testing/Emscripten prep)
option(MCRF_HEADLESS "Build without graphics dependencies (SFML, ImGui)" OFF)

# SDL2 backend option (SDL2 + OpenGL ES 2 - for Emscripten/WebGL, Android, cross-platform)
option(MCRF_SDL2 "Build with SDL2+OpenGL ES 2 backend instead of SFML" OFF)

# Emscripten builds: use SDL2 if specified, otherwise fall back to headless
if(EMSCRIPTEN)
    if(MCRF_SDL2)
        message(STATUS "Emscripten detected - using SDL2 backend")
        set(MCRF_HEADLESS OFF)
    else()
        set(MCRF_HEADLESS ON)
        message(STATUS "Emscripten detected - forcing HEADLESS mode (use -DMCRF_SDL2=ON for graphics)")
    endif()
endif()

if(MCRF_SDL2)
    message(STATUS "Building with SDL2 backend - SDL2+OpenGL ES 2")
endif()

if(MCRF_HEADLESS)
    message(STATUS "Building in HEADLESS mode - no SFML/ImGui dependencies")
endif()

# Detect cross-compilation for Windows (MinGW)
if(CMAKE_CROSSCOMPILING AND WIN32)
    set(MCRF_CROSS_WINDOWS TRUE)
    message(STATUS "Cross-compiling for Windows using MinGW")
endif()

# Add include directories
include_directories(${CMAKE_SOURCE_DIR}/deps)
include_directories(SYSTEM ${CMAKE_SOURCE_DIR}/deps/libtcod)

# Python includes: use different paths for Windows vs Linux vs Emscripten
if(EMSCRIPTEN)
    # Emscripten build: use Python headers compiled for wasm32-emscripten
    # The pyconfig.h from cross-build has correct LONG_BIT and other settings
    set(PYTHON_WASM_BUILD "${CMAKE_SOURCE_DIR}/deps/cpython/cross-build/wasm32-emscripten/build/python")
    # Force-include wasm pyconfig.h BEFORE anything else to set correct platform defines
    add_compile_options(-include ${PYTHON_WASM_BUILD}/pyconfig.h)
    # Override LONG_BIT - Emscripten's limits.h incorrectly defines it as 64 for wasm32
    add_compile_definitions(LONG_BIT=32)
    # Include wasm build directory FIRST so its pyconfig.h is found by #include "pyconfig.h"
    include_directories(BEFORE ${PYTHON_WASM_BUILD})
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython/Include)
    message(STATUS "Using Emscripten Python from: ${PYTHON_WASM_BUILD}")
elseif(MCRF_CROSS_WINDOWS)
    # Windows cross-compilation: use cpython headers with PC/pyconfig.h
    # Problem: Python.h uses #include "pyconfig.h" which finds Include/pyconfig.h (Linux) first
    # Solution: Use -include to force Windows pyconfig.h to be included first
    # This defines MS_WINDOWS before Python.h is processed, ensuring correct struct layouts
    add_compile_options(-include ${CMAKE_SOURCE_DIR}/deps/cpython/PC/pyconfig.h)
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython/Include)
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython/PC)  # For other Windows-specific headers
    # Also include SFML and libtcod Windows headers
    include_directories(${CMAKE_SOURCE_DIR}/__lib_windows/sfml/include)
    include_directories(SYSTEM ${CMAKE_SOURCE_DIR}/__lib_windows/libtcod/include)
else()
    # Native builds (Linux/Windows): use existing Python setup
    include_directories(${CMAKE_SOURCE_DIR}/deps/cpython)
    include_directories(${CMAKE_SOURCE_DIR}/deps/Python)
endif()

# ImGui and ImGui-SFML include directories (not needed in headless or SDL2 mode)
# SDL2 builds will use ImGui with SDL2 backend later; for now, no ImGui
if(NOT MCRF_HEADLESS AND NOT MCRF_SDL2)
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
endif()

# Collect all the source files
file(GLOB_RECURSE SOURCES "src/*.cpp")

# Add ImGui sources to the build (only if using SFML)
if(NOT MCRF_HEADLESS AND NOT MCRF_SDL2)
    list(APPEND SOURCES ${IMGUI_SOURCES})
endif()

# Find OpenGL (required by ImGui-SFML) - not needed in headless mode
# SDL2 builds handle OpenGL ES 2 differently (via SDL2 or Emscripten)
if(NOT MCRF_HEADLESS AND NOT MCRF_SDL2)
    if(MCRF_CROSS_WINDOWS)
        # For cross-compilation, OpenGL is provided by MinGW
        set(OPENGL_LIBRARIES opengl32)
    else()
        find_package(OpenGL REQUIRED)
        set(OPENGL_LIBRARIES OpenGL::GL)
    endif()
endif()

# Create a list of libraries to link against
if(EMSCRIPTEN)
    # Emscripten build: link against WASM-compiled Python and libtcod
    set(PYTHON_WASM_BUILD "${CMAKE_SOURCE_DIR}/deps/cpython/cross-build/wasm32-emscripten/build/python")
    set(PYTHON_WASM_PREFIX "${CMAKE_SOURCE_DIR}/deps/cpython/cross-build/wasm32-emscripten/prefix")
    set(LIBTCOD_WASM_BUILD "${CMAKE_SOURCE_DIR}/modules/libtcod-headless/build-emscripten")
    # Collect HACL crypto object files (not included in libpython3.14.a)
    file(GLOB PYTHON_HACL_OBJECTS "${PYTHON_WASM_BUILD}/Modules/_hacl/*.o")
    set(LINK_LIBS
        ${PYTHON_WASM_BUILD}/libpython3.14.a
        ${PYTHON_HACL_OBJECTS}
        ${PYTHON_WASM_BUILD}/Modules/expat/libexpat.a
        ${PYTHON_WASM_PREFIX}/lib/libmpdec.a
        ${PYTHON_WASM_PREFIX}/lib/libffi.a
        ${LIBTCOD_WASM_BUILD}/libtcod.a
        ${LIBTCOD_WASM_BUILD}/_deps/lodepng-c-build/liblodepng-c.a
        ${LIBTCOD_WASM_BUILD}/_deps/utf8proc-build/libutf8proc.a)
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/linux)  # Use Linux platform stubs for now
    # For SDL2 builds, add stb headers for image/font loading
    if(MCRF_SDL2)
        include_directories(${CMAKE_SOURCE_DIR}/deps/stb)
    endif()
    message(STATUS "Linking Emscripten Python: ${PYTHON_WASM_BUILD}/libpython3.14.a")
    message(STATUS "Linking Emscripten libtcod: ${LIBTCOD_WASM_BUILD}/libtcod.a")
elseif(MCRF_SDL2)
    # SDL2 build (non-Emscripten): link against SDL2 and system libraries
    # Note: For desktop SDL2 builds in the future
    find_package(SDL2 REQUIRED)
    find_package(OpenGL REQUIRED)
    set(LINK_LIBS
        SDL2::SDL2
        OpenGL::GL
        tcod
        python3.14
        m dl util pthread)
    include_directories(${CMAKE_SOURCE_DIR}/deps/platform/linux)
    include_directories(${CMAKE_SOURCE_DIR}/deps/stb)  # stb_image.h, stb_truetype.h
    link_directories(${CMAKE_SOURCE_DIR}/__lib)
    message(STATUS "Building with SDL2 backend (desktop)")
elseif(MCRF_HEADLESS)
    # Headless build: no SFML, no OpenGL
    if(WIN32 OR MCRF_CROSS_WINDOWS)
        set(LINK_LIBS
            libtcod
            python314)
        if(MCRF_CROSS_WINDOWS)
            include_directories(${CMAKE_SOURCE_DIR}/deps/platform/windows)
            link_directories(${CMAKE_SOURCE_DIR}/__lib_windows/libtcod/lib)
            link_directories(${CMAKE_SOURCE_DIR}/__lib_windows)
        else()
            include_directories(${CMAKE_SOURCE_DIR}/deps/platform/windows)
            link_directories(${CMAKE_SOURCE_DIR}/__lib)
        endif()
    else()
        # Unix/Linux headless build
        set(LINK_LIBS
            tcod
            python3.14
            m dl util pthread)
        include_directories(${CMAKE_SOURCE_DIR}/deps/platform/linux)
        link_directories(${CMAKE_SOURCE_DIR}/__lib)
    endif()
elseif(MCRF_CROSS_WINDOWS)
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
# We ALWAYS need this because libtcod headers expect SDL3, not SDL2
# Our SDL2 backend is separate from libtcod's SDL3 renderer
target_compile_definitions(mcrogueface PRIVATE NO_SDL)

# Define MCRF_HEADLESS for headless builds (excludes SFML/ImGui code)
if(MCRF_HEADLESS)
    target_compile_definitions(mcrogueface PRIVATE MCRF_HEADLESS)
endif()

# Define MCRF_SDL2 for SDL2 builds (uses SDL2+OpenGL ES 2 instead of SFML)
if(MCRF_SDL2)
    target_compile_definitions(mcrogueface PRIVATE MCRF_SDL2)
endif()

# Emscripten-specific link options (use ports for zlib, bzip2, sqlite3)
if(EMSCRIPTEN)
    # Base Emscripten options
    set(EMSCRIPTEN_LINK_OPTIONS
        -sUSE_ZLIB=1
        -sUSE_BZIP2=1
        -sUSE_SQLITE3=1
        -sALLOW_MEMORY_GROWTH=1
        -sSTACK_SIZE=2097152
        -sEXPORTED_RUNTIME_METHODS=ccall,cwrap
        -sASSERTIONS=2
        -sSTACK_OVERFLOW_CHECK=2
        -fexceptions
        -sNO_DISABLE_EXCEPTION_CATCHING
        # Disable features that require dynamic linking support
        -sERROR_ON_UNDEFINED_SYMBOLS=0
        -sALLOW_UNIMPLEMENTED_SYSCALLS=1
        # Preload Python stdlib into virtual filesystem at /lib/python3.14
        --preload-file=${CMAKE_SOURCE_DIR}/wasm_stdlib/lib@/lib
        # Preload game scripts into /scripts
        --preload-file=${CMAKE_SOURCE_DIR}/src/scripts@/scripts
        # Preload assets
        --preload-file=${CMAKE_SOURCE_DIR}/assets@/assets
        # Use custom HTML shell for crisp pixel rendering
        --shell-file=${CMAKE_SOURCE_DIR}/src/shell.html
        # Pre-JS to fix browser zoom causing undefined values in events
        --pre-js=${CMAKE_SOURCE_DIR}/src/emscripten_pre.js
    )

    # Add SDL2 options if using SDL2 backend
    if(MCRF_SDL2)
        list(APPEND EMSCRIPTEN_LINK_OPTIONS
            -sUSE_SDL=2
            -sFULL_ES2=1
            -sMIN_WEBGL_VERSION=2
            -sMAX_WEBGL_VERSION=2
        )
        # SDL2 flags are also needed at compile time for headers
        target_compile_options(mcrogueface PRIVATE
            -sUSE_SDL=2
        )
        message(STATUS "Emscripten SDL2 options enabled: -sUSE_SDL=2 -sFULL_ES2=1")
    endif()

    target_link_options(mcrogueface PRIVATE ${EMSCRIPTEN_LINK_OPTIONS})

    # Output as HTML to use the shell file
    set_target_properties(mcrogueface PROPERTIES SUFFIX ".html")

    # Set Python home for the embedded interpreter
    target_compile_definitions(mcrogueface PRIVATE
        MCRF_WASM_PYTHON_HOME="/lib/python3.14"
    )
endif()

# On Windows, define Py_ENABLE_SHARED for proper Python DLL imports
# Py_PYCONFIG_H prevents Include/pyconfig.h (Linux config) from being included
# (PC/pyconfig.h already defines HAVE_DECLSPEC_DLL and MS_WINDOWS)
if(WIN32 OR MCRF_CROSS_WINDOWS)
    target_compile_definitions(mcrogueface PRIVATE Py_ENABLE_SHARED Py_PYCONFIG_H)
endif()

# On Windows, set subsystem to WINDOWS to hide console (release builds only)
# Use -DMCRF_WINDOWS_CONSOLE=ON for debug builds with console output
option(MCRF_WINDOWS_CONSOLE "Keep console window visible for debugging" OFF)

if(WIN32 AND NOT MCRF_CROSS_WINDOWS)
    # MSVC-specific flags
    if(NOT MCRF_WINDOWS_CONSOLE)
        set_target_properties(mcrogueface PROPERTIES
            WIN32_EXECUTABLE TRUE
            LINK_FLAGS "/SUBSYSTEM:WINDOWS /ENTRY:mainCRTStartup")
    endif()
elseif(MCRF_CROSS_WINDOWS)
    # MinGW cross-compilation
    if(NOT MCRF_WINDOWS_CONSOLE)
        # Release: use -mwindows to hide console
        set_target_properties(mcrogueface PROPERTIES
            WIN32_EXECUTABLE TRUE
            LINK_FLAGS "-mwindows")
    else()
        # Debug: keep console for stdout/stderr output
        message(STATUS "Windows console enabled for debugging")
    endif()
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

