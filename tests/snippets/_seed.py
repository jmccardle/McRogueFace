#!/usr/bin/env python3
"""
Seed pre-script -- chained as the FIRST --exec, BEFORE a documentation snippet,
when generating deterministic screenshots:

    ./mcrogueface --headless \
        --exec tests/snippets/_seed.py \
        --exec tests/snippets/086_procgen_cellular.py \
        --exec tests/snippets/_screenshot.py

Why before, not after: a snippet runs to completion at import -- it builds its scene
and draws its procedural content the moment it is exec'd. Anything that consumes
randomness (`random.random()` cave fills, `random.choice` scatter, ...) has already
drawn by the time the *next* --exec runs. So to make a snippet's pixels reproducible,
the interpreter's global RNG must be seeded BEFORE the snippet executes.

Chaining works because all --exec scripts share one interpreter: this script's
`import random; random.seed(N)` seeds the same module object the snippet later gets
back from its own `import random`. (Snippets that pass an explicit `seed=` to
NoiseSource / HeightMap / BSP are already deterministic and unaffected by this; those
generators use a separate TCOD RNG that `random.seed` does not touch -- see #381.)

This script is intentionally a no-op for the pass/fail suite; it is only chained by
tools/generate_snippet_shots.py.
"""

import os
import random

# Same seed for every snippet: a screenshot is a visual-regression ORACLE, so the only
# thing that should ever change a snippet's image is a change in the snippet or the
# engine -- never the RNG. Overridable for debugging a specific capture.
SEED = int(os.environ.get("MCRF_SEED", "42"))
random.seed(SEED)
