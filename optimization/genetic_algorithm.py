"""
optimization/genetic_algorithm.py — GAOptimizer(MetaheuristicOptimizer)

Chromosome: a sorted tuple of 3 distinct vertiport indices (which 3 of the
7 vertiports are charging stations). The "cycle selection" half of the
joint decision is not separately encoded in the chromosome — for a given
station placement, `optimization.fitness.evaluate()` deterministically
(greedily) generates the best cycle pool and exact-cover partition it can,
which is standard practice for this kind of two-level design problem
(outer metaheuristic over the hard combinatorial siting variable, inner
deterministic/greedy solve for the coverage variable). This keeps the GA's
search space to the tractable C(7,3)=35 combinations while the *quality* of
each evaluation still fully reflects duty-cycle feasibility.
"""
import random
import config
from optimization.base_optimizer import MetaheuristicOptimizer
from optimization import fitness as fitness_mod


class GAOptimizer(MetaheuristicOptimizer):
    def __init__(self, ordered_vertiport_ids, required_flights, spec,
                 population_size=None, generations=None, crossover_rate=None,
                 mutation_rate=None, elitism=None, seed=None, pool_size=None):
        super().__init__(ordered_vertiport_ids, required_flights, spec)
        self.n_stations_total = len(ordered_vertiport_ids)
        self.k = config.N_CHARGE_STATIONS
        self.population_size = population_size or config.GA_POPULATION_SIZE
        self.generations = generations or config.GA_GENERATIONS
        self.crossover_rate = crossover_rate or config.GA_CROSSOVER_RATE
        self.mutation_rate = mutation_rate or config.GA_MUTATION_RATE
        self.elitism = elitism if elitism is not None else config.GA_ELITISM
        self.pool_size = pool_size
        self.rng = random.Random(seed if seed is not None else config.RANDOM_SEED)

    # ---- chromosome helpers ----
    def _random_chromosome(self):
        return tuple(sorted(self.rng.sample(range(self.n_stations_total), self.k)))

    def initialize_population(self):
        pop = set()
        while len(pop) < self.population_size:
            pop.add(self._random_chromosome())
        return list(pop)

    def evaluate_population(self, population):
        scored = []
        for chrom in population:
            result = fitness_mod.evaluate(
                chrom, self.ordered_vertiport_ids, self.required_flights,
                self.spec, pool_size=self.pool_size
            )
            scored.append((chrom, result))
        scored.sort(key=lambda cr: cr[1]["fitness"])
        return scored

    def _tournament_select(self, scored, k=3):
        contenders = self.rng.sample(scored, min(k, len(scored)))
        contenders.sort(key=lambda cr: cr[1]["fitness"])
        return contenders[0][0]

    def _crossover(self, parent_a, parent_b):
        if self.rng.random() > self.crossover_rate:
            return parent_a
        pool = list(set(parent_a) | set(parent_b))
        if len(pool) < self.k:
            pool = list(range(self.n_stations_total))
        child = tuple(sorted(self.rng.sample(pool, self.k)))
        return child

    def _mutate(self, chrom):
        if self.rng.random() > self.mutation_rate:
            return chrom
        chrom = set(chrom)
        removable = self.rng.choice(list(chrom))
        chrom.remove(removable)
        available = [i for i in range(self.n_stations_total) if i not in chrom]
        chrom.add(self.rng.choice(available))
        return tuple(sorted(chrom))

    def evolve_step(self, population, scored):
        next_gen = [chrom for chrom, _ in scored[: self.elitism]]  # elitism
        while len(next_gen) < self.population_size:
            pa = self._tournament_select(scored)
            pb = self._tournament_select(scored)
            child = self._crossover(pa, pb)
            child = self._mutate(child)
            next_gen.append(child)
        return next_gen

    def run(self, verbose=False):
        population = self.initialize_population()
        best = None
        for gen in range(self.generations):
            scored = self.evaluate_population(population)
            gen_best_chrom, gen_best_result = scored[0]
            self.history.append(gen_best_result["fitness"])
            if best is None or gen_best_result["fitness"] < best["fitness"]:
                best = dict(gen_best_result)
                best["chromosome"] = gen_best_chrom
                best["generation_found"] = gen
            if verbose:
                print(f"gen {gen:3d}  best_fitness={gen_best_result['fitness']:.1f}  "
                      f"fleet={gen_best_result['fleet_size']}  "
                      f"uncovered={gen_best_result['n_uncovered']}  "
                      f"stations={sorted(gen_best_result['station_set'].station_ids)}")
            if self.stopping_criterion(gen, self.generations - 1):
                population = self.evolve_step(population, scored)
                break
            population = self.evolve_step(population, scored)

        return best
