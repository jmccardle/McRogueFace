#pragma once
#include <unordered_map>
#include <vector>
#include <memory>
#include <cmath>

class UIEntity;

/**
 * SpatialHash - O(1) average spatial queries for entities (#115)
 *
 * Divides the grid into buckets and tracks which entities are in each bucket.
 * Queries only check entities in nearby buckets instead of all entities.
 *
 * Performance characteristics:
 * - Insert: O(1)
 * - Remove: O(n) where n = entities in bucket (typically small)
 * - Update position: O(n) where n = entities in bucket
 * - Query radius: O(k) where k = entities in checked buckets (vs O(N) for all entities)
 */
class SpatialHash {
public:
    // Default bucket size of 32 cells balances memory and query performance
    explicit SpatialHash(int bucket_size = 32);

    // Insert entity into spatial hash based on current position
    void insert(std::shared_ptr<UIEntity> entity);

    // Remove entity from spatial hash
    void remove(std::shared_ptr<UIEntity> entity);

    // Update entity position - call when entity moves
    // This removes from old bucket and inserts into new bucket if needed
    void update(std::shared_ptr<UIEntity> entity, float old_x, float old_y);

    // Query all entities within radius of a point
    // Returns entities whose positions are within the circular radius
    std::vector<std::shared_ptr<UIEntity>> queryRadius(float x, float y, float radius) const;

    // Clear all entities from the hash
    void clear();

    // Get statistics for debugging
    size_t bucketCount() const { return buckets.size(); }

private:
    int bucket_size;

    // Hash function for bucket coordinates
    struct PairHash {
        size_t operator()(const std::pair<int, int>& p) const {
            // Combine hash of both coordinates
            return std::hash<int>()(p.first) ^ (std::hash<int>()(p.second) << 16);
        }
    };

    // Map from bucket coordinates to list of entities in that bucket
    // Using weak_ptr to avoid preventing entity deletion
    std::unordered_map<std::pair<int, int>, std::vector<std::weak_ptr<UIEntity>>, PairHash> buckets;

    // Get bucket coordinates for a world position
    std::pair<int, int> getBucket(float x, float y) const {
        return {
            static_cast<int>(std::floor(x / bucket_size)),
            static_cast<int>(std::floor(y / bucket_size))
        };
    }

    // Get all bucket coordinates that overlap with a radius query
    std::vector<std::pair<int, int>> getBucketsInRadius(float x, float y, float radius) const;
};
