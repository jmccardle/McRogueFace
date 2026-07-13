#include "PathProvider.h"
#include "PyGridData.h"
#include "UIGridPathfinding.h"
#include "UIGridPoint.h"

static bool cellWalkable(GridData& grid, int x, int y) {
    if (x < 0 || x >= grid.grid_w || y < 0 || y >= grid.grid_h) return false;
    return grid.isWalkable(x, y);  // #332
}

// -----------------------------------------------------------------------------
// DijkstraProvider
// -----------------------------------------------------------------------------
DijkstraProvider::DijkstraProvider(std::shared_ptr<DijkstraMap> map)
    : map_(std::move(map)) {}

sf::Vector2i DijkstraProvider::nextStep(sf::Vector2i from, GridData& /*grid*/, bool* ok) {
    if (!map_) {
        if (ok) *ok = false;
        return {-1, -1};
    }
    bool valid = false;
    sf::Vector2i step = map_->descentStep(from.x, from.y, &valid);
    if (ok) *ok = valid;
    return step;
}

// -----------------------------------------------------------------------------
// AStarProvider
// -----------------------------------------------------------------------------
AStarProvider::AStarProvider(std::vector<sf::Vector2i> path)
    : path_(std::move(path)) {}

sf::Vector2i AStarProvider::nextStep(sf::Vector2i /*from*/, GridData& /*grid*/, bool* ok) {
    if (index_ >= path_.size()) {
        if (ok) *ok = false;
        return {-1, -1};
    }
    if (ok) *ok = true;
    return path_[index_++];
}

// -----------------------------------------------------------------------------
// TargetProvider
// -----------------------------------------------------------------------------
TargetProvider::TargetProvider(sf::Vector2i target)
    : target_(target) {}

sf::Vector2i TargetProvider::nextStep(sf::Vector2i from, GridData& grid, bool* ok) {
    int dx = target_.x - from.x;
    int dy = target_.y - from.y;
    if (dx == 0 && dy == 0) {
        if (ok) *ok = false;
        return {-1, -1};  // already at target
    }
    int sx = (dx > 0) ? 1 : ((dx < 0) ? -1 : 0);
    int sy = (dy > 0) ? 1 : ((dy < 0) ? -1 : 0);
    sf::Vector2i step{from.x + sx, from.y + sy};
    if (!cellWalkable(grid, step.x, step.y)) {
        if (ok) *ok = false;
        return {-1, -1};
    }
    if (ok) *ok = true;
    return step;
}
