#pragma once
#include "Common.h"
#include <vector>
#include <string>
#include <memory>

// Forward declarations
class UIEntity;
class UIGrid;
class DijkstraMap;

// =============================================================================
// BehaviorType - matches Python mcrfpy.Behavior enum values
// =============================================================================
enum class BehaviorType : int {
    IDLE     = 0,
    CUSTOM   = 1,
    NOISE4   = 2,
    NOISE8   = 3,
    PATH     = 4,
    WAYPOINT = 5,
    PATROL   = 6,
    LOOP     = 7,
    SLEEP    = 8,
    SEEK     = 9,
    FLEE     = 10
};

// =============================================================================
// BehaviorResult - outcome of a single behavior step
// =============================================================================
enum class BehaviorResult {
    NO_ACTION,  // No movement attempted (IDLE, CUSTOM, etc.)
    MOVED,      // Entity wants to move to target_cell
    DONE,       // Behavior completed (path exhausted, sleep finished)
    BLOCKED     // Movement blocked (wall or collision)
};

// =============================================================================
// BehaviorOutput - result of executing a behavior
// =============================================================================
struct BehaviorOutput {
    BehaviorResult result = BehaviorResult::NO_ACTION;
    sf::Vector2i target_cell{0, 0};  // For MOVED/BLOCKED: the intended destination
};

// =============================================================================
// EntityBehavior - behavior state attached to each entity
// =============================================================================
struct EntityBehavior {
    BehaviorType type = BehaviorType::IDLE;

    // Waypoint/path data
    std::vector<sf::Vector2i> waypoints;
    int current_waypoint_index = 0;
    int patrol_direction = 1;  // +1 forward, -1 backward
    std::vector<sf::Vector2i> current_path;
    int path_step_index = 0;

    // Sleep data
    int sleep_turns_remaining = 0;

    // Dijkstra map (for SEEK/FLEE)
    std::shared_ptr<DijkstraMap> dijkstra_map;

    void reset() {
        type = BehaviorType::IDLE;
        waypoints.clear();
        current_waypoint_index = 0;
        patrol_direction = 1;
        current_path.clear();
        path_step_index = 0;
        sleep_turns_remaining = 0;
        dijkstra_map = nullptr;
    }
};

// =============================================================================
// Behavior execution - does NOT modify entity position, just returns intent
// =============================================================================
BehaviorOutput executeBehavior(UIEntity& entity, UIGrid& grid);
