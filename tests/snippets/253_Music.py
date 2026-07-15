# mcrf: objects=[Caption,Music,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("music_demo")
scene.children.append(mcrfpy.Caption(text="Music demo", pos=(20, 20)))
mcrfpy.current_scene = scene

# Load and play background music
music = mcrfpy.Music("assets/sfx/splat1.ogg")
music.volume = 50  # 50% volume
music.loop = True
music.play()

# Control playback
music.pause()
music.position = 0.0  # Jump to a position in seconds
music.play()

# Check status
print(f"Duration: {music.duration}s")
print(f"Playing: {music.playing}")
