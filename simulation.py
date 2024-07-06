from multiprocessing import Pool

import numpy as np
import pybullet as p

import terrain


class Simulation:
    def __init__(self, sim_id=0):
        self.physicsClientId = p.connect(p.DIRECT)
        self.sim_id = sim_id
        self.summit = None
        self.mountain_id = None

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
        p.setPhysicsEngineParameter(enableFileCaching=0, physicsClientId=pid)

        p.setGravity(0, 0, -10, physicsClientId=pid)

        # Create terrain
        arena_size = 20
        terrain.make_arena(arena_size=arena_size)
        terrain.make_mountain(arena_size=arena_size)

        xml_file = "temp" + str(self.sim_id) + ".urdf"
        xml_str = cr.to_xml()
        with open(xml_file, "w") as f:
            f.write(xml_str)

        cid = p.loadURDF(xml_file, physicsClientId=pid)

        # Find the mountain and summit if not already found
        if self.summit is None:
            self.find_mountain_and_summit()

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
        # Find the mountain and summit once for all creatures
        if self.summit is None:
            self.find_mountain_and_summit()

        for cr in pop.creatures:
            cr.set_summit(self.summit)
            self.run_creature(cr, iterations)


class ThreadedSim:
    def __init__(self, pool_size):
        self.sims = [Simulation(i) for i in range(pool_size)]
        self.summit = None
        self.mountain_id = None

    def find_mountain_and_summit(self):
        # Use the first simulation to find the mountain and summit
        self.sims[0].find_mountain_and_summit()
        self.summit = self.sims[0].summit
        self.mountain_id = self.sims[0].mountain_id

    @staticmethod
    def static_run_creature(sim, cr, iterations):
        cr.set_summit(sim.summit)
        sim.run_creature(cr, iterations)
        return cr

    def eval_population(self, pop, iterations):
        """
        pop is a Population object
        iterations is frames in pybullet to run for at 240fps
        """
        # Find the mountain and summit once for all creatures
        if self.summit is None:
            self.find_mountain_and_summit()
        for sim in self.sims:
            sim.summit = self.summit
            sim.mountain_id = self.mountain_id
        pool_args = []
        start_ind = 0
        pool_size = len(self.sims)
        while start_ind < len(pop.creatures):
            this_pool_args = []
            for i in range(start_ind, start_ind + pool_size):
                if i == len(pop.creatures):  # the end
                    break
                # work out the sim ind
                sim_ind = i % len(self.sims)
                this_pool_args.append(
                    [self.sims[sim_ind], pop.creatures[i], iterations]
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
        pop.creatures = new_creatures
