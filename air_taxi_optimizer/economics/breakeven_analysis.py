"""
economics/breakeven_analysis.py — solves for the ticket price ($/pax-km)
such that cumulative revenue equals cumulative cost at the target horizon
(config.BREAKEVEN_YEARS = 2).

    revenue(T) = price_per_pax_km * annual_pax_km * T
    cost(T)    = CAPEX + OPEX_per_year * T

    breakeven:  price = (CAPEX + OPEX_per_year * T) / (annual_pax_km * T)
"""
import config


class BreakEvenAnalyzer:
    @staticmethod
    def solve_ticket_price(cost_model, hourly_pax_km: float,
                            horizon_years: float = None) -> dict:
        horizon_years = horizon_years or config.BREAKEVEN_YEARS
        capex = cost_model.capex_usd()
        opex_per_year = cost_model.opex_usd_per_year()
        annual_pax_km = cost_model.annual_pax_km(hourly_pax_km)

        total_cost = capex + opex_per_year * horizon_years
        total_pax_km = annual_pax_km * horizon_years

        price_per_pax_km = total_cost / total_pax_km if total_pax_km > 0 else float("inf")

        return {
            "capex_usd": capex,
            "opex_per_year_usd": opex_per_year,
            "total_cost_over_horizon_usd": total_cost,
            "annual_pax_km": annual_pax_km,
            "total_pax_km_over_horizon": total_pax_km,
            "breakeven_price_usd_per_pax_km": price_per_pax_km,
            "horizon_years": horizon_years,
        }
