# McRogueFace Build Makefile
# Usage:
#   make              - Build for Linux (default)
#   make windows      - Cross-compile for Windows using MinGW (release)
#   make windows-debug - Cross-compile for Windows with console & debug symbols
#   make clean        - Clean Linux build
#   make clean-windows - Clean Windows build
#   make run          - Run the Linux build
#
# WebAssembly / Emscripten:
#   make wasm         - Build full game for web (requires emsdk activated)
#   make wasm-game    - Build game for web with fullscreen canvas (no REPL)
#   make playground   - Build minimal playground for web REPL
#   make serve        - Serve wasm build locally on port 8080
#   make serve-game   - Serve wasm-game build locally on port 8080
#   make clean-wasm   - Clean Emscripten builds
#
# Packaging:
#   make package-windows-light  - Windows with minimal stdlib (~5 MB)
#   make package-windows-full   - Windows with full stdlib (~15 MB)
#   make package-linux-light    - Linux with minimal stdlib
#   make package-linux-full     - Linux with full stdlib
#   make package-all            - All platform/preset combinations
#
# Release:
#   make version-bump NEXT_VERSION=x.y.z-suffix
#     Tags HEAD with current version, builds all packages, bumps to NEXT_VERSION

.PHONY: all linux windows windows-debug clean clean-windows clean-dist run
.PHONY: wasm wasm-game wasm-debug playground playground-debug serve serve-game serve-playground clean-wasm
.PHONY: package-windows-light package-windows-full package-linux-light package-linux-full package-all
.PHONY: version-bump
.PHONY: debug debug-test asan asan-test valgrind-test massif-test analyze clean-debug

# Number of parallel jobs for compilation
JOBS := $(shell nproc 2>/dev/null || echo 4)

all: linux

linux:
	@echo "Building McRogueFace for Linux..."
	@mkdir -p build
	@cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j$(JOBS)
	@echo "Build complete! Run with: ./build/mcrogueface"

windows:
	@echo "Cross-compiling McRogueFace for Windows..."
	@mkdir -p build-windows
	@cd build-windows && cmake .. \
		-DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/mingw-w64-x86_64.cmake \
		-DCMAKE_BUILD_TYPE=Release && make -j$(JOBS)
	@echo "Windows build complete! Output: build-windows/mcrogueface.exe"

windows-debug:
	@echo "Cross-compiling McRogueFace for Windows (debug with console)..."
	@mkdir -p build-windows-debug
	@cd build-windows-debug && cmake .. \
		-DCMAKE_TOOLCHAIN_FILE=../cmake/toolchains/mingw-w64-x86_64.cmake \
		-DCMAKE_BUILD_TYPE=Debug \
		-DMCRF_WINDOWS_CONSOLE=ON && make -j$(JOBS)
	@echo "Windows debug build complete! Output: build-windows-debug/mcrogueface.exe"
	@echo "Run from cmd.exe to see console output"

clean:
	@echo "Cleaning Linux build..."
	@rm -rf build

clean-windows:
	@echo "Cleaning Windows builds..."
	@rm -rf build-windows build-windows-debug

clean-dist:
	@echo "Cleaning distribution packages..."
	@rm -rf dist

clean-all: clean clean-windows clean-wasm clean-debug clean-dist
	@echo "All builds and packages cleaned."

run: linux
	@cd build && ./mcrogueface

# Debug and sanitizer targets
debug:
	@echo "Building McRogueFace with debug Python (pydebug assertions)..."
	@mkdir -p build-debug
	@cd build-debug && cmake .. \
		-DCMAKE_BUILD_TYPE=Debug \
		-DMCRF_DEBUG_PYTHON=ON && make -j$(JOBS)
	@echo "Debug build complete! Output: build-debug/mcrogueface"

debug-test: debug
	@echo "Running test suite with debug Python..."
	cd tests && MCRF_BUILD_DIR=../build-debug \
		MCRF_LIB_DIR=../__lib_debug \
		python3 run_tests.py -v

asan:
	@echo "Building McRogueFace with ASan + UBSan..."
	@mkdir -p build-asan
	@cd build-asan && cmake .. \
		-DCMAKE_BUILD_TYPE=Debug \
		-DMCRF_DEBUG_PYTHON=ON \
		-DMCRF_SANITIZE_ADDRESS=ON \
		-DMCRF_SANITIZE_UNDEFINED=ON && make -j$(JOBS)
	@echo "ASan build complete! Output: build-asan/mcrogueface"

asan-test: asan
	@echo "Running test suite under ASan + UBSan..."
	cd tests && MCRF_BUILD_DIR=../build-asan \
		MCRF_LIB_DIR=../__lib_debug \
		PYTHONMALLOC=malloc \
		ASAN_OPTIONS="detect_leaks=1:halt_on_error=1:print_summary=1" \
		LSAN_OPTIONS="suppressions=$(CURDIR)/sanitizers/asan.supp" \
		UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1" \
		python3 run_tests.py -v --sanitizer

valgrind-test: debug
	@echo "Running test suite under Valgrind memcheck..."
	cd tests && MCRF_BUILD_DIR=../build-debug \
		MCRF_LIB_DIR=../__lib_debug \
		MCRF_TIMEOUT_MULTIPLIER=50 \
		PYTHONMALLOC=malloc \
		python3 run_tests.py -v --valgrind

massif-test: debug
	@echo "Running heap profiling under Valgrind Massif..."
	@mkdir -p build-debug
	cd build-debug && valgrind --tool=massif \
		--massif-out-file=massif.out \
		--pages-as-heap=no \
		--detailed-freq=10 \
		--max-snapshots=100 \
		./mcrogueface --headless --exec ../tests/benchmarks/stress_test_suite.py
	@echo "Massif output: build-debug/massif.out"
	@echo "View with: ms_print build-debug/massif.out"

analyze:
	@echo "Running cppcheck static analysis..."
	cppcheck --enable=warning,performance,portability \
		--suppress=missingIncludeSystem \
		--suppress=unusedFunction \
		--suppress=noExplicitConstructor \
		--suppress=missingOverride \
		--inline-suppr \
		-I src/ -I deps/ -I deps/cpython -I deps/Python \
		-I src/platform -I src/3d -I src/tiled -I src/ldtk -I src/audio \
		--std=c++20 \
		--quiet \
		src/ 2>&1
	@echo "Static analysis complete."

clean-debug:
	@echo "Cleaning debug/sanitizer builds..."
	@rm -rf build-debug build-asan

# Packaging targets using tools/package.sh
package-windows-light: windows
	@./tools/package.sh windows light

package-windows-full: windows
	@./tools/package.sh windows full

package-linux-light: linux
	@./tools/package.sh linux light

package-linux-full: linux
	@./tools/package.sh linux full

package-all: windows linux
	@./tools/package.sh all

# Legacy target for backwards compatibility
package-windows: package-windows-full

# Emscripten / WebAssembly targets
# Requires: source ~/emsdk/emsdk_env.sh (or wherever your emsdk is installed)
#
# For iterative development, configure once then rebuild:
#   source ~/emsdk/emsdk_env.sh && emmake make -C build-emscripten
#
wasm:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-emscripten/Makefile ]; then \
		echo "Configuring WebAssembly build (full game)..."; \
		mkdir -p build-emscripten; \
		cd build-emscripten && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Release \
			-DMCRF_SDL2=ON; \
	fi
	@echo "Building McRogueFace for WebAssembly..."
	@emmake make -C build-emscripten -j$(JOBS)
	@echo "WebAssembly build complete! Files in build-emscripten/"
	@echo "Run 'make serve' to test locally"

playground:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-playground/Makefile ]; then \
		echo "Configuring Playground build..."; \
		mkdir -p build-playground; \
		cd build-playground && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Release \
			-DMCRF_SDL2=ON \
			-DMCRF_PLAYGROUND=ON; \
	fi
	@echo "Building McRogueFace Playground for WebAssembly..."
	@emmake make -C build-playground -j$(JOBS)
	@echo "Playground build complete! Files in build-playground/"
	@echo "Run 'make serve-playground' to test locally"

serve:
	@echo "Serving WebAssembly build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-emscripten && python3 -m http.server 8080

serve-playground:
	@echo "Serving Playground build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-playground && python3 -m http.server 8080

wasm-game:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-wasm-game/Makefile ]; then \
		echo "Configuring WebAssembly game build (fullscreen, no REPL)..."; \
		mkdir -p build-wasm-game; \
		cd build-wasm-game && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Release \
			-DMCRF_SDL2=ON \
			-DMCRF_GAME_SHELL=ON; \
	fi
	@echo "Building McRogueFace game for WebAssembly..."
	@emmake make -C build-wasm-game -j$(JOBS)
	@echo "Game build complete! Files in build-wasm-game/"
	@echo "Run 'make serve-game' to test locally"

serve-game:
	@echo "Serving game build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-wasm-game && python3 -m http.server 8080

wasm-demo:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-wasm-demo/Makefile ]; then \
		echo "Configuring WebAssembly demo build..."; \
		mkdir -p build-wasm-demo; \
		cd build-wasm-demo && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Release \
			-DMCRF_SDL2=ON \
			-DMCRF_DEMO=ON \
			-DMCRF_GAME_SHELL=ON; \
	fi
	@echo "Building McRogueFace demo for WebAssembly..."
	@emmake make -C build-wasm-demo -j$(JOBS)
	@cp web/index.html build-wasm-demo/index.html
	@echo "Demo build complete! Files in build-wasm-demo/"
	@echo "Run 'make serve-demo' to test locally"

serve-demo:
	@echo "Serving demo build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-wasm-demo && python3 -m http.server 8080

clean-wasm:
	@echo "Cleaning Emscripten builds..."
	@rm -rf build-emscripten build-playground build-wasm-game build-wasm-demo build-wasm-debug build-playground-debug

wasm-debug:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-wasm-debug/Makefile ]; then \
		echo "Configuring WebAssembly debug build (DWARF + source maps)..."; \
		mkdir -p build-wasm-debug; \
		cd build-wasm-debug && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Debug \
			-DMCRF_SDL2=ON \
			-DMCRF_WASM_DEBUG=ON; \
	fi
	@echo "Building McRogueFace for WebAssembly (debug)..."
	@emmake make -C build-wasm-debug -j$(JOBS)
	@echo "Debug WASM build complete! Files in build-wasm-debug/"
	@echo "Debug artifacts: .wasm.map (source map), .symbols (symbol map)"
	@echo "Run 'make serve-wasm-debug' to test locally"

serve-wasm-debug:
	@echo "Serving debug WASM build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-wasm-debug && python3 -m http.server 8080

playground-debug:
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	@if [ ! -f build-playground-debug/Makefile ]; then \
		echo "Configuring Playground debug build (DWARF + source maps)..."; \
		mkdir -p build-playground-debug; \
		cd build-playground-debug && emcmake cmake .. \
			-DCMAKE_BUILD_TYPE=Debug \
			-DMCRF_SDL2=ON \
			-DMCRF_PLAYGROUND=ON \
			-DMCRF_WASM_DEBUG=ON; \
	fi
	@echo "Building McRogueFace Playground for WebAssembly (debug)..."
	@emmake make -C build-playground-debug -j$(JOBS)
	@echo "Playground debug build complete! Files in build-playground-debug/"
	@echo "Run 'make serve-playground-debug' to test locally"

serve-playground-debug:
	@echo "Serving debug Playground build at http://localhost:8080"
	@echo "Press Ctrl+C to stop"
	@cd build-playground-debug && python3 -m http.server 8080

# Current version extracted from source
CURRENT_VERSION := $(shell grep 'MCRFPY_VERSION' src/McRogueFaceVersion.h | sed 's/.*"\(.*\)"/\1/')

# Release workflow: tag current version, build all packages, bump to next version
# Usage: make version-bump NEXT_VERSION=0.2.6-prerelease-7drl2026
version-bump:
ifndef NEXT_VERSION
	$(error Usage: make version-bump NEXT_VERSION=x.y.z-suffix)
endif
	@if ! command -v emcmake >/dev/null 2>&1; then \
		echo "Error: emcmake not found. Run 'source ~/emsdk/emsdk_env.sh' first."; \
		exit 1; \
	fi
	# git status (clean working dir check), but ignore modules/, because building submodules dirties their subdirs
	@if [ -n "$$(git status --porcelain | grep -v modules)" ]; then \
		echo "Error: Working tree is not clean. Commit or stash changes first."; \
		exit 1; \
	fi
	@echo "=== Releasing $(CURRENT_VERSION) ==="
	@# Idempotent tag: ok if it already points at HEAD (resuming partial run)
	@if git rev-parse "$(CURRENT_VERSION)" >/dev/null 2>&1; then \
		TAG_COMMIT=$$(git rev-parse "$(CURRENT_VERSION)^{}"); \
		HEAD_COMMIT=$$(git rev-parse HEAD); \
		if [ "$$TAG_COMMIT" != "$$HEAD_COMMIT" ]; then \
			echo "Error: Tag $(CURRENT_VERSION) already exists but points to a different commit."; \
			exit 1; \
		fi; \
		echo "Tag $(CURRENT_VERSION) already exists at HEAD (resuming)."; \
	else \
		git tag "$(CURRENT_VERSION)"; \
	fi
	$(MAKE) package-linux-full
	$(MAKE) package-windows-full
	$(MAKE) wasm
	@echo "Packaging WASM build..."
	@mkdir -p dist
	cd build-emscripten && zip -r ../dist/McRogueFace-$(CURRENT_VERSION)-WASM.zip \
		mcrogueface.html mcrogueface.js mcrogueface.wasm mcrogueface.data
	@echo ""
	@echo "Bumping version: $(CURRENT_VERSION) -> $(NEXT_VERSION)"
	@sed -i 's|MCRFPY_VERSION "$(CURRENT_VERSION)"|MCRFPY_VERSION "$(NEXT_VERSION)"|' src/McRogueFaceVersion.h
	@TAGGED_HASH=$$(git rev-parse --short HEAD); \
	git add src/McRogueFaceVersion.h && \
	git commit -m "Version bump: $(CURRENT_VERSION) ($$TAGGED_HASH) -> $(NEXT_VERSION)"
	@echo ""
	@echo "=== Release $(CURRENT_VERSION) complete ==="
	@echo "Tag:  $(CURRENT_VERSION)"
	@echo "Next: $(NEXT_VERSION)"
	@echo "Packages:"
	@ls -lh dist/*$(CURRENT_VERSION)* 2>/dev/null
