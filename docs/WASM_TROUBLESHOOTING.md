# WASM / Emscripten Troubleshooting Guide

Practical solutions for common issues when building, testing, and deploying McRogueFace as a WebAssembly application.

## Build Issues

### "emcmake not found"

The Emscripten SDK must be activated in your current shell before building:

```bash
source ~/emsdk/emsdk_env.sh
make wasm
```

This sets `PATH`, `EMSDK`, and other environment variables. You need to re-run it for each new terminal session.

### Build fails during CMake configure

If CMake fails during the Emscripten configure step, delete the build directory and re-configure:

```bash
rm -rf build-emscripten
make wasm
```

The Makefile targets skip CMake if a `Makefile` already exists in the build directory. Stale CMake caches from a prior SDK version or changed options cause configure errors.

### "memory access out of bounds" at startup

Usually caused by insufficient stack or memory. The build defaults to a 2 MB stack (`-sSTACK_SIZE=2097152`) and growable heap (`-sALLOW_MEMORY_GROWTH=1`). If you hit stack limits with deep recursion (e.g. during Python import), increase the stack size in `CMakeLists.txt`:

```cmake
-sSTACK_SIZE=4194304  # 4 MB
```

### Link errors about undefined symbols

The Emscripten build uses `-sERROR_ON_UNDEFINED_SYMBOLS=0` because some libc/POSIX symbols are stubbed. If you add new C++ code that calls missing POSIX APIs, you will get a runtime error rather than a link error. Check the browser console for `Aborted(Assertion failed: missing function: ...)`.

## Runtime Issues

### Python import errors

The WASM build bundles a filtered Python stdlib at build time via `--preload-file`. If a Python module is missing at runtime:

1. Check `wasm_stdlib/lib/` — this is the preloaded stdlib tree
2. If the module should be included, add it to `tools/stdlib_modules.yaml` under the appropriate category
3. Rebuild: `rm -rf build-emscripten && make wasm`

Some modules (like `socket`, `ssl`, `multiprocessing`) are intentionally excluded because they require OS features unavailable in the browser.

### "Synchronous XMLHttpRequest on the main thread is deprecated"

This warning appears when Python code triggers synchronous file I/O during module import. It's harmless but can cause slight UI freezes. The engine preloads all files into Emscripten's virtual filesystem before Python starts, so actual network requests don't happen.

### IndexedDB / persistent storage errors

The build uses `-lidbfs.js` for persistent storage (save games, user preferences). Common issues:

- **"mkdir failed" on first load**: The engine calls `FS.mkdir('/idbfs')` during initialization. If the path already exists from a prior version, this fails silently. The `emscripten_pre.js` file patches this.
- **Data not persisting**: Call `FS.syncfs(false, callback)` from JavaScript to flush changes to IndexedDB. The C++ side exposes `sync_storage()` via `Module.ccall`.
- **Private browsing**: IndexedDB is unavailable in some private/incognito modes. The engine falls back gracefully but data won't persist.

### Black screen / no rendering

Check the browser's developer console (F12) for errors. Common causes:

- **WebGL 2 not supported**: The build requires WebGL 2 (`-sMIN_WEBGL_VERSION=2`). Very old browsers or software renderers may not support it.
- **Canvas size is zero**: If the HTML container has no explicit size, the canvas may render at 0x0. The custom `shell.html` handles this, but custom embedding needs to set canvas dimensions.
- **Exception during init**: A Python error during `game.py` execution will abort rendering. Check console for Python tracebacks.

### Audio not working

Audio is stubbed in the WASM build. `SoundBuffer`, `Sound`, and `Music` objects exist but do nothing. This is documented in the Web Build Constraints table in CLAUDE.md.

## Debugging

### Enable debug builds

Use the debug WASM targets for full DWARF symbols and source maps:

```bash
make wasm-debug         # Full game with debug info
make playground-debug   # REPL with debug info
```

These produce larger binaries but enable:
- **Source-level debugging** in Chrome DevTools (via DWARF and source maps)
- **Readable stack traces** (via `--emit-symbol-map`)

### Reading WASM stack traces

Production WASM stack traces show mangled names like `$_ZN7UIFrame6renderEv`. To demangle:

1. Use the debug build which emits a `.symbols` file
2. Or pipe through `c++filt`: `echo '_ZN7UIFrame6renderEv' | c++filt`
3. Or use Chrome's DWARF extension for inline source mapping

### Browser developer tools

- **Chrome**: DevTools > Sources > shows C++ source files with DWARF debug builds
- **Firefox**: Debugger > limited DWARF support, better with source maps
- **Console**: All `printf`/`std::cout` output goes to the browser console
- **Network**: Check that `.data` (preloaded files) and `.wasm` loaded successfully
- **Memory**: Use Chrome's Memory tab to profile WASM heap usage

### Assertions

The build enables `-sASSERTIONS=2` and `-sSTACK_OVERFLOW_CHECK=2` by default (both debug and release). These catch:
- Null pointer dereferences in WASM memory
- Stack overflow before it corrupts the heap
- Invalid Emscripten API usage

## Deployment

### File sizes

Typical build sizes:

| Build | .wasm | .data | .js | Total |
|-------|-------|-------|-----|-------|
| Release | ~15 MB | ~25 MB | ~200 KB | ~40 MB |
| Debug | ~40 MB | ~25 MB | ~300 KB | ~65 MB |

The `.data` file contains the Python stdlib and game assets. Use the "light" stdlib preset to reduce it.

### Serving requirements

WASM files require specific HTTP headers:
- `Content-Type: application/wasm` for `.wasm` files
- CORS headers if serving from a CDN

The `make serve` targets use Python's `http.server` which handles MIME types correctly for local development.

### Embedding in custom pages

The build produces an HTML file from `shell.html` (or `shell_game.html`). To embed in your own page, you need:

1. The `.js`, `.wasm`, and `.data` files from the build directory
2. A canvas element with `id="canvas"`
3. Load the `.js` file, which bootstraps everything:

```html
<canvas id="canvas" width="1024" height="768"></canvas>
<script src="mcrogueface.js"></script>
```

### Game shell vs playground shell

- `make wasm` / `make wasm-game`: Uses `shell.html` or `shell_game.html` — includes REPL widget or fullscreen canvas
- `make playground`: Uses `shell.html` with REPL chrome — intended for interactive testing
- Set `MCRF_GAME_SHELL=ON` in CMake for fullscreen-only (no REPL)

## Known Limitations

1. **No dynamic module loading**: All Python modules must be preloaded at build time
2. **No threading**: JavaScript is single-threaded; Python's `threading` module is non-functional
3. **No filesystem writes to disk**: Writes go to an in-memory filesystem (optionally synced to IndexedDB)
4. **No audio**: Sound API is fully stubbed
5. **No ImGui console**: The debug overlay is desktop-only
6. **Input differences**: Some keyboard shortcuts are intercepted by the browser (Ctrl+W, F5, etc.)
