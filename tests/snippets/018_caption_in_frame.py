# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev status=ok
# Caption in Frame - Text inside containers
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

# Card-style container with text
card = mcrfpy.Frame(
    pos=(262, 184), size=(500, 400),
    fill_color=mcrfpy.Color(50, 60, 80),
    outline=3.0,
    outline_color=mcrfpy.Color(100, 120, 160)
)
scene.children.append(card)

# Title in card
card_title = mcrfpy.Caption(text="Player Stats", pos=(180, 30))
card_title.fill_color = mcrfpy.Color(255, 220, 100)
card.children.append(card_title)

# Stats
stats = [
    "Health: 100/100",
    "Mana: 50/50",
    "Strength: 15",
    "Defense: 12",
    "Speed: 18",
]

for i, stat in enumerate(stats):
    line = mcrfpy.Caption(text=stat, pos=(50, 100 + i * 50))
    line.fill_color = mcrfpy.Color(200, 200, 200)
    card.children.append(line)
