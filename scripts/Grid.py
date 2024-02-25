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
    def __init__(self, title, gx, gy, gs, x, y, w, h, visible=False):
        self.title = title
        self.grid_x = gx
        self.grid_y = gy
        self.grid_size = gs
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.visible = visible

        self.points = []
        self.entities = []
        
    def at(self, x, y):
        if not (x > 0 and y > 0 and x < self.grid_x and y < self.grid_y): return None
        return self.points[y * self.grid_y + x]

    def __repr__(self):
        return f"<Grid {self.grid_x}x{self.grid_y}, grid_size={self.grid_size}, (({self.x},{self.y}), ({self.w}, {self.h})), visible={self.visible}>"


# CGrid(Grid* _g, int _ti, int _si, int _x, int _y, bool _v)
class Entity:
    def __init__(self, parent, tex_index, sprite_index, x, y, visible=True):
        self.parent = parent
        self.tex_index = tex_index
        self.sprite_index = sprite_index
        self.x = x
        self.y = y
        self.visible = visible
        
    def __repr__(self):
        return f"<Entity on grid {repr(self.parent)}@({self.x},{self.y}), TI={self.tex_index}, SI={self.sprite_index}, visible={self.visible}>"
