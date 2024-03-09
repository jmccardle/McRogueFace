#print("Hello mcrogueface")
import mcrfpy
import cos_play
# Universal stuff
font = mcrfpy.Font("assets/JetbrainsMono.ttf")
texture = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 12, 11)
texture_cold = mcrfpy.Texture("assets/kenney_ice.png", 16, 12, 11)
texture_hot = mcrfpy.Texture("assets/kenney_lava.png", 16, 12, 11)

# Test stuff
mcrfpy.createScene("boom")
#mcrfpy.setScene("boom")
ui = mcrfpy.sceneUI("boom")
box = mcrfpy.Frame(40, 60, 200, 300, fill_color=(255,128,0), outline=4.0, outline_color=(64,64,255,96))
ui.append(box)

#caption = mcrfpy.Caption(10, 10, "Clicky", font, (255, 255, 255, 255), (0, 0, 0, 255))
#box.click = lambda x, y, btn, type: print("Hello callback: ", x, y, btn, type)
#box.children.append(caption)

test_sprite_number = 86 
sprite = mcrfpy.Sprite(20, 60, texture, test_sprite_number, 4.0)
spritecap = mcrfpy.Caption(5, 5, "60", font)
def click_sprite(x, y, btn, action):
    global test_sprite_number
    if action != "start": return
    if btn in ("left", "wheel_up"):
        test_sprite_number -= 1
    elif btn in ("right", "wheel_down"):
        test_sprite_number += 1
    sprite.sprite_number = test_sprite_number # TODO - inconsistent naming for __init__, __repr__ and getsetter: sprite_number vs sprite_index
    spritecap.text = test_sprite_number

sprite.click = click_sprite # TODO - sprites don't seem to correct for screen position or scale when clicking
box.children.append(sprite)
box.children.append(spritecap)
box.click = click_sprite

# Loading Screen
mcrfpy.createScene("loading")
ui = mcrfpy.sceneUI("loading")
mcrfpy.setScene("loading")
logo_texture = mcrfpy.Texture("assets/temp_logo.png", 1024, 1, 1)
logo_sprite = mcrfpy.Sprite(50, 50, logo_texture, 0, 0.5)
ui.append(logo_sprite)
logo_sprite.click = lambda *args: mcrfpy.setScene("menu")
logo_caption = mcrfpy.Caption(70, 600, "Click to Proceed", font, (255, 0, 0, 255), (0, 0, 0, 255))
logo_caption.fill_color =(255, 0, 0, 255)
ui.append(logo_caption)


# menu screen
mcrfpy.createScene("menu")

for e in [
    mcrfpy.Caption(10, 10, "Crypt of Sokoban", font, (255, 255, 255), (0, 0, 0)),
    mcrfpy.Caption(20, 55, "a McRogueFace demo project", font, (192, 192, 192), (0, 0, 0)),
    mcrfpy.Frame(15, 70, 150, 60, fill_color=(64, 64, 128)),
    mcrfpy.Frame(15, 145, 150, 60, fill_color=(64, 64, 128)),
    mcrfpy.Frame(15, 220, 150, 60, fill_color=(64, 64, 128)),
    mcrfpy.Frame(15, 295, 150, 60, fill_color=(64, 64, 128)),
    #mcrfpy.Frame(900, 10, 100, 100, fill_color=(255, 0, 0)),
    ]:
    mcrfpy.sceneUI("menu").append(e)

def click_once(fn):
    def wraps(*args, **kwargs):
        #print(args)
        action = args[3]
        if action != "start": return
        return fn(*args, **kwargs)
    return wraps

@click_once
def asdf(x, y, btn, action):
    print(f"clicky @({x},{y}) {action}->{btn}")

@click_once
def clicked_exit(*args):
    mcrfpy.exit()

menu_btns = [
    ("Boom", lambda *args: 1 / 0),
    ("Exit", clicked_exit), 
    ("About", lambda *args: mcrfpy.setScene("about")), 
    ("Settings", lambda *args: mcrfpy.setScene("settings")), 
    ("Start", lambda *args: mcrfpy.setScene("play"))
    ]
for i in range(len(mcrfpy.sceneUI("menu"))):
    e = mcrfpy.sceneUI("menu")[i] # TODO - fix iterator
    #print(e, type(e))
    if type(e) is not mcrfpy.Frame: continue
    label, fn = menu_btns.pop()
    #print(label)
    e.children.append(mcrfpy.Caption(5, 5, label, font, (192, 192, 255), (0,0,0)))
    e.click = fn


# settings screen
mcrfpy.createScene("settings")
window_scaling = 1.0

scale_caption = mcrfpy.Caption(180, 70, "1.0x", font, (255, 255, 255), (0, 0, 0))
scale_caption.fill_color = (255, 255, 255) # TODO - mcrfpy.Caption.__init__ is not setting colors
for e in [
    mcrfpy.Caption(10, 10, "Settings", font, (255, 255, 255), (0, 0, 0)),
    mcrfpy.Frame(15, 70, 150, 60, fill_color=(64, 64, 128)), # +
    mcrfpy.Frame(300, 70, 150, 60, fill_color=(64, 64, 128)), # -
    mcrfpy.Frame(15, 295, 150, 60, fill_color=(64, 64, 128)),
    scale_caption,
    ]:
    mcrfpy.sceneUI("settings").append(e)

@click_once
def game_scale(x, y, btn, action, delta):
    global window_scaling
    print(f"WIP - scale the window from {window_scaling:.1f} to {window_scaling+delta:.1f}")
    window_scaling += delta
    scale_caption.text = f"{window_scaling:.1f}x"
    mcrfpy.setScale(window_scaling)
    #mcrfpy.setScale(2)

settings_btns = [
    ("back", lambda *args: mcrfpy.setScene("menu")),
    ("-", lambda x, y, btn, action: game_scale(x, y, btn, action, -0.1)),
    ("+", lambda x, y, btn, action: game_scale(x, y, btn, action, +0.1))
    ]

for i in range(len(mcrfpy.sceneUI("settings"))):
    e = mcrfpy.sceneUI("settings")[i] # TODO - fix iterator
    #print(e, type(e))
    if type(e) is not mcrfpy.Frame: continue
    label, fn = settings_btns.pop()
    #print(label, fn)
    e.children.append(mcrfpy.Caption(5, 5, label, font, (192, 192, 255), (0,0,0)))
    e.click = fn
