# cw-envt.py
import random
import time

import numpy as np
import pybullet as p
import pybullet_data

import creature
import terrain

p.connect(p.GUI)
p.setAdditionalSearchPath(pybullet_data.getDataPath())

p.setGravity(0, 0, -10)

arena_size = 20

terrain.make_arena(arena_size=arena_size)

# make_rocks(arena_size=arena_size)

mountain_position = (0, 0, -1)  # Adjust as needed
mountain_orientation = p.getQuaternionFromEuler((0, 0, 0))
p.setAdditionalSearchPath("shapes/")
# mountain = p.loadURDF("mountain.urdf", mountain_position, mountain_orientation, useFixedBase=1)
# mountain = p.loadURDF("mountain_with_cubes.urdf", mountain_position, mountain_orientation, useFixedBase=1)

mountain = p.loadURDF(
    "gaussian_pyramid.urdf", mountain_position, mountain_orientation, useFixedBase=1
)

# generate a random creature
cr = creature.Creature(gene_count=3)
# save it to XML
with open("test.urdf", "w") as f:
    f.write(cr.to_xml())
# load it into the sim
rob1 = p.loadURDF("test.urdf", (0, 0, 10))

p.setRealTimeSimulation(1)

while True:
    time.sleep(1.0 / 240.0)
    if (
        p.getBasePositionAndOrientation(rob1)[0][2]
        < p.getBasePositionAndOrientation(mountain)[0][2]
    ):
        print("Creature fell from mountain")
        break
