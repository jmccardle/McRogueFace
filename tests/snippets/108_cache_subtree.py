# mcrf: objects=[Caption,Color,Frame,Scene] verified=0.2.8-dev@a7ba486 status=ok
# Cache Subtree - Performance optimization
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="cache_subtree Performance",
    pos=(360, 50))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Complex UI without caching
no_cache = mcrfpy.Frame(
    pos=(100, 150), size=(350, 300),
    fill_color=mcrfpy.Color(60, 60, 80),
    cache_subtree=False
)
scene.children.append(no_cache)
no_cache.children.append(mcrfpy.Caption(text="cache_subtree=False", pos=(80, 10)))

# Add many children
for i in range(50):
    f = mcrfpy.Frame(
        pos=(10 + (i % 10) * 33, 40 + (i // 10) * 50),
        size=(28, 40),
        fill_color=mcrfpy.Color(100 + i * 2, 100, 200 - i * 2)
    )
    no_cache.children.append(f)

# Complex UI with caching
with_cache = mcrfpy.Frame(
    pos=(500, 150), size=(350, 300),
    fill_color=mcrfpy.Color(60, 60, 80),
    cache_subtree=True  # Renders children to texture
)
scene.children.append(with_cache)
with_cache.children.append(mcrfpy.Caption(text="cache_subtree=True", pos=(80, 10)))

for i in range(50):
    f = mcrfpy.Frame(
        pos=(10 + (i % 10) * 33, 40 + (i // 10) * 50),
        size=(28, 40),
        fill_color=mcrfpy.Color(100 + i * 2, 100, 200 - i * 2)
    )
    with_cache.children.append(f)

scene.children.append(mcrfpy.Caption(
    text="Caching reduces draw calls for static content",
    pos=(280, 500)
))
