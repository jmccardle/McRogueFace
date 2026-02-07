# tiled_analysis.py - Wang set adjacency analysis utility
# Prints adjacency graph, terrain chains, and valid/invalid pair counts
# for exploring tileset Wang transition rules.
#
# Usage:
#   cd build && ./mcrogueface --headless --exec ../tests/demo/screens/tiled_analysis.py

import mcrfpy
import sys
from collections import defaultdict

# -- Configuration --------------------------------------------------------
PUNY_BASE = "/home/john/Development/7DRL2026_Liber_Noster_jmccardle/assets_sources/PUNY_WORLD_v1/PUNY_WORLD_v1"
TSX_PATH = PUNY_BASE + "/Tiled/punyworld-overworld-tiles.tsx"
WANG_SET_NAME = "overworld"


def analyze_wang_set(tileset, wang_set_name):
    """Analyze a Wang set and print adjacency information."""
    ws = tileset.wang_set(wang_set_name)
    T = ws.terrain_enum()

    print("=" * 60)
    print(f"Wang Set Analysis: {ws.name}")
    print(f"  Type: {ws.type}")
    print(f"  Colors: {ws.color_count}")
    print("=" * 60)

    # List all terrains
    terrains = [t for t in T if t != T.NONE]
    print(f"\nTerrains ({len(terrains)}):")
    for t in terrains:
        print(f"  {t.value:3d}: {t.name}")

    # Test all pairs for valid Wang transitions using 2x2 grids
    adjacency = defaultdict(set)  # terrain -> set of valid neighbors
    valid_pairs = []
    invalid_pairs = []

    for a in terrains:
        for b in terrains:
            if b.value <= a.value:
                continue
            # Create a 2x2 map: columns of A and B
            dm = mcrfpy.DiscreteMap((2, 2))
            dm.set(0, 0, a)
            dm.set(1, 0, b)
            dm.set(0, 1, a)
            dm.set(1, 1, b)
            results = ws.resolve(dm)
            has_invalid = any(r == -1 for r in results)
            if not has_invalid:
                valid_pairs.append((a, b))
                adjacency[a.name].add(b.name)
                adjacency[b.name].add(a.name)
            else:
                invalid_pairs.append((a, b))

    # Print adjacency graph
    print(f"\nAdjacency Graph ({len(valid_pairs)} valid pairs):")
    print("-" * 40)
    for t in terrains:
        neighbors = sorted(adjacency.get(t.name, set()))
        if neighbors:
            print(f"  {t.name}")
            for n in neighbors:
                print(f"    <-> {n}")
        else:
            print(f"  {t.name} (ISOLATED - no valid neighbors)")

    # Find terrain chains (connected components)
    print(f"\nTerrain Chains (connected components):")
    print("-" * 40)
    visited = set()
    chains = []

    def bfs(start):
        chain = []
        queue = [start]
        while queue:
            node = queue.pop(0)
            if node in visited:
                continue
            visited.add(node)
            chain.append(node)
            for neighbor in sorted(adjacency.get(node, set())):
                if neighbor not in visited:
                    queue.append(neighbor)
        return chain

    for t in terrains:
        if t.name not in visited:
            chain = bfs(t.name)
            if chain:
                chains.append(chain)

    for i, chain in enumerate(chains):
        print(f"\n  Chain {i+1}: {len(chain)} terrains")
        for name in chain:
            neighbors = sorted(adjacency.get(name, set()))
            connections = ", ".join(neighbors) if neighbors else "(none)"
            print(f"    {name} -> [{connections}]")

    # Find linear paths within chains
    print(f"\nLinear Paths (degree-1 endpoints to degree-1 endpoints):")
    print("-" * 40)
    for chain in chains:
        # Find nodes with degree 1 (endpoints) or degree > 2 (hubs)
        endpoints = [n for n in chain if len(adjacency.get(n, set())) == 1]
        hubs = [n for n in chain if len(adjacency.get(n, set())) > 2]

        if endpoints:
            print(f"  Endpoints: {', '.join(endpoints)}")
        if hubs:
            print(f"  Hubs: {', '.join(hubs)} (branch points)")

        # Trace from each endpoint
        for ep in endpoints:
            path = [ep]
            current = ep
            prev = None
            while True:
                neighbors = adjacency.get(current, set()) - {prev} if prev else adjacency.get(current, set())
                if len(neighbors) == 0:
                    break
                if len(neighbors) > 1:
                    path.append(f"({current} branches)")
                    break
                nxt = list(neighbors)[0]
                path.append(nxt)
                prev = current
                current = nxt
                if len(adjacency.get(current, set())) != 2:
                    break  # reached endpoint or hub
            print(f"  Path: {' -> '.join(path)}")

    # Summary statistics
    total_possible = len(terrains) * (len(terrains) - 1) // 2
    print(f"\nSummary:")
    print(f"  Total terrain types: {len(terrains)}")
    print(f"  Valid transitions: {len(valid_pairs)} / {total_possible} "
          f"({100*len(valid_pairs)/total_possible:.1f}%)")
    print(f"  Invalid transitions: {len(invalid_pairs)}")
    print(f"  Connected components: {len(chains)}")

    # Print invalid pairs for reference
    if invalid_pairs:
        print(f"\nInvalid Pairs ({len(invalid_pairs)}):")
        for a, b in invalid_pairs:
            print(f"  {a.name} X {b.name}")

    return valid_pairs, invalid_pairs, chains


def main():
    print("Loading tileset...")
    tileset = mcrfpy.TileSetFile(TSX_PATH)
    print(f"  {tileset.name}: {tileset.tile_count} tiles "
          f"({tileset.columns} cols, {tileset.tile_width}x{tileset.tile_height}px)")

    analyze_wang_set(tileset, WANG_SET_NAME)
    print("\nDone!")


if __name__ == "__main__":
    main()
    sys.exit(0)
