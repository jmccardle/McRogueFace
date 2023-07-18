```
* python API overhaul
	* At the very least, a function to turn a color tuple to sf::Color would be good.
	  All the sf::Color objects going into / out of Python need to support transparency (4th value of Alpha) - Python would tolerate it, C++ needs to allow it (parse "iii|i", default alpha of 0 for fully nontransparent)
	* The entire method of reading properties to re-ingest Grids/Menus is stupid.
	  C++ classes should be exposed more directly, or have clean methods to accept the changes from Python code.
	* return actual exceptions instead of std::cout and NULL
	* smart pointers (`std::shared_ptr<PyObject>`) to C++-ify Python object passing? Can this be made to work with reference counting?
	* Raise Exceptions - see *janknote* in the Animation API method
* C++ hygene: Make data members private, call getter/setter methods
	* std::shared_ptr, not bare pointers. The grid/entity/component connections suffer from this
* SFML: "widget" hierarchy. Keep all sizes/positions in the RectangleShape objects. Make Grid and UIMenu subclasses of the same base, and keep a single map of drawable widgets.
	* UIMenu should become a "frame", and draw any objects of the "Widget" class relatively to its own positions
	* "Widget" as an abstract class should set the template for going to/from Python; don't copy to and from Python, the C++ object *is* the Python object.
	* ==Buttons don't know their parent...?== So there's arithmetic happening in the event loop to determine it's actual positions. Fix this with the widgets-on-widgets system (so we can go deeper, and just ask the widgets if they or their children were clicked)
* Keep aspect ratio correct (and hopefully unbork any mouse issues) when maximizing / full screening the game
```

# r/RoguelikeDev Does the Complete Roguelike Tutorial - July 2023

## Planning

Event ends roughly 26 August (last post will be 22 August)

* Add and remove keystroke registration from Python scripts
* Error checking: raise Python exceptions instead of null reference segfault in C++
* Proper exception handling: figure out the "any code at REPL shows the unhandled exception" bug thingy
* Extra clarity: display more status info about what Python stuff is being done
  - load all files in directory at first
  - list modules / classes found
  - list Scenes that were found
  - Read all Python modules, then call objects & methods at C++-managed events (Engine provided decorators, perhaps??)
* PythonScene version of MenuScene
  - instantiate PythonScenes
* Switch Scenes from Python (edge of board / stairs / teleportation feature)
* Update the visible map from Python (fix "map blank until you move" bug)
  - update "camera state" and "Recenter camera" buttons' API info as well without a whole Turn
* C++/TCOD Entity pathfinding without calling Python every Turn
* Replace jank .py files that define engine-required objects with C++ definitions inside of `mcrfpy` module

This actually a pretty big list, but there's about 7 weeks left, so it's just over one item per week.

I have no bad feelings if these items leak over to EngJam or beyond.



## Notes 12 July

Some changes to make in McRFPy_API.cpp:
* create a parallel to _registerPyAction which will register a keystroke to a Python label in the current scene.

## Notes 13 July

- working on API endpoint `_registerInputAction`.

it will add "_py" as a suffix to the action string and register it along with other scene actions.

- Adding public Scene methods. These are on the base class with default of return `false`.

`bool Scene::registerActionInjected(int code, std::string name)` and `unregisterActionInjected`

the PythonScene (and other scenes that support injected user input) can override this method, check existing registrations, and return `true` when succeeding.

- then remove `McRFPy_API::player_input`

This behavior can be more flexibly implemented in Python using keyboard registration. There's some deduplication as well, since I have a Python implementation of collision detection anyway (for items, doors, and NPCs).

Also, upgraded to C++20 (g++ `c++2a`), mostly because I want to use map::contains.

More ideas:

* Need to make "pan" and "zoom" optional on each grid (for minimap type use cases)
* clicks are handled by C++ and only used on buttons. Grids could have a Python click function (with pixel & grid coords available)
* pixel-on-menu Python click function should be possible too
* Need to call a Python update function when C++ events cause camera following to change: UI is only updating after player input


Continue with:

* implement checks in PythonScene::registerActionInjected - Save injected actions, don't let regular actions be overwritten, return success
* Remove PythonScene key definitions and McRFPy_API::player_input
* re-implement walking via keyboard input in Python
* Find a good spot for camera following to update Python immediately
* Find a good spot for grid updates to redraw TCOD line of sight immediately

## Notes 16 July

Main problem that came up today: all Python code is executed at the moment the GameEngine instantiates the PythonScene, which is actually when the game starts up. The active scene at that point is the MenuScene, so the Python code registers events against that scene (which rejects injected event binding and has no API functionality).

Workaround: There's a clickable button that performs the input registration. This is good for working out the behavior, but doesn't really allow Python scripts to properly control and set up their own environment.

The module name is passed to the PythonScene constructor, and the `start()` method is called to set up class objects. Can I add more methods that are called on this module to swap scenes?

## Notes 17 July

The player entity is moving around via Python now!

Unfortunately, the "actiononce" macro I use in C++ is not the behavior passed on to the Python key events. Key release events are being passed to Python just the way that keypresses are.

I'll need to expose more of the input event properties down to Python. I also don't like how keycodes are being passed from python to C++, which currently limits user input to key strokes. Mouse buttons and mouse wheel should be possible too (just as they are under the SFML event binding).

