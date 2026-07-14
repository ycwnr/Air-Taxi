"""network/data_loader.py — loads & validates stations.json and demand_matrix.json."""
import json
from core.vertiport import Vertiport
import config


def load_vertiports() -> dict:
    """Returns {vertiport_id: Vertiport}."""
    with open(config.STATIONS_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    vertiports = {}
    for v in raw["vertiports"]:
        vertiports[v["id"]] = Vertiport(
            id=v["id"], code=v["code"], name=v["name"], lat=v["lat"], lon=v["lon"]
        )
    return vertiports


def load_demand_matrix() -> tuple:
    """Returns (order: List[str], matrix: dict[str, dict[str, int]]) after validation."""
    with open(config.DEMAND_FILE, encoding="utf-8") as f:
        raw = json.load(f)
    order = raw["order"]
    m = raw["matrix"]

    # --- validation ---
    for k in order:
        assert k in m, f"Missing row for {k} in demand matrix"
        assert len(m[k]) == len(order), f"Row {k} has wrong length"

    for i, a in enumerate(order):
        for j, b in enumerate(order):
            v_ab = m[a][j]
            v_ba = m[b][i]
            assert v_ab == v_ba, f"Demand matrix not symmetric at ({a},{b}): {v_ab} vs {v_ba}"
            assert v_ab >= 0, f"Negative demand at ({a},{b})"

    matrix = {a: {b: m[a][j] for j, b in enumerate(order)} for a in order}
    return order, matrix


def load_all():
    vertiports = load_vertiports()
    order, demand = load_demand_matrix()
    return vertiports, order, demand
