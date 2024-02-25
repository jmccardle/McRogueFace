class Caption:
    def __init__(self, text, textsize, color):
        self.text = text
        self.textsize = textsize
        self.color = color

    def __repr__(self):
        return f"<Caption text={self.text}, textsize={self.textsize}, color={self.color}>"

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

    def __repr__(self):
        return f"<Button ({self.x}, {self.y}, {self.w}, {self.h}), bgcolor={self.bgcolor}, textcolor={self.textcolor}, actioncode={self.actioncode}>"

class Sprite:
    def __init__(self, tex_index, sprite_index, x, y):
        self.tex_index = tex_index
        self.sprite_index = sprite_index
        self.x = x
        self.y = y

    def __repr__(self):
        return f"<Sprite tex_index={self.tex_index}, self.sprite_index={self.sprite_index}, x={self.x}, y={self.y}>"

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
