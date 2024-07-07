import csv
import os
import sys
import time
from statistics import mean, median, stdev

import numpy as np
import pybullet as p

import creature
import genome
import population
import simulation
import terrain


def log_iteration(iteration, pop, filename="evolution_log.csv"):
    """
    Log the current iteration's data to a CSV file.
    Each call to this function will append a new row to the file.
    """
    # Collect data
    fits = [cr.finalize_distance() for cr in pop.creatures]
    links = [len(cr.get_expanded_links()) for cr in pop.creatures]
    distances = [cr.get_distance_travelled() for cr in pop.creatures]
    energies = [cr.energy_consumed for cr in pop.creatures]
    energy_efficiencies = [
        0 if d / (e + 1e-6) > 1000 or d / (e + 1e-6) < -1000 else d / (e + 1e-6)
        for d, e in zip(distances, energies)
    ]
    gene_counts = [len(cr.dna) for cr in pop.creatures]

    # Calculate statistics
    data = {
        "Iteration": iteration,
        "Best Fitness": max(fits),
        "Average Fitness": mean(fits),
        "Median Fitness": median(fits),
        "Worst Fitness": min(fits),
        "Fitness Diversity": stdev(fits),
        "Average Links": mean(links),
        "Median Links": median(links),
        "Max Links": max(links),
        "Best Distance": max(distances),
        "Average Distance": mean(distances),
        "Median Distance": median(distances),
        "Best Energy Efficiency": max(energy_efficiencies),
        "Average Energy Efficiency": mean(energy_efficiencies),
        "Median Energy Efficiency": median(energy_efficiencies),
        "Average Gene Count": mean(gene_counts),
        "Median Gene Count": median(gene_counts),
        "Max Gene Count": max(gene_counts),
        "Timestamp": time.time(),
    }

    # Write data to CSV file
    file_exists = os.path.isfile(filename)

    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())

        if not file_exists:
            writer.writeheader()  # Write header if file doesn't exist

        writer.writerow(data)


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

    pop = population.Population(pop_size=120, gene_count=5)

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

    for iteration in range(start_iteration, 100):
        # Set creature starting position
        for cr in pop.creatures:
            cr.update_position((-5, 5, 1.5))

        sim.eval_population(pop, 2400)
        fits = [cr.finalize_distance() for cr in pop.creatures]
        links = [len(cr.get_expanded_links()) for cr in pop.creatures]
        print(
            iteration,
            "fittest:",
            np.round(np.max(fits), 3),
            "median:",
            np.round(np.median(fits), 3),
            "median links",
            np.round(np.median(links)),
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
            dna = genome.Genome.point_mutate(dna, rate=0.2, amount=0.25)
            dna = genome.Genome.shrink_mutate(dna, rate=0.1)
            dna = genome.Genome.grow_mutate(dna, rate=0.2)
            cr = creature.Creature(1)
            cr.update_dna(dna)
            new_creatures.append(cr)

        log_iteration(iteration, pop)
        # elitism
        max_fit = np.max(fits)
        for cr in pop.creatures:
            if cr.finalize_distance() == max_fit:
                new_cr = creature.Creature(1)
                new_cr.update_dna(cr.dna)
                new_creatures[0] = new_cr
                filename = f"elite_{iteration}.csv"
                genome.Genome.to_csv(cr.dna, filename)
                break

        pop.creatures = new_creatures


if __name__ == "__main__":
    csv_file = sys.argv[1] if len(sys.argv) > 1 else None
    run_simulation(csv_file)
