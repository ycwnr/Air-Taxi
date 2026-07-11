"""
optimization/aco_optimizer.py — ACOOptimizer(MetaheuristicOptimizer)

Ant-Colony variant over the same C(7,3) station-placement search space as
the GA. Included so the report can compare metaheuristics on identical
fitness evaluations (optimization.fitness.evaluate), per the assignment's
"any metaheuristic of your choice" wording and to demonstrate the
Strategy-pattern extensibility described in the architecture doc.

Pheromone is kept per-station (7 values); a candidate solution samples 3
distinct stations proportionally to pheromone^alpha, then pheromone is
reinforced inversely to the resulting fitness (lower fitness = more
deposit) and evaporated each iteration.
"""
import random
import config
from optimization.base_optimizer import MetaheuristicOptimizer
from optimization import fitness as fitness_mod


class ACOOptimizer(MetaheuristicOptimizer):
    def __init__(self, ordered_vertiport_ids, required_flights, spec,
                 n_ants=None, iterations=None, evaporation=0.3, alpha=1.5,
                 seed=None, pool_size=None):
        super().__init__(ordered_vertiport_ids, required_flights, spec)
        self.n_stations_total = len(ordered_vertiport_ids)
        self.k = config.N_CHARGE_STATIONS
        self.n_ants = n_ants or config.GA_POPULATION_SIZE
        self.iterations = iterations or config.GA_GENERATIONS
        self.evaporation = evaporation
        self.alpha = alpha
        self.pool_size = pool_size
        self.rng = random.Random(seed if seed is not None else config.RANDOM_SEED)
        self.pheromone = [1.0] * self.n_stations_total

    def _sample_solution(self):
        weights = [p ** self.alpha for p in self.pheromone]
        chosen = set()
        candidates = list(range(self.n_stations_total))
        while len(chosen) < self.k:
            w = [weights[i] for i in candidates]
            total = sum(w)
            r = self.rng.uniform(0, total)
            acc = 0.0
            pick = candidates[-1]
            for i, wi in zip(candidates, w):
                acc += wi
                if acc >= r:
                    pick = i
                    break
            chosen.add(pick)
            candidates.remove(pick)
        return tuple(sorted(chosen))

    def initialize_population(self):
        return [self._sample_solution() for _ in range(self.n_ants)]

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

    def evolve_step(self, population, scored):
        # evaporate
        self.pheromone = [(1 - self.evaporation) * p for p in self.pheromone]
        # reinforce using top ants (elitist deposit)
        for chrom, result in scored[: max(1, self.n_ants // 5)]:
            deposit = 1.0 / (1.0 + result["fitness"])
            for idx in chrom:
                self.pheromone[idx] += deposit
        return [self._sample_solution() for _ in range(self.n_ants)]

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
