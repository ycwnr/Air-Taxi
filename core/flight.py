"""core/flight.py — a single directed flight leg to be covered."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    """One atomic eVTOL leg. `aircraft_class` and `is_reposition` are additive
    fields (defaulted) so existing positional call sites (tests, etc.) keep working."""
    flight_id: str
    origin: str
    destination: str
    distance_km: float
    duration_min: float
    pax: int
    # FIX 2: which vehicle class this leg requires (defaults to the legacy primary class)
    aircraft_class: str = "4seat"
    # FIX 1: True for synthetic repositioning legs inserted to close a duty-cycle loop
    is_reposition: bool = False

    def __repr__(self):
        tag = " [reposition]" if self.is_reposition else ""
        return (f"<Flight {self.flight_id}: {self.origin}->{self.destination} "
                f"({self.pax}pax, {self.distance_km:.1f}km, {self.aircraft_class}){tag}>")