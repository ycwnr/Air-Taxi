"""network/demand_processor.py"""
import math
from core.flight import Flight


def choose_fleet_mix(pax: int, d_km: float, specs: dict, max_n=None):
    """
    FIX 2: Cost-aware vehicle-mix search for one OD pair's demand.

    Cost proxy per leg = distance_km * seat_capacity * cask_usd_per_pax_km,
    i.e. CASK x ASK for that leg — the same cost basis economics/cost_model.py
    already uses, so the routing decision and the economics stay consistent.

    Returns list[(aircraft_class, pax_carried)] describing the flights to emit,
    or [] if pax <= 0.
    """
    if pax <= 0:
        return []

    # A class is usable for this OD pair only if the leg is within its range —
    # a 2-seater simply cannot fly a leg beyond its physical range, no matter
    # how attractive the cost looks on paper.
    usable_classes = {k: s for k, s in specs.items() if d_km <= s.range_km}
    if not usable_classes:
        # No class can fly this distance at all — this is a network design
        # problem (an OD pair beyond every aircraft's range), not something
        # the fleet-mix heuristic can fix. Fall back to the longest-range
        # class so build_required_flights still produces a Flight (it will
        # correctly come back infeasible later in soc_simulator, surfacing
        # the issue instead of silently dropping demand).
        usable_classes = {max(specs, key=lambda k: specs[k].range_km):
                          specs[max(specs, key=lambda k: specs[k].range_km)]}

    max_n = max_n or (pax // 2 + 2)
    best = None  # (cost, empty_seats, n_flights, combo)

    class_keys = list(usable_classes.keys())
    counts_by_class = {k: range(0, max_n) for k in class_keys}

    # Search is intentionally small/bounded: real demand cells are <= ~100
    # pax/hour, so exhaustive small-integer search is cheap and exact.
    def _search(idx, remaining_pax, combo):
        nonlocal best
        if idx == len(class_keys):
            capacity = sum(counts_by_class_used * usable_classes[k].seat_capacity
                            for k, counts_by_class_used in combo.items())
            if capacity < pax:
                return
            cost = sum(n * usable_classes[k].seat_capacity * d_km
                       * usable_classes[k].cask_usd_per_pax_km
                       for k, n in combo.items())
            empty = capacity - pax
            n_flights = sum(combo.values())
            key = (cost, empty, n_flights)
            if best is None or key < best[0]:
                best = (key, dict(combo))
            return
        k = class_keys[idx]
        seat = usable_classes[k].seat_capacity
        upper = math.ceil(pax / seat) + 1
        for n in range(0, upper + 1):
            combo[k] = n
            _search(idx + 1, remaining_pax, combo)
        combo.pop(k, None)

    _search(0, pax, {})
    _, combo = best

    result = []
    remaining = pax
    for aircraft_class, n in combo.items():
        seat_cap = usable_classes[aircraft_class].seat_capacity
        for _ in range(n):
            if remaining <= 0:
                break
            carried = min(seat_cap, remaining)
            remaining -= carried
            result.append((aircraft_class, carried))
    return result


def build_required_flights(order, demand, dist_matrix, specs: dict) -> list:
    """
    FIX 2: `specs` replaces the single `spec` argument — pass the full dict
    from core.evtol_spec.load_all_specs(), e.g. {"2seat": ..., "4seat": ...}.
    Each OD pair's demand is resolved into a cost-aware vehicle mix via
    choose_fleet_mix() instead of a fixed ceil(pax / seat_capacity).
    """
    flights = []
    for a in order:
        for b in order:
            if a == b:
                continue
            pax = demand[a][b]
            if pax <= 0:
                continue
            d_km = dist_matrix[a][b]
            mix = choose_fleet_mix(pax, d_km, specs)
            for k, (aircraft_class, carried) in enumerate(mix):
                spec = specs[aircraft_class]
                dur = spec.flight_time_min(d_km)
                flights.append(Flight(
                    flight_id=f"{a}-{b}-{k}",
                    origin=a,
                    destination=b,
                    distance_km=d_km,
                    duration_min=dur,
                    pax=carried,
                    aircraft_class=aircraft_class,
                ))
    return flights


def summarize(flights: list, seat_capacity: int = None) -> dict:
    """Unchanged behavior, but total_ask is now computed per-flight using
    each flight's OWN aircraft_class capacity rather than one global seat_capacity,
    since flights are no longer homogeneous."""
    total_pax = sum(f.pax for f in flights)
    total_km = sum(f.distance_km for f in flights)
    out = {
        "n_flights": len(flights),
        "total_pax": total_pax,
        "total_pax_km": sum(f.pax * f.distance_km for f in flights),
        "total_distance_km": total_km,
    }
    if seat_capacity is not None:
        out["total_ask"] = total_km * seat_capacity
    return out