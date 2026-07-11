"""core/flight.py — a single required directed flight leg to be covered."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Flight:
    """One atomic eVTOL leg that must be covered exactly once by the schedule."""
    flight_id: str      # unique id, e.g. "karaj-ika-0"
    origin: str          # vertiport id
    destination: str     # vertiport id
    distance_km: float
    duration_min: float
    pax: int              # passengers actually carried on this specific flight

    def __repr__(self):
        return f"<Flight {self.flight_id}: {self.origin}->{self.destination} ({self.pax}pax, {self.distance_km:.1f}km)>"
