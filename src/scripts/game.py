import mcrfpy
import code

#t = mcrfpy.Texture("assets/kenney_tinydungeon.png", 16, 16) # 12, 11)
t = mcrfpy.Texture("assets/kenney_TD_MR_IP.png", 16, 16) # 12, 11)
btn_tex = mcrfpy.Texture("assets/48px_ui_icons-KenneyNL.png", 48, 48)
font = mcrfpy.Font("assets/JetbrainsMono.ttf")

frame_color = (64, 64, 128)

import random
import cos_entities as ce
import cos_level as cl
from cos_itemdata import itemdata
#import cos_tiles as ct

class Resources:
    def __init__(self):
        self.music_enabled = True
        self.music_volume = 40
        self.sfx_enabled = True
        self.sfx_volume = 100
        self.master_volume = 100

        # load the music/sfx files here
        self.splats = []
        for i in range(1, 10):
            mcrfpy.createSoundBuffer(f"assets/sfx/splat{i}.ogg")


    def play_sfx(self, sfx_id):
        if self.sfx_enabled and self.sfx_volume and self.master_volume:
            mcrfpy.setSoundVolume(self.master_volume/100 * self.sfx_volume)
            mcrfpy.playSound(sfx_id)

    def play_music(self, track_id):
        if self.music_enabled and self.music_volume and self.master_volume:
            mcrfpy.setMusicVolume(self.master_volume/100 * self.music_volume)
            mcrfpy.playMusic(...)

resources = Resources()

class Crypt:
    def __init__(self):
        play = mcrfpy.Scene("play")
        self.ui = mcrfpy.sceneUI("play")

        entity_frame = mcrfpy.Frame(pos=(815, 10), size=(194, 595), fill_color=frame_color)
        inventory_frame = mcrfpy.Frame(pos=(10, 610), size=(800, 143), fill_color=frame_color)
        stats_frame = mcrfpy.Frame(pos=(815, 610), size=(194, 143), fill_color=frame_color)

        #self.level = cl.Level(30, 23)
        self.entities = []
        self.depth=1
        self.stuck_btn = SweetButton(self.ui, (810, 700), "Stuck", icon=19, box_width=150, box_height = 60, click=self.stuck)

        self.level_plan = {
                1: [("spawn", "button", "boulder"), ("exit")],
                2: [("spawn", "button", "treasure", "treasure", "treasure", "rat", "rat", "boulder"), ("exit")],
                #2: [("spawn", "button", "boulder"), ("rat"), ("exit")],
                3: [("spawn", "button", "boulder"), ("rat"), ("exit")],
                4: [("spawn", "button", "rat"), ("boulder", "rat", "treasure"), ("exit")],
                5: [("spawn", "button", "rat"), ("boulder", "rat"), ("exit")],
                6: {(("spawn", "button"), ("boulder", "treasure", "exit")),
                    (("spawn", "boulder"), ("button", "treasure", "exit"))},
                7: {(("spawn", "button"), ("boulder", "treasure", "exit")),
                    (("spawn", "boulder"), ("button", "treasure", "exit"))},
                8: {(("spawn", "treasure", "button"), ("boulder", "treasure", "exit")),
                    (("spawn", "treasure", "boulder"), ("button", "treasure", "exit"))}
                #9: self.lv_planner
                }

        # empty void for the player to initialize into
        self.headsup = mcrfpy.Frame(pos=(10, 684), size=(320, 64), fill_color=(0, 0, 0, 0))
        self.sidebar = mcrfpy.Frame(pos=(860, 4), size=(160, 600), fill_color=(96, 96, 160))

        # Heads Up (health bar, armor bar) config
        self.health_bar = [mcrfpy.Sprite(x=32*i, y=2, texture=t, sprite_index=659, scale=2) for i in range(10)]
        [self.headsup.children.append(i) for i in self.health_bar]
        self.armor_bar = [mcrfpy.Sprite(x=32*i, y=42, texture=t, sprite_index=659, scale=2) for i in range(10)]
        [self.headsup.children.append(i) for i in self.armor_bar]
        # (40, 3), caption, font, fill_color=font_color
        self.stat_captions = mcrfpy.Caption(text="HP:10\nDef:0(+0)", pos=(325,0), font=font, fill_color=(255, 255, 255))
        self.stat_captions.outline = 3
        self.stat_captions.outline_color = (0, 0, 0)
        self.headsup.children.append(self.stat_captions)

        # Side Bar (inventory, level info) config
        self.level_caption = mcrfpy.Caption(text="Level: 1", pos=(5,5), font=font, fill_color=(255, 255, 255))
        self.level_caption.font_size = 26 
        self.level_caption.outline = 3
        self.level_caption.outline_color = (0, 0, 0)
        self.sidebar.children.append(self.level_caption)
        self.inv_sprites = [mcrfpy.Sprite(x=15, y=70 + 95*i, texture=t, sprite_index=659, scale=6.0) for i in range(5)]
        for i in self.inv_sprites:
            self.sidebar.children.append(i)
        self.key_captions = [
                mcrfpy.Sprite(x=75, y=130 + (95*2) + 95 * i, texture=t, sprite_index=384 + i, scale=3.0) for i in range(3)
                ]
        for i in self.key_captions:
            self.sidebar.children.append(i)
        self.inv_captions = [
                mcrfpy.Caption(text="x", pos=(25, 130 + 95 * i), font=font, fill_color=(255, 255, 255)) for i in range(5)
                ]
        for i in self.inv_captions:
            i.font_size = 16
            self.sidebar.children.append(i)

        liminal_void = mcrfpy.Grid(grid_size=(1, 1), texture=t, pos=(0, 0), size=(16, 16))
        self.grid = liminal_void
        self.player = ce.PlayerEntity(game=self)
        self.spawn_point = (0, 0)

        # level creation moves player to the game level at the generated spawn point
        self.create_level(self.depth)
        #self.grid = mcrfpy.Grid(20, 15, t, (10, 10), (1014, 758))
        self.swap_level(self.level, self.spawn_point)

        # Test Entities
        #ce.BoulderEntity(9, 7, game=self)
        #ce.BoulderEntity(9, 8, game=self)
        #ce.ExitEntity(12, 6, 14, 4, game=self)
        # scene setup

        ## might be done by self.swap_level
        #[self.ui.append(e) for e in (self.grid, self.stuck_btn.base_frame)] # entity_frame, inventory_frame, stats_frame)]

        self.possibilities = None # track WFC possibilities between rounds
        self.enemies = []
        #mcrfpy.setTimer("enemy_test", self.enemy_movement, 750)

        #mcrfpy.Frame(x, y, box_width+shadow_offset, box_height, fill_color = (0, 0, 0, 255))
        #Sprite(0, 3, btn_tex, icon, icon_scale)

    #def enemy_movement(self, *args):
    #    for e in self.enemies: e.act()

    #def spawn_test_rat(self):
    #    success = False
    #    while not success:
    #        x, y = [random.randint(0, i-1) for i in self.grid.grid_size]
    #        success = self.grid.at((x,y)).walkable
    #    self.enemies.append(ce.EnemyEntity(x, y, game=self))

    def gui_update(self):
        self.stat_captions.text = f"HP:{self.player.hp}\nDef:{self.player.calc_defense()}(+{self.player.calc_defense() - self.player.base_defense})"
        for i, hs in enumerate(self.health_bar):
            full_hearts = self.player.hp - (i*2)
            empty_hearts = self.player.max_hp - (i*2)
            hs.sprite_number = 659
            if empty_hearts >= 2:
                hs.sprite_number = 208
            if full_hearts >= 2:
                hs.sprite_number = 210
            elif full_hearts == 1:
                hs.sprite_number = 209
        for i, arm_s in enumerate(self.armor_bar):
            full_hearts = self.player.calc_defense() - (i*2)
            arm_s.sprite_number = 659
            if full_hearts >= 2:
                arm_s.sprite_number = 211
            elif full_hearts == 1:
                arm_s.sprite_number = 212

        #items = self.player.equipped[:] + self.player.inventory[:]
        for i in range(5):
            if i == 0:
                item = self.player.equipped[0] if len(self.player.equipped) > 0 else None
            elif i == 1:
                item = self.player.equipped[1] if len(self.player.equipped) > 1 else None
            elif i == 2:
                item = self.player.inventory[0] if len(self.player.inventory) > 0 else None
            elif i == 3:
                item = self.player.inventory[1] if len(self.player.inventory) > 1 else None
            elif i == 4:
                item = self.player.inventory[2] if len(self.player.inventory) > 2 else None
            if item is None:
                self.inv_sprites[i].sprite_number = 659
                if i > 1: self.key_captions[i - 2].sprite_number = 659
                self.inv_captions[i].text = ""
                continue
            self.inv_sprites[i].sprite_number = item.sprite
            if i > 1:
                self.key_captions[i - 2].sprite_number = 384 + (i - 2)
            if item.zap_cooldown_remaining:
                self.inv_captions[i].text = f"[{item.zap_cooldown_remaining}] {item.text})"
            else:
                self.inv_captions[i].text = item.text
            self.inv_captions[i].fill_color = item.text_color

    def lv_planner(self, target_level):
        """Plan room sequence in levels > 9"""
        monsters = (target_level - 6) // 2
        target_rooms = min(int(target_level // 2), 6)
        target_treasure = min(int(target_level // 3), 4)
        rooms = []
        for i in range(target_rooms):
            rooms.append([])
        for o in ("spawn", "boulder", "button", "exit"):
            r = random.randint(0, target_rooms-1)
            rooms[r].append(o)
        monster_table = {
            "rat": int(monsters * 0.8) + 2,
            "big rat": max(int(monsters * 0.2) - 2, 0),
            "cyclops": max(int(monsters * 0.1) - 3, 0)
            }
        monster_table = {k: v for k, v in monster_table.items() if v > 0}
        monster_names = list(monster_table.keys())
        monster_weights = [monster_table[k] for k in monster_names]
        for m in range(monsters):
            r = random.randint(0, target_rooms - 1)
            rooms[r].append(random.choices(monster_names, weights = monster_weights)[0])

        for t in range(target_treasure):
            r = random.randint(0, target_rooms - 1)
            rooms[r].append("treasure")

        return rooms

    def treasure_planner(self, treasure_level):
        """Plan treasure contents at all levels"""
        
        # find item name in base_wts key (base weight of the category)
        #base_weight = lambda s: base_wts[list([t for t in base_wts.keys() if s in t])[0]]
        #weights = {d[0]: base_weight(d[0]) for d in item_minlv.items() if treasure_level > d[1]}
        #if self.player.archetype is None:
        #    prefs = []
        #elif self.player.archetype == "viking":
        #    prefs = ["axe2", "axe3", "green_pot"]
        #elif self.player.archetype == "knight":
        #    prefs = ["sword2", "shield", "grey_pot"]
        #elif self.player.archetype == "wizard":
        #    prefs = ["staff", "staff2", "blue_pot"]
        #for i in prefs:
        #    if i in weights: weights[i] *= 3
        weights = {}
        for item in itemdata:
            data = itemdata[item]
            if data.min_lv > treasure_level or treasure_level > data.max_lv: continue
            weights[item] = data.base_wt
            if self.player.archetype is not None and data.affinity == self.player.archetype:
                weights[item] *= 3
        return weights

    def start(self):
        resources.play_sfx(1)
        play.activate()
        play.on_key = self.cos_keys

    def add_entity(self, e:ce.COSEntity):
        self.entities.append(e)
        self.entities.sort(key = lambda e: e.draw_order, reverse=False)
        # hack / workaround for grid.entities not interable
        while len(self.grid.entities): # while there are entities on the grid,
            self.grid.entities.pop(0) # remove the 1st ("0th")
        for e in self.entities:
            self.grid.entities.append(e._entity)

    def create_level(self, depth, _luck = 0):
        #if depth < 3:
        #    features = None
        self.level = cl.Level(20, 20)
        self.grid = self.level.grid
        if depth in self.level_plan:
            plan = self.level_plan[depth]
        else:
            plan = self.lv_planner(depth)
        coords = self.level.generate(plan)
        self.entities = []
        if self.player:
            luck = self.player.luck
        else:
            luck = 0
        buttons = []
        for k, v in sorted(coords, key=lambda i: i[0]): # "button" before "exit"; "button", "button", "door", "exit" -> alphabetical is correct sequence
            if k == "spawn":
                if self.player:
                    self.add_entity(self.player)
                    #self.player.draw_pos = v
                    self.spawn_point = v
            elif k == "boulder":
                ce.BoulderEntity(v[0], v[1], game=self)
            elif k == "treasure":
                ce.TreasureEntity(v[0], v[1], treasure_table = self.treasure_planner(depth + luck), game=self)
            elif k == "button":
                buttons.append(v)
            elif k == "exit":
                btn = buttons.pop(0)
                ce.ExitEntity(v[0], v[1], btn[0], btn[1], game=self)
            elif k == "rat":
                ce.EnemyEntity(*v, game=self)
            elif k == "big rat":
                ce.EnemyEntity(*v, game=self, base_damage=2, hp=4, sprite=130)
            elif k == "cyclops":
                ce.EnemyEntity(*v, game=self, base_damage=3, hp=8, sprite=109, base_defense=2)
                
        #if self.depth > 2:
            #for i in range(10):
            #    self.spawn_test_rat()

    def stuck(self, sweet_btn, args):
        if args[3] == "end": return
        self.create_level(self.depth)
        self.swap_level(self.level, self.spawn_point)

    def cos_keys(self, key, state):
        d = None
        if state == "end": return
        elif key == "Grave":
            code.InteractiveConsole(locals=globals()).interact()
            return
        elif key == "Z":
            self.player.do_zap()
            self.enemy_turn()
            return
        elif key == "W": d = (0, -1)
        elif key == "A": d = (-1, 0)
        elif key == "S": d = (0, 1)
        elif key == "D": d = (1, 0)
        elif key == "Num1":
            if len(self.player.inventory) > 0:
                self.player.inventory[0].consume(self.player)
                self.player.inventory[0] = None
                self.enemy_turn()
            else:
                print("No item")
        elif key == "Num2":
            if len(self.player.inventory) > 1:
                self.player.inventory[1].consume(self.player)
                self.player.inventory[1] = None
            else:
                print("No item")
        elif key == "Num3":
            if len(self.player.inventory) > 2:
                self.player.inventory[2].consume(self.player)
                self.player.inventory[2] = None
            else:
                print("No item")

        #elif key == "M": self.level.generate()
        #elif key == "R":
        #    self.level.reset()
        #    self.possibilities = None
        #elif key == "T":
        #    self.level.split()
        #    self.possibilities = None
        #elif key == "Y": self.level.split(single=True)
        #elif key == "U": self.level.highlight(+1)
        #elif key == "I": self.level.highlight(-1)
        #elif key == "O":
        #    self.level.wall_rooms()
        #    self.possibilities = None
        #elif key == "P": ct.format_tiles(self.grid)
        #elif key == "P":
            #self.possibilities = ct.wfc_pass(self.grid, self.possibilities)
        elif key == "P":
            self.depth += 1
            print(f"Descending: lv {self.depth}")
            self.stuck(None, [1,2,3,4])
        elif key == "Period":
            self.enemy_turn()
        elif key == "X":
            self.pull_boulder_search()
        else:
            print(key)
        if d:
            self.entities.sort(key = lambda e: e.draw_order, reverse=False)
            self.player.try_move(*d)
            self.enemy_turn()

    def enemy_turn(self):
        self.entities.sort(key = lambda e: e.draw_order, reverse=False)
        for e in self.entities:
            e.act()
        # end of enemy turn = player turn
        for i in self.player.equipped:
            i.tick()
        self.gui_update()



    def pull_boulder_search(self):
        for dx, dy in ( (0, -1), (-1, 0), (1, 0), (0, 1) ):
            for e in self.entities:
                if e.draw_pos.x != self.player.draw_pos.x + dx or e.draw_pos.y != self.player.draw_pos.y + dy: continue
                if type(e) == ce.BoulderEntity:
                    self.pull_boulder_move((dx, dy), e)
                    return self.enemy_turn()
        else:
            print("No boulder found to pull.")

    def pull_boulder_move(self, p, target_boulder):
        print(p, target_boulder)
        self.entities.sort(key = lambda e: e.draw_order, reverse=False)
        if self.player.try_move(-p[0], -p[1], test=True):
            old_pos = self.player.draw_pos
            self.player.try_move(-p[0], -p[1])
            target_boulder.do_move(old_pos.x, old_pos.y)

    def swap_level(self, new_level, spawn_point):
        self.level = new_level
        self.grid = self.level.grid
        self.grid.zoom = 2.0
        # Center the camera on the middle of the grid (pixel coordinates: cells * tile_size / 2)
        gw, gh = self.grid.grid_size
        self.grid.center = (gw * 16 / 2, gh * 16 / 2)
        # TODO, make an entity mover function
        #self.add_entity(self.player)
        self.player.grid = self.grid
        self.player.draw_pos = spawn_point
        #self.grid.entities.append(self.player._entity)

        # reform UI (workaround to ui collection iterators crashing)
        while len(self.ui) > 0:
            try:
                self.ui.pop(0)
            except:
                pass
        self.ui.append(self.grid)
        self.ui.append(self.stuck_btn.base_frame)
        self.ui.append(self.headsup)

        self.level_caption.text = f"Level: {self.depth}"
        self.ui.append(self.sidebar)
        self.gui_update()

class SweetButton:
    def __init__(self, ui:mcrfpy.UICollection, 
                 pos:"Tuple[int, int]",
                 caption:str, font=font, font_size=24, font_color=(255,255,255), font_outline_color=(0, 0, 0), font_outline_width=2,
                 shadow_offset = 8, box_width=200, box_height = 80, shadow_color=(64, 64, 86), box_color=(96, 96, 160), 
                 icon=4, icon_scale=1.75, shadow=True, click=lambda *args: None):
        self.ui = ui
        #self.shadow_box = mcrfpy.Frame
        x, y = pos

        # box w/ drop shadow
        self.shadow_offset = shadow_offset
        self.base_frame = mcrfpy.Frame(pos=(x, y), size=(box_width+shadow_offset, box_height), fill_color=(0, 0, 0, 255))
        self.base_frame.on_click = self.do_click

        # drop shadow won't need configured, append directly
        if shadow:
            self.base_frame.children.append(mcrfpy.Frame(pos=(0, 0), size=(box_width, box_height), fill_color=shadow_color))

        # main button is where the content lives
        self.main_button = mcrfpy.Frame(pos=(shadow_offset, shadow_offset), size=(box_width, box_height), fill_color=box_color)
        self.click = click
        self.base_frame.children.append(self.main_button)

        # main button icon
        self.icon = mcrfpy.Sprite(x=0, y=3, texture=btn_tex, sprite_index=icon, scale=icon_scale)
        self.main_button.children.append(self.icon)

        # main button caption
        self.caption = mcrfpy.Caption(text=caption, pos=(40, 3), font=font, fill_color=font_color)
        self.caption.font_size = font_size
        self.caption.outline_color=font_outline_color
        self.caption.outline=font_outline_width
        self.main_button.children.append(self.caption)

    def unpress(self):
        """Helper func for when graphics changes or glitches make the button stuck down"""
        self.main_button.x, self.main_button.y = (self.shadow_offset, self.shadow_offset)

    def do_click(self, x, y, mousebtn, event):
        if event == "start":
            self.main_button.x, self.main_button.y = (0, 0)
        elif event == "end":
            self.main_button.x, self.main_button.y = (self.shadow_offset, self.shadow_offset)
        result = self.click(self, (x, y, mousebtn, event))
        if result: # return True from event function to instantly un-pop
            self.main_button.x, self.main_button.y = (self.shadow_offset, self.shadow_offset)

    @property
    def text(self):
        return self.caption.text

    @text.setter
    def text(self, value):
        self.caption.text = value

    @property
    def sprite_number(self):
        return self.icon.sprite_number

    @sprite_number.setter
    def sprite_number(self, value):
        self.icon.sprite_number = value

class MainMenu:
    def __init__(self):
        menu = mcrfpy.Scene("menu")
        self.ui = mcrfpy.sceneUI("menu")
        menu.activate()
        self.crypt = None

        components = []
        # demo grid
        self.demo = cl.Level(20, 20)
        self.grid = self.demo.grid
        self.grid.zoom = 1.75
        # Center the camera on the middle of the grid (pixel coordinates: cells * tile_size / 2)
        gw, gh = self.grid.grid_size
        self.grid.center = (gw * 16 / 2, gh * 16 / 2)
        coords = self.demo.generate(
                [("boulder", "boulder", "rat", "cyclops", "boulder"), ("spawn"), ("rat", "big rat"), ("button", "boulder", "exit")]
                )
        self.entities = []
        self.add_entity = lambda e: self.entities.append(e)
        #self.create_level = lambda *args: None
        buttons = []
        #self.depth = 20
        for k, v in sorted(coords, key=lambda i: i[0]): # "button" before "exit"; "button", "button", "door", "exit" -> alphabetical is correct sequence
            if k == "spawn":
                self.player = ce.PlayerEntity(game=self)
                self.player.draw_pos = v
                #if self.player:
                #    self.add_entity(self.player)
                #    #self.player.draw_pos = v
                #    self.spawn_point = v
            elif k == "boulder":
                ce.BoulderEntity(v[0], v[1], game=self)
            elif k == "treasure":
                ce.TreasureEntity(v[0], v[1], treasure_table = {}, game=self)
            elif k == "button":
                buttons.append(v)
            elif k == "exit":
                btn = buttons.pop(0)
                ce.ExitEntity(v[0], v[1], btn[0], btn[1], game=self)
            elif k == "rat":
                ce.EnemyEntity(*v, game=self)
            elif k == "big rat":
                ce.EnemyEntity(*v, game=self, base_damage=2, hp=4, sprite=124)
            elif k == "cyclops":
                ce.EnemyEntity(*v, game=self, base_damage=3, hp=8, sprite=109, base_defense=2, can_push=True, move_cooldown=0)
        #self.demo = cl.Level(20, 20)
        #self.create_level(self.depth)
        for e in self.entities:
            self.grid.entities.append(e._entity)
        def just_wiggle(*args):
            try:
                self.player.try_move(*random.choice(((1, 0),(-1, 0),(0, 1),(0, -1))))
                for e in self.entities:
                    e.act()
            except:
                pass
        mcrfpy.setTimer("demo_motion", just_wiggle, 100)
        components.append(
                self.demo.grid
                )


        # title text
        drop_shadow = mcrfpy.Caption(text="Crypt Of Sokoban", pos=(150, 10), font=font, fill_color=(96, 96, 96), outline_color=(192, 0, 0))
        drop_shadow.outline = 3
        drop_shadow.font_size = 64
        components.append(
                drop_shadow
            )

        title_txt = mcrfpy.Caption(text="Crypt Of Sokoban", pos=(158, 18), font=font, fill_color=(255, 255, 255))
        title_txt.font_size = 64
        components.append(
                title_txt
            )

        # toast: text over the demo grid that fades out on a timer
        self.toast = mcrfpy.Caption(text="", pos=(150, 400), font=font, fill_color=(0, 0, 0))
        self.toast.font_size = 28
        self.toast.outline = 2
        self.toast.outline_color = (255, 255, 255)
        self.toast_event = None
        components.append(self.toast)

        # button - PLAY
        #playbtn = mcrfpy.Frame(284, 548, 456, 120, fill_color = 
        play_btn = SweetButton(self.ui, (20, 248), "PLAY", box_width=200, box_height=110, icon=1, icon_scale=2.0, click=self.play)
        components.append(play_btn.base_frame)

        # button - config menu pane
        #self.config = lambda self, sweet_btn, *args: print(f"boop, sweet button {sweet_btn} config {args}")
        config_btn = SweetButton(self.ui, (10, 678), "Settings", icon=2, click=self.show_config)
        components.append(config_btn.base_frame)

        # button - insta-1080p scaling
        scale_btn = SweetButton(self.ui, (10+256, 678), "Scale up\nto 1080p", icon=15, click=self.scale)
        self.scaled = False
        components.append(scale_btn.base_frame)

        # button - music toggle
        music_btn = SweetButton(self.ui, (10+256*2, 678), "Music\nON", icon=12, click=self.music_toggle)
        resources.music_enabled = True
        resources.music_volume = 40
        components.append(music_btn.base_frame)

        # button - sfx toggle
        sfx_btn = SweetButton(self.ui, (10+256*3, 678), "SFX\nON", icon=0, click=self.sfx_toggle)
        resources.sfx_enabled = True
        resources.sfx_volume = 40
        components.append(sfx_btn.base_frame)


        [self.ui.append(e) for e in components]

    def toast_say(self, txt, delay=10):
        "kick off a toast event"
        if self.toast_event is not None:
            mcrfpy.delTimer("toast_timer")
        self.toast.text = txt
        self.toast_event = 350
        self.toast.fill_color = (255, 255, 255, 255)
        self.toast.outline = 2
        self.toast.outline_color = (0, 0, 0, 255)
        mcrfpy.setTimer("toast_timer", self.toast_callback, 100)

    def toast_callback(self, *args):
        "fade out the toast text"
        self.toast_event -= 5
        if self.toast_event < 0:
            self.toast_event = None
            mcrfpy.delTimer("toast_timer")
            mcrfpy.text = ""
            return
        a = min(self.toast_event, 255)
        self.toast.fill_color = (255, 255, 255, a)
        self.toast.outline_color = (0, 0, 0, a)

    def show_config(self, sweet_btn, args):
        self.toast_say("Beep, Boop! Configurations will go here.")

    def play(self, sweet_btn, args):
        #if args[3] == "start": return # DRAMATIC on release action!
        if args[3] == "end": return
        mcrfpy.delTimer("demo_motion")  # Clean up the demo timer
        self.crypt = Crypt()
        #mcrfpy.setScene("play")
        self.crypt.start()

    def scale(self, sweet_btn, args, window_scale=None):
        if args[3] == "end": return
        if not window_scale:
            self.scaled = not self.scaled
            window_scale = 1.3
        else:
            self.scaled = True
        sweet_btn.unpress()
        if self.scaled:
            self.toast_say("Windowed mode only, sorry!\nCheck Settings for for fine-tuned controls.")
            mcrfpy.setScale(window_scale)
            sweet_btn.text = "Scale down\n to 1.0x"
        else:
            mcrfpy.setScale(1.0)
            sweet_btn.text = "Scale up\nto 1080p"

    def music_toggle(self, sweet_btn, args):
        if args[3] == "end": return
        resources.music_enabled = not resources.music_enabled
        print(f"music: {resources.music_enabled}")
        if resources.music_enabled:
            mcrfpy.setMusicVolume(self.music_volume)
            sweet_btn.text = "Music is ON"
            sweet_btn.sprite_number = 12
        else:
            self.toast_say("Use your volume keys or\nlook in Settings for a volume meter.")
            mcrfpy.setMusicVolume(0)
            sweet_btn.text = "Music is OFF"
            sweet_btn.sprite_number = 17

    def sfx_toggle(self, sweet_btn, args):
        if args[3] == "end": return
        resources.sfx_enabled = not resources.sfx_enabled
        #print(f"sfx: {resources.sfx_enabled}")
        if resources.sfx_enabled:
            mcrfpy.setSoundVolume(self.sfx_volume)
            sweet_btn.text = "SFX are ON"
            sweet_btn.sprite_number = 0
        else:
            self.toast_say("Use your volume keys or\nlook in Settings for a volume meter.")
            mcrfpy.setSoundVolume(0)
            sweet_btn.text = "SFX are OFF"
            sweet_btn.sprite_number = 17

mainmenu = MainMenu()
