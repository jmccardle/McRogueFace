@echo off
REM Windows build script for McRogueFace
REM Run this over SSH without Visual Studio GUI

echo Building McRogueFace for Windows...

REM Clean previous build
if exist build_win rmdir /s /q build_win
mkdir build_win
cd build_win

REM Generate Visual Studio project files with CMake
REM Use -G to specify generator, -A for architecture
REM Visual Studio 2022 = "Visual Studio 17 2022"
REM Visual Studio 2019 = "Visual Studio 16 2019"
cmake -G "Visual Studio 17 2022" -A x64 ..
if errorlevel 1 (
    echo CMake configuration failed!
    exit /b 1
)

REM Build using MSBuild (comes with Visual Studio)
REM You can also use cmake --build . --config Release
msbuild McRogueFace.sln /p:Configuration=Release /p:Platform=x64 /m
if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build completed successfully!
echo Executable location: build_win\Release\mcrogueface.exe

REM Alternative: Using cmake to build (works with any generator)
REM cmake --build . --config Release --parallel

cd ..