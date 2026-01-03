"""Base class for demo screens."""
import mcrfpy

class DemoScreen:
    """Base class for all demo screens."""

    name = "Base Screen"
    description = "Override this description"

    def __init__(self, scene_name):
        self.scene_name = scene_name
        _scene = mcrfpy.Scene(scene_name)
        self.ui = mcrfpy.sceneUI(scene_name)

    def setup(self):
        """Override to set up the screen content."""
        pass

    def get_screenshot_name(self):
        """Return the screenshot filename for this screen."""
        return f"{self.scene_name}.png"

    def add_title(self, text, y=10):
        """Add a title caption."""
        title = mcrfpy.Caption(text=text, pos=(400, y))
        title.fill_color = mcrfpy.Color(255, 255, 255)
        title.outline = 2
        title.outline_color = mcrfpy.Color(0, 0, 0)
        self.ui.append(title)
        return title

    def add_description(self, text, y=50):
        """Add a description caption."""
        desc = mcrfpy.Caption(text=text, pos=(50, y))
        desc.fill_color = mcrfpy.Color(200, 200, 200)
        self.ui.append(desc)
        return desc

    def add_code_example(self, code, x=50, y=100):
        """Add a code example caption."""
        code_cap = mcrfpy.Caption(text=code, pos=(x, y))
        code_cap.fill_color = mcrfpy.Color(150, 255, 150)
        self.ui.append(code_cap)
        return code_cap
