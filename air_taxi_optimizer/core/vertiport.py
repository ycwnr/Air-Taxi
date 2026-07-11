"""core/vertiport.py — Vertiport domain model."""
from dataclasses import dataclass


@dataclass
class Vertiport:
    id: str
    code: str
    name: str
    lat: float
    lon: float
    is_charging_station: bool = False

    def __repr__(self):
        chg = "⚡" if self.is_charging_station else " "
        return f"<Vertiport {self.code}{chg}>"

    def __hash__(self):
        return hash(self.id)
