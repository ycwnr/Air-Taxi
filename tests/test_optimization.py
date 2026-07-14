import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from core.evtol_spec import load_all_specs
from core.flight import Flight
from optimization.genetic_algorithm import GAOptimizer
from optimization import fitness as fitness_mod


def test_ga_chromosome_always_valid_size():
    spec = load_all_specs()[config.PRIMARY_AIRCRAFT_CLASS]
    order = ["a", "b", "c", "d", "e", "f", "g"]
    flights = [Flight("a-b-0", "a", "b", 10, 2, 4), Flight("b-a-0", "b", "a", 10, 2, 4)]
    ga = GAOptimizer(order, flights, spec, population_size=6, generations=2, pool_size=20)
    pop = ga.initialize_population()
    for chrom in pop:
        assert len(chrom) == config.N_CHARGE_STATIONS
        assert len(set(chrom)) == config.N_CHARGE_STATIONS
        assert all(0 <= i < len(order) for i in chrom)


def test_ga_run_returns_feasible_best():
    fitness_mod.clear_cache()
    spec = load_all_specs()[config.PRIMARY_AIRCRAFT_CLASS]
    order = ["a", "b", "c", "d", "e", "f", "g"]
    flights = [Flight("a-b-0", "a", "b", 10, 2, 4), Flight("b-a-0", "b", "a", 10, 2, 4)]
    ga = GAOptimizer(order, flights, spec, population_size=6, generations=3, pool_size=20)
    best = ga.run()
    assert best["n_uncovered"] == 0
    assert best["fleet_size"] >= 1


if __name__ == "__main__":
    test_ga_chromosome_always_valid_size()
    test_ga_run_returns_feasible_best()
    print("test_optimization.py: all tests passed")
