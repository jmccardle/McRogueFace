#!/usr/bin/env python3
"""
Comprehensive test for Issue #76: UIEntityCollection returns wrong type for derived classes

This test demonstrates that when retrieving entities from a UIEntityCollection,
derived Entity classes lose their type and are returned as base Entity objects.

The bug: The C++ implementation of UIEntityCollection::getitem creates a new
PyUIEntityObject with type "Entity" instead of preserving the original Python type.
"""

import mcrfpy
from mcrfpy import automation
import sys
import gc

# Define several derived Entity classes with different features
class Player(mcrfpy.Entity):
    def __init__(self, x, y):
        # Entity expects Vector position and optional texture
        super().__init__(mcrfpy.Vector(x, y))
        self.health = 100
        self.inventory = []
        self.player_id = "PLAYER_001"
    
    def take_damage(self, amount):
        self.health -= amount
        return self.health > 0

class Enemy(mcrfpy.Entity):
    def __init__(self, x, y, enemy_type="goblin"):
        # Entity expects Vector position and optional texture
        super().__init__(mcrfpy.Vector(x, y))
        self.enemy_type = enemy_type
        self.aggression = 5
        self.patrol_route = [(x, y), (x+1, y), (x+1, y+1), (x, y+1)]
    
    def get_next_move(self):
        return self.patrol_route[0]

class Treasure(mcrfpy.Entity):
    def __init__(self, x, y, value=100):
        # Entity expects Vector position and optional texture
        super().__init__(mcrfpy.Vector(x, y))
        self.value = value
        self.collected = False
    
    def collect(self):
        if not self.collected:
            self.collected = True
            return self.value
        return 0

def test_type_preservation():
    """Comprehensive test of type preservation in UIEntityCollection"""
    print("=== Testing UIEntityCollection Type Preservation (Issue #76) ===\n")
    
    # Create a grid to hold entities
    grid = mcrfpy.Grid(30, 30)
    grid.x = 10
    grid.y = 10
    grid.w = 600
    grid.h = 600
    
    # Add grid to scene
    scene_ui = mcrfpy.sceneUI("test")
    scene_ui.append(grid)
    
    # Create various entity instances
    player = Player(5, 5)
    enemy1 = Enemy(10, 10, "orc")
    enemy2 = Enemy(15, 15, "skeleton")
    treasure = Treasure(20, 20, 500)
    base_entity = mcrfpy.Entity(mcrfpy.Vector(25, 25))
    
    print("Created entities:")
    print(f"  - Player at (5,5): type={type(player).__name__}, health={player.health}")
    print(f"  - Enemy at (10,10): type={type(enemy1).__name__}, enemy_type={enemy1.enemy_type}")
    print(f"  - Enemy at (15,15): type={type(enemy2).__name__}, enemy_type={enemy2.enemy_type}")
    print(f"  - Treasure at (20,20): type={type(treasure).__name__}, value={treasure.value}")
    print(f"  - Base Entity at (25,25): type={type(base_entity).__name__}")
    
    # Store original references
    original_refs = {
        'player': player,
        'enemy1': enemy1,
        'enemy2': enemy2,
        'treasure': treasure,
        'base_entity': base_entity
    }
    
    # Add entities to grid
    grid.entities.append(player)
    grid.entities.append(enemy1)
    grid.entities.append(enemy2)
    grid.entities.append(treasure)
    grid.entities.append(base_entity)
    
    print(f"\nAdded {len(grid.entities)} entities to grid")
    
    # Test 1: Direct indexing
    print("\n--- Test 1: Direct Indexing ---")
    retrieved_entities = []
    for i in range(len(grid.entities)):
        entity = grid.entities[i]
        retrieved_entities.append(entity)
        print(f"grid.entities[{i}]: type={type(entity).__name__}, id={id(entity)}")
    
    # Test 2: Check type preservation
    print("\n--- Test 2: Type Preservation Check ---")
    r_player = grid.entities[0]
    r_enemy1 = grid.entities[1]
    r_treasure = grid.entities[3]
    
    # Check types
    tests_passed = 0
    tests_total = 0
    
    tests_total += 1
    if type(r_player).__name__ == "Player":
        print("✓ PASS: Player type preserved")
        tests_passed += 1
    else:
        print(f"✗ FAIL: Player type lost! Got {type(r_player).__name__} instead of Player")
        print("  This is the core Issue #76 bug!")
    
    tests_total += 1
    if type(r_enemy1).__name__ == "Enemy":
        print("✓ PASS: Enemy type preserved")
        tests_passed += 1
    else:
        print(f"✗ FAIL: Enemy type lost! Got {type(r_enemy1).__name__} instead of Enemy")
    
    tests_total += 1
    if type(r_treasure).__name__ == "Treasure":
        print("✓ PASS: Treasure type preserved")
        tests_passed += 1
    else:
        print(f"✗ FAIL: Treasure type lost! Got {type(r_treasure).__name__} instead of Treasure")
    
    # Test 3: Check attribute preservation
    print("\n--- Test 3: Attribute Preservation ---")
    
    # Test Player attributes
    try:
        tests_total += 1
        health = r_player.health
        inv = r_player.inventory
        pid = r_player.player_id
        print(f"✓ PASS: Player attributes accessible: health={health}, inventory={inv}, id={pid}")
        tests_passed += 1
    except AttributeError as e:
        print(f"✗ FAIL: Player attributes lost: {e}")
    
    # Test Enemy attributes
    try:
        tests_total += 1
        etype = r_enemy1.enemy_type
        aggr = r_enemy1.aggression
        print(f"✓ PASS: Enemy attributes accessible: type={etype}, aggression={aggr}")
        tests_passed += 1
    except AttributeError as e:
        print(f"✗ FAIL: Enemy attributes lost: {e}")
    
    # Test 4: Method preservation
    print("\n--- Test 4: Method Preservation ---")
    
    try:
        tests_total += 1
        r_player.take_damage(10)
        print(f"✓ PASS: Player method callable, health now: {r_player.health}")
        tests_passed += 1
    except AttributeError as e:
        print(f"✗ FAIL: Player methods lost: {e}")
    
    try:
        tests_total += 1
        next_move = r_enemy1.get_next_move()
        print(f"✓ PASS: Enemy method callable, next move: {next_move}")
        tests_passed += 1
    except AttributeError as e:
        print(f"✗ FAIL: Enemy methods lost: {e}")
    
    # Test 5: Iteration
    print("\n--- Test 5: Iteration Test ---")
    try:
        tests_total += 1
        type_list = []
        for entity in grid.entities:
            type_list.append(type(entity).__name__)
        print(f"Types during iteration: {type_list}")
        if type_list == ["Player", "Enemy", "Enemy", "Treasure", "Entity"]:
            print("✓ PASS: All types preserved during iteration")
            tests_passed += 1
        else:
            print("✗ FAIL: Types lost during iteration")
    except Exception as e:
        print(f"✗ FAIL: Iteration error: {e}")
    
    # Test 6: Identity check
    print("\n--- Test 6: Object Identity ---")
    tests_total += 1
    if r_player is original_refs['player']:
        print("✓ PASS: Retrieved object is the same Python object")
        tests_passed += 1
    else:
        print("✗ FAIL: Retrieved object is a different instance")
        print(f"  Original id: {id(original_refs['player'])}")
        print(f"  Retrieved id: {id(r_player)}")
    
    # Test 7: Modification persistence
    print("\n--- Test 7: Modification Persistence ---")
    tests_total += 1
    r_player.x = 50
    r_player.y = 50
    
    # Retrieve again
    r_player2 = grid.entities[0]
    if r_player2.x == 50 and r_player2.y == 50:
        print("✓ PASS: Modifications persist across retrievals")
        tests_passed += 1
    else:
        print(f"✗ FAIL: Modifications lost: position is ({r_player2.x}, {r_player2.y})")
    
    # Take screenshot
    automation.screenshot("/tmp/issue_76_test.png")
    
    # Summary
    print(f"\n=== SUMMARY ===")
    print(f"Tests passed: {tests_passed}/{tests_total}")
    
    if tests_passed < tests_total:
        print("\nIssue #76: The C++ implementation creates new PyUIEntityObject instances")
        print("with type 'Entity' instead of preserving the original Python type.")
        print("This causes derived classes to lose their type, attributes, and methods.")
        print("\nThe fix requires storing and restoring the original Python type")
        print("when creating objects in UIEntityCollection::getitem.")
    
    return tests_passed == tests_total

def run_test(runtime):
    """Timer callback to run the test"""
    try:
        success = test_type_preservation()
        print("\nOverall result: " + ("PASS" if success else "FAIL"))
    except Exception as e:
        print(f"\nTest error: {e}")
        import traceback
        traceback.print_exc()
        print("\nOverall result: FAIL")
    
    sys.exit(0)

# Set up the test scene
mcrfpy.createScene("test")
mcrfpy.setScene("test")

# Schedule test to run after game loop starts
mcrfpy.setTimer("test", run_test, 100)