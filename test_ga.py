import os
import sys

import numpy as np
import pybullet as p

import creature
import genome
import population
import simulation
import terrain


def run_simulation(csv_file=None):
    start_iteration = 0
    initial_dna = None

    if csv_file:
        assert os.path.exists(
            csv_file
        ), f"Tried to load {csv_file} but it does not exist"
        initial_dna = genome.Genome.from_csv(csv_file)
        start_iteration = int(csv_file.split("_")[1].split(".")[0]) + 1
        print(f"Resuming from iteration {start_iteration}")
    else:
        print("Starting from scratch.")

    pop = population.Population(pop_size=60, gene_count=5)

    if initial_dna is not None:
        pop.creatures[0].update_dna(initial_dna)

    sim = simulation.ThreadedSim(pool_size=6)

    # PyBullet setup
    p.connect(p.DIRECT)
    p.setPhysicsEngineParameter(enableFileCaching=0)
    p.configureDebugVisualizer(p.COV_ENABLE_GUI, 0)
    p.setGravity(0, 0, -10)

    # Create terrain
    arena_size = 20
    terrain.make_arena(arena_size=arena_size)

    mountain_position = (0, 0, 0)
    mountain_orientation = p.getQuaternionFromEuler((0, 0, 0))
    p.setAdditionalSearchPath("shapes/")
    mountain = p.loadURDF(
        "gaussian_pyramid.urdf",
        mountain_position,
        mountain_orientation,
        useFixedBase=1,
    )

    for iteration in range(start_iteration, 1000):
        # Set creature starting position
        for cr in pop.creatures:
            cr.update_position((-5, 5, 1.5))

        sim.eval_population(pop, 2400)
        fits = [cr.get_fitness() for cr in pop.creatures]
        links = [len(cr.get_expanded_links()) for cr in pop.creatures]
        print(
            iteration,
            "fittest:",
            np.round(np.max(fits), 3),
            "mean:",
            np.round(np.mean(fits), 3),
            "mean links",
            np.round(np.mean(links)),
            "max links",
            np.round(np.max(links)),
        )
        fit_map = population.Population.get_fitness_map(fits)
        new_creatures = []
        for i in range(len(pop.creatures)):
            p1_ind = population.Population.select_parent(fit_map)
            p2_ind = population.Population.select_parent(fit_map)
            p1 = pop.creatures[p1_ind]
            p2 = pop.creatures[p2_ind]
            # now we have the parents!
            dna = genome.Genome.crossover(p1.dna, p2.dna)
            dna = genome.Genome.point_mutate(dna, rate=0.1, amount=0.25)
            dna = genome.Genome.shrink_mutate(dna, rate=0.25)
            dna = genome.Genome.grow_mutate(dna, rate=0.1)
            cr = creature.Creature(1)
            cr.update_dna(dna)
            new_creatures.append(cr)
        # elitism
        max_fit = np.max(fits)
        for cr in pop.creatures:
            if cr.get_fitness() == max_fit:
                new_cr = creature.Creature(1)
                new_cr.update_dna(cr.dna)
                new_creatures[0] = new_cr
                filename = f"elite_{iteration}.csv"
                genome.Genome.to_csv(cr.dna, filename)
                break

        pop.creatures = new_creatures

    self.assertNotEqual(fits[0], 0)


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_simulation(csv_file)
