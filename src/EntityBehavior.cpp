#include "EntityBehavior.h"
#include "UIEntity.h"
#include "UIGrid.h"
#include "UIGridPathfinding.h"
#include <random>
#include <algorithm>

// Thread-local random engine for behavior randomness
static thread_local std::mt19937 rng{std::random_device{}()};

// =============================================================================
// Per-behavior execution functions
// =============================================================================

static BehaviorOutput executeIdle(UIEntity& entity, UIGrid& grid) {
    return {BehaviorResult::NO_ACTION, {}};
}

static BehaviorOutput executeCustom(UIEntity& entity, UIGrid& grid) {
    // CUSTOM does nothing built-in — step callback handles everything
    return {BehaviorResult::NO_ACTION, {}};
}

static bool isCellWalkable(UIGrid& grid, int x, int y) {
    if (x < 0 || x >= grid.grid_w || y < 0 || y >= grid.grid_h) return false;
    return grid.at(x, y).walkable;
}

static BehaviorOutput executeNoise(UIEntity& entity, UIGrid& grid, bool include_diagonals) {
    int cx = entity.cell_position.x;
    int cy = entity.cell_position.y;

    // Build candidate moves
    std::vector<sf::Vector2i> candidates;
    // Cardinal directions
    sf::Vector2i dirs4[] = {{0, -1}, {0, 1}, {-1, 0}, {1, 0}};
    sf::Vector2i dirs8[] = {{0, -1}, {0, 1}, {-1, 0}, {1, 0},
                            {-1, -1}, {1, -1}, {-1, 1}, {1, 1}};

    auto* dirs = include_diagonals ? dirs8 : dirs4;
    int count = include_diagonals ? 8 : 4;

    for (int i = 0; i < count; i++) {
        int nx = cx + dirs[i].x;
        int ny = cy + dirs[i].y;
        if (isCellWalkable(grid, nx, ny)) {
            candidates.push_back({nx, ny});
        }
    }

    if (candidates.empty()) {
        return {BehaviorResult::NO_ACTION, {}};
    }

    std::uniform_int_distribution<int> dist(0, candidates.size() - 1);
    auto target = candidates[dist(rng)];
    return {BehaviorResult::MOVED, target};
}

static BehaviorOutput executePath(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (behavior.path_step_index >= static_cast<int>(behavior.current_path.size())) {
        return {BehaviorResult::DONE, {}};
    }

    auto target = behavior.current_path[behavior.path_step_index];
    behavior.path_step_index++;

    if (!isCellWalkable(grid, target.x, target.y)) {
        return {BehaviorResult::BLOCKED, target};
    }

    return {BehaviorResult::MOVED, target};
}

static BehaviorOutput executeWaypoint(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (behavior.waypoints.empty()) {
        return {BehaviorResult::DONE, {}};
    }

    // If we've reached the current waypoint, advance to next
    auto& wp = behavior.waypoints[behavior.current_waypoint_index];
    if (entity.cell_position.x == wp.x && entity.cell_position.y == wp.y) {
        behavior.current_waypoint_index++;
        if (behavior.current_waypoint_index >= static_cast<int>(behavior.waypoints.size())) {
            return {BehaviorResult::DONE, {}};
        }
        // Clear path to recompute for new waypoint
        behavior.current_path.clear();
        behavior.path_step_index = 0;
    }

    // Compute path to current waypoint if needed
    if (behavior.current_path.empty() || behavior.path_step_index >= static_cast<int>(behavior.current_path.size())) {
        auto& target_wp = behavior.waypoints[behavior.current_waypoint_index];
        // Use grid pathfinding (A*)
        TCODPath path(grid.getTCODMap());
        path.compute(entity.cell_position.x, entity.cell_position.y, target_wp.x, target_wp.y);

        behavior.current_path.clear();
        behavior.path_step_index = 0;
        int px, py;
        while (path.walk(&px, &py, true)) {
            behavior.current_path.push_back({px, py});
        }

        if (behavior.current_path.empty()) {
            return {BehaviorResult::BLOCKED, target_wp};
        }
    }

    // Follow the path
    auto target = behavior.current_path[behavior.path_step_index];
    behavior.path_step_index++;

    if (!isCellWalkable(grid, target.x, target.y)) {
        return {BehaviorResult::BLOCKED, target};
    }

    return {BehaviorResult::MOVED, target};
}

static BehaviorOutput executePatrol(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (behavior.waypoints.empty()) {
        return {BehaviorResult::NO_ACTION, {}};
    }

    // Check if at current waypoint
    auto& wp = behavior.waypoints[behavior.current_waypoint_index];
    if (entity.cell_position.x == wp.x && entity.cell_position.y == wp.y) {
        int next = behavior.current_waypoint_index + behavior.patrol_direction;
        if (next < 0 || next >= static_cast<int>(behavior.waypoints.size())) {
            behavior.patrol_direction *= -1;
            next = behavior.current_waypoint_index + behavior.patrol_direction;
        }
        behavior.current_waypoint_index = next;
        behavior.current_path.clear();
        behavior.path_step_index = 0;
    }

    // Same path-following logic as waypoint
    if (behavior.current_path.empty() || behavior.path_step_index >= static_cast<int>(behavior.current_path.size())) {
        auto& target_wp = behavior.waypoints[behavior.current_waypoint_index];
        TCODPath path(grid.getTCODMap());
        path.compute(entity.cell_position.x, entity.cell_position.y, target_wp.x, target_wp.y);

        behavior.current_path.clear();
        behavior.path_step_index = 0;
        int px, py;
        while (path.walk(&px, &py, true)) {
            behavior.current_path.push_back({px, py});
        }

        if (behavior.current_path.empty()) {
            return {BehaviorResult::BLOCKED, target_wp};
        }
    }

    auto target = behavior.current_path[behavior.path_step_index];
    behavior.path_step_index++;

    if (!isCellWalkable(grid, target.x, target.y)) {
        return {BehaviorResult::BLOCKED, target};
    }

    return {BehaviorResult::MOVED, target};
}

static BehaviorOutput executeLoop(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (behavior.waypoints.empty()) {
        return {BehaviorResult::NO_ACTION, {}};
    }

    // Check if at current waypoint
    auto& wp = behavior.waypoints[behavior.current_waypoint_index];
    if (entity.cell_position.x == wp.x && entity.cell_position.y == wp.y) {
        behavior.current_waypoint_index = (behavior.current_waypoint_index + 1) % behavior.waypoints.size();
        behavior.current_path.clear();
        behavior.path_step_index = 0;
    }

    // Same path-following logic
    if (behavior.current_path.empty() || behavior.path_step_index >= static_cast<int>(behavior.current_path.size())) {
        auto& target_wp = behavior.waypoints[behavior.current_waypoint_index];
        TCODPath path(grid.getTCODMap());
        path.compute(entity.cell_position.x, entity.cell_position.y, target_wp.x, target_wp.y);

        behavior.current_path.clear();
        behavior.path_step_index = 0;
        int px, py;
        while (path.walk(&px, &py, true)) {
            behavior.current_path.push_back({px, py});
        }

        if (behavior.current_path.empty()) {
            return {BehaviorResult::BLOCKED, target_wp};
        }
    }

    auto target = behavior.current_path[behavior.path_step_index];
    behavior.path_step_index++;

    if (!isCellWalkable(grid, target.x, target.y)) {
        return {BehaviorResult::BLOCKED, target};
    }

    return {BehaviorResult::MOVED, target};
}

static BehaviorOutput executeSleep(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (behavior.sleep_turns_remaining > 0) {
        behavior.sleep_turns_remaining--;
        if (behavior.sleep_turns_remaining == 0) {
            return {BehaviorResult::DONE, {}};
        }
    }
    return {BehaviorResult::NO_ACTION, {}};
}

static BehaviorOutput executeSeek(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (!behavior.dijkstra_map) {
        return {BehaviorResult::NO_ACTION, {}};
    }

    // Use Dijkstra map to find the lowest-distance neighbor (moving toward target)
    int cx = entity.cell_position.x;
    int cy = entity.cell_position.y;
    float best_dist = std::numeric_limits<float>::max();
    sf::Vector2i best_cell = {cx, cy};
    bool found = false;

    sf::Vector2i dirs[] = {{0, -1}, {0, 1}, {-1, 0}, {1, 0},
                           {-1, -1}, {1, -1}, {-1, 1}, {1, 1}};

    for (auto& dir : dirs) {
        int nx = cx + dir.x;
        int ny = cy + dir.y;
        if (!isCellWalkable(grid, nx, ny)) continue;

        float dist = behavior.dijkstra_map->getDistance(nx, ny);
        if (dist >= 0 && dist < best_dist) {
            best_dist = dist;
            best_cell = {nx, ny};
            found = true;
        }
    }

    if (!found || (best_cell.x == cx && best_cell.y == cy)) {
        return {BehaviorResult::BLOCKED, {cx, cy}};
    }

    return {BehaviorResult::MOVED, best_cell};
}

static BehaviorOutput executeFlee(UIEntity& entity, UIGrid& grid) {
    auto& behavior = entity.behavior;

    if (!behavior.dijkstra_map) {
        return {BehaviorResult::NO_ACTION, {}};
    }

    // Use Dijkstra map to find the highest-distance neighbor (fleeing from target)
    int cx = entity.cell_position.x;
    int cy = entity.cell_position.y;
    float best_dist = -1.0f;
    sf::Vector2i best_cell = {cx, cy};
    bool found = false;

    sf::Vector2i dirs[] = {{0, -1}, {0, 1}, {-1, 0}, {1, 0},
                           {-1, -1}, {1, -1}, {-1, 1}, {1, 1}};

    for (auto& dir : dirs) {
        int nx = cx + dir.x;
        int ny = cy + dir.y;
        if (!isCellWalkable(grid, nx, ny)) continue;

        float dist = behavior.dijkstra_map->getDistance(nx, ny);
        if (dist >= 0 && dist > best_dist) {
            best_dist = dist;
            best_cell = {nx, ny};
            found = true;
        }
    }

    if (!found || (best_cell.x == cx && best_cell.y == cy)) {
        return {BehaviorResult::BLOCKED, {cx, cy}};
    }

    return {BehaviorResult::MOVED, best_cell};
}

// =============================================================================
// Main dispatch
// =============================================================================
BehaviorOutput executeBehavior(UIEntity& entity, UIGrid& grid) {
    switch (entity.behavior.type) {
        case BehaviorType::IDLE:     return executeIdle(entity, grid);
        case BehaviorType::CUSTOM:   return executeCustom(entity, grid);
        case BehaviorType::NOISE4:   return executeNoise(entity, grid, false);
        case BehaviorType::NOISE8:   return executeNoise(entity, grid, true);
        case BehaviorType::PATH:     return executePath(entity, grid);
        case BehaviorType::WAYPOINT: return executeWaypoint(entity, grid);
        case BehaviorType::PATROL:   return executePatrol(entity, grid);
        case BehaviorType::LOOP:     return executeLoop(entity, grid);
        case BehaviorType::SLEEP:    return executeSleep(entity, grid);
        case BehaviorType::SEEK:     return executeSeek(entity, grid);
        case BehaviorType::FLEE:     return executeFlee(entity, grid);
    }
    return {BehaviorResult::NO_ACTION, {}};
}
