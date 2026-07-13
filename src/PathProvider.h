#pragma once
#include "Common.h"
#include <memory>
#include <vector>

class GridData;
class DijkstraMap;

// =============================================================================
// PathProvider (#315) - strategy interface for "what's my next cell?"
//
// EntityBehavior's SEEK/FLEE execute step() by asking the active PathProvider
// for a single cell. Three concrete providers satisfy every pathfinding shape
// the engine exposes today.
// =============================================================================
class PathProvider {
public:
    virtual ~PathProvider() = default;

    // Return the next cell to step to. Sets *ok=true on a valid step, false
    // otherwise. The provider is responsible for walkability checks -
    // DijkstraProvider relies on the TCOD map used at compute time,
    // TargetProvider re-queries the live grid, AStarProvider trusts the
    // pre-computed path.
    virtual sf::Vector2i nextStep(sf::Vector2i from, GridData& grid, bool* ok) = 0;

    // Hint for providers that hold iteration state (currently only A*).
    virtual void reset() {}
};

// Descend a precomputed DijkstraMap. For SEEK, pass the map as-is; for FLEE,
// pass DijkstraMap.inverted().
class DijkstraProvider : public PathProvider {
public:
    explicit DijkstraProvider(std::shared_ptr<DijkstraMap> map);
    sf::Vector2i nextStep(sf::Vector2i from, GridData& grid, bool* ok) override;

private:
    std::shared_ptr<DijkstraMap> map_;
};

// Replay a pre-computed A* path.
class AStarProvider : public PathProvider {
public:
    explicit AStarProvider(std::vector<sf::Vector2i> path);
    sf::Vector2i nextStep(sf::Vector2i from, GridData& grid, bool* ok) override;
    void reset() override { index_ = 0; }

private:
    std::vector<sf::Vector2i> path_;
    size_t index_ = 0;
};

// Take a single Chebyshev step toward a fixed target cell. Used when full
// pathfinding is overkill (e.g. an adjacent target). Returns no-step if the
// straight-line neighbor is blocked - callers can treat that as BLOCKED.
class TargetProvider : public PathProvider {
public:
    explicit TargetProvider(sf::Vector2i target);
    sf::Vector2i nextStep(sf::Vector2i from, GridData& grid, bool* ok) override;

private:
    sf::Vector2i target_;
};
