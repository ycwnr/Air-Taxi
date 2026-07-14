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
    fleet_by_class: dict          # {"2seat": n, "4seat": n}
    specs: dict                    # {"2seat": EVTOLSpec, "4seat": EVTOLSpec}
    ask_by_class: dict              # actual flown ASK per class, INCLUDING reposition km

    def capex_usd(self) -> float:
        return sum(n * self.specs[k].purchase_price_usd for k, n in self.fleet_by_class.items())

    def annual_operating_hours(self) -> float:
        return config.OPERATING_HOURS_PER_DAY * config.OPERATING_DAYS_PER_YEAR

    def opex_usd_per_year(self) -> float:
        hourly_opex = sum(self.specs[k].cask_usd_per_pax_km * ask
                           for k, ask in self.ask_by_class.items())
        return hourly_opex * self.annual_operating_hours()

    def annual_pax_km(self, hourly_pax_km: float) -> float:
        """Scale one representative hour of ACTUAL passenger-km (revenue
        basis) up to a full operating year."""
        return hourly_pax_km * self.annual_operating_hours()

    def total_cost_usd(self, years: float) -> float:
        return self.capex_usd() + self.opex_usd_per_year() * years