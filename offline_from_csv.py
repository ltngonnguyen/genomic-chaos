# offline_from_csv.py
import os
import random
import sys
import tempfile
import time

import numpy as np
import pybullet as p
import pybullet_data

import creature
import genome
import terrain  # Import the terrain module


def main(csv_file):
    assert os.path.exists(csv_file), (
        "Tried to load " + csv_file + " but it does not exist"
    )

    p.connect(p.DIRECT)
    p.setPhysicsEngineParameter(enableFileCaching=0)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
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
    # save it to a temporary URDF for PyBullet to load
    robot_file = tempfile.NamedTemporaryFile(mode="w", suffix=".urdf", delete=False)
    with robot_file as f:
        f.write(cr.to_xml())
    # load it into the sim
    quadrant_positions = [(5, 5, 1.5), (-5, 5, 1.5), (5, -5, 1.5), (-5, -5, 1.5)]
    try:
        for pos in quadrant_positions:
            rob1 = p.loadURDF(robot_file.name, pos, (0, 0, 0, 1))
            start_pos, orn = p.getBasePositionAndOrientation(rob1)
            break  # only use the first position for simplicity
    finally:
        os.unlink(robot_file.name)

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
        elapsed_time += wait_time
        if elapsed_time > total_time:
            break

    print("TOTAL DISTANCE MOVED:", dist_moved)


def main_from_cli():
    assert len(sys.argv) == 2, "Usage: python offline_from_csv.py csv_filename"
    main(sys.argv[1])


if __name__ == "__main__":
    main_from_cli()
