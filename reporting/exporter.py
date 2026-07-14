"""reporting/exporter.py — writes final results to JSON/CSV."""
import json
import csv
import config


def export_json(payload: dict, filename: str):
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = config.OUTPUT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    return path


def export_schedule_csv(schedule: list, filename: str):
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = config.OUTPUT_DIR / filename
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["tail_no", "aircraft_class", "leg", "from", "to",
                          "distance_km", "pax", "depart_min", "duration_min", "soc_after_pct"])
        for a in schedule:
            for leg in a["legs"]:
                writer.writerow([a["tail_no"], a["aircraft_class"], leg["leg"],
                                  leg["from"], leg["to"], leg["distance_km"], leg["pax"],
                                  leg["depart_min"], leg["duration_min"], leg["soc_after_pct"]])
    return path
