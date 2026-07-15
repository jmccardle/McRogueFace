# mcrf: objects=[Caption,NoiseSource,Scene] verified=0.2.8-dev status=ok
import mcrfpy

# Create a noise source
noise = mcrfpy.NoiseSource(dimensions=2, algorithm='simplex', seed=42)

# Point queries
value = noise.get((10.5, 20.3))               # Basic noise: -1.0 to 1.0
fbm_val = noise.fbm((10.5, 20.3), octaves=6)   # Fractal brownian motion
turb_val = noise.turbulence((10.5, 20.3))      # Turbulence (absolute fbm)

# Batch sampling into HeightMap
hmap = noise.sample((100, 100), mode='fbm', octaves=4)

# Direct heightmap integration
hmap.add_noise(noise, scale=0.5)

scene = mcrfpy.Scene("noise_demo")
mcrfpy.current_scene = scene
scene.children.append(mcrfpy.Caption(
    text=f"noise={value:.3f} fbm={fbm_val:.3f} turb={turb_val:.3f}",
    pos=(10, 10)
))
