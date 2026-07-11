"""
main.py — orchestrates the full pipeline end-to-end. Contains no algorithmic
logic; every step delegates to the relevant package. Run with:

    python3 main.py
"""
import time
import config
from network.data_loader import load_all
from network.distance_calculator import build_distance_matrix
from network.demand_processor import build_required_flights, summarize
from core.evtol_spec import load_all_specs
from optimization.genetic_algorithm import GAOptimizer
from optimization import fitness as fitness_mod
from validation.result_comparator import brute_force_optimum, compare
from reporting.schedule_report import build_schedule, format_schedule_text
from reporting.visualizer import plot_convergence, plot_soc_curves, plot_fleet_gantt
from reporting.exporter import export_json, export_schedule_csv
from economics.cost_model import CostModel
from economics.breakeven_analysis import BreakEvenAnalyzer
from utils.logger import get_logger

log = get_logger("main")


def main():
    t0 = time.time()
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 1-2. Load & validate data
    log.info("Loading vertiports & demand matrix...")
    vertiports, order, demand = load_all()
    vertiport_codes = {vid: v.code for vid, v in vertiports.items()}

    # 3. Distance matrix
    dist_matrix = build_distance_matrix(vertiports)

    # 4. eVTOL specs (literature-derived, config.py)
    specs = load_all_specs()
    primary_spec = specs[config.PRIMARY_AIRCRAFT_CLASS]
    log.info(f"Primary aircraft: {primary_spec.label} "
              f"({primary_spec.seat_capacity} seats, {primary_spec.range_km} km range, "
              f"{primary_spec.battery_capacity_kwh} kWh)")

    # 5. Required flights from demand
    required_flights = build_required_flights(order, demand, dist_matrix, primary_spec)
    demand_summary = summarize(required_flights, seat_capacity=primary_spec.seat_capacity)
    log.info(f"Required flights this hour: {demand_summary['n_flights']}  "
              f"total pax: {demand_summary['total_pax']}  "
              f"total pax-km: {demand_summary['total_pax_km']:.1f}")

    # 6-7. Metaheuristic optimization (GA) over charging-station placement
    log.info(f"Running GA over {config.GA_GENERATIONS} generations, "
              f"population {config.GA_POPULATION_SIZE}...")
    ga = GAOptimizer(order, required_flights, primary_spec)
    ga_best = ga.run(verbose=False)
    log.info(f"GA best: fleet={ga_best['fleet_size']}  "
              f"uncovered={ga_best['n_uncovered']}  "
              f"stations={sorted(ga_best['station_set'].station_ids)}")

    # 8. Validation: brute-force the full C(7,3)=35 search space as ground truth
    log.info("Running brute-force validation over all 35 station placements...")
    # NOTE: fitness_mod's pool cache is intentionally NOT cleared here -
    # station sets already evaluated during the GA phase are reused as-is,
    # so this validation pass only pays the cost of the combos the GA didn't
    # already visit.
    bf_results = brute_force_optimum(order, required_flights, primary_spec)
    comparison = compare(ga_best, bf_results)
    log.info(f"Validation: GA {'MATCHES' if comparison['matches_global_optimum'] else 'DOES NOT MATCH'} "
              f"global optimum (gap={comparison['fitness_gap']}). "
              f"Optimal stations: {comparison['brute_force_optimal_stations']} "
              f"-> fleet size {comparison['brute_force_optimal_fleet_size']}")

    # Use the *global optimum* (brute-force, since search space is tiny) as the
    # final reported solution, with the GA comparison retained for the report.
    final = bf_results[0]

    # 9. Schedule report
    schedule = build_schedule(final["selected_cycles"], vertiport_codes)
    schedule_text = format_schedule_text(schedule)

    # 10. Economics
    cost_model = CostModel(fleet_size=final["fleet_size"], spec=primary_spec,
                            hourly_ask=demand_summary["total_ask"])
    breakeven = BreakEvenAnalyzer.solve_ticket_price(cost_model, demand_summary["total_pax_km"])

    # 11. Export everything
    charging_station_names = [vertiports[vid].name for vid in final["station_set"].station_ids]
    payload = {
        "vertiports": {vid: {"code": v.code, "name": v.name, "lat": v.lat, "lon": v.lon}
                        for vid, v in vertiports.items()},
        "aircraft_spec": {
            "class": primary_spec.key, "label": primary_spec.label,
            "seat_capacity": primary_spec.seat_capacity,
            "cruise_speed_kmh": primary_spec.cruise_speed_kmh,
            "range_km": primary_spec.range_km,
            "battery_capacity_kwh": primary_spec.battery_capacity_kwh,
            "purchase_price_usd": primary_spec.purchase_price_usd,
            "operating_cost_per_hour_usd": primary_spec.operating_cost_per_hour_usd,
            "cask_usd_per_pax_km": primary_spec.cask_usd_per_pax_km,
        },
        "demand_summary": demand_summary,
        "optimal_solution": {
            "charging_stations": sorted(final["station_set"].station_ids),
            "charging_station_names": charging_station_names,
            "fleet_size": final["fleet_size"],
            "n_uncovered_flights": final["n_uncovered"],
        },
        "ga_validation": comparison,
        "economics": breakeven,
        "runtime_sec": None,
    }

    export_json(payload, "results.json")
    export_schedule_csv(schedule, "schedule.csv")
    plot_convergence(ga.history, config.OUTPUT_DIR / "ga_convergence.png")
    plot_soc_curves(final["selected_cycles"], config.OUTPUT_DIR / "soc_curves.png")
    plot_fleet_gantt(schedule, config.OUTPUT_DIR / "fleet_gantt.png")

    with open(config.OUTPUT_DIR / "schedule.txt", "w", encoding="utf-8") as f:
        f.write(schedule_text)

    runtime = time.time() - t0
    payload["runtime_sec"] = round(runtime, 2)
    export_json(payload, "results.json")

    log.info(f"Done in {runtime:.1f}s. Fleet size = {final['fleet_size']} "
              f"({primary_spec.label}). Break-even ticket price = "
              f"${breakeven['breakeven_price_usd_per_pax_km']:.3f}/pax-km.")
    log.info(f"Outputs written to {config.OUTPUT_DIR}")

    return payload, schedule


if __name__ == "__main__":
    main()
