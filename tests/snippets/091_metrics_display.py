# mcrf: objects=[Caption,Color,Frame,Scene,Timer] verified=0.2.8-dev@a7ba486 status=ok
# Metrics Display - Performance monitoring
import mcrfpy

scene = mcrfpy.Scene("demo")
mcrfpy.current_scene = scene

scene.children.append(mcrfpy.Frame(pos=(0, 0), size=(1024, 768), fill_color=mcrfpy.Color(30, 30, 40)))

_caption = mcrfpy.Caption(
    text="Performance Metrics",
    pos=(400, 80))
_caption.fill_color = mcrfpy.Color(255, 220, 100)
scene.children.append(_caption)

# Create metric displays
labels = {}
metrics_list = ["frame_time", "fps", "draw_calls", "ui_elements", "visible_elements"]

for i, name in enumerate(metrics_list):
    label = mcrfpy.Caption(text=f"{name}: --", pos=(300, 180 + i * 60))
    scene.children.append(label)
    labels[name] = label

# Add some elements to track
for i in range(50):
    frame = mcrfpy.Frame(
        pos=(100 + (i % 10) * 80, 500 + (i // 10) * 50),
        size=(60, 40),
        fill_color=mcrfpy.Color(80 + i * 3, 80, 150 - i * 2)
    )
    scene.children.append(frame)

def update_metrics(timer, runtime):
    metrics = mcrfpy.getMetrics()
    for name in metrics_list:
        if name in metrics:
            value = metrics[name]
            if isinstance(value, float):
                labels[name].text = f"{name}: {value:.2f}"
            else:
                labels[name].text = f"{name}: {value}"

timer = mcrfpy.Timer("metrics", update_metrics, 100)
