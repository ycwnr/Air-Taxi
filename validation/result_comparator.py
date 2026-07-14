"""
validation/result_comparator.py — cross-checks the GA's result against a
brute-force enumeration baseline (the true optimum over all C(7,3)=35
possible charging-station placements) and/or against course reference
output if `reference_runner.run_reference()` produced one.
"""
import itertools
from optimization import fitness as fitness_mod


def brute_force_optimum(ordered_vertiport_ids, required_flights, spec, pool_size=None):
    """Exhaustively evaluates every 3-of-7 station placement. Feasible because
    C(7,3) = 35 is small; this is the ground-truth baseline for validating
    the GA/ACO/PSO metaheuristics without needing external reference code."""
    n = len(ordered_vertiport_ids)
    k = 3
    results = []
    for combo in itertools.combinations(range(n), k):
        r = fitness_mod.evaluate(combo, ordered_vertiport_ids, required_flights, spec,
                                  pool_size=pool_size)
        r = dict(r)
        r["chromosome"] = combo
        results.append(r)
    results.sort(key=lambda r: r["fitness"])
    return results


def compare(ga_best: dict, brute_force_results: list) -> dict:
    true_best = brute_force_results[0]
    gap = ga_best["fitness"] - true_best["fitness"]
    same_station_set = ga_best["station_set"].station_ids == true_best["station_set"].station_ids
    return {
        "ga_fitness": ga_best["fitness"],
        "ga_fleet_size": ga_best["fleet_size"],
        "ga_stations": sorted(ga_best["station_set"].station_ids),
        "brute_force_optimal_fitness": true_best["fitness"],
        "brute_force_optimal_fleet_size": true_best["fleet_size"],
        "brute_force_optimal_stations": sorted(true_best["station_set"].station_ids),
        "fitness_gap": gap,
        "matches_global_optimum": (gap == 0),
        "same_station_set_as_optimum": same_station_set,
    }
