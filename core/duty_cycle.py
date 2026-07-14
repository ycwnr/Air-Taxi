"""
core/duty_cycle.py — DutyCycle domain model.

A DutyCycle is an ordered sequence of Flights (interleaved implicitly with
ground/turnaround/charging time) flown by a *single* aircraft within one
planning cycle (config.CYCLE_LENGTH_HOURS). One selected DutyCycle in the
final exact-cover solution corresponds to one aircraft's rotation, so
`len(selected_cycles)` is the fleet size the optimizer is minimizing.

NOTE (closed-loop / periodic operation, see cycle_generation & battery_sim):
A DutyCycle is only "repeatable" (i.e. the aircraft can fly the exact same
duty cycle again immediately afterwards, hour after hour) if BOTH:
  1. it is a closed loop: flights[0].origin == flights[-1].destination, and
  2. it is SoC-periodic: soc_trace[-1] (after any mandatory end-of-cycle
     top-up charge) is back at the cycle's start_soc.
`is_closed_loop` / `is_periodic` surface those two properties so reporting
and validation can check them explicitly instead of just trusting the
generator.
"""
from dataclasses import dataclass, field
from typing import List
import itertools

_counter = itertools.count(1)


@dataclass
class DutyCycle:
    flights: List
    aircraft_class: str
    soc_trace: List[float] = field(default_factory=list)
    charge_events: List[tuple] = field(default_factory=list)
    is_feasible: bool = False
    is_closed_loop: bool = False   # FIX 1: True once a return-to-origin leg was appended/confirmed
    cycle_id: int = field(default_factory=lambda: next(_counter))

    @property
    def total_distance_km(self) -> float:
        return sum(f.distance_km for f in self.flights)

    @property
    def total_pax(self) -> int:
        return sum(f.pax for f in self.flights)

    @property
    def flight_ids(self):
        """All flight ids in this cycle, INCLUDING synthetic reposition legs."""
        return {f.flight_id for f in self.flights}

    @property
    def required_flight_ids(self):
        """FIX 1: Only the demand-covering legs — this is what the exact-cover
        solver must match against, since reposition legs are not part of the
        required-flight universe and would otherwise never subset-match."""
        return {f.flight_id for f in self.flights if not f.is_reposition}

    @property
    def is_closed_loop(self) -> bool:
        """True if the aircraft lands back at the vertiport it started from,
        i.e. the cycle can be flown again immediately without repositioning."""
        if not self.flights:
            return False
        return self.flights[0].origin == self.flights[-1].destination

    @property
    def is_periodic(self) -> bool:
        """True if the end-of-cycle SoC (after any final top-up charge) has
        been restored to the cycle's starting SoC, so the SAME charge profile
        repeats on every future repetition of this cycle."""
        if self.end_soc is None:
            return False
        return abs(self.end_soc - self.start_soc) <= 1e-6

    def __repr__(self):
        route = " -> ".join(f.origin for f in self.flights) + (
            f" -> {self.flights[-1].destination}" if self.flights else ""
        )
        loop = "closed" if self.is_closed_loop else "OPEN"
        return f"<DutyCycle#{self.cycle_id} [{self.aircraft_class}] {route} feasible={self.is_feasible} {loop}>"