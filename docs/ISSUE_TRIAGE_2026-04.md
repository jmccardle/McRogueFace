# McRogueFace Issue Triage — April 2026

**46 open issues** across #53–#304. Grouped by system, ordered by impact.

---

## Group 1: Render Cache Dirty Flags (Bugfix Cluster)

**4 issues — all quick-to-moderate fixes, high user-visible impact**

These are systemic bugs where Python property setters bypass the render cache invalidation system (#144). They cause stale frames when using `clip_children` or `cache_subtree`. Issue #291 is the umbrella audit; the other three are specific bugs it identified.

| Issue | Title | Difficulty |
|-------|-------|------------|
| #291 | Audit all Python property setters for missing markDirty() calls | Medium — systematic sweep of all tp_getset setters |
| #290 | UIDrawable base x/y/pos setters don't propagate dirty flags to parent | Quick — add markCompositeDirty() call in set_float_member() |
| #289 | Caption Python property setters don't call markDirty() | Quick — add markDirty() to text/font_size/fill_color setters |
| #288 | UICollection mutations don't invalidate parent Frame's render cache | Quick — add markCompositeDirty() in append/remove/etc |

**Dependencies:** None external. #291 depends on #288–#290 being fixed first (or done together).

**Recommendation: Tackle first.** These are correctness bugs affecting every user of the caching system. The fixes are mechanical (add missing dirty-flag calls), low risk, and testable. One focused session can close all four.

---

## Group 2: Grid Dangling Pointer Bugs

**3 issues — moderate fixes, memory safety impact**

All three are the same class of bug: raw `UIGrid*` pointers in child objects that dangle when the parent grid is destroyed. Part of the broader memory safety audit (#279).

| Issue | Title | Difficulty |
|-------|-------|------------|
| #270 | GridLayer::parent_grid dangling raw pointer | Moderate — convert to weak_ptr or add invalidation |
| #271 | UIGridPoint::parent_grid dangling raw pointer | Moderate — same pattern as #270 |
| #277 | GridChunk::parent_grid dangling raw pointer | Moderate — same pattern as #270 |

**Dependencies:** These are the last 3 unfixed bugs from the memory safety audit (#279). Fixing all three would effectively close #279.

**Recommendation: Tackle second.** Same fix pattern applied three times. Closes the memory safety audit chapter.

---

## Group 3: Animation System Fixes

**2 issues — one bugfix, one feature**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #256 | Animation system bypasses spatial hash updates for entity position | Moderate — hook animation property changes into spatial hash |
| #218 | Color and Vector animation targets | Minor feature — compound property animation support |

**Dependencies:** #256 is independent. #218 is a nice-to-have that improves DX.

---

## Group 4: Grid Layer & Rendering Fixes

**2 issues — quick fixes**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #257 | Grid layers with z_index of zero are on top of entities | Quick — change `>=0` to `>0` or similar in draw order |
| #152 | Sparse Grid Layers | Major feature — default values + sub-grid chunk optimization |

**Dependencies:** #257 is standalone. #152 builds on the existing layer system.

---

## Group 5: API Cleanup & Consistency

**1 issue — quick, blocks v1.0**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #304 | Remove camelCase module functions before 1.0 | Quick — delete 4 method entries from mcrfpyMethods[], update tests |

**Dependencies:** Snake_case aliases already added. This is a breaking change gated on the 1.0 release.

---

## Group 6: Multi-Tile Entity Rendering

**5 issues — parent + 4 children, all tier3-future**

Umbrella issue #233 with four sub-issues for different approaches to entities larger than one grid cell.

| Issue | Title | Difficulty |
|-------|-------|------------|
| #233 | Enhance Entity rendering and positioning capabilities (parent) | Meta/tracking |
| #234 | Entity origin offset for oversized sprites | Minor — add pixel offset to entity draw position |
| #235 | Texture display bounds for non-uniform sprite content | Minor — support non-cell-aligned sprite regions |
| #236 | Multi-tile entities using oversized sprites | Minor — render single large sprite across cells |
| #237 | Multi-tile entities using composite sprites | Major — multiple sprite indices per entity |

**Dependencies:** #234 is the simplest starting point. #236 and #237 build on #234/#235.

---

## Group 7: Memory Safety Audit Tail

**9 issues — testing/tooling infrastructure for the #279 audit**

These are the remaining items from the 7DRL 2026 post-mortem. The actual bugs are mostly fixed; these are about preventing regressions and improving the safety toolchain.

| Issue | Title | Difficulty |
|-------|-------|------------|
| #279 | Engine memory safety audit — meta/tracking | Meta — close when #270/#271/#277 done |
| #287 | Regression tests for each bug from #258–#278 | Medium — write targeted test scripts |
| #285 | CI pipeline for debug-test and asan-test | Medium — CI/CD configuration |
| #286 | Re-enable ASan leak detection | Tiny — remove detect_leaks=0 suppression |
| #284 | Valgrind Massif heap profiling target | Tiny — add Makefile target |
| #283 | Atheris fuzzing harness for Python API | Major — significant new infrastructure |
| #282 | Install modern Clang for TSan/fuzzing | Minor — toolchain upgrade |
| #281 | Free-threaded CPython + TSan Makefile targets | Minor — Makefile additions |
| #280 | Instrumented libtcod debug build | Minor — rebuild libtcod with sanitizers |

**Dependencies:** #286 depends on #266/#275 (both closed). #287 depends on the actual bugs being fixed. #283 depends on #282.

---

## Group 8: Grid Data Model Enhancements

**3 issues — foundation work for game data**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #293 | DiscreteMap serialization via bytes | Minor — add bytes() and from_bytes() to DiscreteMap |
| #294 | Entity.gridstate as DiscreteMap reference | Minor — refactor internal representation |
| #149 | Reduce the size of UIGrid.cpp | Refactoring — break 1400+ line file into logical units |

**Dependencies:** #294 depends on #293. #149 is independent refactoring.

---

## Group 9: Performance Optimization

**4 issues — significant effort, needs benchmarks first**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #255 | Tracking down performance improvement opportunities | Investigation — profiling session |
| #117 | Memory Pool for Entities | Major — custom allocator |
| #145 | TexturePool with power-of-2 RenderTexture reuse | Major — deferred from #144 |
| #124 | Grid Point Animation | Major — per-tile animation system, needs design |

**Dependencies:** #255 should be done first to identify where optimization matters. #145 builds on the dirty-flag system (#144, closed). #124 is a large standalone feature.

---

## Group 10: WASM / Playground Tooling

**3 issues — all tier3-future**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #238 | Emscripten debugging infrastructure (DWARF, source maps) | Minor — build config additions |
| #239 | Automated WASM testing with headless browser | Major — new test infrastructure |
| #240 | Developer troubleshooting docs for WASM deployments | Documentation — write guide |

**Dependencies:** #238 supports #239. #240 is standalone documentation.

---

## Group 11: LLM Agent Testbed

**3 issues — research/demo infrastructure**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #55 | McRogueFace as Agent Simulation Environment | Major — umbrella/vision issue |
| #154 | Grounded Multi-Agent Testbed | Major — research infrastructure |
| #156 | Turn-based LLM Agent Orchestration | Major — orchestration layer |

**Dependencies:** #156 depends on #154. Both depend on #55 conceptually. These also depend on #53 (alternative input methods) and mature API stability.

---

## Group 12: Demo Games & Tutorials

**2 issues — showcase/marketing**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #248 | Crypt of Sokoban Remaster (7DRL prep) | Major — full game remaster |
| #167 | r/roguelikedev Tutorial Series Demo Game | Major — tutorial content + demo game |

**Dependencies:** Both benefit from a stable, well-documented API. #167 specifically needs the API to be settled.

---

## Group 13: Platform & Architecture (Far Future)

**5 issues — large features, mostly deferred**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #70 | Package mcrfpy without embedded interpreter (wheels) | Major — significant build system rework |
| #62 | Multiple Windows | Major — architectural change |
| #67 | Grid Stitching / infinite world prototype | Major — new rendering/data infrastructure |
| #54 | Jupyter Notebook Interface | Major — alternative rendering target |
| #53 | Alternative Input Methods | Major — depends on #220 |

---

## Group 14: Concurrency

**1 issue — deferred**

| Issue | Title | Difficulty |
|-------|-------|------------|
| #220 | Secondary Concurrency Model: Subinterpreter Support | Major — Python 3.12+ subinterpreters |

**Dependencies:** Depends on free-threaded CPython work (#281).

---

## Summary by Priority

| Priority | Groups | Issue Count | Session Estimate |
|----------|--------|-------------|-----------------|
| **Do now** | G1 (dirty flags), G2 (dangling ptrs) | 7 | 1 session |
| **Do soon** | G3 (animation), G4 (grid fixes), G5 (API cleanup) | 5 | 1 session |
| **Foundation** | G7 (safety tests), G8 (grid data) | 12 | 2-3 sessions |
| **When ready** | G6 (multi-tile), G9 (perf), G10 (WASM) | 12 | 3-4 sessions |
| **Future** | G11 (LLM), G12 (demos), G13 (platform), G14 (concurrency) | 10 | unbounded |

## Recommended First Session

**Groups 1 + 2: Dirty flags + dangling pointers (7 issues)**

Rationale:
- All are correctness/safety bugs, not features — fixes don't need design decisions
- Dirty flag fixes (#288-#291) share the same mechanical pattern: add missing `markDirty()` or `markCompositeDirty()` calls
- Dangling pointer fixes (#270, #271, #277) share the same pattern: convert `UIGrid*` to `weak_ptr<UIGrid>` or add invalidation on grid destruction
- Closing these also effectively closes the meta issue #279
- High confidence of completing all 7 in one session
- Clears the way for performance work (Group 9) which depends on correct caching
