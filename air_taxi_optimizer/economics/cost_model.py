"""
economics/cost_model.py — CAPEX/OPEX calculation from the final fleet
composition and duty-cycle statistics.

IMPORTANT: Project.txt explicitly supplies CASK (cost per available seat-km)
for each aircraft class ($11.00/pax-km for 2-seat, $7.05/pax-km for 4-seat)
and says the break-even ticket price must be derived from it. So OPEX here
is computed as CASK x ASK (Available Seat-Kilometers actually flown by the
fleet), NOT from a separately-invented per-hour operating cost — that keeps
the economic analysis anchored to the numbers the assignment actually gives
us, rather than to the literature-estimated `operating_cost_per_hour_usd`
figure in config.py (which is kept only as auxiliary/reference info).
"""
from dataclasses import dataclass
import config


@dataclass
class CostModel:
    fleet_size: int
    spec: object          # EVTOLSpec (single aircraft class used for the fleet)
    hourly_ask: float      # available seat-km flown by the fleet in one representative hour

    def capex_usd(self) -> float:
        return self.fleet_size * self.spec.purchase_price_usd

    def annual_operating_hours(self) -> float:
        return config.OPERATING_HOURS_PER_DAY * config.OPERATING_DAYS_PER_YEAR

    def annual_ask(self) -> float:
        """Scale one representative operating hour's ASK up to a full year,
        assuming the demand pattern (and therefore flight schedule) repeats
        every operating hour of every operating day."""
        return self.hourly_ask * self.annual_operating_hours()

    def opex_usd_per_year(self) -> float:
        """OPEX = CASK ($/pax-km, used here as $/available-seat-km per the
        assignment's CASK definition) x annual ASK flown by the fleet."""
        return self.spec.cask_usd_per_pax_km * self.annual_ask()

    def total_cost_usd(self, years: float) -> float:
        return self.capex_usd() + self.opex_usd_per_year() * years

    def annual_pax_km(self, hourly_pax_km: float) -> float:
        """Scale one representative hour of ACTUAL passenger-km (revenue
        basis) up to a full operating year."""
        return hourly_pax_km * self.annual_operating_hours()
