# McRogueFace - 2D Game Engine

An experimental prototype game engine built for my own use in 7DRL 2023.

*Blame my wife for the name*

## Tenets:

* C++ first, Python close behind.
* Entity-Component system based on David Churchill's Memorial University COMP4300 course lectures available on Youtube.
* Graphics, particles and shaders provided by SFML.
* Pathfinding, noise generation, and other Roguelike goodness provided by TCOD.

## Why?

I did the r/RoguelikeDev TCOD tutorial in Python. I loved it, but I did not want to be limited to ASCII. I want to be able to draw pixels on top of my tiles (like lines or circles) and eventually incorporate even more polish.

## To-do

* ✅ Initial Commit
* ✅ Integrate scene, action, entity, component system from COMP4300 engine
* ✅ Windows / Visual Studio project
* ✅ Draw Sprites
* ✅ Play Sounds
* ✅ Draw UI, spawn entity from Python code
* ❌ Python AI for entities (NPCs on set paths, enemies towards player)
* ✅ Walking / Collision
* ❌ "Boards" (stairs / doors / walk off edge of screen)
* ❌ Cutscenes - interrupt normal controls, text scroll, character portraits
* ❌ Mouse integration - tooltips, zoom, click to select targets, cursors
