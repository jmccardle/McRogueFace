# CMake toolchain file for cross-compiling to Windows using MinGW-w64
# Usage: cmake -DCMAKE_TOOLCHAIN_FILE=cmake/toolchains/mingw-w64-x86_64.cmake ..

set(CMAKE_SYSTEM_NAME Windows)
set(CMAKE_SYSTEM_PROCESSOR x86_64)

# Specify the cross-compiler (use posix variant for std::mutex support)
set(CMAKE_C_COMPILER x86_64-w64-mingw32-gcc-posix)
set(CMAKE_CXX_COMPILER x86_64-w64-mingw32-g++-posix)
set(CMAKE_RC_COMPILER x86_64-w64-mingw32-windres)

# Target environment location
set(CMAKE_FIND_ROOT_PATH /usr/x86_64-w64-mingw32)

# Add MinGW system include directories for Windows headers
include_directories(SYSTEM /usr/x86_64-w64-mingw32/include)

# Adjust search behavior
set(CMAKE_FIND_ROOT_PATH_MODE_PROGRAM NEVER)
set(CMAKE_FIND_ROOT_PATH_MODE_LIBRARY ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_INCLUDE ONLY)
set(CMAKE_FIND_ROOT_PATH_MODE_PACKAGE ONLY)

# Static linking of libgcc and libstdc++ to avoid runtime dependency issues
# Enable auto-import for Python DLL data symbols
set(CMAKE_EXE_LINKER_FLAGS_INIT "-static-libgcc -static-libstdc++ -Wl,--enable-auto-import")
set(CMAKE_SHARED_LINKER_FLAGS_INIT "-static-libgcc -static-libstdc++ -Wl,--enable-auto-import")

# Windows-specific defines
add_definitions(-DWIN32 -D_WIN32 -D_WINDOWS)
add_definitions(-DMINGW_HAS_SECURE_API)

# Disable console window for GUI applications (optional, can be overridden)
# set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -mwindows")
