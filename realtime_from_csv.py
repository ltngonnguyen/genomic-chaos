# realtime_from_csv.py
import os
import random
import sys
import time

import numpy as np
import pybullet as p

import creature
import genome
import terrain  # Import the terrain module


def main(csv_file):
    assert os.path.exists(csv_file), (
        "Tried to load " + csv_file + " but it does not exist"
    )

    p.connect(p.GUI)
    p.setPhysicsEngineParameter(enableFileCaching=0)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setGravity(0, 0, -10)

    arena_size = 20
    terrain.make_arena(arena_size=arena_size)

    mountain_position = (0, 0, -1)
    mountain_orientation = p.getQuaternionFromEuler((0, 0, 0))
    p.setAdditionalSearchPath("shapes/")
    mountain = p.loadURDF(
        "gaussian_pyramid.urdf", mountain_position, mountain_orientation, useFixedBase=1
    )

    # generate a random creature
    cr = creature.Creature(gene_count=1)
    dna = genome.Genome.from_csv(csv_file)
    cr.update_dna(dna)
    # save it to XML
    with open("test.urdf", "w") as f:
        f.write(cr.to_xml())
    # load it into the sim
    rob1 = p.loadURDF("test.urdf", (5, -5, 1.5), (0, 0, 0, 1))
    start_pos, orn = p.getBasePositionAndOrientation(rob1)

    # iterate
    elapsed_time = 0
    wait_time = 1.0 / 240  # seconds
    total_time = 30  # seconds
    step = 0
    while True:
        p.stepSimulation()
        step += 1
        if step % 24 == 0:
            motors = cr.get_motors()
            assert len(motors) == p.getNumJoints(rob1), "Something went wrong"
            for jid in range(p.getNumJoints(rob1)):
                mode = p.VELOCITY_CONTROL
                vel = motors[jid].get_output()
                p.setJointMotorControl2(rob1, jid, controlMode=mode, targetVelocity=vel)
            new_pos, orn = p.getBasePositionAndOrientation(rob1)
            dist_moved = np.linalg.norm(np.asarray(start_pos) - np.asarray(new_pos))
            print(dist_moved)
        time.sleep(wait_time)
        elapsed_time += wait_time
        if elapsed_time > total_time:
            break

    print("TOTAL DISTANCE MOVED:", dist_moved)


if __name__ == "__main__":
    assert len(sys.argv) == 2, "Usage: python realtime_from_csv.py csv_filename"
    main(sys.argv[1])
