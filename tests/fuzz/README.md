# McRogueFace Python API fuzzing harness (#283)

Native clang+libFuzzer+ASan harness that drives the `mcrfpy` Python API from
Python fuzz targets. libFuzzer instruments the C++ engine code (where all the
#258-#278 bugs live); Python drives the fuzzing logic through a simple byte
consumer. No atheris dependency — Python-level coverage would add nothing here
because the bugs live below the API boundary.

## Prerequisites

- `clang-18`, `clang++-18`, `lld-18` on `PATH` (Debian: `apt install clang-18 lld-18`)
- `libclang_rt.fuzzer-18-dev` (for `-fsanitize=fuzzer`) — verify with
  `clang-18 -print-file-name=libclang_rt.fuzzer-x86_64.a`
- Debug CPython built per top-level CLAUDE.md (`tools/build_debug_python.sh`)

## Build

```sh
make fuzz-build
```

Produces `build-fuzz/mcrfpy_fuzz`, a single libFuzzer-linked executable. All
six fuzz targets share this binary — target selection is by env var.

## Run

```sh
make fuzz                            # 30s smoke on each of 6 targets
make fuzz FUZZ_SECONDS=300           # 5min each
make fuzz-long TARGET=grid_entity SECONDS=3600   # 1hr on one target
make fuzz-repro TARGET=grid_entity CRASH=tests/fuzz/crashes/grid_entity-abc123
make clean-fuzz                      # Wipe build-fuzz/, corpora/, crashes/
```

Corpora live under `tests/fuzz/corpora/<target>/` (gitignored — libFuzzer
grows these), crashes under `tests/fuzz/crashes/` (gitignored — triage
dir). Seed inputs committed to `tests/fuzz/seeds/<target>/` are read-only.

## Targets

| Script | Surface | Hunts |
|---|---|---|
| `fuzz_grid_entity.py` | EntityCollection append/remove/insert/extend/slice across differently-sized grids, `entity.die` during iteration | #258-#263, #273, #274 |
| `fuzz_property_types.py` | Random property get/set with type confusion on Frame/Caption/Sprite/Entity/Grid/TileLayer/ColorLayer | #267, #268, #272 |
| `fuzz_anim_timer_scene.py` | Animation + Timer state machine, Frame reparenting, scene swap in callbacks | #269, #270, #275, #277 |
| `fuzz_maps_procgen.py` | HeightMap/DiscreteMap ops and conversions, NoiseSource.sample, BSP.to_heightmap | new |
| `fuzz_fov.py` | grid.compute_fov + is_in_fov, transparent toggling | new |
| `fuzz_pathfinding_behavior.py` | DijkstraMap, grid.step, entity behavior fields | #273-adjacent |

Any target not yet implemented is a stub that still compiles and runs cleanly
— `make fuzz` reports it as a no-op.

## Adding a new target

1. Add `<name>` to `FUZZ_TARGETS` in the Makefile.
2. Create `tests/fuzz/fuzz_<name>.py` defining `fuzz_one_input(data: bytes) -> None`.
3. Create `tests/fuzz/seeds/<name>/.gitkeep` so the seed dir exists.
4. Import `ByteStream` and `EXPECTED_EXCEPTIONS` from `fuzz_common`. Wrap the
   fuzz body in `try: ... except EXPECTED_EXCEPTIONS: pass` so Python noise
   doesn't pollute libFuzzer output — real bugs come from ASan/UBSan.

No C++ code changes are needed to add a target. The harness loads
`fuzz_<MCRF_FUZZ_TARGET>.py` by name at init time.

## Triage

A crash in `tests/fuzz/crashes/` is a file containing the exact bytes that
triggered it. Reproduce with `make fuzz-repro TARGET=<name> CRASH=<path>`.
The binary will rerun ONCE against that input and ASan will print the stack.
Useful ASan tweaks when investigating:

```sh
ASAN_OPTIONS="detect_leaks=0:symbolize=1:print_stacktrace=1" \
    ./build-fuzz/mcrfpy_fuzz path/to/crash_input
```

If the crash reproduces a known fixed issue (#258-#278), delete the crash file
and move on. If it's new, file a Gitea issue with the crash file attached and
apply appropriate `system:*` and `priority:*` labels per CLAUDE.md.

## CI integration

Not wired into `tests/run_tests.py`. Fuzz runs are non-deterministic and too
long for normal suite runs. Follow-up issue will add a scheduled weekly job.

## References

- Plan: `/home/john/.claude/plans/abundant-gliding-hummingbird.md`
- libFuzzer: https://llvm.org/docs/LibFuzzer.html
- Bug inventory: #279 (meta), #258-#278 (individual bugs)
