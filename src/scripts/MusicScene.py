import mcrfpy
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED, GREEN, BLUE = (255, 0, 0), (0, 255, 0), (0, 0, 255)
DARKRED, DARKGREEN, DARKBLUE = (192, 0, 0), (0, 192, 0), (0, 0, 192)
class MusicScene:
    def __init__(self, ui_name = "demobox1", grid_name = "demogrid"):
        # Texture & Sound Loading
        print("Load textures")
        mcrfpy.createTexture("./assets/test_portraits.png", 32, 8, 8) #0 - portraits
        mcrfpy.createTexture("./assets/alives_other.png", 16, 64, 64) #1 - TinyWorld NPCs
        mcrfpy.createTexture("./assets/alives_other.png", 32, 32, 32) #2 - TinyWorld NPCs - 2x2 sprite
    #     	{"createSoundBuffer", McRFPy_API::_createSoundBuffer, METH_VARARGS, "(filename)"},
	#{"loadMusic", McRFPy_API::_loadMusic, METH_VARARGS, "(filename)"},
	#{"setMusicVolume", McRFPy_API::_setMusicVolume, METH_VARARGS, "(int)"},
	#{"setSoundVolume", McRFPy_API::_setSoundVolume, METH_VARARGS, "(int)"},
	#{"playSound", McRFPy_API::_playSound, METH_VARARGS, "(int)"},
	#{"getMusicVolume", McRFPy_API::_getMusicVolume, METH_VARARGS, ""},
	#{"getSoundVolume", McRFPy_API::_getSoundVolume, METH_VARARGS, ""},
    
        mcrfpy.loadMusic("./assets/ultima.ogg")
        mcrfpy.createSoundBuffer("./assets/boom.wav")
        self.ui_name = ui_name
        self.grid_name = grid_name

        print("Create UI")
        # Create dialog UI
        mcrfpy.createMenu(ui_name, 20, 540, 500, 200)
        mcrfpy.createCaption(ui_name, f"Music Volume: {mcrfpy.getMusicVolume()}", 24, RED)
        mcrfpy.createCaption(ui_name, f"SFX Volume: {mcrfpy.getSoundVolume()}", 24, RED)
        #mcrfpy.createButton(ui_name, 250, 20, 100, 50, DARKBLUE, (0, 0, 0), "clicky", "testaction")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKRED, (0, 0, 0), "Music+", "mvol+")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKGREEN, (0, 0, 0), "Music-", "mvol-")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, GREEN, "SFX+", "svol+")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKBLUE, RED, "SFX-", "svol-")
        mcrfpy.createButton(ui_name, 250, 0, 130, 40, DARKRED, (0, 0, 0), "REPL", "startrepl")
        mcrfpy.createSprite(ui_name, 1, 0, 20, 40, 3.0)
        
        print("Create UI 2")
        entitymenu = "entitytestmenu"
        
        mcrfpy.createMenu(entitymenu, 840, 20, 20, 500)
        mcrfpy.createButton(entitymenu, 0, 10, 150, 40, DARKBLUE, BLACK, "PlayM", "playm")
        mcrfpy.createButton(entitymenu, 0, 60, 150, 40, DARKBLUE, BLACK, "StopM", "stopm")
        mcrfpy.createButton(entitymenu, 0, 110, 150, 40, DARKBLUE, BLACK, "SFX", "boom")
        print("Make UIs visible")
        self.menus = mcrfpy.listMenus()
        self.menus[0].visible = True
        self.menus[1].w = 170
        self.menus[1].visible = True
        mcrfpy.modMenu(self.menus[0])
        mcrfpy.modMenu(self.menus[1])
        self.mvol = mcrfpy.getMusicVolume()
        self.svol = mcrfpy.getSoundVolume()
        mcrfpy.registerPyAction("mvol+", lambda: self.setmvol(self.mvol+10))
        mcrfpy.registerPyAction("mvol-", lambda: self.setmvol(self.mvol-10))
        mcrfpy.registerPyAction("svol+", lambda: self.setsvol(self.svol+10))
        mcrfpy.registerPyAction("svol-", lambda: self.setsvol(self.svol-10))
        mcrfpy.registerPyAction("playm", lambda: None)
        mcrfpy.registerPyAction("stopm", lambda: None)
        mcrfpy.registerPyAction("boom", lambda: mcrfpy.playSound(0))
        
    def setmvol(self, v):
        mcrfpy.setMusicVolume(int(v))
        self.menus[0].captions[0].text = f"Music Volume: {mcrfpy.getMusicVolume():.1f}"
        mcrfpy.modMenu(self.menus[0])
        self.mvol = mcrfpy.getMusicVolume()
        
    def setsvol(self, v):
        mcrfpy.setSoundVolume(int(v))
        self.menus[0].captions[1].text = f"Sound Volume: {mcrfpy.getSoundVolume():.1f}"
        mcrfpy.modMenu(self.menus[0])
        self.svol = mcrfpy.getSoundVolume()

scene = None
def start():
    global scene
    scene = MusicScene()

