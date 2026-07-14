"""
optimization/pso_optimizer.py — PSOOptimizer(MetaheuristicOptimizer)

Discrete PSO adaptation for the same station-siting search space. Each
particle's "position" is a 3-of-7 station set; "velocity" is modeled as a
mutation probability pulled toward the particle's personal best and the
global best (standard discrete-PSO trick for combinatorial problems).
Included primarily as a second alternate strategy alongside ACO, per the
architecture's Strategy-pattern extension point — GA remains the primary,
fully-tuned optimizer used in main.py.
"""
import random
import config
from optimization.base_optimizer import MetaheuristicOptimizer
from optimization import fitness as fitness_mod


class PSOOptimizer(MetaheuristicOptimizer):
    def __init__(self, ordered_vertiport_ids, required_flights, spec,
                 n_particles=None, iterations=None, pull_pbest=0.4, pull_gbest=0.4,
                 seed=None, pool_size=None):
        super().__init__(ordered_vertiport_ids, required_flights, spec)
        self.n_stations_total = len(ordered_vertiport_ids)
        self.k = config.N_CHARGE_STATIONS
        self.n_particles = n_particles or config.GA_POPULATION_SIZE
        self.iterations = iterations or config.GA_GENERATIONS
        self.pull_pbest = pull_pbest
        self.pull_gbest = pull_gbest
        self.pool_size = pool_size
        self.rng = random.Random(seed if seed is not None else config.RANDOM_SEED)

    def _random_chromosome(self):
        return tuple(sorted(self.rng.sample(range(self.n_stations_total), self.k)))

    def initialize_population(self):
        return [self._random_chromosome() for _ in range(self.n_particles)]

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

    def _move_toward(self, current, target, prob):
        current = set(current)
        target_only = [s for s in target if s not in current]
        if not target_only or self.rng.random() > prob:
            return tuple(sorted(current))
        remove = self.rng.choice(list(current))
        add = self.rng.choice(target_only)
        current.discard(remove)
        current.add(add)
        return tuple(sorted(current))

    def evolve_step(self, population, scored):
        gbest = scored[0][0]
        next_gen = []
        for chrom in population:
            pbest = chrom  # simplification: no per-particle memory kept across steps
            moved = self._move_toward(chrom, pbest, self.pull_pbest)
            moved = self._move_toward(moved, gbest, self.pull_gbest)
            next_gen.append(moved)
        return next_gen

    def run(self, verbose=False):
        population = self.initialize_population()
        best = None
        for it in range(self.iterations):
            scored = self.evaluate_population(population)
            it_best_chrom, it_best_result = scored[0]
            self.history.append(it_best_result["fitness"])
            if best is None or it_best_result["fitness"] < best["fitness"]:
                best = dict(it_best_result)
                best["chromosome"] = it_best_chrom
                best["generation_found"] = it
            if verbose:
                print(f"iter {it:3d}  best_fitness={it_best_result['fitness']:.1f}  "
                      f"fleet={it_best_result['fleet_size']}")
            population = self.evolve_step(population, scored)
        return best
