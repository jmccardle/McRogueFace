# data sources: CSS docs, jennyscrayoncollection 2017 article on Crayola colors, XKCD color survey

# target: Single C++ header file to provide a struct of color RGB codes and names.
# This file pre-computes the nearest neighbor of every color.
# if an RGB code being searched for is closer than the nearest neighbor, it's the closest color name.

def hex_to_rgb(txt):
    if '#' in txt: txt = txt.replace('#', '')
    r = txt[0:2]
    g = txt[2:4]
    b = txt[4:6]
    return tuple([int(s, 16) for s in (r,g,b)])

class palette:
    def __init__(self, name, filename, priority):
        self.name = name
        self.priority = priority
        with open(filename, "r") as f:
            print(f"scanning {filename}")
            self.colors = {}
            for line in f.read().split('\n'):
                if len(line.split('\t')) < 2: continue
                name, code = line.split('\t')
                #print(name, code)
                self.colors[name] = hex_to_rgb(code)
                
    def __repr__(self):
        return f"<Palette '{self.name}' - {len(self.colors)} colors, priority = {self.priority}>"
    
palettes = [
    #palette("jenny", "jenny_colors.txt", 3), # I should probably use wikipedia as a source for copyright reasons
    palette("crayon", "wikicrayons_colors.txt", 2),
    palette("xkcd", "xkcd_colors.txt", 1),
    palette("css", "css_colors.txt", 0),
    #palette("matplotlib", "matplotlib_colors.txt", 2) # there's like 10 colors total, I think we'll survive without them
    ]

all_colors = []

from math import sqrt
def rgbdist(c1, c2):
    return sqrt((c1.r - c2.r)**2 + (c1.g - c2.g)**2 + (c1.b - c2.b)**2)

class Color:
    def __init__(self, r, g, b, name, prefix, priority):
        self.r = r
        self.g = g
        self.b = b
        self.name = name
        self.prefix = prefix
        self.priority = priority
        self.nearest_neighbor = None
        
    def __repr__(self):
        return f"<Color ({self.r}, {self.g}, {self.b}) - '{self.prefix}:{self.name}', priority = {self.priority}, nearest_neighbor={self.nearest_neighbor.name if self.nearest_neighbor is not None else None}>"
    
    def nn(self, colors):
        nearest = None
        nearest_dist = 999999
        for c in colors:
            dist = rgbdist(self, c)
            if dist == 0: continue
            if dist < nearest_dist:
                nearest = c
                nearest_dist = dist
        self.nearest_neighbor = nearest
        
for p in palettes:
    prefix = p.name
    priority = p.priority
    for name, rgb in p.colors.items():
        all_colors.append(Color(*rgb, name, prefix, priority))
    print(f"{prefix}->{len(all_colors)}")
        
for c in all_colors:
    c.nn(all_colors)

smallest_dist = 9999999999999
largest_dist = 0
for c in all_colors:
    dist = rgbdist(c, c.nearest_neighbor)
    if dist > largest_dist: largest_dist = dist
    if dist < smallest_dist: smallest_dist = dist
    #print(f"{c.prefix}:{c.name} -> {c.nearest_neighbor.prefix}:{c.nearest_neighbor.name}\t{rgbdist(c, c.nearest_neighbor):.2f}")
# questions -

# are there any colors where their nearest neighbor's nearest neighbor isn't them? (There should be)
nonnear_pairs = 0
for c in all_colors:
    neighbor = c.nearest_neighbor
    their_neighbor = neighbor.nearest_neighbor
    if c is not their_neighbor:
        #print(f"{c.prefix}:{c.name} -> {neighbor.prefix}:{neighbor.name} -> {their_neighbor.prefix}:{their_neighbor.name}")
        nonnear_pairs += 1
print("Non-near pairs:", nonnear_pairs)
    #print(f"{c.prefix}:{c.name} -> {c.nearest_neighbor.prefix}:{c.nearest_neighbor.name}\t{rgbdist(c, c.nearest_neighbor):.2f}")

# Are there duplicates? They should be removed from the palette that won't be used
dupes = 0
for c in all_colors:
    for c2 in all_colors:
        if c is c2: continue
        if c.r == c2.r and c.g == c2.g and c.b == c2.b:
            dupes += 1
print("dupes:", dupes, "this many will need to be removed:", dupes / 2)

# What order to put them in? Do we want large radiuses first, or some sort of "common color" table?

# does manhattan distance change any answers over the 16.7M RGB values?

# What's the worst case lookup? (Checking all 1200 colors to find the name?)