class Caption:
    def __init__(self, text, textsize, color):
        self.text = text
        self.textsize = textsize
        self.color = color

class Button:
    def __init__(self, x, y, w, h, bgcolor, textcolor, text, actioncode):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bgcolor = bgcolor
        self.textcolor = textcolor
        self.text = text
        self.actioncode = actioncode

class Sprite:
    def __init__(self, tex_index, x, y):
        self.tex_index = tex_index
        self.x = x
        self.y = y

class UIMenu:
    def __init__(self, title, x, y, w, h, bgcolor, visible=False):
        self.title = title
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.bgcolor = bgcolor
        self.visible = visible
        self.captions = []
        self.buttons = []
        self.sprites = []

    def __repr__(self):
        return f"<UIMenu title={repr(self.title)}, x={self.x}, y={self.y}, w={self.w}, h={self.h}, bgcolor={self.bgcolor}, visible={self.visible}, {len(self.captions)} captions, {len(self.buttons)} buttons, {len(self.sprites)} sprites>"
