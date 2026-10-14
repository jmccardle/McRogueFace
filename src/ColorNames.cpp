#include "ColorNames.h"
#include <algorithm>

namespace mcrf::color_names {

namespace {

bool is_ascii_alnum(unsigned char c)
{
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9');
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

const Entry* find(std::string_view key)
{
    const Entry* last = entries + entry_count;
    const Entry* it = std::lower_bound(entries, last, key,
        [](const Entry& e, std::string_view k) { return std::string_view(e.name) < k; });
    return (it != last && std::string_view(it->name) == key) ? it : nullptr;
}

std::vector<std::string> suggestions(std::string_view key, std::size_t limit)
{
    // Close means at most a third of the name wrong (at least one edit).
    std::size_t max_dist = std::max<std::size_t>(1, key.size() / 3);
    std::vector<std::pair<std::size_t, const Entry*>> scored;
    for (std::size_t i = 0; i < entry_count; ++i) {
        std::size_t d = edit_distance(key, entries[i].name);
        if (d <= max_dist) scored.push_back({d, &entries[i]});
    }
    std::stable_sort(scored.begin(), scored.end(),
        [](const auto& a, const auto& b) { return a.first < b.first; });
    std::vector<std::string> out;
    for (std::size_t i = 0; i < scored.size() && i < limit; ++i)
        out.push_back(scored[i].second->name);
    return out;
}

} // namespace mcrf::color_names
