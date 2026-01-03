"""McRogueFace - Message Log Widget (enhanced)

Documentation: https://mcrogueface.github.io/cookbook/ui_message_log
Repository: https://github.com/jmccardle/McRogueFace/blob/master/docs/cookbook/ui/ui_message_log_enhanced.py

This code is extracted from the McRogueFace documentation and can be
run directly with: ./mcrogueface path/to/this/file.py
"""

def handle_keys(key, state):
    if state != "start":
        return

    if key == "PageUp":
        log.scroll_up(5)
    elif key == "PageDown":
        log.scroll_down(5)

mcrfpy.keypressScene(handle_keys)

# Or with mouse scroll on the frame
def on_log_scroll(x, y, button, action):
    # Note: You may need to implement scroll detection
    # based on your input system
    pass

log.frame.click = on_log_scroll