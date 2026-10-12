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
// match. Must agree with key() in tools/generate_color_table.py.
std::string normalize(std::string_view name);

// Index of a source prefix ("xkcd", case and surrounding spaces ignored), or -1.
int source_index(std::string_view prefix);

// The entry for a normalized key: in `source` only, or (source < 0) the first source in
// precedence order that has it. nullptr when there is none.
const Entry* find(std::string_view key, int source = -1);

// Up to `limit` names close to `key` (edit distance), for "did you mean" messages.
// Unprefixed (source < 0) suggestions are plain names; otherwise "source:name".
std::vector<std::string> suggestions(std::string_view key, int source, std::size_t limit = 3);

// The names a lookup in `source` (or unprefixed, source < 0) can reach, one per key,
// in the source's own spelling, ordered by key.
std::vector<const Entry*> names(int source = -1);

} // namespace mcrf::color_names
