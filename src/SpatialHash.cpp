#include "SpatialHash.h"
#include "UIEntity.h"
#include <algorithm>

SpatialHash::SpatialHash(int bucket_size)
    : bucket_size(bucket_size)
{
}

void SpatialHash::insert(std::shared_ptr<UIEntity> entity)
{
    if (!entity) return;

    auto bucket_coord = getBucket(entity->position.x, entity->position.y);
    buckets[bucket_coord].push_back(entity);
}

void SpatialHash::remove(std::shared_ptr<UIEntity> entity)
{
    if (!entity) return;

    auto bucket_coord = getBucket(entity->position.x, entity->position.y);
    auto it = buckets.find(bucket_coord);
    if (it == buckets.end()) return;

    auto& bucket = it->second;

    // Remove the entity from the bucket
    bucket.erase(
        std::remove_if(bucket.begin(), bucket.end(),
            [&entity](const std::weak_ptr<UIEntity>& wp) {
                auto sp = wp.lock();
                return !sp || sp == entity;
            }),
        bucket.end()
    );

    // Remove empty buckets to save memory
    if (bucket.empty()) {
        buckets.erase(it);
    }
}

void SpatialHash::update(std::shared_ptr<UIEntity> entity, float old_x, float old_y)
{
    if (!entity) return;

    auto old_bucket = getBucket(old_x, old_y);
    auto new_bucket = getBucket(entity->position.x, entity->position.y);

    // Only update if bucket changed
    if (old_bucket == new_bucket) return;

    // Remove from old bucket
    auto it = buckets.find(old_bucket);
    if (it != buckets.end()) {
        auto& bucket = it->second;
        bucket.erase(
            std::remove_if(bucket.begin(), bucket.end(),
                [&entity](const std::weak_ptr<UIEntity>& wp) {
                    auto sp = wp.lock();
                    return !sp || sp == entity;
                }),
            bucket.end()
        );
        if (bucket.empty()) {
            buckets.erase(it);
        }
    }

    // Add to new bucket
    buckets[new_bucket].push_back(entity);
}

std::vector<std::pair<int, int>> SpatialHash::getBucketsInRadius(float x, float y, float radius) const
{
    std::vector<std::pair<int, int>> result;

    // Get bounding box in bucket coordinates
    int min_bx = static_cast<int>(std::floor((x - radius) / bucket_size));
    int max_bx = static_cast<int>(std::floor((x + radius) / bucket_size));
    int min_by = static_cast<int>(std::floor((y - radius) / bucket_size));
    int max_by = static_cast<int>(std::floor((y + radius) / bucket_size));

    // Iterate all buckets in the bounding box
    for (int bx = min_bx; bx <= max_bx; ++bx) {
        for (int by = min_by; by <= max_by; ++by) {
            result.emplace_back(bx, by);
        }
    }

    return result;
}

std::vector<std::pair<int, int>> SpatialHash::getBucketsInRect(float x, float y, float width, float height) const
{
    std::vector<std::pair<int, int>> result;

    int min_bx = static_cast<int>(std::floor(x / bucket_size));
    int max_bx = static_cast<int>(std::floor((x + width) / bucket_size));
    int min_by = static_cast<int>(std::floor(y / bucket_size));
    int max_by = static_cast<int>(std::floor((y + height) / bucket_size));

    for (int bx = min_bx; bx <= max_bx; ++bx) {
        for (int by = min_by; by <= max_by; ++by) {
            result.emplace_back(bx, by);
        }
    }

    return result;
}

std::vector<std::shared_ptr<UIEntity>> SpatialHash::queryRadius(float x, float y, float radius) const
{
    std::vector<std::shared_ptr<UIEntity>> result;
    float radius_sq = radius * radius;

    auto bucket_coords = getBucketsInRadius(x, y, radius);

    for (const auto& coord : bucket_coords) {
        auto it = buckets.find(coord);
        if (it == buckets.end()) continue;

        for (const auto& wp : it->second) {
            auto entity = wp.lock();
            if (!entity) continue;

            // Check if entity is actually within the circular radius
            float dx = entity->position.x - x;
            float dy = entity->position.y - y;
            if (dx * dx + dy * dy <= radius_sq) {
                result.push_back(entity);
            }
        }
    }

    return result;
}

std::vector<std::shared_ptr<UIEntity>> SpatialHash::queryRect(float x, float y, float width, float height) const
{
    std::vector<std::shared_ptr<UIEntity>> result;

    auto bucket_coords = getBucketsInRect(x, y, width, height);

    for (const auto& coord : bucket_coords) {
        auto it = buckets.find(coord);
        if (it == buckets.end()) continue;

        for (const auto& wp : it->second) {
            auto entity = wp.lock();
            if (!entity) continue;

            // Check if entity is within the rectangle
            float ex = entity->position.x;
            float ey = entity->position.y;
            if (ex >= x && ex < x + width && ey >= y && ey < y + height) {
                result.push_back(entity);
            }
        }
    }

    return result;
}

void SpatialHash::clear()
{
    buckets.clear();
}

size_t SpatialHash::totalEntities() const
{
    size_t count = 0;
    for (const auto& [coord, bucket] : buckets) {
        for (const auto& wp : bucket) {
            if (wp.lock()) {
                ++count;
            }
        }
    }
    return count;
}

void SpatialHash::cleanBucket(std::vector<std::weak_ptr<UIEntity>>& bucket)
{
    bucket.erase(
        std::remove_if(bucket.begin(), bucket.end(),
            [](const std::weak_ptr<UIEntity>& wp) {
                return wp.expired();
            }),
        bucket.end()
    );
}
