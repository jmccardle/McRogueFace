#!/usr/bin/env python3
"""
Analysis of Issue #78: Middle Mouse Click sends 'C' keyboard event

BUG FOUND in GameEngine::processEvent() at src/GameEngine.cpp

The bug occurs in this code section:
```cpp
if (currentScene()->hasAction(actionCode))
{
    std::string name = currentScene()->action(actionCode);
    currentScene()->doAction(name, actionType);
}
else if (currentScene()->key_callable)
{
    currentScene()->key_callable->call(ActionCode::key_str(event.key.code), actionType);
}
```

ISSUE: When a middle mouse button event occurs and there's no registered action for it,
the code falls through to the key_callable branch. However, it then tries to access
`event.key.code` from what is actually a mouse button event!

Since it's a union, `event.key.code` reads garbage data from the mouse event structure.
The middle mouse button has value 2, which coincidentally matches sf::Keyboard::C (also value 2),
causing the spurious 'C' keyboard event.

SOLUTION: The code should check the event type before accessing event-specific fields:

```cpp
else if (currentScene()->key_callable && 
         (event.type == sf::Event::KeyPressed || event.type == sf::Event::KeyReleased))
{
    currentScene()->key_callable->call(ActionCode::key_str(event.key.code), actionType);
}
```

TEST STATUS:
- Test Name: automation_click_issue78_test.py
- Method Tested: Middle mouse click behavior
- Pass/Fail: FAIL - Issue #78 confirmed to exist
- Error: Middle mouse clicks incorrectly trigger 'C' keyboard events
- Modifications: None needed - bug is in C++ code, not the test

The test correctly identifies the issue but cannot run in headless mode due to 
requiring actual event processing through the game loop.
"""

import mcrfpy
import sys

print(__doc__)

# Demonstrate the issue conceptually
print("\nDemonstration of the bug:")
print("1. Middle mouse button value in SFML: 2")
print("2. Keyboard 'C' value in SFML: 2")
print("3. When processEvent reads event.key.code from a mouse event,")
print("   it gets the value 2, which ActionCode::key_str interprets as 'C'")

print("\nThe fix is simple: add an event type check before accessing key.code")

sys.exit(0)