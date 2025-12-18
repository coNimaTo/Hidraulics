import numpy as np
import argparse
import os
import time

from terrain import *


def main():

    cycles = 5
    N_droplets = 100000
    batch_size = 50

    # Terrain parameters
    shape = height, width = 256,256
    scale = 250

    # particle
    initial_volume = 1
    min_volume = 0.1
    evaporation_rate = 0.025

    # particle dynamics
    dt = 0.25
    g = 10
    z_scale = 5 # el terreno esta normalizado, esto define una "altura"
    friction = 0.01

    min_speed = 0.01
    min_slope = 0.1

    # erosion/sedimentation
    p_c = 8
    erosion_rate = 0.7 
    deposition_rate = .25
    initial_sediment = 0

    kernel = np.array([[1,2,1],
                    [2,4,2],
                    [1,2,1]]) / 16
    
    # Command-line arguments
    parser = argparse.ArgumentParser(description="Hydraulic erosión on terrain.")
    parser.add_argument("--volume", type=float, default = initial_volume,
                        help="Initial volume of the droplets.")
    parser.add_argument("--evaporation_rate", type=float, default = evaporation_rate,
                        help="Evaporation rate.")
    parser.add_argument("--deposition_rate", type=float, default = deposition_rate,
                        help="Deposition rate.")
    parser.add_argument("--erosion_rate", type=float, default = erosion_rate,
                        help="Erosion rate.")
    parser.add_argument("--g", type=float, default = g,
                        help="Gravity.")
    parser.add_argument("--k", type=float, default = friction,
                        help="friction.")
    
    parser.add_argument("--log_dir", type=str, required=True,
                        help="Directory to save logs and models.")
    
    args = parser.parse_args()

    # Argument definition
    initial_volume      = args.volume
    evaporation_rate    = args.evaporation_rate
    deposition_rate     = args.deposition_rate
    erosion_rate        = args.erosion_rate
    g                   = args.g
    friction            = args.k

    log_dir = args.log_dir
    os.makedirs(log_dir, exist_ok=True)
    os.chdir(f"{os.getcwd()}/{log_dir}")

    class droplet():
        """
        Water droplet
        """
        def __init__(self, height, width, erosion_kernel = np.array([1])):
            self.inbounds = True
            # Dsp esto lo puede tener una clase que sea el terreno
            self.height = height
            self.width = width
            
            self.sediment = initial_sediment # masa de sedimento
            self.volume = initial_volume # tamaño gota, se ira evaporando
            
            # Erosion Kernel
            if erosion_kernel.shape[0] == erosion_kernel.shape[1]:
                self.erosion_radius = (erosion_kernel.shape[0]-1)//2
                self.kernel = np.array(erosion_kernel)
            else:
                print("Kernel Error, not square")
            
            # Variables dinamicas de la gota
            self.ipos = np.random.randint([0,0],[height-1, width-1], 2)
            self.pos = np.array(self.ipos, float)
            self.vel = np.zeros(2)

            self.max_speed = 0

        def reset(self):
            """
            Resets variables
            """
            self.inbounds = True
            self.sediment = initial_sediment
            self.volume = initial_volume

            self.ipos = np.random.randint([0,0],[self.height-1, self.width-1], 2)
            self.pos = np.array(self.ipos, float)
            self.vel = np.zeros(2)

            self.max_speed = 0

        def is_inbounds(self)->bool:
            """
            Checks if the droplet is still on the map
            """
            # Podria cambiar esto por un try:except Index en la parte del step
            # xq creo q el indexing de python ya checkea esto, asi q seria al dope hacerlo dos veces
            if self.pos[0] >= self.height - 1 or self.pos[1] >= self.width - 1:
                return False
            elif self.pos[0] < 0 or self.pos[1] < 0:
                return False
            else: 
                return True
        
        def is_still(self, speed, slope)->bool:
            """
            Checks if the droplet stopped and won't move
            """
            if (speed < min_speed) and (slope < min_slope):
                return True
            else: 
                return False
                

        def step(self, terrain, grad_terrain):
            
            if not self.inbounds:
                print("step not executed, out of bounds")
                return
            if self.volume <= min_volume:
                print("step not executed, droplet evaporated")
                return

            # Dinamica
            slope = np.array((grad_terrain[0][*self.ipos],grad_terrain[1][*self.ipos]))

            self.vel -= dt*slope*g
            self.pos += dt*self.vel # + dt**2 * slope * g / 2
            self.vel *= (1-dt*friction)
            
            # Check q esta en la grilla
            if not self.is_inbounds():
                # print("out of bounds")
                self.inbounds = False
                return 

            # Erosion/Sedimentation
            Deltah = terrain[*np.array(self.pos,int)] - terrain[*self.ipos]
            if not (Deltah == 0):
                speed = np.sqrt(self.vel.dot(self.vel))
                if speed > self.max_speed:
                    self.max_speed = speed

                capacity = -Deltah * speed * self.volume * p_c

                # ---Sedimentation
                # If it goes uphill all sediment is deposited until Deltah gets to 0
                if Deltah > 0:
                    s_diff = min(self.sediment, Deltah) * deposition_rate
                    terrain[*self.ipos] += s_diff

                # If it carries more sediment than its capacity adjust until capacity or Deltah gets to 0
                elif self.sediment > capacity:
                    s_diff = min((self.sediment-capacity), -Deltah) * deposition_rate
                    terrain[*self.ipos] += s_diff

                # ---Erosion
                # If it carries less sediment than its capacity adjust until capacity
                else:
                    s_diff = - min((capacity-self.sediment), -Deltah) * erosion_rate

                    xi, yi = self.ipos
                    for i in range(-self.erosion_radius, self.erosion_radius):
                        for j in range(-self.erosion_radius, self.erosion_radius):
                            terrain[xi+i, yi+j] += s_diff * self.kernel[i + self.erosion_radius, j + self.erosion_radius]

                self.sediment -= s_diff
                

            # Set new index position
            self.ipos = np.array(self.pos, int)

            # Evaporation
            self.volume *= (1-evaporation_rate*dt)
            
            if self.volume <= min_volume:
                self.inbounds = False
                # print("droplet evaporated")
                terrain[*self.ipos] += self.sediment
                return

    # Terrain generation
    pnoise_kwargs = {"octaves":4,           # Number of noise layers
                 "persistence": 0.6,    # Amplitude of each successive octave
                 "lacunarity": 1.8,     # Frequency multiplier between octaves
                 "base": 74,            # Base seed for the noise (optional)
                 }           

    terrain = get_terrain(shape, scale, pnoise_kwargs)
    np.savetxt("terrain_0.txt", terrain, delimiter = "\t")

    # terrain = np.loadtxt("terrain_0.txt", delimiter = "\t")
    # Gradiente
    grad_terrain = np.gradient(terrain)
    

    # Erosion simulation
    steps = []
    speeds = []

    pepe = droplet(height, width, kernel)

    for c in range(cycles):
        time_start = time.time()
        for i in range(N_droplets//batch_size):
            
            # Hago un Batch antes de actualizar el mapa de gradiente
            for j in range(batch_size):
                pepe.reset()
                i=0
                while pepe.inbounds and i < 250:
                    pepe.step(terrain = terrain, grad_terrain=grad_terrain)
                    i+=1

                steps.append(i)
                speeds.append(pepe.max_speed)
            grad_terrain = np.gradient(terrain)
            
        print(f"mean steps: {np.mean(steps)}")
        print(f"mean max speed: {np.mean(speeds)}")
        print(f"absolute max speed: {np.max(speeds)}")

        np.savetxt(f"terrain_{c+1}.txt", terrain, delimiter = "\t")
        
        print(f"cycle finished in {time.time()-time_start} seconds")

if __name__ == "__main__":
    main()
