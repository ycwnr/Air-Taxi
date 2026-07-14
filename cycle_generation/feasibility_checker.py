"""cycle_generation/feasibility_checker.py — pure, independently-testable rules."""
import config


def within_range(distance_km: float, spec) -> bool:
    return distance_km <= spec.range_km


def within_time_budget(elapsed_min: float, next_flight_min: float,
                        cycle_length_hours: float = config.CYCLE_LENGTH_HOURS) -> bool:
    return (elapsed_min + next_flight_min) <= cycle_length_hours * 60.0


def within_flight_count(n_flights_so_far: int,
                         max_flights: int = config.MAX_FLIGHTS_PER_CYCLE) -> bool:
    return n_flights_so_far < max_flights


def continuity_ok(prev_flight, next_flight) -> bool:
    return prev_flight is None or prev_flight.destination == next_flight.origin
