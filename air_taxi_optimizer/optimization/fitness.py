"""
optimization/fitness.py — decodes a chromosome into (ChargingStationSet,
selected DutyCycles) and scores it. Lower is better.

fitness = fleet_size + PENALTY_PER_UNCOVERED_FLIGHT * n_uncovered
"""
from battery_sim.charging_station_set import ChargingStationSet
from cycle_generation.cycle_generator import generate_cycle_pool
from optimization.exact_cover_solver import GreedyExactCoverSolver

PENALTY_PER_UNCOVERED_FLIGHT = 50  # >> any realistic fleet size, forces coverage first

_solver = GreedyExactCoverSolver()
_pool_cache = {}  # station_set -> cycle pool (cycle generation is the expensive step)


def decode_station_set(indices, ordered_vertiport_ids) -> ChargingStationSet:
    return ChargingStationSet.from_indices(indices, ordered_vertiport_ids)


def evaluate(indices, ordered_vertiport_ids, required_flights, spec,
             pool_size=None, use_cache=True):
    """
    indices: iterable of 3 distinct ints in range(len(ordered_vertiport_ids))
    Returns dict with fitness, fleet_size, n_uncovered, station_set, selected_cycles
    """
    station_set = decode_station_set(indices, ordered_vertiport_ids)

    cache_key = station_set.station_ids
    if use_cache and cache_key in _pool_cache:
        pool = _pool_cache[cache_key]
    else:
        pool = generate_cycle_pool(required_flights, spec, station_set, pool_size=pool_size)
        if use_cache:
            _pool_cache[cache_key] = pool

    required_ids = {f.flight_id for f in required_flights}
    selected, uncovered = _solver.solve(pool, required_ids)

    fleet_size = len(selected)
    n_uncovered = len(uncovered)
    fitness = fleet_size + PENALTY_PER_UNCOVERED_FLIGHT * n_uncovered

    return {
        "fitness": fitness,
        "fleet_size": fleet_size,
        "n_uncovered": n_uncovered,
        "station_set": station_set,
        "selected_cycles": selected,
        "uncovered_flight_ids": uncovered,
    }


def clear_cache():
    _pool_cache.clear()
