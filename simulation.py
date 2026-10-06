import os
import tempfile
from multiprocessing import Manager, Pool

import numpy as np
import pybullet as p

import terrain


class Simulation:
    def __init__(self, sim_id=0):
        self.physicsClientId = p.connect(p.DIRECT)
        self.sim_id = sim_id
        self.summit = None
        self.mountain_id = None

    def close(self):
        p.disconnect(physicsClientId=self.physicsClientId)

    def load_world(self):
        arena_size = 20
        terrain.make_arena(arena_size=arena_size)
        shapes_dir = os.path.join(os.path.dirname(__file__), "shapes")
        p.setAdditionalSearchPath(shapes_dir, physicsClientId=self.physicsClientId)
        self.mountain_id = p.loadURDF(
            "gaussian_pyramid.urdf",
            [0, 0, -1],
            [0, 0, 0, 1],
            useFixedBase=1,
            physicsClientId=self.physicsClientId,
        )
        self.find_mountain_and_summit()

    def find_mountain_and_summit(self):
        # Find the mountain by looping through all bodies and checking their info
        self.mountain_id = next(
            (
                i
                for i in range(p.getNumBodies(physicsClientId=self.physicsClientId))
                if p.getBodyInfo(i, physicsClientId=self.physicsClientId)[1].decode(
                    "utf-8"
                )
                == "mountain"
            ),
            None,
        )

        if self.mountain_id is None:
            raise Exception("Mountain (gaussian_pyramid.urdf) not found in simulation")

        # Get the AABB (Axis-Aligned Bounding Box) of the mountain
        _, aabb_max = p.getAABB(self.mountain_id, physicsClientId=self.physicsClientId)

        # The summit is the highest point of the AABB
        self.summit = np.array([0, 0, aabb_max[2]])

    def run_creature(self, cr, iterations=2400):
        pid = self.physicsClientId
        p.resetSimulation(physicsClientId=pid)
        self.summit = None
        self.mountain_id = None
        p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)

        p.setGravity(0, 0, -10, physicsClientId=pid)
        self.load_world()

        xml_str = cr.to_xml()
        xml_file = tempfile.NamedTemporaryFile(
            mode="w", suffix=f"-{self.sim_id}.urdf", delete=False
        )
        with xml_file as f:
            f.write(xml_str)

        try:
            cid = p.loadURDF(xml_file.name, physicsClientId=pid)
        finally:
            os.unlink(xml_file.name)

        # Pass the summit to the creature
        cr.set_summit(self.summit)

        # Set starting position
        p.resetBasePositionAndOrientation(
            cid, [-5, 5, 1.5], [0, 0, 0, 1], physicsClientId=pid
        )

        for step in range(iterations):
            p.stepSimulation(physicsClientId=pid)
            if step % 24 == 0:
                self.update_motors(cid=cid, cr=cr)

            pos, orn = p.getBasePositionAndOrientation(cid, physicsClientId=pid)
            cr.update_position(pos)

        cr.finalize_distance()

    def update_motors(self, cid, cr):
        """
        cid is the id in the physics engine
        cr is a creature object
        """
        for jid in range(p.getNumJoints(cid, physicsClientId=self.physicsClientId)):
            m = cr.get_motors()[jid]

            p.setJointMotorControl2(
                cid,
                jid,
                controlMode=p.VELOCITY_CONTROL,
                targetVelocity=m.get_output(),
                force=5,
                physicsClientId=self.physicsClientId,
            )

    def eval_population(self, pop, iterations):
        for cr in pop.creatures:
            self.run_creature(cr, iterations)


class ThreadedSim:
    def __init__(self, pool_size):
        self.pool_size = pool_size
        self.completed = 0

    @staticmethod
    def static_run_creature(sim_id, cr_ind, cr, iterations, completed, lock):
        sim = Simulation(sim_id)
        try:
            sim.run_creature(cr, iterations)
        finally:
            sim.close()

        # This is the only shared state in the parallel path. The lock keeps
        # progress accounting deterministic without sharing PyBullet state.
        with lock:
            completed.value += 1
        return cr_ind, cr

    def eval_population(self, pop, iterations):
        """
        pop is a Population object
        iterations is frames in pybullet to run for at 240fps
        """
        pool_args = []
        start_ind = 0
        pool_size = self.pool_size

        manager = Manager()
        completed = manager.Value("i", 0)
        lock = manager.Lock()

        while start_ind < len(pop.creatures):
            this_pool_args = []
            for i in range(start_ind, start_ind + pool_size):
                if i == len(pop.creatures):  # the end
                    break
                # work out the sim ind
                sim_ind = i % pool_size
                this_pool_args.append(
                    [sim_ind, i, pop.creatures[i], iterations, completed, lock]
                )
            pool_args.append(this_pool_args)
            start_ind = start_ind + pool_size

        new_creatures = []
        for pool_argset in pool_args:
            with Pool(pool_size) as p:
                # it works on a copy of the creatures, so receive them
                creatures = p.starmap(ThreadedSim.static_run_creature, pool_argset)
                # and now put those creatures back into the main
                # self.creatures array
                new_creatures.extend(creatures)
        pop.creatures = [cr for _, cr in sorted(new_creatures, key=lambda item: item[0])]
        self.completed = completed.value
