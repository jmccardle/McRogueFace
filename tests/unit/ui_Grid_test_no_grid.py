#!/usr/bin/env python3
"""Test setup without Grid creation"""
import mcrfpy

print("Starting test...")

# Create test scene
print("[DEBUG] Creating scene...")
mcrfpy.createScene("grid_test")
print("[DEBUG] Setting scene...")
mcrfpy.setScene("grid_test")
print("[DEBUG] Getting UI...")
ui = mcrfpy.sceneUI("grid_test")
print("[DEBUG] UI retrieved")

# Test texture creation
print("[DEBUG] Creating texture...")
texture = mcrfpy.Texture("assets/kenney_ice.png", 16, 16)
print("[DEBUG] Texture created")

# Test vector creation
print("[DEBUG] Creating vectors...")
pos = mcrfpy.Vector(10, 10)
size = mcrfpy.Vector(400, 300)
print("[DEBUG] Vectors created")

print("All setup complete, Grid creation would happen here")
print("PASS")