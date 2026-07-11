"""
core/duty_cycle.py — DutyCycle domain model.

A DutyCycle is an ordered sequence of Flights (interleaved implicitly with
ground/turnaround/charging time) flown by a *single* aircraft within one
planning cycle (config.CYCLE_LENGTH_HOURS). One selected DutyCycle in the
final exact-cover solution corresponds to one aircraft's rotation, so
`len(selected_cycles)` is the fleet size the optimizer is minimizing.
"""
from dataclasses import dataclass, field
from typing import List
import itertools

_counter = itertools.count(1)


@dataclass
class DutyCycle:
    flights: List  # List[Flight], in flown order
    aircraft_class: str
    soc_trace: List[float] = field(default_factory=list)   # SoC after each flight
    charge_events: List[tuple] = field(default_factory=list)  # (after_flight_idx, minutes)
    is_feasible: bool = False
    cycle_id: int = field(default_factory=lambda: next(_counter))

    @property
    def total_distance_km(self) -> float:
        return sum(f.distance_km for f in self.flights)

    @property
    def total_pax(self) -> int:
        return sum(f.pax for f in self.flights)

    @property
    def flight_ids(self):
        return {f.flight_id for f in self.flights}

    def __repr__(self):
        route = " -> ".join(f.origin for f in self.flights) + (
            f" -> {self.flights[-1].destination}" if self.flights else ""
        )
        return f"<DutyCycle#{self.cycle_id} [{self.aircraft_class}] {route} feasible={self.is_feasible}>"
