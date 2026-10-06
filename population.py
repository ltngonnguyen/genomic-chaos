import creature
import numpy as np


class Population:
    def __init__(self, pop_size, gene_count):
        self.creatures = [creature.Creature(gene_count=gene_count) for i in range(pop_size)]

    @staticmethod
    def get_fitness_map(fits):
        fitmap = []
        total = 0
        min_fit = min(fits)
        offset = abs(min_fit) + 1e-6 if min_fit <= 0 else 0
        for f in fits:
            total = total + f + offset
            fitmap.append(total)
        return fitmap
    
    @staticmethod
    def select_parent(fitmap):
        if not fitmap or fitmap[-1] <= 0:
            return 0
        r = np.random.rand()  # 0-1
        r = r * fitmap[-1]
        for i in range(len(fitmap)):
            if r <= fitmap[i]:
                return i
        return len(fitmap) - 1
