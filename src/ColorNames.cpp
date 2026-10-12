#include "ColorNames.h"
#include <algorithm>
#include <cstring>

namespace mcrf::color_names {

namespace {

bool is_ascii_alnum(unsigned char c)
{
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9');
}

std::string_view trim(std::string_view s)
{
    while (!s.empty() && (s.front() == ' ' || s.front() == '\t')) s.remove_prefix(1);
    while (!s.empty() && (s.back() == ' ' || s.back() == '\t')) s.remove_suffix(1);
    return s;
}

std::size_t edit_distance(std::string_view a, std::string_view b)
{
    std::vector<std::size_t> row(b.size() + 1);
    for (std::size_t j = 0; j <= b.size(); ++j) row[j] = j;
    for (std::size_t i = 1; i <= a.size(); ++i) {
        std::size_t diag = row[0];
        row[0] = i;
        for (std::size_t j = 1; j <= b.size(); ++j) {
            std::size_t up = row[j];
            row[j] = std::min({row[j] + 1, row[j - 1] + 1, diag + (a[i - 1] == b[j - 1] ? 0 : 1)});
            diag = up;
        }
    }
    return row[b.size()];
}

// The entries whose key equals `key`: entries is sorted by (key, source).
std::pair<const Entry*, const Entry*> key_range(std::string_view key)
{
    const Entry* first = entries;
    const Entry* last = entries + entry_count;
    auto lo = std::lower_bound(first, last, key,
        [](const Entry& e, std::string_view k) { return std::string_view(e.key) < k; });
    auto hi = std::upper_bound(lo, last, key,
        [](std::string_view k, const Entry& e) { return k < std::string_view(e.key); });
    return {lo, hi};
}

} // namespace

std::string normalize(std::string_view name)
{
    std::string out;
    out.reserve(name.size());
    for (unsigned char c : name) {
        if (c >= 0x80) out.push_back((char)c);
        else if (is_ascii_alnum(c)) out.push_back((char)((c >= 'A' && c <= 'Z') ? c - 'A' + 'a' : c));
    }
    return out;
}

int source_index(std::string_view prefix)
{
    prefix = trim(prefix);
    for (std::size_t i = 0; i < source_count; ++i) {
        std::string_view p(source_prefixes[i]);
        if (p.size() == prefix.size() &&
            std::equal(p.begin(), p.end(), prefix.begin(), [](char a, char b) {
                return a == ((b >= 'A' && b <= 'Z') ? b - 'A' + 'a' : b);
            }))
            return (int)i;
    }
    return -1;
}

const Entry* find(std::string_view key, int source)
{
    auto [lo, hi] = key_range(key);
    for (const Entry* e = lo; e != hi; ++e)
        if (source < 0 || e->source == source) return e;
    return nullptr;
}

std::vector<const Entry*> names(int source)
{
    std::vector<const Entry*> out;
    const char* prev = nullptr;
    for (std::size_t i = 0; i < entry_count; ++i) {
        const Entry& e = entries[i];
        if (source >= 0) {
            if (e.source == source) out.push_back(&e);
        } else if (!prev || std::strcmp(prev, e.key) != 0) {
            out.push_back(&e);  // first entry of each key is its unprefixed winner
        }
        prev = e.key;
    }
    return out;
}

std::vector<std::string> suggestions(std::string_view key, int source, std::size_t limit)
{
    // Close means at most a third of the name wrong (at least one edit).
    std::size_t max_dist = std::max<std::size_t>(1, key.size() / 3);
    std::vector<std::pair<std::size_t, const Entry*>> scored;
    for (const Entry* e : names(source)) {
        std::size_t d = edit_distance(key, e->key);
        if (d <= max_dist) scored.push_back({d, e});
    }
    std::stable_sort(scored.begin(), scored.end(),
        [](const auto& a, const auto& b) { return a.first < b.first; });
    std::vector<std::string> out;
    for (std::size_t i = 0; i < scored.size() && i < limit; ++i) {
        const Entry* e = scored[i].second;
        out.push_back(source < 0 ? std::string(e->name)
                                 : std::string(source_prefixes[e->source]) + ":" + e->name);
    }
    return out;
}

} // namespace mcrf::color_names
