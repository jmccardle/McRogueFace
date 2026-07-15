# mcrf: objects=[Caption,NoiseSource,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create terrain with multiple noise layers
base_noise = mcrfpy.NoiseSource(seed=12345)
detail_noise = mcrfpy.NoiseSource(seed=67890, lacunarity=3.0)

# Start with base terrain
terrain = base_noise.sample((100, 100),
    world_size=(10.0, 10.0),  # Larger scale features
    mode='fbm',
    octaves=4
)

# Normalize to 0-1 range
terrain.add_constant(1.0).scale(0.5)

# Add detail layer
terrain.add_noise(detail_noise,
    world_size=(50.0, 50.0),  # Finer detail
    scale=0.2
)

# Apply erosion and smoothing
terrain.rain_erosion(1000).smooth(2)

scene = mcrfpy.Scene("terrain_demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Caption(
    text=f"terrain size={terrain.size}",
    pos=(10, 10)
))
