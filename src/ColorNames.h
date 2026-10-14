#pragma once
// Named-colour lookup behind Color("red") (#458). Pure C++; PyColor turns failures into
// Python exceptions. The table itself is generated: src/ColorNameTable.h, from
// tools/color_names/*.tsv by tools/generate_color_table.py.
#include "ColorNameTable.h"
#include <string>
#include <string_view>
#include <vector>

namespace mcrf::color_names {

// The lookup key: ASCII lowercased, with every ASCII character that is not a letter or
// digit removed ("Dark_Green" -> "darkgreen"). Non-ASCII bytes are kept, so they never
// match. Must agree with key() in tools/generate_color_table.py (the table stores only
// names already in this form).
std::string normalize(std::string_view name);

// The entry for a normalized key, or nullptr.
const Entry* find(std::string_view key);

// Up to `limit` names close to `key` (edit distance), for "did you mean" messages.
std::vector<std::string> suggestions(std::string_view key, std::size_t limit = 3);

} // namespace mcrf::color_names
