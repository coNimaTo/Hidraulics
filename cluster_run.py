import numpy as np

from terrain import *
from droplet import *

dt = 0.25

kernel = np.array([[1,2,1],
                   [2,4,2],
                   [1,2,1]]) / 16

cycles = 10
N_droplets = 50000
batch_size = 50

# Terrain parameters
shape = height, width = 256,256
scale = 250


pnoise_kwargs = {"octaves":6,           # Number of noise layers
                 "persistence": 0.6,    # Amplitude of each successive octave
                 "lacunarity": 1.8,     # Frequency multiplier between octaves
                 "base": 74,            # Base seed for the noise (optional)
                 }           

terrain = get_terrain(shape, scale, pnoise_kwargs)
np.savetxt("terrain_0.txt", terrain, delimiter = "\t")

# Gradiente
grad_terrain = np.gradient(terrain)

terrain_copy = terrain.copy()

steps = []
speeds = []


pepe = droplet(height, width, kernel)

for c in range(cycles):
    for i in range(N_droplets//batch_size):
        
        # Hago un Batch antes de actualizar el mapa de gradiente
        for j in range(batch_size):
                pepe.reset()
                i=0
                while pepe.inbounds:
                    pepe.step(terrain = terrain_copy, grad_terrain=grad_terrain)
                    i+=1

                steps.append(i)
                speeds.append(pepe.max_speed)
        grad_terrain = np.gradient(terrain_copy)
        
    print(f"mean steps: {np.mean(steps)}")
    print(f"mean max speed: {np.mean(speeds)}")
    print(f"absolute max speed: {np.max(speeds)}")

    np.savetxt(f"terrain_{c+1}.txt", terrain_copy, delimiter = "\t")