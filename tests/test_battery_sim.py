import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.battery import Battery
from core.evtol_spec import load_all_specs
from core.flight import Flight
from battery_sim.soc_simulator import simulate
from battery_sim.charging_station_set import ChargingStationSet
import config


def _spec():
    return load_all_specs()[config.PRIMARY_AIRCRAFT_CLASS]


def test_battery_discharge_reduces_soc():
    spec = _spec()
    b = Battery(capacity_kwh=spec.battery_capacity_kwh, soc=1.0)
    b.discharge_for_distance(50, spec)
    assert 0.0 < b.soc < 1.0


def test_battery_never_reports_floor_violation_when_full():
    spec = _spec()
    b = Battery(capacity_kwh=spec.battery_capacity_kwh, soc=1.0)
    assert not b.violates_floor()


def test_soc_simulator_flags_infeasible_long_hop_without_charging():
    spec = _spec()
    huge_leg = Flight("x-y-0", "x", "y", distance_km=spec.range_km * 5, duration_min=10, pax=4)
    cycle = simulate([huge_leg], spec.key, spec, charging_set=None)
    assert cycle.is_feasible is False


def test_soc_simulator_feasible_short_hop():
    spec = _spec()
    short_leg = Flight("a-b-0", "a", "b", distance_km=10, duration_min=2, pax=2)
    cycle = simulate([short_leg], spec.key, spec, charging_set=None)
    assert cycle.is_feasible is True
    assert cycle.soc_trace[-1] >= config.MIN_SOC_FLOOR


def test_charging_station_set_validates_size():
    try:
        ChargingStationSet(frozenset({"a", "b"}))
        assert False, "should have raised"
    except ValueError:
        pass


if __name__ == "__main__":
    test_battery_discharge_reduces_soc()
    test_battery_never_reports_floor_violation_when_full()
    test_soc_simulator_flags_infeasible_long_hop_without_charging()
    test_soc_simulator_feasible_short_hop()
    test_charging_station_set_validates_size()
    print("test_battery_sim.py: all tests passed")
