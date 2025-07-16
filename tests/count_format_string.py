#!/usr/bin/env python3
# Count format string characters

fmt = "|OOOOfOOifizfffi"
print(f"Format string: {fmt}")

# Remove the | prefix
fmt_chars = fmt[1:]
print(f"Format chars after |: {fmt_chars}")
print(f"Length: {len(fmt_chars)}")

# Count each type
o_count = fmt_chars.count('O')
f_count = fmt_chars.count('f')
i_count = fmt_chars.count('i')
z_count = fmt_chars.count('z')
s_count = fmt_chars.count('s')

print(f"\nCounts:")
print(f"O (objects): {o_count}")
print(f"f (floats): {f_count}")
print(f"i (ints): {i_count}")
print(f"z (strings): {z_count}")
print(f"s (strings): {s_count}")
print(f"Total: {o_count + f_count + i_count + z_count + s_count}")

# List out each position
print("\nPosition by position:")
for i, c in enumerate(fmt_chars):
    print(f"{i+1}: {c}")