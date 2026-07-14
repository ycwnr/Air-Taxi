"""
battery_sim/charging_station_set.py

Wraps "which N of the 7 vertiports are charging-capable" as a first-class,
validated object. This is exactly the decision variable half of the GA
chromosome (the other half being which duty cycles are selected).
"""
from dataclasses import dataclass, field
from typing import FrozenSet
import config


@dataclass(frozen=True)
class ChargingStationSet:
    station_ids: FrozenSet[str]

    def __post_init__(self):
        if len(self.station_ids) != config.N_CHARGE_STATIONS:
            raise ValueError(
                f"ChargingStationSet must contain exactly {config.N_CHARGE_STATIONS} "
                f"stations, got {len(self.station_ids)}: {self.station_ids}"
            )

    def can_charge(self, vertiport_id: str) -> bool:
        return vertiport_id in self.station_ids

    def apply_to(self, vertiports: dict):
        """Mutates a {id: Vertiport} dict's is_charging_station flags in place."""
        for vid, v in vertiports.items():
            v.is_charging_station = vid in self.station_ids

    @classmethod
    def from_indices(cls, indices, ordered_ids) -> "ChargingStationSet":
        return cls(frozenset(ordered_ids[i] for i in indices))

    def __repr__(self):
        return f"<ChargingStationSet {sorted(self.station_ids)}>"
