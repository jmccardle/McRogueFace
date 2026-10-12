#pragma once
// #477: UTF-8 is the engine's text encoding, regardless of locale.
//
// Every std::string that holds text -- a caption, a window title, anything that
// came from or goes back to a Python str -- is UTF-8, as it is in Python 3.15.
// It is decoded only where glyphs are drawn:
//   - SFML: sf::String(std::string) widens through std::locale(), one code point
//     per byte, so text must cross into SFML through from_utf8() and back out
//     through to_utf8(). Never hand SFML a bare std::string of text.
//   - SDL2: the glyph loops walk code points with next_codepoint().
//   - Headless: stores the bytes; nothing to decode.

#include <cstdint>
#include <string>

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
#include <SFML/System/String.hpp>
#endif

namespace mcrf {
namespace utf8 {

constexpr uint32_t REPLACEMENT = 0xFFFD;

// Decode the code point starting at s[i] and advance i past it. A malformed or
// truncated sequence decodes to U+FFFD and consumes one byte, so a bad byte
// shows as one replacement glyph instead of swallowing its neighbours.
inline uint32_t next_codepoint(const std::string& s, size_t& i)
{
    const auto byte = [&](size_t k) { return static_cast<unsigned char>(s[k]); };
    const unsigned char lead = byte(i);
    uint32_t cp;
    int extra;
    uint32_t min;
    if (lead < 0x80)                { cp = lead;        extra = 0; min = 0; }
    else if ((lead & 0xE0) == 0xC0) { cp = lead & 0x1F; extra = 1; min = 0x80; }
    else if ((lead & 0xF0) == 0xE0) { cp = lead & 0x0F; extra = 2; min = 0x800; }
    else if ((lead & 0xF8) == 0xF0) { cp = lead & 0x07; extra = 3; min = 0x10000; }
    else { ++i; return REPLACEMENT; }

    if (i + extra >= s.size()) { ++i; return REPLACEMENT; }  // truncated
    for (int k = 1; k <= extra; ++k) {
        const unsigned char c = byte(i + k);
        if ((c & 0xC0) != 0x80) { ++i; return REPLACEMENT; }
        cp = (cp << 6) | (c & 0x3F);
    }
    // Overlong forms, surrogates and values past U+10FFFF are not UTF-8.
    if (cp < min || (cp >= 0xD800 && cp <= 0xDFFF) || cp > 0x10FFFF) {
        ++i;
        return REPLACEMENT;
    }
    i += extra + 1;
    return cp;
}

} // namespace utf8

#if !defined(MCRF_HEADLESS) && !defined(MCRF_SDL2)
inline sf::String from_utf8(const std::string& s)
{
    return sf::String::fromUtf8(s.begin(), s.end());
}

inline std::string to_utf8(const sf::String& s)
{
    const auto bytes = s.toUtf8();
    return std::string(bytes.begin(), bytes.end());
}
#else
// The SDL2 and headless backends store text as UTF-8 bytes already.
inline const std::string& from_utf8(const std::string& s) { return s; }
inline const std::string& to_utf8(const std::string& s) { return s; }
#endif

} // namespace mcrf
