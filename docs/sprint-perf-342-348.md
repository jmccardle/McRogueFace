# Sprint plan: hot-path perf batch (#342, #343, #344, #348)

Durable plan to fix four profiler-identified hot paths in one sprint, with
**before/after measurement built in**. Baselines below were captured on the
pre-fix tree (master tip `03c9b9f`/`ef0408e`, engine code = #331 `182da62`).

Companion: `docs/profiling.md` (the rig). All four share the same class of fix as
#331 — stop re-doing per-call ceremony on a hot path.

## Measurement protocol (run identically before and after)

One harness drives all four scenarios in isolation, step()-only / pure-loop (no
screenshots — avoids the PNG trap):

```
tests/benchmarks/sprint_perf_baseline.py
```

**Wall-clock** (Release `build/`, representative -O3), median of 3 runs:
```
./build/mcrogueface --headless --exec tests/benchmarks/sprint_perf_baseline.py
```

**Instruction counts** (profile `build-profile/`, deterministic), one run:
```
valgrind --tool=callgrind --callgrind-out-file=build-profile/cg_baseline.out \
  build-profile/mcrogueface --headless --exec tests/benchmarks/sprint_perf_baseline.py
callgrind_annotate [--inclusive=yes] build-profile/cg_baseline.out
```

Re-run both after each fix; compare the same `BASELINE | ...` lines and the same
per-function Ir. Callgrind is the primary acceptance signal (deterministic);
wall-clock is the sanity check.

**Note on wall-clock vs Callgrind divergence** (observed here, expected): the key
scenario dominates wall-clock (`automation.keyDown` blocks on X11/OS syscalls — many
ms, few app instructions) while the animation scenario dominates Callgrind
(`Animation::update` ~42% of instructions — pure CPU, no syscalls). Judge each fix by
the metric that reflects its cost: CPU-bound fixes (#342/#348) by Callgrind Ir;
per-event fixes (#344) by Callgrind Ir (wall-clock too noisy).

## Baseline numbers (pre-fix)

Harness scale: anim=500 frames×2 props/200 steps, update=5000 steps, keys=3000
events, grid=120²×5 passes. Callgrind harness total = **3,522,924,932 Ir**.

| Issue | Wall-clock (median/3) | Target function (Callgrind) | Self Ir | % harness | calls (observed) |
|---|---|---|---|---|---|
| #342 | 6.68 ms / 200k ops | `UIFrame::setProperty(string,float)` | 158.6M | 4.50% | 5.2M |
| #343 | 172 ms / 5k steps | `PyObject_GetAttrString("update")`/step | ~3.4k Ir/call | small | ~1/step |
| #344 | 665 ms / 6k ops (noisy 98–135 µs) | `PyObject_CallFunction` (enum ctor) | 19.18M | 0.54% | 6,000 |
| #348 | 81.8 ms / 72k ops | `UIGridView::get_grid` | 72.5M | 2.06% | 72,000 |

Supporting inclusive costs for #342: `Animation::applyValue` 621M (17.63%),
`Animation::update` 1,479M (41.99%). For #344: `injectKeyEvent` 308M (8.76%) is
harness-only injection machinery, **not** a fix target. For #348: `get_grid`'s
callees `lookup`/`registerObject`/`PyWeakref_NewRef` each fire 72,000× → **0% cache
hit** (the defect).

## Suggested order

1. **#348** first — biggest self-cost after animation, cleanest fix, clearest
   Callgrind signal (cache-hit rate 0%→~100%), and it de-risks the shim for the
   others touching the grid.
2. **#342** — highest % of harness instructions; the win is CPU/frame-budget, which
   Callgrind reveals even though wall-clock hid it.
3. **#343**, **#344** — smaller, mechanical; batch together.

## Per-issue plan

### #348 — get_grid re-allocates a Grid wrapper + weakref per call
- **Root cause** (`src/UIGridView.cpp` `get_grid`): allocates a temporary `UIGrid`
  wrapper, caches only a **weakref** to it, returns it; caller drops it → weakref
  dies → next call misses and re-allocates. 0% cache hit.
- **Fix direction**: give the shim a persistent handle to its own `UIGrid` wrapper
  (strong ref owned for the shim's lifetime, or store `PyObject*` on GridData and
  return it INCREF'd) so repeated access reuses one object. Mind the Grid↔wrapper
  ownership cycle — reuse the `#251` tp_dealloc `use_count()` break pattern.
- **Files**: `src/UIGridView.cpp`, `src/UIGrid.h/.cpp`, possibly `PythonObjectCache`.
- **Acceptance**: `get_grid` inclusive Ir drops sharply; `PyWeakref_NewRef` /
  `registerObject` call counts under `get_grid` fall from 72,000 to ~1;
  `348_grid_churn` wall-clock improves. No new leak (ASan test suite clean).
- **Risk**: ownership/lifetime — must not leak the grid or double-free. Add a
  regression test that hammers `grid.at()` in a loop and checks refcount stability.

### #342 — Animation applyValue → setProperty strcmp cascade
- **Root cause** (`src/Animation.cpp` `applyValue` → `UIDrawable::setProperty(const
  std::string&, ...)`, e.g. `src/UIFrame.cpp:843`): per active animation per frame,
  the property name is re-resolved by a linear string-compare chain.
- **Fix direction**: resolve the property **once** at `Animation::start()` to a
  stable handle — an enum id or a cached setter (member function pointer / small
  dispatch struct) — and call that each frame. Keep the string path for the
  one-time resolve and for `setProperty`'s existing public callers.
- **Files**: `src/Animation.h/.cpp`, `src/UIFrame.cpp`, `src/UICaption.cpp`,
  `src/UISprite.cpp`, `src/UIEntity.cpp`, `src/UIGrid.cpp` (each `setProperty`).
- **Acceptance**: `setProperty` self Ir (158.6M) and `applyValue` inclusive (621M)
  drop; `342_anim_dispatch` wall-clock improves modestly. Common props (`x`,
  `opacity`) already hit early in the cascade, so expect a larger win on deep props
  (`fill_color.a`) — consider adding a deep-property variant to the harness.
- **Risk**: keep behavior identical for every property/type combination; the
  existing animation tests must stay green.

### #343 — PyScene::update GetAttrString every frame
- **Root cause** (`src/PySceneObject.cpp:405`): `PyObject_GetAttrString(self,
  "update")` every frame even when the subclass doesn't override `update`.
- **Fix direction**: resolve once whether the subclass overrides `update` (cache a
  bool or the bound method), skip the lookup otherwise — mirror the hover fast-path
  guard at `src/PyScene.cpp:361` (`is_python_subclass`).
- **Files**: `src/PySceneObject.cpp` (+ wherever per-scene override state lives).
- **Acceptance**: per-step `GetAttrString("update")` calls → 0 for a plain scene;
  `343_scene_update` wall-clock improves. Overriding scenes still get `update` called.
- **Risk**: must still invoke `update` when it IS overridden (incl. late-bound /
  monkeypatched). Test both a plain and an overriding scene.

### #344 — on_key rebuilds Key/InputState enum members per event
- **Root cause** (`src/PySceneObject.cpp:362,373`): `PyObject_CallFunction(enum_class,
  "i", value)` per event constructs the IntEnum member via Python `EnumMeta.__call__`.
- **Fix direction**: pre-build the enum members once into a lookup table (array/dict
  keyed by int value) and return the cached `PyObject*` (INCREF) per event.
- **Files**: `src/PySceneObject.cpp`, `src/PyKey.cpp`, `src/PyInputState*` (enum defs).
- **Acceptance**: `PyObject_CallFunction` (enum ctor) 6,000-call / 19.18M-Ir cost →
  near-zero (replaced by an array index + INCREF). Wall-clock is too noisy to gate on.
- **Risk**: cached members must stay valid for the interpreter lifetime; hold strong
  refs. Enum identity/equality must be unchanged (existing `test_callback_enums.py`).

## Post-fix results (Callgrind A/B, same harness)

Harness total Ir: **3,522,924,932 → 3,211,532,731 (−311.4M, −8.8%)**.

| Issue | Metric | Baseline | Post-fix | Delta |
|---|---|---|---|---|
| #348 | `get_grid` inclusive Ir | 72,575,645 | 2,089,926 | **−97%** |
| #342 | `Animation::update` inclusive Ir | 1,479,186,800 | 1,207,377,600 | **−18.4%** (−272M) |
| #342 | variant `__do_visit` self Ir (anim) | 473.2M | 98.8M | **−79%** |
| #344 | enum-ctor `PyObject_CallFunction` self Ir | 19.18M | 0.228M | **−99%** |
| #343 | `call_update` Ir **per frame** (real doFrame loop) | 4,559 | 3 | **−99.9%** (~1,500×) |

Wall-clock (Release, median/3): #342 6.68→5.91 ms, #343 172→157 ms, #344 665→454 ms
(−31%), #348 81.8→72 ms. Wall-clock understates the CPU wins (the animation win is
hidden behind syscalls in other scenarios; judge by Callgrind Ir).

### #343 measured in the real game loop (not `step()`)

`mcrfpy.step()` bypasses `updatePythonScenes()`, so #343 is invisible headless-`step()`.
It was instead measured on the actual `doFrame()` loop (headless `run()`, which shares
the exact `doFrame` path with the windowed loop), driven by a keep-alive timer and
bounded with `timeout -s INT`. Normalized by `call_update` **Ir/call** so the (necessarily
uncontrolled) frame count doesn't matter:

- Without fix: `call_update` inclusive **794,878,505 Ir / 174,375 frames = 4,559 Ir/frame**
  — 35% of *all* instructions in a bare-scene loop (the failed `GetAttrString("update")`
  + `PyErr_Clear` every frame).
- With fix: **1,114,407 Ir / 371,469 frames ≈ 3 Ir/frame** (just the type-pointer compare).
- Throughput: **2.1× more frames** completed in the same Callgrind budget (371k vs 174k).

Bench script: `scratchpad/bench343.py` (bare Scene + keep-alive timer, no `step()`).

## Profiling course-corrections (the sprint working as intended)

The rig **disproved two guessed hot spots** and found the real ones. Recorded here so
we don't re-guess:

- **#342 — the strcmp cascade was cold.** `std::string == const char*` short-circuits
  on length, so each `setProperty` name compare is ~0.15%. The real cost was the two
  per-frame `std::variant` `std::visit` dispatches (`interpolate()` + `applyValue()`),
  **~473M Ir / 13.4% of the harness**. A first attempt to cut the `update()` weak_ptr
  triple-lock was also a dead end — locking an *empty* weak_ptr is nearly free (no
  control block, no atomics), so it was a wash/slight regression and was reverted. The
  shipped fix is a scalar-float fast path (`isSimpleFloatAnim`) that interpolates and
  applies directly, bypassing both visits: variant machinery **473M → 99M**.
- **#343 — real but off the `step()` path.** `GameEngine::step()` (headless) does **not**
  call `updatePythonScenes()`, so `call_update` never runs under `mcrfpy.step()` — the
  sprint's step()-only harness can't see it. Measured instead on the real `doFrame()`
  loop (see "#343 measured in the real game loop" above): **4,559 → 3 Ir/frame**, a large,
  genuine win — it was just measured with the wrong tool at first. (Verified a base
  `mcrfpy.Scene` has no `__dict__`, so `update` can only come from a subclass → the guard
  is safe.)
- **#344 / #348 — guesses confirmed.** Cached enum members and a persistent Grid
  wrapper are large, clean wins exactly as predicted.

## Definition of done

- [x] All four target metrics measured in `cg_*` A/B (above); #343 documented as
      correct-but-not-headless-measurable.
- [x] `cd tests && python3 run_tests.py` green (307/307), incl. new regression tests
      `issue_34{2,4,8}_*`.
- [x] Each commit references its issue (`closes #NNN`); this doc carries post-fix numbers.
