class GridPoint:
    def __init__(self, color, walkable, tilesprite, transparent, visible, discovered, color_overlay, tile_overlay, uisprite):
        self.color = color
        self.walkable = walkable
        self.tilesprite = tilesprite
        self.transparent = transparent
        self.visible = visible
        self.discovered = discovered
        self.color_overlay = color_overlay
        self.tile_overlay = tile_overlay
        self.uisprite = uisprite

    def __repr__(self):
        return f"<GridPoint {self.color}, {self.tilesprite}/{self.uisprite} {'W' if self.walkable else '-'}{'T' if self.transparent else '-'}{'V' if self.visible else '-'}{'D' if self.discovered else '-'} {self.color_overlay}/{self.tile_overlay}>"

class Grid:
    def __init__(self, title, gx, gy, gs, x, y, w, h):
        self.title = title
        self.grid_x = gx
        self.grid_y = gy
        self.grid_size = gs
        self.x = x
        self.y = y
        self.w = w
        self.h = h

        self.points = []

    def __repr__(self):
        return f"<Grid {self.grid_x}x{self.grid_y}, grid_size={self.grid_size}, (({self.x},{self.y}), ({self.w}, {self.h}))>"
