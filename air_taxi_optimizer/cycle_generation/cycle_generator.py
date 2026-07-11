"""
cycle_generation/cycle_generator.py — builds the pool of candidate,
SoC-feasible duty cycles that the exact-cover stage chooses from.

Strategy: rather than growing independent, mutually-overlapping cycles at
random (which tends to leave most flights only coverable by inefficient
single-flight fallbacks), this module repeatedly constructs a FULL random-
order partition of the required flights into duty cycles ("greedy chain
packing"): flights are consumed from a shrinking pool, so within one restart
every cycle is automatically flight-disjoint from every other cycle in that
same restart. Doing this for several random restarts and pooling all the
resulting cycles together gives optimization.exact_cover_solver a rich,
partially-redundant set of candidate cycles to select the smallest
non-overlapping subset from (it may even mix cycles from different
restarts).

Each tentative extension of a chain is verified against the SoC floor via
battery_sim.soc_simulator.simulate(), so every cycle returned here is
already guaranteed 15%-floor-feasible for the given ChargingStationSet.
"""
import random
import config
from cycle_generation import feasibility_checker as fc
from battery_sim.soc_simulator import simulate


def _build_full_partition(required_flights, spec, charging_set, rng):
    """One random-order greedy packing of ALL required flights into
    SoC-feasible duty cycles. Returns list[DutyCycle] (a full partition)."""
    unused = {f.flight_id: f for f in required_flights}
    cycles = []

    while unused:
        start_id = rng.choice(list(unused.keys()))
        sequence = [unused.pop(start_id)]

        while fc.within_flight_count(len(sequence)):
            current_dest = sequence[-1].destination
            candidates = [f for f in unused.values() if f.origin == current_dest]
            if not candidates:
                break
            # Most-constrained-next heuristic: prefer routing through
            # destinations that currently have the FEWEST remaining unused
            # outgoing flights, so those bottleneck nodes get threaded into a
            # chain now rather than being stranded as an orphan single-flight
            # cycle once every other chain has already consumed their peers.
            # A little random jitter keeps restarts diverse.
            def _out_degree(flight):
                return sum(1 for f in unused.values() if f.origin == flight.destination)
            rng.shuffle(candidates)
            candidates.sort(key=lambda f: _out_degree(f))

            added = False
            for cand in candidates:
                trial_seq = sequence + [cand]
                trial_cycle = simulate(trial_seq, spec.key, spec, charging_set)
                if not trial_cycle.is_feasible:
                    continue
                # Time budget must include any charging stops incurred along
                # the way, not just flight + turnaround time, or cycles can
                # silently blow past config.CYCLE_LENGTH_HOURS.
                total_elapsed = (
                    sum(f.duration_min for f in trial_seq)
                    + config.TURNAROUND_MIN * len(trial_seq)
                    + sum(mins for _, mins in trial_cycle.charge_events)
                )
                if total_elapsed > config.CYCLE_LENGTH_HOURS * 60.0:
                    continue
                sequence = trial_seq
                unused.pop(cand.flight_id)
                added = True
                break
            if not added:
                break

        final_cycle = simulate(sequence, spec.key, spec, charging_set)
        cycles.append(final_cycle)

    return cycles


def generate_cycle_pool(required_flights, spec, charging_set,
                         pool_size: int = None, seed: int = None,
                         n_restarts: int = None) -> list:
    """
    Runs several independent full-partition constructions (each internally
    flight-disjoint) and pools all resulting SoC-feasible DutyCycles together
    (deduplicated by flight sequence) for the exact-cover solver to choose
    from. Also guarantees single-flight fallback cycles exist for every
    required flight, so exact coverage is always achievable.
    """
    n_restarts = n_restarts or config.N_PARTITION_RESTARTS
    base_seed = seed if seed is not None else config.RANDOM_SEED

    pool = []
    seen_signatures = set()

    for r in range(n_restarts):
        rng = random.Random(base_seed + r * 7919)  # distinct stream per restart
        partition = _build_full_partition(required_flights, spec, charging_set, rng)
        for cycle in partition:
            if not cycle.is_feasible or not cycle.flights:
                continue
            sig = tuple(f.flight_id for f in cycle.flights)
            if sig in seen_signatures:
                continue
            seen_signatures.add(sig)
            pool.append(cycle)

    # Single-flight fallbacks guarantee a feasible exact cover always exists,
    # even for flights that never landed in a good chain across all restarts.
    for f in required_flights:
        sig = (f.flight_id,)
        if sig in seen_signatures:
            continue
        cycle = simulate([f], spec.key, spec, charging_set)
        if cycle.is_feasible:
            seen_signatures.add(sig)
            pool.append(cycle)

    if pool_size:
        # Keep the biggest (most flight-efficient) cycles plus all fallbacks,
        # to cap pool size without hurting coverage or fleet efficiency.
        singles = [c for c in pool if len(c.flights) == 1]
        multis = [c for c in pool if len(c.flights) > 1]
        multis.sort(key=lambda c: -len(c.flights))
        budget = max(0, pool_size - len(singles))
        pool = multis[:budget] + singles

    return pool
