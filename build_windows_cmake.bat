@echo off
REM Windows build script using cmake --build (generator-agnostic)
REM This version works with any CMake generator

echo Building McRogueFace for Windows using CMake...

REM Set build directory
set BUILD_DIR=build_win
set CONFIG=Release

REM Clean previous build
if exist %BUILD_DIR% rmdir /s /q %BUILD_DIR%
mkdir %BUILD_DIR%
cd %BUILD_DIR%

REM Configure with CMake
REM You can change the generator here if needed:
REM   -G "Visual Studio 17 2022" (VS 2022)
REM   -G "Visual Studio 16 2019" (VS 2019)
REM   -G "MinGW Makefiles" (MinGW)
REM   -G "Ninja" (Ninja build system)
cmake -G "Visual Studio 17 2022" -A x64 -DCMAKE_BUILD_TYPE=%CONFIG% ..
if errorlevel 1 (
    echo CMake configuration failed!
    cd ..
    exit /b 1
)

REM Build using cmake (works with any generator)
cmake --build . --config %CONFIG% --parallel
if errorlevel 1 (
    echo Build failed!
    cd ..
    exit /b 1
)

echo.
echo Build completed successfully!
echo Executable: %BUILD_DIR%\%CONFIG%\mcrogueface.exe
echo.

cd ..