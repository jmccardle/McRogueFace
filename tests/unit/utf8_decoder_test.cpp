// utf8_decoder_test.cpp - mcrf::utf8::next_codepoint reports malformed input distinctly
// from a legitimate U+FFFD (#511). Utf8.h is header-only; no engine needed.
// Compile: g++ -std=c++17 -DMCRF_HEADLESS -I../../src utf8_decoder_test.cpp -o /tmp/utf8_decoder_test && /tmp/utf8_decoder_test

#include "Utf8.h"
#include <iostream>

static int failed = 0;

static void expect(const char* name, const std::string& in, uint32_t cp, bool malformed, size_t consumed)
{
    size_t i = 0;
    bool m = !malformed;
    const uint32_t got = mcrf::utf8::next_codepoint(in, i, &m);
    if (got == cp && m == malformed && i == consumed) {
        std::cout << "[PASS] " << name << "\n";
    } else {
        std::cout << "[FAIL] " << name << ": cp=" << std::hex << got << std::dec
                  << " malformed=" << m << " consumed=" << i << "\n";
        failed++;
    }
}

int main()
{
    expect("ascii", "A", 'A', false, 1);
    expect("2-byte", "\xC3\xA9", 0xE9, false, 2);
    expect("4-byte", "\xF0\x9F\x98\x80", 0x1F600, false, 4);
    expect("literal U+FFFD is not malformed", "\xEF\xBF\xBD", 0xFFFD, false, 3);
    expect("stray continuation byte", "\x80", 0xFFFD, true, 1);
    expect("invalid lead 0xFF", "\xFF", 0xFFFD, true, 1);
    expect("truncated 3-byte", "\xE2\x82", 0xFFFD, true, 1);
    expect("overlong NUL", "\xC0\x80", 0xFFFD, true, 1);
    expect("surrogate", "\xED\xA0\x80", 0xFFFD, true, 1);
    expect("past U+10FFFF", "\xF4\x90\x80\x80", 0xFFFD, true, 1);

    // Omitting the out-param still works (UICaption, glyph loops).
    size_t i = 0;
    if (mcrf::utf8::next_codepoint("\xFF", i) != mcrf::utf8::REPLACEMENT || i != 1) {
        std::cout << "[FAIL] no out-param\n"; failed++;
    }
    std::cout << (failed ? "FAIL" : "PASS") << "\n";
    return failed ? 1 : 0;
}
