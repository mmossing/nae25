"""
Block definitions for NAE25 stages 83-128.

Primary source: content/planning/nae_my_itinerary_v2.csv — provides exact
dates, depart/arrive cities, distance, and elevation for every stage. Rest
rows in the CSV define block boundaries directly.

Supplementary: content/planning/nae25_stages_*_poi.md — provides descriptive
route labels for blocks 96-128 (e.g. "Mexico City to Oaxaca").
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

PLANNING_DIR = Path(__file__).parents[2] / "content" / "planning"
ITINERARY_CSV = PLANNING_DIR / "nae_my_itinerary_v2.csv"


def _parse_number(s: str) -> float | None:
    s = (s or "").replace(",", "").strip()
    m = re.search(r"[\d]+\.?\d*", s)
    return float(m.group()) if m else None


def _poi_route_labels() -> dict[int, str]:
    """Return {stage_low: route_label} from the POI markdown files."""
    labels: dict[int, str] = {}
    for f in PLANNING_DIR.glob("nae25_stages_*_poi.md"):
        m = re.search(r"nae25_stages_(\d+)-(\d+)_poi\.md", f.name)
        if not m:
            continue
        stage_low = int(m.group(1))
        content = f.read_text()
        route_match = re.search(r"^## (.+)$", content, re.MULTILINE)
        if route_match:
            labels[stage_low] = route_match.group(1).strip()
    return labels


def _load_itinerary_stages() -> list[dict]:
    """Load all riding stages from the itinerary CSV, sorted by stage number."""
    stages: list[dict] = []
    with ITINERARY_CSV.open() as f:
        for row in csv.DictReader(f):
            try:
                stage_num = int(row["Stage"])
            except (ValueError, KeyError):
                continue
            try:
                d = date.fromisoformat(row["Date"].strip())
            except (ValueError, KeyError):
                continue
            stages.append({
                "stage": stage_num,
                "date": d,
                "depart": row.get("Depart", "").strip(),
                "arrive": row.get("Arrive", "").strip(),
                "distance_km": _parse_number(row.get("Distance (km)")),
                "elevation_m": _parse_number(row.get("Up (m)")),
            })
    return sorted(stages, key=lambda s: s["stage"])


def _make_block(stage_list: list[dict], poi_labels: dict[int, str]) -> dict:
    stage_low = stage_list[0]["stage"]
    stage_high = stage_list[-1]["stage"]
    # Use POI label if available, otherwise build one from city names.
    if stage_low in poi_labels:
        label = poi_labels[stage_low]
        source = "planning_doc"
    elif stage_list[0]["depart"] and stage_list[-1]["arrive"]:
        label = f"{stage_list[0]['depart']} → {stage_list[-1]['arrive']}"
        source = "itinerary_csv"
    else:
        label = f"Stages {stage_low}-{stage_high}"
        source = "itinerary_csv"
    return {
        "block_id": f"block_{stage_low:03d}_{stage_high:03d}",
        "stage_low": stage_low,
        "stage_high": stage_high,
        "date_start": stage_list[0]["date"],
        "date_end": stage_list[-1]["date"],
        "route_label": label,
        "source": source,
        "stages": stage_list,
    }


def get_all_blocks() -> list[dict]:
    """
    Return block dicts for all stages 83-128.

    Blocks are derived from the itinerary CSV: a rest day (date gap > 1)
    between consecutive stage rows closes the current block. Any resulting
    single-stage block is merged into the preceding block.
    """
    stages = _load_itinerary_stages()
    if not stages:
        return []

    poi_labels = _poi_route_labels()
    blocks: list[dict] = []
    group = [stages[0]]

    for s in stages[1:]:
        if (s["date"] - group[-1]["date"]).days > 1:
            blocks.append(_make_block(group, poi_labels))
            group = [s]
        else:
            group.append(s)

    blocks.append(_make_block(group, poi_labels))

    # Merge any single-stage block into its predecessor.
    merged: list[dict] = [blocks[0]]
    for b in blocks[1:]:
        if len(b["stages"]) == 1:
            combined = merged[-1]["stages"] + b["stages"]
            merged[-1] = _make_block(combined, poi_labels)
        else:
            merged.append(b)
    return merged


def get_documented_stages() -> list[dict]:
    """Return flat list of all stage dicts (83-128) with block_id attached."""
    result: list[dict] = []
    for block in get_all_blocks():
        for s in block["stages"]:
            result.append({**s, "block_id": block["block_id"]})
    return result
