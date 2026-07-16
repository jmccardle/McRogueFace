# mcrf: objects=[BSP,Color,ColorLayer,Grid,HeightMap,NoiseSource,Scene] verified=0.2.8-dev status=ok
import mcrfpy

scene = mcrfpy.Scene("heightmap-demo")
mcrfpy.current_scene = scene

grid = mcrfpy.Grid(grid_size=(20, 20))
scene.children.append(grid)

# Create a heightmap
hmap = mcrfpy.HeightMap((20, 20))

# Method chaining for terrain generation
hmap.fill(0.5).add_hill((10, 10), 8, 0.3).normalize()

# Subscript access
value = hmap[5, 5]

# Combine multiple heightmaps
noise_source = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)
noise_map = noise_source.sample((20, 20))
hmap.multiply(noise_map)  # Apply as mask

# Convert BSP to heightmap
bsp = mcrfpy.BSP(pos=(0, 0), size=(20, 20))
bsp.split_recursive(depth=3, min_size=(4, 4), seed=42)
rooms = bsp.to_heightmap(select='leaves', shrink=1)
hmap.add(rooms)

# Visualize the heightmap on the grid via a ColorLayer gradient
color_layer = mcrfpy.ColorLayer(z_index=1, name="height_color")
grid.add_layer(color_layer)
color_layer.apply_gradient(hmap, (0.0, 1.0), mcrfpy.Color(0, 0, 0), mcrfpy.Color(255, 255, 255))
