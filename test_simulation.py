import unittest
import simulation
import creature
import population

class TestSim(unittest.TestCase):
    def testSimExists(self):
        sim = simulation.Simulation()
        try:
            self.assertIsNotNone(sim)
        finally:
            sim.close()

    def testSimId(self):
        sim = simulation.Simulation()
        try:
            self.assertIsNotNone(sim.physicsClientId)
        finally:
            sim.close()

    def testRun(self):
        sim = simulation.Simulation()
        try:
            self.assertIsNotNone(sim.run_creature)
        finally:
            sim.close()

    def testPos(self):
        sim = simulation.Simulation()
        cr = creature.Creature(gene_count = 3)
        try:
            sim.run_creature(cr, iterations=120)
            self.assertNotEqual(cr.start_position, cr.last_position)
        finally:
            sim.close()
    
    def testPop(self):
        pop = population.Population(pop_size=5, gene_count=3)
        sim = simulation.Simulation()
        try:
            for cr in pop.creatures:
                sim.run_creature(cr, iterations=120)
            dists = [cr.get_distance_travelled() for cr in pop.creatures]
            self.assertIsNotNone(dists)
        finally:
            sim.close()

## uncomment this to test the 
## multi-threaded sim
#    def testProc(self):
#        pop = population.Population(pop_size=20, gene_count=3)
#        tsim = simulation.ThreadedSim(pool_size=8)
#        tsim.eval_population(pop, 2400)
#        dists = [cr.get_distance_travelled() for cr in pop.creatures]
#        self.assertIsNotNone(dists)

    def testThreadedSimTracksCompletedWork(self):
        pop = population.Population(pop_size=2, gene_count=2)
        tsim = simulation.ThreadedSim(pool_size=2)
        tsim.eval_population(pop, 60)
        self.assertEqual(tsim.completed, 2)

    def testProcNoThread(self):
        pop = population.Population(pop_size=4, gene_count=3)
        sim = simulation.Simulation()
        try:
            sim.eval_population(pop, 120)
            dists = [cr.get_distance_travelled() for cr in pop.creatures]
            self.assertIsNotNone(dists)
        finally:
            sim.close()
