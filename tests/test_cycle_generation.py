import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import config
from cycle_generation import feasibility_checker as fc
from core.flight import Flight
from core.evtol_spec import load_all_specs
from battery_sim.charging_station_set import ChargingStationSet
from cycle_generation.cycle_generator import generate_cycle_pool


def test_within_time_budget():
    assert fc.within_time_budget(0, 100) is True
    assert fc.within_time_budget(200, 100) is False


def test_within_flight_count():
    assert fc.within_flight_count(0) is True
    assert fc.within_flight_count(config.MAX_FLIGHTS_PER_CYCLE) is False


def test_continuity_ok():
    f1 = Flight("a-b-0", "a", "b", 10, 2, 2)
    f2 = Flight("b-c-0", "b", "c", 10, 2, 2)
    f3 = Flight("d-c-0", "d", "c", 10, 2, 2)
    assert fc.continuity_ok(f1, f2) is True
    assert fc.continuity_ok(f1, f3) is False
    assert fc.continuity_ok(None, f2) is True


def test_generate_cycle_pool_covers_every_flight_with_some_cycle():
    spec = load_all_specs()[config.PRIMARY_AIRCRAFT_CLASS]
    flights = [
        Flight("a-b-0", "a", "b", 10, 2, 4),
        Flight("b-a-0", "b", "a", 10, 2, 4),
    ]
    cs = ChargingStationSet(frozenset({"a", "b", "c"}))  # 3 arbitrary ids, only a/b matter here
    pool = generate_cycle_pool(flights, spec, cs, pool_size=50, n_restarts=5)
    covered = set()
    for cyc in pool:
        covered |= cyc.flight_ids
    assert covered == {"a-b-0", "b-a-0"}


if __name__ == "__main__":
    test_within_time_budget()
    test_within_flight_count()
    test_continuity_ok()
    test_generate_cycle_pool_covers_every_flight_with_some_cycle()
    print("test_cycle_generation.py: all tests passed")
