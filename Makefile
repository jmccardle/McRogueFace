# McRogueFace Build Makefile
# Usage:
#   make              - Build for Linux (default)
#   make windows      - Cross-compile for Windows using MinGW (release)
#   make windows-debug - Cross-compile for Windows with console & debug symbols
#   make clean        - Clean Linux build
#   make clean-windows - Clean Windows build
#   make run          - Run the Linux build
#
# Profiling (see docs/profiling.md):
#   make profile      - RelWithDebInfo + frame pointers build in build-profile/
#   make callgrind SCRIPT=tests/benchmarks/foo.py - Callgrind a headless benchmark
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
.PHONY: debug debug-test asan asan-test tsan tsan-test valgrind-test massif-test analyze clean-debug
.PHONY: profile callgrind clean-profile
.PHONY: install-hooks

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

clean-all: clean clean-windows clean-wasm clean-debug clean-profile clean-dist
	@echo "All builds and packages cleaned."

run: linux
	@cd build && ./mcrogueface

# Install git hooks by symlinking tools/hooks/* into .git/hooks/ (idempotent).
install-hooks:
	@hooks_dir="$$(git rev-parse --git-path hooks)"; \
	mkdir -p "$$hooks_dir"; \
	for hook in tools/hooks/*; do \
		[ -e "$$hook" ] || continue; \
		name="$$(basename "$$hook")"; \
		ln -sf "$$(pwd)/$$hook" "$$hooks_dir/$$name"; \
		echo "Linked $$hooks_dir/$$name -> $$hook"; \
	done

# ---------------------------------------------------------------------------
# Documentation / release
#
# Every piece of the docs pipeline already existed; nothing chained them, so the
# site drifted 26 engine commits behind without anything noticing. These targets
# are the chain.
#
# SITE_DIR is the mcrogueface.github.io checkout. Override if yours lives elsewhere:
#     make release-docs SITE_DIR=/path/to/mcrogueface.github.io
# ---------------------------------------------------------------------------
SITE_DIR ?= $(CURDIR)/../mcrogueface.github.io

# Two DIFFERENT refs, easily conflated:
#
#   BASE_REF     the PREVIOUS release. The API delta is measured against it, to answer
#                "what changed, and which pages does that oblige us to revisit?"
#   RELEASE_REF  the tag being CUT. The site pins its source links to it, which is what
#                freezes this version into the site's history.
#
# When cutting a release, set both:
#     make release-docs BASE_REF=0.2.8 RELEASE_REF=0.2.9
#
# Note: BASE_REF must carry api/manifest.json. The manifest infrastructure landed in
# 54624b3, so tags older than that (0.2.8 included) have no baseline to diff against --
# api_delta will say so rather than inventing one.
BASE_REF    ?= $(shell git describe --tags --abbrev=0 2>/dev/null)
RELEASE_REF ?= $(shell git describe --tags --always --abbrev=0 2>/dev/null)

# Regenerate everything derived from the compiled module: man page, API reference
# (HTML + Markdown), type stubs, and the tracked api/manifest.json.
docs: linux
	@./tools/generate_all_docs.sh
	@./build/mcrogueface --headless --exec ../tools/generate_api_manifest.py

# Re-run every docs snippet and stamp its `# mcrf:` header with what actually
# happened (status from the run, verified from the engine, objects from the source).
stamp-snippets: linux
	@python3 tools/stamp_snippets.py

# CI gate: fail if any snippet is broken or its stamp is stale. Writes nothing.
check-snippets: linux
	@python3 tools/stamp_snippets.py --check

# Render a deterministic preview PNG for every snippet into snippet-shots/ (gitignored;
# the images belong in the doc-site repo, which pulls them from here -- see #381). The
# images are a visual-regression oracle: a changed PNG means behaviour changed.
snippet-shots: linux
	@python3 tools/generate_snippet_shots.py

# What changed in the API since the last release, and which site pages that
# obligates you to update (resolved via each page's `mcrf.objects` frontmatter).
api-delta:
	@python3 tools/api_delta.py $(BASE_REF) . --site-dir $(SITE_DIR) --format md

# The full release documentation pass. Run this when cutting a tag: it refreshes
# everything the engine derives, proves the published samples still run, rebuilds
# the site's generated reference + snippet library against this engine, and prints
# the checklist of hand-written pages the API change obligates you to revisit.
#
# Deliberately NOT automatic: it does not commit, and it does not touch the
# hand-written pages. It tells you what it found and leaves the judgment to you.
release-docs: docs stamp-snippets
	@echo ""
	@echo "=== Regenerating the site against this engine (SITE_DIR=$(SITE_DIR)) ==="
	@test -d "$(SITE_DIR)" || { echo "SITE_DIR not found: $(SITE_DIR)"; exit 1; }
	@cd "$(SITE_DIR)" && python3 tools/build_reference.py
	@cd "$(SITE_DIR)" && python3 tools/build_library.py --ref $(RELEASE_REF)
	@echo ""
	@echo "=== API delta $(BASE_REF) -> now, and the pages it obligates ==="
	@python3 tools/api_delta.py $(BASE_REF) . --site-dir $(SITE_DIR) --format md
	@echo ""
	@echo "Site pinned to RELEASE_REF=$(RELEASE_REF); delta measured from BASE_REF=$(BASE_REF)."
	@echo "Next: review the delta above, update the hand-written pages it names,"
	@echo "      then commit both repos. For a Gitea checklist issue instead, run:"
	@echo "      python3 tools/api_delta.py $(BASE_REF) . --site-dir $(SITE_DIR) --format gitea"

.PHONY: docs stamp-snippets check-snippets snippet-shots api-delta release-docs

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

# Profiling build (#345): RelWithDebInfo (-O2 -g) + frame pointers, self-contained
# in build-profile/ (lib/assets/scripts copied like the normal build). Suited to
# both Callgrind (deterministic, no perms) and perf (--call-graph fp).
profile:
	@echo "Building McRogueFace for profiling (RelWithDebInfo + frame pointers)..."
	@mkdir -p build-profile
	@cd build-profile && cmake .. \
		-DCMAKE_BUILD_TYPE=RelWithDebInfo \
		-DMCRF_PROFILE=ON && make -j$(JOBS)
	@echo "Profile build complete! Binary: build-profile/mcrogueface"

# Callgrind a headless benchmark script. Deterministic, exact instruction counts,
# no special permissions. Usage: make callgrind SCRIPT=tests/benchmarks/foo.py
# Output: callgrind.out (feed to callgrind_annotate).
SCRIPT ?= tests/benchmarks/issue_331_property_read_bench.py
callgrind: profile
	@echo "Running Callgrind on $(SCRIPT)..."
	@cd build-profile && valgrind --tool=callgrind \
		--callgrind-out-file=callgrind.out \
		./mcrogueface --headless --exec ../$(SCRIPT)
	@echo "Done. Annotate with: callgrind_annotate build-profile/callgrind.out | head -60"

clean-profile:
	@echo "Cleaning profile build..."
	@rm -rf build-profile

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

# Fuzzing targets (clang-18 + libFuzzer + ASan + UBSan).
# Design: ONE instrumented executable `mcrfpy_fuzz` that embeds CPython,
# registers the mcrfpy module, and dispatches each libFuzzer iteration to
# a Python `fuzz_one_input(data)` function loaded from the script named by
# the MCRF_FUZZ_TARGET env var. libFuzzer instruments the C++ engine code
# where all the #258-#278 bugs live. No atheris dependency.
FUZZ_TARGETS := grid_entity property_types anim_timer_scene maps_procgen fov pathfinding_behavior audio_dsp import_parsers texture_factory shader_bindings
FUZZ_SECONDS ?= 30

# Shared env for running the fuzz binary. PYTHONHOME points at the build-fuzz
# copy of the bundled stdlib (post-build copied into build-fuzz/lib/).
# ASAN_OPTIONS: leak detection disabled because libFuzzer intentionally holds
# inputs for its corpus; abort_on_error ensures crashes are loud and repro-able.
define FUZZ_ENV
MCRF_LIB_DIR=../__lib_debug \
PYTHONMALLOC=malloc \
PYTHONHOME=../__lib/Python \
ASAN_OPTIONS="detect_leaks=0:halt_on_error=1:abort_on_error=1:print_stacktrace=1" \
UBSAN_OPTIONS="print_stacktrace=1:halt_on_error=1"
endef

fuzz-build:
	@echo "Building mcrfpy_fuzz with libFuzzer + ASan (clang-18)..."
	@mkdir -p build-fuzz
	@cd build-fuzz && CC=clang-18 CXX=clang++-18 cmake .. \
		-DCMAKE_BUILD_TYPE=Debug \
		-DMCRF_DEBUG_PYTHON=ON \
		-DMCRF_SANITIZE_ADDRESS=ON \
		-DMCRF_SANITIZE_UNDEFINED=ON \
		-DMCRF_FUZZER=ON \
		-DCMAKE_EXE_LINKER_FLAGS=-fuse-ld=lld && make -j$(JOBS) mcrfpy_fuzz
	@echo "Fuzz build complete! Output: build-fuzz/mcrfpy_fuzz"

fuzz: fuzz-build
	@for t in $(FUZZ_TARGETS); do \
		if [ ! -f tests/fuzz/fuzz_$$t.py ]; then \
			echo "SKIP: tests/fuzz/fuzz_$$t.py does not exist yet"; \
			continue; \
		fi; \
		echo "=== fuzzing $$t for $(FUZZ_SECONDS)s ==="; \
		mkdir -p tests/fuzz/corpora/$$t tests/fuzz/crashes; \
		( cd build-fuzz && $(FUZZ_ENV) MCRF_FUZZ_TARGET=$$t \
		  ./mcrfpy_fuzz \
		    -max_total_time=$(FUZZ_SECONDS) \
		    -artifact_prefix=../tests/fuzz/crashes/$$t- \
		    ../tests/fuzz/corpora/$$t ../tests/fuzz/seeds/$$t ) || exit 1; \
	done

fuzz-long: fuzz-build
	@test -n "$(TARGET)" || (echo "Usage: make fuzz-long TARGET=<name> SECONDS=<n>"; exit 1)
	@test -f tests/fuzz/fuzz_$(TARGET).py || (echo "No target: tests/fuzz/fuzz_$(TARGET).py"; exit 1)
	@mkdir -p tests/fuzz/corpora/$(TARGET) tests/fuzz/crashes
	@( cd build-fuzz && $(FUZZ_ENV) MCRF_FUZZ_TARGET=$(TARGET) \
	  ./mcrfpy_fuzz \
	    -max_total_time=$(or $(SECONDS),3600) \
	    -artifact_prefix=../tests/fuzz/crashes/$(TARGET)- \
	    ../tests/fuzz/corpora/$(TARGET) ../tests/fuzz/seeds/$(TARGET) )

fuzz-repro:
	@test -n "$(TARGET)" || (echo "Usage: make fuzz-repro TARGET=<name> CRASH=<path>"; exit 1)
	@test -n "$(CRASH)" || (echo "Usage: make fuzz-repro TARGET=<name> CRASH=<path>"; exit 1)
	@( cd build-fuzz && $(FUZZ_ENV) MCRF_FUZZ_TARGET=$(TARGET) \
	  ./mcrfpy_fuzz ../$(CRASH) )

clean-fuzz:
	@echo "Cleaning fuzz build and corpora..."
	@rm -rf build-fuzz tests/fuzz/corpora tests/fuzz/crashes

tsan:
	@echo "Building McRogueFace with TSan + free-threaded Python..."
	@echo "NOTE: Requires free-threaded debug Python built with:"
	@echo "  tools/build_debug_python.sh --tsan"
	@mkdir -p build-tsan
	@cd build-tsan && cmake .. \
		-DCMAKE_BUILD_TYPE=Debug \
		-DMCRF_FREE_THREADED_PYTHON=ON \
		-DMCRF_SANITIZE_THREAD=ON && make -j$(JOBS)
	@echo "TSan build complete! Output: build-tsan/mcrogueface"

tsan-test: tsan
	@echo "Running test suite under TSan..."
	cd tests && MCRF_BUILD_DIR=../build-tsan \
		MCRF_LIB_DIR=../__lib_debug \
		TSAN_OPTIONS="halt_on_error=1:second_deadlock_stack=1" \
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
	@rm -rf build-debug build-asan build-tsan build-fuzz

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
