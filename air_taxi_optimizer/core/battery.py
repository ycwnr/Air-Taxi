"""core/battery.py — Battery state-of-charge model."""
from dataclasses import dataclass
import config


@dataclass
class Battery:
    capacity_kwh: float
    soc: float = 1.0  # fraction 0..1

    def discharge_for_distance(self, distance_km: float, spec) -> float:
        """Discharge battery for a flight of `distance_km`. Returns resulting SoC."""
        energy_used = distance_km * spec.energy_consumption_per_km
        self.soc -= energy_used / self.capacity_kwh
        return self.soc

    def charge_for_minutes(self, minutes: float, spec) -> float:
        energy_added = minutes * spec.charge_rate_kwh_per_min
        self.soc = min(1.0, self.soc + energy_added / self.capacity_kwh)
        return self.soc

    def violates_floor(self) -> bool:
        return self.soc < config.MIN_SOC_FLOOR

    def clone(self) -> "Battery":
        return Battery(capacity_kwh=self.capacity_kwh, soc=self.soc)
