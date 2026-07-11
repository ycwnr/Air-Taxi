"""
config.py
=========
Single source of truth for every tunable constant used across the pipeline.
No algorithmic file should hard-code a number that belongs here.

Literature sources for the eVTOL parameters (Step 1 of the assignment,
"literature review of a representative manufacturer"):

  2-seat class  -> modeled on Volocopter VoloCity (public spec sheet + press):
                   cruise ~100 km/h, operational range ~35 km, MTOM ~1,000 kg,
                   battery-swap turnaround. Exact battery kWh and unit price are
                   not publicly disclosed by Volocopter, so they are estimated
                   from MTOM / energy-density norms for multicopter eVTOLs
                   (~45 kWh usable pack, ~$450,000 target unit price), flagged
                   as ESTIMATED below.
  4-seat class  -> modeled on Joby Aviation S4 (public spec sheet):
                   cruise ~322 km/h (200 mph), range ~161 km (100 mi),
                   battery 150-180 kWh (using 165 kWh midpoint), unit price
                   ~$1,300,000 (2026 list price).

Ticket CASK figures ($11.00 / $7.05 per pax-km) and the 3-charging-station,
15% SoC floor, 4-hour cycle-length, 2-year break-even constraints are taken
directly from Project.txt (the assignment brief).
"""

from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIONS_FILE = DATA_DIR / "stations.json"
DEMAND_FILE = DATA_DIR / "demand_matrix.json"
OUTPUT_DIR = BASE_DIR / "output"

# --------------------------------------------------------------------------
# Network / operational constraints (from Project.txt)
# --------------------------------------------------------------------------
N_CHARGE_STATIONS = 3          # exactly 3 of 7 vertiports must be charging-capable
MIN_SOC_FLOOR = 0.15            # battery must never drop below 15% SoC
TURNAROUND_MIN = 5              # minutes on ground between consecutive flights
CYCLE_LENGTH_HOURS = 4          # duty-cycle planning block used by cycle_generation
PLANNING_HORIZON = "hourly"     # demand matrix represents one representative hour
BREAKEVEN_YEARS = 2             # operator must break even within this horizon
OPERATING_HOURS_PER_DAY = 16    # assumed daily UAM operating window (06:00-22:00)
OPERATING_DAYS_PER_YEAR = 350   # assumed annual operating days (maintenance downtime excluded)

# --------------------------------------------------------------------------
# eVTOL fleet specifications (literature-derived, see module docstring)
# --------------------------------------------------------------------------
EVTOL_SPECS = {
    "2seat": {
        "label": "2-Seat class (Volocopter VoloCity-derived)",
        "seat_capacity": 2,
        "cruise_speed_kmh": 100.0,
        "range_km": 35.0,                 # manufacturer-stated operational range
        "battery_capacity_kwh": 45.0,     # ESTIMATED (not publicly disclosed)
        "charge_time_min_full": 40.0,     # ESTIMATED fast-charge/swap time, full pack
        "purchase_price_usd": 450_000.0,  # ESTIMATED target unit price
        "operating_cost_per_hour_usd": 250.0,  # ESTIMATED (crew/mx/insurance/energy)
        "cask_usd_per_pax_km": 11.00,     # given in Project.txt
    },
    "4seat": {
        "label": "4-Seat class (Joby Aviation S4-derived)",
        "seat_capacity": 4,
        "cruise_speed_kmh": 322.0,
        "range_km": 161.0,
        "battery_capacity_kwh": 165.0,    # midpoint of disclosed 150-180 kWh
        "charge_time_min_full": 18.0,     # midpoint of disclosed 15-20 min fast charge
        "purchase_price_usd": 1_300_000.0,
        "operating_cost_per_hour_usd": 650.0,  # ESTIMATED (crew/mx/insurance/energy)
        "cask_usd_per_pax_km": 7.05,      # given in Project.txt
    },
}

# Which aircraft class is used to convert passenger demand into discrete flights.
# The 4-seat class is materially cheaper per pax-km and has far greater range,
# so the fleet is built primarily around it; the 2-seat class is kept available
# for low-demand legs / robustness comparisons.
PRIMARY_AIRCRAFT_CLASS = "4seat"

# --------------------------------------------------------------------------
# Metaheuristic (GA) hyperparameters
# --------------------------------------------------------------------------
GA_POPULATION_SIZE = 16
GA_GENERATIONS = 25
GA_CROSSOVER_RATE = 0.8
GA_MUTATION_RATE = 0.3
GA_ELITISM = 2
RANDOM_SEED = 42

# --------------------------------------------------------------------------
# Cycle generation
# --------------------------------------------------------------------------
# NOTE: the charging-station search space here is C(7,3)=35, small enough to
# brute-force exhaustively (see validation.result_comparator), so the GA is
# intentionally run with a modest population/generations - it exists to
# demonstrate + validate the metaheuristic approach the assignment requires,
# not because exhaustive search is otherwise necessary. A results cache keyed
# by station-set is shared across the GA and brute-force phases within one
# process (optimization.fitness._pool_cache) so no station set's duty-cycle
# pool is ever rebuilt twice.
MAX_CYCLE_POOL_PER_STATION_SET = 1500   # cap candidate duty cycles per evaluation
MAX_FLIGHTS_PER_CYCLE = 20              # safety cap on legs per 4h duty cycle
N_PARTITION_RESTARTS = 40               # random-order full-partition constructions per station set

# --------------------------------------------------------------------------
# Economics
# --------------------------------------------------------------------------
DISCOUNT_RATE_ANNUAL = 0.0   # simple (non-discounted) break-even per assignment wording
