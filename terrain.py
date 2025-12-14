import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt

import numpy as np

from noise import pnoise2

def get_terrain(shape, scale, noise_kwargs):
    """
    Generates a terrain using perlin noise
    
    :param shape: shape of the np.array
    :param scale: defines the size of the features (masomenos)
    :param noise_kwargs: arguments for noise.pnoise2

    :returns terrain: np.array with values between 0 and 1
    """
    terrain = np.zeros(shape)

    for i in range(shape[0]):
        for j in range(shape[1]):
            terrain[i][j] = pnoise2(i / scale, j / scale, **noise_kwargs)

    return (terrain - terrain.min()) / (terrain.max() - terrain.min())

