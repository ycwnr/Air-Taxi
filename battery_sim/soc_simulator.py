"""
battery_sim/soc_simulator.py — walks a candidate flight sequence, discharging
the battery per flight and recharging at charging-capable vertiports, marking
the resulting DutyCycle feasible/infeasible against the 15% SoC floor
(config.MIN_SOC_FLOOR).

Charging policy (mandatory top-up, look-ahead sized), unchanged:
  1. SoC must NEVER drop below the 15% floor, ever.
  2. Every time the aircraft is on the ground at a charging-capable
     vertiport, it MUST charge — even if it's already above the floor.
  3. It does not need to charge to 100%: it charges just enough so SoC
     will not drop below 15% before the NEXT charging-capable stop it
     will visit later in the sequence (or, if there is no later charging
     stop, enough to cover the rest of the sequence). It is allowed to
     charge more than this minimum, but never less.

NEW — periodic end-of-cycle top-up (requirement 3):
  The whole point of a duty cycle is that the SAME aircraft flies it again,
  hour after hour. That is only true if the battery is back at the exact
  SoC it started the cycle with by the time the cycle "loops" — otherwise
  every repetition would start from a different SoC and the charge profile
  (and therefore feasibility) would silently drift. So, once all flights in
  the sequence are done, if the aircraft has landed back at its cycle's
  home vertiport (see DutyCycle.is_closed_loop / requirement 2) AND that
  vertiport is charging-capable, we add ONE final mandatory charge event
  that tops the battery back up to `start_soc`. That event is recorded with
  index == len(flight_sequence) (one past the last leg) so reporting can
  tell it apart from an ordinary mid-cycle charge stop — it happens *after*
  the last leg, before the cycle repeats.

  If the cycle isn't closed, or its home vertiport isn't charging-capable,
  we simply cannot make it periodic with a physical charger, so `end_soc`
  is left at whatever SoC the aircraft actually landed with and
  DutyCycle.is_periodic will be False. This is a real physical limitation
  of "only 3 of 7 vertiports have chargers", not a bug — see
  cycle_generation/cycle_generator.py, which is why cycle homes are chosen
  from charging-capable vertiports in the first place whenever possible.
"""
from core.battery import Battery
from core.duty_cycle import DutyCycle
import config


def _energy_horizon_kwh(flight_sequence, start_idx, charging_set, spec):
    """Total energy (kWh) needed for flights[start_idx:], stopping right
    before the next flight whose ORIGIN is a charging-capable vertiport
    (since the aircraft will recharge again there). If no such flight
    exists, the horizon covers all remaining flights."""
    horizon_kwh = 0.0
    n = len(flight_sequence)
    for j in range(start_idx, n):
        if j > start_idx and charging_set is not None and charging_set.can_charge(flight_sequence[j].origin):
            break
        horizon_kwh += flight_sequence[j].distance_km * spec.energy_consumption_per_km
    return horizon_kwh


def simulate(flight_sequence, aircraft_class, spec, charging_set,
             start_soc: float = 1.0, enforce_periodic: bool = None) -> DutyCycle:
    """
    flight_sequence: ordered list[Flight] representing one aircraft's rotation.
    charging_set: ChargingStationSet (or None -> no charging available at all).
    enforce_periodic: if True, try to add the end-of-cycle top-up charge
        described above. Defaults to config.REQUIRE_PERIODIC_SOC. Callers
        doing cheap feasibility probes on PARTIAL sequences (e.g. while a
        chain is still being built) should pass False explicitly, since the
        periodic top-up only makes sense once the sequence is final.
    """
    if enforce_periodic is None:
        enforce_periodic = config.REQUIRE_PERIODIC_SOC

    battery = Battery(capacity_kwh=spec.battery_capacity_kwh, soc=start_soc)
    soc_trace = []
    charge_events = []
    feasible = True
    n = len(flight_sequence)

    for idx, flight in enumerate(flight_sequence):
        origin_can_charge = charging_set is not None and charging_set.can_charge(flight.origin)

        if origin_can_charge:
            horizon_kwh = _energy_horizon_kwh(flight_sequence, idx, charging_set, spec)
            required_soc = config.MIN_SOC_FLOOR + horizon_kwh / battery.capacity_kwh
            target_soc = min(1.0, required_soc)
            deficit = target_soc - battery.soc
            if deficit > 0:
                energy_deficit_kwh = deficit * battery.capacity_kwh
                minutes_needed = energy_deficit_kwh / spec.charge_rate_kwh_per_min
                battery.charge_for_minutes(minutes_needed, spec)
                charge_events.append((idx, round(minutes_needed, 1)))

        energy_needed = flight.distance_km * spec.energy_consumption_per_km
        projected_soc = battery.soc - energy_needed / battery.capacity_kwh
        if projected_soc < config.MIN_SOC_FLOOR:
            feasible = False
            break

        battery.discharge_for_distance(flight.distance_km, spec)
        soc_trace.append(round(battery.soc, 4))
        if battery.violates_floor():
            feasible = False
            break

    fully_simulated = feasible and len(soc_trace) == n
    end_soc = round(battery.soc, 4) if fully_simulated else None

    if fully_simulated and enforce_periodic and n > 0:
        home = flight_sequence[0].origin
        is_closed = flight_sequence[-1].destination == home
        home_can_charge = charging_set is not None and charging_set.can_charge(home)
        if is_closed and home_can_charge:
            deficit = start_soc - battery.soc
            if deficit > 1e-9:
                energy_deficit_kwh = deficit * battery.capacity_kwh
                minutes_needed = energy_deficit_kwh / spec.charge_rate_kwh_per_min
                battery.charge_for_minutes(minutes_needed, spec)
                # idx == n (one past the last leg) marks an END-OF-CYCLE
                # top-up, distinct from the mid-cycle charge stops above.
                charge_events.append((n, round(minutes_needed, 1)))
            end_soc = round(battery.soc, 4)

    cycle = DutyCycle(
        flights=list(flight_sequence),
        aircraft_class=aircraft_class,
        soc_trace=soc_trace,
        charge_events=charge_events,
        is_feasible=fully_simulated,
        start_soc=start_soc,
        end_soc=end_soc,
    )
    return cycle