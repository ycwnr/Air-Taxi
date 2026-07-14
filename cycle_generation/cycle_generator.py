"""cycle_generation/cycle_generator.py"""
import random
import config
from cycle_generation import feasibility_checker as fc
from battery_sim.soc_simulator import simulate
from core.flight import Flight


def _build_return_leg(current_vertiport, origin_vertiport, dist_matrix, spec, leg_index):
    """FIX 1: Synthesizes the zero-passenger repositioning leg needed to close
    the loop back to the cycle's starting vertiport."""
    if current_vertiport == origin_vertiport:
        return None
    d_km = dist_matrix[current_vertiport][origin_vertiport]
    return Flight(
        flight_id=f"RPST-{current_vertiport}-{origin_vertiport}-{leg_index}",
        origin=current_vertiport,
        destination=origin_vertiport,
        distance_km=d_km,
        duration_min=spec.flight_time_min(d_km),
        pax=0,
        aircraft_class=spec.key,
        is_reposition=True,
    )


def _close_loop(sequence, unused, spec, charging_set, dist_matrix, rng):
    """
    FIX 1: Attempts to append a return-to-origin leg. If the direct return
    violates the 15% SoC floor or blows the 4h cycle-time budget, we backtrack
    by shedding the *last* consumed required flight back into `unused` and
    retry closing from the shorter chain — a shorter chain both shortens the
    remaining distance-to-cover AND gives the SoC-floor check at the
    now-earlier tail one more real chance to have topped up at a charging
    stop before the loop closes. This is routing-level, not a cosmetic append:
    the candidate sequence is re-run through the full soc_simulator before
    being accepted.
    """
    origin_id = sequence[0].origin
    while True:
        if sequence[-1].destination == origin_id:
            return sequence, True  # already closed (rare, but possible)

        return_leg = _build_return_leg(sequence[-1].destination, origin_id,
                                        dist_matrix, spec, len(sequence))
        trial_seq = sequence + [return_leg]
        trial_cycle = simulate(trial_seq, spec.key, spec, charging_set)
        total_elapsed = (
            sum(f.duration_min for f in trial_seq)
            + config.TURNAROUND_MIN * len(trial_seq)
            + sum(mins for _, mins in trial_cycle.charge_events)
        )
        if trial_cycle.is_feasible and total_elapsed <= config.CYCLE_LENGTH_HOURS * 60.0:
            return trial_seq, True

        if len(sequence) <= 1:
            return sequence, False  # could not close even a single-leg cycle

        dropped = sequence[-1]
        if not dropped.is_reposition:
            unused[dropped.flight_id] = dropped
        sequence = sequence[:-1]


def _build_full_partition(required_flights, spec, charging_set, dist_matrix, rng):
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

        # FIX 1: enforce closed loop before finalizing the cycle
        sequence, closed = _close_loop(sequence, unused, spec, charging_set, dist_matrix, rng)

        final_cycle = simulate(sequence, spec.key, spec, charging_set)
        final_cycle.is_closed_loop = closed
        cycles.append(final_cycle)

    return cycles


def generate_cycle_pool(required_flights, specs, charging_set, dist_matrix,
                         pool_size: int = None, seed: int = None,
                         n_restarts: int = None) -> list:
    """
    FIX 2: `specs` is now a dict {aircraft_class: EVTOLSpec}. Required flights
    are partitioned by their `aircraft_class` and each partition is threaded
    using ITS OWN spec (range/speed/charge-rate), since one physical aircraft
    cannot switch class mid-route.
    """
    n_restarts = n_restarts or config.N_PARTITION_RESTARTS
    base_seed = seed if seed is not None else config.RANDOM_SEED

    by_class = {}
    for f in required_flights:
        by_class.setdefault(f.aircraft_class, []).append(f)

    pool = []
    seen_signatures = set()

    for aircraft_class, flights_of_class in by_class.items():
        spec = specs[aircraft_class]
        class_offset = abs(hash(aircraft_class)) % 10_000

        for r in range(n_restarts):
            rng = random.Random(base_seed + class_offset + r * 7919)
            partition = _build_full_partition(flights_of_class, spec, charging_set,
                                               dist_matrix, rng)
            for cycle in partition:
                if not cycle.is_feasible or not cycle.flights:
                    continue
                sig = tuple(f.flight_id for f in cycle.flights)
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                pool.append(cycle)

        # Single-flight fallbacks per class, closed with an immediate return leg
        for f in flights_of_class:
            sig = (f.flight_id,)
            if sig in seen_signatures:
                continue
            single, closed = _close_loop([f], {}, spec, charging_set, dist_matrix,
                                          random.Random(base_seed))
            cycle = simulate(single, spec.key, spec, charging_set)
            cycle.is_closed_loop = closed
            if cycle.is_feasible:
                seen_signatures.add(sig)
                pool.append(cycle)

    if pool_size:
        singles = [c for c in pool if len(c.required_flight_ids) <= 1]
        multis = [c for c in pool if len(c.required_flight_ids) > 1]
        multis.sort(key=lambda c: -len(c.required_flight_ids))
        budget = max(0, pool_size - len(singles))
        pool = multis[:budget] + singles

    return pool