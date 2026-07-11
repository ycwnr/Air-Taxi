"""
network/demand_processor.py — turns the symmetric hourly passenger demand
matrix into a concrete list of directed `Flight` objects that must each be
covered exactly once by the exact-cover / metaheuristic stage.

The demand matrix gives passengers/hour required *between* each OD pair.
Because the matrix is symmetric (d(a,b) == d(b,a)), that same passenger flow
must be served in BOTH directions each hour — i.e. an aircraft carrying
travelers from A to B does not, by itself, satisfy the B->A requirement.
So for every ordered pair (a,b) with a != b and demand > 0, we generate
ceil(demand / seats) discrete directed flights of a fixed aircraft class.
"""
import math
from core.flight import Flight


def build_required_flights(order, demand, dist_matrix, spec) -> list:
    """
    order: list of vertiport ids
    demand: dict[a][b] -> pax/hour (symmetric)
    dist_matrix: dict[a][b] -> km
    spec: EVTOLSpec used to size flights (seat capacity)
    """
    flights = []
    for a in order:
        for b in order:
            if a == b:
                continue
            pax = demand[a][b]
            if pax <= 0:
                continue
            n_flights = math.ceil(pax / spec.seat_capacity)
            remaining = pax
            for k in range(n_flights):
                carried = min(spec.seat_capacity, remaining)
                remaining -= carried
                d_km = dist_matrix[a][b]
                dur = spec.flight_time_min(d_km)
                flights.append(Flight(
                    flight_id=f"{a}-{b}-{k}",
                    origin=a,
                    destination=b,
                    distance_km=d_km,
                    duration_min=dur,
                    pax=carried,
                ))
    return flights


def summarize(flights: list, seat_capacity: int = None) -> dict:
    total_pax = sum(f.pax for f in flights)
    total_km = sum(f.distance_km for f in flights)
    out = {
        "n_flights": len(flights),
        "total_pax": total_pax,
        "total_pax_km": sum(f.pax * f.distance_km for f in flights),
        "total_distance_km": total_km,
    }
    if seat_capacity is not None:
        # Available Seat-Kilometers: every flight flies at full seat capacity
        # regardless of how many passengers it actually carries.
        out["total_ask"] = total_km * seat_capacity
    return out
