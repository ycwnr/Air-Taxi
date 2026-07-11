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
        schedule.append({
            "tail_no": f"AT-{tail_no:02d}",
            "aircraft_class": cycle.aircraft_class,
            "n_legs": len(cycle.flights),
            "total_distance_km": round(cycle.total_distance_km, 1),
            "total_pax": cycle.total_pax,
            "charge_events": cycle.charge_events,
            "legs": legs,
        })
    return schedule


def format_schedule_text(schedule: list) -> str:
    lines = []
    for a in schedule:
        lines.append(f"\n{a['tail_no']} [{a['aircraft_class']}] — {a['n_legs']} legs, "
                     f"{a['total_distance_km']} km, {a['total_pax']} pax carried")
        for leg in a["legs"]:
            chg = ""
            lines.append(
                f"   t+{leg['depart_min']:>5.1f}min  {leg['from']:>4} -> {leg['to']:<4} "
                f"({leg['distance_km']:>5.1f} km, {leg['pax']} pax, "
                f"SoC after: {leg['soc_after_pct']}%)"
            )
        if a["charge_events"]:
            lines.append(f"   charge stops: {a['charge_events']}")
    return "\n".join(lines)
