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
