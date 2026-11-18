#pragma once
#include <algorithm>
#include <climits>

// #552: the highest z_index among the children of one owner (a Scene, a Frame, a Grid), kept so that
// adding a drawable that has no z_index of its own (it goes ten above the highest) is O(1) instead of
// a scan of the collection. The owner keeps one of these next to its children vector; every writer of
// a member's z_index or of the membership reports to it through the methods below. `valid` false
// means "unknown": the next auto z_index scans once and sets it. Copies start unknown (a copied owner
// does not share the children vector's history).
struct ChildZ {
    int max_z = 0;
    bool valid = false;

    ChildZ() = default;
    ChildZ(const ChildZ&) {}
    ChildZ& operator=(const ChildZ&) { valid = false; return *this; }

    template <class Items> static int scan(const Items& items) {
        int top = INT_MIN;
        for (const auto& d : items) top = std::max(top, d->z_index);
        return top;
    }
    static int above(int top) { return top <= INT_MAX - 10 ? top + 10 : INT_MAX; }

    void invalidate() { valid = false; }

    // The z_index a drawable without one gets, before it is pushed onto `items` (any container of
    // pointers to drawables). An empty collection starts at 0.
    template <class Items> int next_auto(const Items& items) {
        if (items.empty()) return 0;
        if (!valid) {
            max_z = scan(items);
            valid = true;
        }
        return above(max_z);
    }

    // The same answer with no owner to cache it (a collection whose Frame / Grid / Scene is gone).
    template <class Items> static int next_auto_uncached(const Items& items) {
        return items.empty() ? 0 : above(scan(items));
    }

    // A drawable with z_index `z` was added; `was_empty`: the collection had no other member.
    void added(int z, bool was_empty) {
        if (was_empty) { max_z = z; valid = true; }
        else if (valid) max_z = std::max(max_z, z);
    }

    // A member's z_index went from `old_z` to `new_z`.
    void changed(int old_z, int new_z) {
        if (!valid) return;
        if (new_z >= max_z) max_z = new_z;
        else if (old_z == max_z) valid = false;
    }

    // A member with z_index `z` left.
    void removed(int z) {
        if (valid && z >= max_z) valid = false;
    }
};
