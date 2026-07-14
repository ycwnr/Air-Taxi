"""reporting/schedule_report.py — per-aircraft hourly route table."""


def build_schedule(selected_cycles, vertiport_codes: dict) -> list:
    """
    vertiport_codes: {vertiport_id: code}
    Returns list of dicts, one per aircraft (tail), with its ordered route.
    """
    schedule = []
    for tail_no, cycle in enumerate(
        sorted(selected_cycles, key=lambda c: -len(c.flights)), start=1
    ):
        legs = []
        t = 0.0
        n_legs = len(cycle.flights)
        for i, f in enumerate(cycle.flights):
            legs.append({
                "leg": i + 1,
                "from": vertiport_codes.get(f.origin, f.origin),
                "to": vertiport_codes.get(f.destination, f.destination),
                "distance_km": round(f.distance_km, 1),
                "pax": f.pax,
                "depart_min": round(t, 1),
                "duration_min": round(f.duration_min, 1),
                "soc_after_pct": round(cycle.soc_trace[i] * 100, 1) if i < len(cycle.soc_trace) else None,
            })
            t += f.duration_min + 5  # + turnaround
            for ev_idx, ev_min in cycle.charge_events:
                if ev_idx == i:
                    t += ev_min

        # End-of-cycle top-up (requirement 3): charge_events entries with
        # idx == n_legs happen AFTER the last leg, once the aircraft is back
        # home, to restore start_soc before the cycle repeats.
        end_of_cycle_charge_min = sum(
            ev_min for ev_idx, ev_min in cycle.charge_events if ev_idx == n_legs
        )
        t += end_of_cycle_charge_min

        schedule.append({
            "tail_no": f"AT-{tail_no:02d}",
            "aircraft_class": cycle.aircraft_class,
            "n_legs": n_legs,
            "total_distance_km": round(cycle.total_distance_km, 1),
            "total_pax": cycle.total_pax,
            "charge_events": cycle.charge_events,
            "is_closed_loop": cycle.is_closed_loop,
            "is_periodic": cycle.is_periodic,
            "cycle_duration_min": round(t, 1),
            "end_of_cycle_charge_min": round(end_of_cycle_charge_min, 1),
            "legs": legs,
        })
    return schedule


def format_schedule_text(schedule: list) -> str:
    lines = []
    for a in schedule:
        loop_tag = "closed-loop, repeats indefinitely" if a["is_periodic"] else (
            "closed-loop, NOT SoC-periodic" if a["is_closed_loop"] else "OPEN (does not return to base)"
        )
        lines.append(f"\n{a['tail_no']} [{a['aircraft_class']}] — {a['n_legs']} legs, "
                     f"{a['total_distance_km']} km, {a['total_pax']} pax carried  [{loop_tag}]")
        for leg in a["legs"]:
            lines.append(
                f"   t+{leg['depart_min']:>5.1f}min  {leg['from']:>4} -> {leg['to']:<4} "
                f"({leg['distance_km']:>5.1f} km, {leg['pax']} pax, "
                f"SoC after: {leg['soc_after_pct']}%)"
            )
        if a["charge_events"]:
            mid = [ev for ev in a["charge_events"] if ev[0] < a["n_legs"]]
            end = [ev for ev in a["charge_events"] if ev[0] >= a["n_legs"]]
            if mid:
                lines.append(f"   mid-cycle charge stops: {mid}")
            if end:
                lines.append(f"   end-of-cycle top-up (resets SoC for the repeat): {end}")
    return "\n".join(lines)