#!/bin/bash
#
# mcrf-init.sh - Initialize a McRogueFace game project
#
# Creates a game project directory with symlinks to a pre-built engine,
# so game developers only write Python + assets, never rebuild the engine.
#
# Usage:
#   mcrf-init                  # initialize current directory
#   mcrf-init my-game          # create and initialize my-game/
#
# Setup (add to ~/.bashrc):
#   alias mcrf-init='/path/to/McRogueFace/mcrf-init.sh'
#   # or: export PATH="$PATH:/path/to/McRogueFace"
#
# After init:
#   make run                   # run the game
#   make dist                  # package for distribution

set -e

# --- Resolve engine root (where this script lives) ---
ENGINE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --- Determine game directory ---
if [ -n "$1" ]; then
    GAME_DIR="$(pwd)/$1"
    mkdir -p "$GAME_DIR"
else
    GAME_DIR="$(pwd)"
fi

# --- Colors ---
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

info()  { echo -e "${GREEN}[mcrf]${NC} $1"; }
warn()  { echo -e "${YELLOW}[mcrf]${NC} $1"; }
error() { echo -e "${RED}[mcrf]${NC} $1"; }

# --- Safety checks ---
if [ "$GAME_DIR" = "$ENGINE_ROOT" ]; then
    error "Cannot init inside the engine directory itself."
    exit 1
fi

if [ ! -f "$ENGINE_ROOT/build/mcrogueface" ]; then
    error "Engine not built. Run 'make' in $ENGINE_ROOT first."
    exit 1
fi

# Engine version for packaging
ENGINE_VERSION=$(grep 'MCRFPY_VERSION' "$ENGINE_ROOT/src/McRogueFaceVersion.h" \
    | sed 's/.*"\(.*\)"/\1/')

info "Initializing McRogueFace game project"
info "  Engine: $ENGINE_ROOT (v${ENGINE_VERSION})"
info "  Game:   $GAME_DIR"
echo

# --- Create game directories ---
mkdir -p "$GAME_DIR/assets"
mkdir -p "$GAME_DIR/scripts"

# --- Set up build/ (Linux) ---
info "Setting up build/ (Linux)..."
mkdir -p "$GAME_DIR/build"

# Binary
ln -sfn "$ENGINE_ROOT/build/mcrogueface" "$GAME_DIR/build/mcrogueface"

# Shared libraries (entire lib/ tree: .so files + Python stdlib + extensions)
ln -sfn "$ENGINE_ROOT/build/lib" "$GAME_DIR/build/lib"

# Game content: symlink to project's own directories
ln -sfn ../assets  "$GAME_DIR/build/assets"
ln -sfn ../scripts "$GAME_DIR/build/scripts"

# --- Set up build-windows/ (if engine has it) ---
if [ -f "$ENGINE_ROOT/build-windows/mcrogueface.exe" ]; then
    info "Setting up build-windows/..."
    mkdir -p "$GAME_DIR/build-windows"

    # Executable
    ln -sfn "$ENGINE_ROOT/build-windows/mcrogueface.exe" "$GAME_DIR/build-windows/mcrogueface.exe"

    # DLLs
    for dll in "$ENGINE_ROOT/build-windows/"*.dll; do
        [ -f "$dll" ] && ln -sfn "$dll" "$GAME_DIR/build-windows/$(basename "$dll")"
    done

    # Python stdlib zip
    [ -f "$ENGINE_ROOT/build-windows/python314.zip" ] && \
        ln -sfn "$ENGINE_ROOT/build-windows/python314.zip" "$GAME_DIR/build-windows/python314.zip"

    # Python lib directory
    [ -d "$ENGINE_ROOT/build-windows/lib" ] && \
        ln -sfn "$ENGINE_ROOT/build-windows/lib" "$GAME_DIR/build-windows/lib"

    # Game content
    ln -sfn ../assets  "$GAME_DIR/build-windows/assets"
    ln -sfn ../scripts "$GAME_DIR/build-windows/scripts"
else
    warn "No Windows build found (skipping build-windows/)"
fi

# --- WASM build info ---
info "WASM support: use 'make wasm' to build (requires emsdk)"

# --- Starter game.py ---
if [ ! -f "$GAME_DIR/scripts/game.py" ]; then
    info "Creating starter scripts/game.py..."
    cat > "$GAME_DIR/scripts/game.py" << 'PYTHON'
"""McRogueFace Game - created by mcrf-init"""
import mcrfpy

scene = mcrfpy.Scene("title")
ui = scene.children

ui.append(mcrfpy.Caption(
    text="My McRogueFace Game",
    pos=(512, 300),
    font=mcrfpy.Font("assets/JetbrainsMono.ttf"),
    fill_color=(255, 255, 255),
    font_size=48
))

ui.append(mcrfpy.Caption(
    text="Press ESC to quit",
    pos=(512, 400),
    font=mcrfpy.Font("assets/JetbrainsMono.ttf"),
    fill_color=(180, 180, 180),
    font_size=24
))

def on_key(key, state):
    if key == mcrfpy.Key.ESCAPE and state == mcrfpy.InputState.PRESSED:
        mcrfpy.exit()

scene.on_key = on_key
mcrfpy.current_scene = scene
PYTHON
fi

# --- Copy a default font if game assets/ is empty ---
if [ -z "$(ls -A "$GAME_DIR/assets/" 2>/dev/null)" ]; then
    if [ -f "$ENGINE_ROOT/assets/JetbrainsMono.ttf" ]; then
        info "Copying default font to assets/..."
        cp "$ENGINE_ROOT/assets/JetbrainsMono.ttf" "$GAME_DIR/assets/"
    fi
fi

# --- .gitignore ---
if [ ! -f "$GAME_DIR/.gitignore" ]; then
    info "Creating .gitignore..."
    cat > "$GAME_DIR/.gitignore" << 'GITIGNORE'
# McRogueFace game project
build/
build-windows/
build-wasm/
dist/
__pycache__/
*.pyc
*.png.bak
GITIGNORE
fi

# --- pyrightconfig.json (for Vim/LSP autocomplete) ---
if [ ! -f "$GAME_DIR/pyrightconfig.json" ]; then
    info "Creating pyrightconfig.json (IDE autocomplete)..."
    cat > "$GAME_DIR/pyrightconfig.json" << PYRIGHT
{
    "include": ["scripts"],
    "extraPaths": ["${ENGINE_ROOT}/stubs"],
    "pythonVersion": "3.14",
    "pythonPlatform": "Linux",
    "typeCheckingMode": "basic",
    "reportMissingModuleSource": false
}
PYRIGHT
fi

# --- Makefile ---
info "Creating Makefile..."
cat > "$GAME_DIR/Makefile" << MAKEFILE
# McRogueFace Game Project Makefile
# Generated by mcrf-init
#
# Engine: ${ENGINE_ROOT}

ENGINE_ROOT := ${ENGINE_ROOT}
GAME_NAME   := $(basename "$GAME_DIR")
GAME_DIR    := \$(shell pwd)

# Game version - edit this or create a VERSION file
VERSION := \$(shell cat VERSION 2>/dev/null || echo "0.1.0")

# Engine version (from the linked build)
ENGINE_VERSION := \$(shell grep 'MCRFPY_VERSION' "\$(ENGINE_ROOT)/src/McRogueFaceVersion.h" \\
    | sed 's/.*"\\(.*\\)"/\\1/' 2>/dev/null || echo "unknown")

.PHONY: run run-windows wasm serve-wasm dist dist-linux dist-windows dist-wasm clean-dist clean-wasm info

# ============================================================
# Run targets
# ============================================================

run:
	@cd build && ./mcrogueface

run-headless:
	@cd build && ./mcrogueface --headless --exec ../scripts/game.py

run-windows:
	@echo "Launch build-windows/mcrogueface.exe on a Windows machine or via Wine"

serve-wasm:
	@if [ ! -f build-wasm/mcrogueface.html ]; then \\
		echo "No WASM build found. Run 'make wasm' first."; \\
		exit 1; \\
	fi
	@echo "Serving WASM build at http://localhost:8080"
	@cd build-wasm && python3 -m http.server 8080

# ============================================================
# WASM build (requires emsdk)
# ============================================================

wasm:
	@if ! command -v emcmake >/dev/null 2>&1; then \\
		echo "Error: emcmake not found. Activate emsdk first:"; \\
		echo "  source ~/emsdk/emsdk_env.sh"; \\
		exit 1; \\
	fi
	@echo "Building WASM with game assets..."
	@emcmake cmake -S "\$(ENGINE_ROOT)" -B build-wasm \\
		-DMCRF_SDL2=ON \\
		-DMCRF_GAME_SHELL=ON \\
		-DMCRF_ASSETS_DIR="\$(GAME_DIR)/assets" \\
		-DMCRF_SCRIPTS_DIR="\$(GAME_DIR)/scripts"
	@emmake make -C build-wasm -j\$\$(nproc)
	@echo ""
	@echo "WASM build complete: build-wasm/"
	@echo "  make serve-wasm   - test in browser"
	@echo "  make dist-wasm    - package for distribution"

clean-wasm:
	@rm -rf build-wasm
	@echo "Cleaned build-wasm/"

# ============================================================
# Distribution packaging
# ============================================================

dist: dist-linux dist-windows dist-wasm
	@echo ""
	@echo "=== Packages ==="
	@ls -lh dist/ 2>/dev/null

dist-linux:
	@if [ ! -f build/mcrogueface ]; then \\
		echo "Error: build/mcrogueface not found. Run mcrf-init first."; \\
		exit 1; \\
	fi
	@echo "Packaging \$(GAME_NAME) for Linux..."
	@mkdir -p dist
	\$(eval PKG := dist/\$(GAME_NAME)-\$(VERSION)-Linux)
	@rm -rf \$(PKG)
	@mkdir -p \$(PKG)/lib
	@# Binary
	@cp "\$(ENGINE_ROOT)/build/mcrogueface" \$(PKG)/
	@# Shared libraries
	@for lib in libpython3.14.so.1.0 \\
	            libsfml-graphics.so.2.6.1 libsfml-window.so.2.6.1 \\
	            libsfml-system.so.2.6.1 libsfml-audio.so.2.6.1 \\
	            libtcod.so; do \\
		[ -f "\$(ENGINE_ROOT)/__lib/\$\$lib" ] && \\
			cp "\$(ENGINE_ROOT)/__lib/\$\$lib" \$(PKG)/lib/; \\
	done
	@# Library symlinks
	@cd \$(PKG)/lib && \\
		ln -sf libpython3.14.so.1.0 libpython3.14.so && \\
		ln -sf libsfml-graphics.so.2.6.1 libsfml-graphics.so.2.6 && \\
		ln -sf libsfml-graphics.so.2.6.1 libsfml-graphics.so && \\
		ln -sf libsfml-window.so.2.6.1 libsfml-window.so.2.6 && \\
		ln -sf libsfml-window.so.2.6.1 libsfml-window.so && \\
		ln -sf libsfml-system.so.2.6.1 libsfml-system.so.2.6 && \\
		ln -sf libsfml-system.so.2.6.1 libsfml-system.so && \\
		ln -sf libsfml-audio.so.2.6.1 libsfml-audio.so.2.6 && \\
		ln -sf libsfml-audio.so.2.6.1 libsfml-audio.so && \\
		ln -sf libtcod.so libtcod.so.2
	@# Python extension modules
	@if [ -d "\$(ENGINE_ROOT)/__lib/Python/lib.linux-x86_64-3.14" ]; then \\
		mkdir -p \$(PKG)/lib/Python/lib.linux-x86_64-3.14; \\
		for so in "\$(ENGINE_ROOT)/__lib/Python/lib.linux-x86_64-3.14"/*.so; do \\
			case "\$\$(basename \$\$so)" in \\
				*test*|xxlimited*|_ctypes_test*|_xxtestfuzz*) continue ;; \\
				*) cp "\$\$so" \$(PKG)/lib/Python/lib.linux-x86_64-3.14/ ;; \\
			esac; \\
		done; \\
	fi
	@# Python stdlib
	@if [ -d "\$(ENGINE_ROOT)/__lib/Python/Lib" ]; then \\
		mkdir -p \$(PKG)/lib/Python; \\
		cp -r "\$(ENGINE_ROOT)/__lib/Python/Lib" \$(PKG)/lib/Python/; \\
		rm -rf \$(PKG)/lib/Python/Lib/test \$(PKG)/lib/Python/Lib/tests \\
		       \$(PKG)/lib/Python/Lib/idlelib \$(PKG)/lib/Python/Lib/tkinter \\
		       \$(PKG)/lib/Python/Lib/turtledemo \$(PKG)/lib/Python/Lib/pydoc_data \\
		       \$(PKG)/lib/Python/Lib/lib2to3 \$(PKG)/lib/Python/Lib/ensurepip \\
		       \$(PKG)/lib/Python/Lib/_pyrepl; \\
		find \$(PKG)/lib/Python/Lib -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true; \\
		find \$(PKG)/lib/Python/Lib -name "*.pyc" -delete 2>/dev/null || true; \\
		find \$(PKG)/lib/Python/Lib -name "test_*.py" -delete 2>/dev/null || true; \\
	fi
	@# Game content (real copies, not symlinks)
	@cp -r assets \$(PKG)/assets
	@cp -r scripts \$(PKG)/scripts
	@# Run script
	@printf '#!/bin/bash\\nDIR="\$\$(cd "\$\$(dirname "\$\$0")" && pwd)"\\nexport LD_LIBRARY_PATH="\$\$DIR/lib:\$\$LD_LIBRARY_PATH"\\nexec "\$\$DIR/mcrogueface" "\$\$@"\\n' > \$(PKG)/run.sh
	@chmod +x \$(PKG)/run.sh
	@# Archive
	@cd dist && tar -czf "\$(GAME_NAME)-\$(VERSION)-Linux.tar.gz" "\$(GAME_NAME)-\$(VERSION)-Linux"
	@rm -rf \$(PKG)
	@echo "Created: dist/\$(GAME_NAME)-\$(VERSION)-Linux.tar.gz"

dist-windows:
	@if [ ! -f "\$(ENGINE_ROOT)/build-windows/mcrogueface.exe" ]; then \\
		echo "No Windows build available. Skipping."; \\
		exit 0; \\
	fi
	@echo "Packaging \$(GAME_NAME) for Windows..."
	@mkdir -p dist
	\$(eval PKG := dist/\$(GAME_NAME)-\$(VERSION)-Windows)
	@rm -rf \$(PKG)
	@mkdir -p \$(PKG)
	@# Executable and DLLs
	@cp "\$(ENGINE_ROOT)/build-windows/mcrogueface.exe" \$(PKG)/
	@for dll in "\$(ENGINE_ROOT)/build-windows/"*.dll; do \\
		[ -f "\$\$dll" ] && cp "\$\$dll" \$(PKG)/; \\
	done
	@# Python stdlib zip
	@[ -f "\$(ENGINE_ROOT)/build-windows/python314.zip" ] && \\
		cp "\$(ENGINE_ROOT)/build-windows/python314.zip" \$(PKG)/ || true
	@# Python lib directory
	@if [ -d "\$(ENGINE_ROOT)/build-windows/lib" ]; then \\
		cp -r "\$(ENGINE_ROOT)/build-windows/lib" \$(PKG)/lib; \\
	fi
	@# Game content (real copies)
	@cp -r assets \$(PKG)/assets
	@cp -r scripts \$(PKG)/scripts
	@# Archive
	@cd dist && zip -qr "\$(GAME_NAME)-\$(VERSION)-Windows.zip" "\$(GAME_NAME)-\$(VERSION)-Windows"
	@rm -rf \$(PKG)
	@echo "Created: dist/\$(GAME_NAME)-\$(VERSION)-Windows.zip"

dist-wasm:
	@if ! command -v emcmake >/dev/null 2>&1; then \\
		echo "WASM: emsdk not activated. Skipping WASM package."; \\
		echo "  To include WASM: source ~/emsdk/emsdk_env.sh && make dist-wasm"; \\
		exit 0; \\
	fi; \\
	if [ ! -f build-wasm/mcrogueface.html ]; then \\
		echo "Building WASM first..."; \\
		\$(MAKE) wasm || exit 1; \\
	fi; \\
	echo "Packaging \$(GAME_NAME) for Web..."; \\
	mkdir -p dist; \\
	PKG="dist/\$(GAME_NAME)-\$(VERSION)-Web"; \\
	rm -rf "\$\$PKG"; \\
	mkdir -p "\$\$PKG"; \\
	cp build-wasm/mcrogueface.html "\$\$PKG/index.html"; \\
	cp build-wasm/mcrogueface.js   "\$\$PKG/"; \\
	cp build-wasm/mcrogueface.wasm "\$\$PKG/"; \\
	cp build-wasm/mcrogueface.data "\$\$PKG/"; \\
	cd dist && zip -qr "\$(GAME_NAME)-\$(VERSION)-Web.zip" "\$(GAME_NAME)-\$(VERSION)-Web"; \\
	rm -rf "\$\$PKG"; \\
	echo "Created: dist/\$(GAME_NAME)-\$(VERSION)-Web.zip"

clean-dist:
	@rm -rf dist
	@echo "Cleaned dist/"

# ============================================================
# Info
# ============================================================

info:
	@echo "Game:    \$(GAME_NAME) v\$(VERSION)"
	@echo "Engine:  McRogueFace v\$(ENGINE_VERSION)"
	@echo "Root:    \$(ENGINE_ROOT)"
	@echo ""
	@echo "Targets:"
	@echo "  make run            Run the game"
	@echo "  make run-headless   Run headless (for testing)"
	@echo "  make wasm           Build for web (requires emsdk)"
	@echo "  make serve-wasm     Test WASM build in browser"
	@echo "  make dist           Package for all platforms"
	@echo "  make dist-linux     Package for Linux only"
	@echo "  make dist-windows   Package for Windows only"
	@echo "  make dist-wasm      Package for web only"
	@echo "  make clean-dist     Remove dist/"
	@echo "  make clean-wasm     Remove build-wasm/"
MAKEFILE

# --- VERSION file ---
if [ ! -f "$GAME_DIR/VERSION" ]; then
    echo "0.1.0" > "$GAME_DIR/VERSION"
fi

# --- Done ---
echo
info "Project ready!"
echo
echo -e "  ${BOLD}make run${NC}       - play the game"
echo -e "  ${BOLD}make dist${NC}      - package for distribution"
echo -e "  ${BOLD}make info${NC}      - show project info"
echo
echo -e "  Edit ${BOLD}scripts/game.py${NC} and ${BOLD}assets/${NC} to build your game."
echo -e "  Edit ${BOLD}VERSION${NC} to set your game version."
