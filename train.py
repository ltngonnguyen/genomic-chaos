import argparse
import csv
import os
import time
from statistics import mean, median, stdev

import numpy as np

import creature
import genome
import population
import simulation


def log_iteration(iteration, pop, filename="evolution_log.csv"):
    """
    Log the current iteration's data to a CSV file.
    Each call to this function appends a new row.
    """
    fits = [cr.finalize_distance() for cr in pop.creatures]
    links = [len(cr.get_expanded_links()) for cr in pop.creatures]
    distances = [cr.get_distance_travelled() for cr in pop.creatures]
    energies = [cr.energy_consumed for cr in pop.creatures]
    energy_efficiencies = [
        0 if d / (e + 1e-6) > 1000 or d / (e + 1e-6) < -1000 else d / (e + 1e-6)
        for d, e in zip(distances, energies)
    ]
    gene_counts = [len(cr.dna) for cr in pop.creatures]

    data = {
        "Iteration": iteration,
        "Best Fitness": max(fits),
        "Average Fitness": mean(fits),
        "Median Fitness": median(fits),
        "Worst Fitness": min(fits),
        "Fitness Diversity": stdev(fits) if len(fits) > 1 else 0,
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

    file_exists = os.path.isfile(filename)
    with open(filename, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)


def run_simulation(
    csv_file=None,
    generations=100,
    pop_size=120,
    gene_count=5,
    pool_size=6,
    iterations=2400,
):
    start_iteration = 0
    initial_dna = None

    if csv_file:
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Tried to load {csv_file} but it does not exist")
        initial_dna = genome.Genome.from_csv(csv_file)
        print("Resuming from saved genome.")
    else:
        print("Starting from scratch.")

    pop = population.Population(pop_size=pop_size, gene_count=gene_count)

    if initial_dna is not None:
        pop.creatures[0].update_dna(initial_dna)

    sim = simulation.ThreadedSim(pool_size=pool_size)

    for iteration in range(start_iteration, generations):
        for cr in pop.creatures:
            cr.update_position((-5, 5, 1.5))

        sim.eval_population(pop, iterations)
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
            "completed",
            sim.completed,
        )

        fit_map = population.Population.get_fitness_map(fits)
        new_creatures = []
        for _ in range(len(pop.creatures)):
            p1_ind = population.Population.select_parent(fit_map)
            p2_ind = population.Population.select_parent(fit_map)
            p1 = pop.creatures[p1_ind]
            p2 = pop.creatures[p2_ind]
            dna = genome.Genome.crossover(p1.dna, p2.dna)
            dna = genome.Genome.point_mutate(dna, rate=0.1, amount=0.25)
            dna = genome.Genome.shrink_mutate(dna, rate=0.25)
            dna = genome.Genome.grow_mutate(dna, rate=0.1)
            cr = creature.Creature(1)
            cr.update_dna(dna)
            new_creatures.append(cr)

        log_iteration(iteration, pop)

        max_fit = np.max(fits)
        for cr in pop.creatures:
            if cr.finalize_distance() == max_fit:
                new_cr = creature.Creature(1)
                new_cr.update_dna(cr.dna)
                new_creatures[0] = new_cr
                genome.Genome.to_csv(cr.dna, f"elite_{iteration}.csv")
                break

        pop.creatures = new_creatures


def main():
    parser = argparse.ArgumentParser(description="Run the evolutionary robotics trainer.")
    parser.add_argument("csv_file", nargs="?", help="Optional saved genome to seed the run")
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--pop-size", type=int, default=120)
    parser.add_argument("--gene-count", type=int, default=5)
    parser.add_argument("--pool-size", type=int, default=6)
    parser.add_argument("--iterations", type=int, default=2400)
    args = parser.parse_args()

    run_simulation(
        csv_file=args.csv_file,
        generations=args.generations,
        pop_size=args.pop_size,
        gene_count=args.gene_count,
        pool_size=args.pool_size,
        iterations=args.iterations,
    )


if __name__ == "__main__":
    main()
