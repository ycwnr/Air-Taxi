"""
core/evtol_spec.py — eVTOL aircraft specification.

Parameters are populated from config.EVTOL_SPECS (literature-derived, see
config.py docstring). Adding a new aircraft class = adding one dict entry
in config.py + optionally a subclass here; nothing else in the codebase
needs to change.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class EVTOLSpec:
    key: str
    label: str
    seat_capacity: int
    cruise_speed_kmh: float
    range_km: float
    battery_capacity_kwh: float
    charge_time_min_full: float
    purchase_price_usd: float
    operating_cost_per_hour_usd: float
    cask_usd_per_pax_km: float

    @property
    def energy_consumption_per_km(self) -> float:
        """kWh consumed per km of cruise flight (derived from range & battery)."""
        # Reserve 15% floor is *not* usable energy in normal ops, so range is
        # defined against the usable (85%) portion of the pack.
        usable_kwh = self.battery_capacity_kwh * 0.85
        return usable_kwh / self.range_km

    @property
    def charge_rate_kwh_per_min(self) -> float:
        return self.battery_capacity_kwh / self.charge_time_min_full

    def flight_time_min(self, distance_km: float) -> float:
        return (distance_km / self.cruise_speed_kmh) * 60.0

    @classmethod
    def from_config(cls, key: str, cfg: dict) -> "EVTOLSpec":
        return cls(
            key=key,
            label=cfg["label"],
            seat_capacity=cfg["seat_capacity"],
            cruise_speed_kmh=cfg["cruise_speed_kmh"],
            range_km=cfg["range_km"],
            battery_capacity_kwh=cfg["battery_capacity_kwh"],
            charge_time_min_full=cfg["charge_time_min_full"],
            purchase_price_usd=cfg["purchase_price_usd"],
            operating_cost_per_hour_usd=cfg["operating_cost_per_hour_usd"],
            cask_usd_per_pax_km=cfg["cask_usd_per_pax_km"],
        )


def load_all_specs() -> dict:
    import config
    return {k: EVTOLSpec.from_config(k, v) for k, v in config.EVTOL_SPECS.items()}
