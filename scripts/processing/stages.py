"""
Build stages.csv and blocks.csv from the itinerary CSV and downloaded Strava files.

The itinerary CSV (nae_my_itinerary_v2.csv) is the authoritative source for
stage numbers, dates, depart/arrive cities, and block boundaries. Strava
activities are matched to stages by date; the longest ride on a given day is
taken as the canonical stage activity.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path

DATA_DIR = Path(__file__).parents[2] / "data"
RAW_DIR = DATA_DIR / "raw" / "activities"
PROCESSED_DIR = DATA_DIR / "processed"

_STAGE_FIELDS = [
    "stage", "date", "block_id", "activity_id",
    "distance_km", "elevation_m", "moving_time_s",
    "avg_hr", "suffer_score", "depart", "arrive", "source",
]

_BLOCK_FIELDS = [
    "block_id", "stage_low", "stage_high", "date_start", "date_end",
    "route_label", "source",
]


def _load_activities() -> dict[date, dict]:
    """Return {date: activity_dict} keeping the longest ride per calendar day."""
    by_date: dict[date, dict] = {}
    for p in sorted(RAW_DIR.glob("*.json")):
        if p.name == ".gitkeep":
            continue
        data = json.loads(p.read_text())
        summary = data.get("summary") or {}
        date_str = (summary.get("start_date_local") or "")[:10]
        if not date_str:
            continue
        act = {
            "activity_id": summary.get("id", ""),
            "date": date.fromisoformat(date_str),
            "distance_m": summary.get("distance") or 0,
            "elevation_m": summary.get("total_elevation_gain") or 0,
            "moving_time_s": summary.get("moving_time") or "",
            "avg_hr": summary.get("average_heartrate") or "",
            "suffer_score": summary.get("suffer_score") or "",
        }
        d = act["date"]
        if d not in by_date or act["distance_m"] > by_date[d]["distance_m"]:
            by_date[d] = act
    return by_date


def build_mapping() -> None:
    """Write data/processed/stages.csv and data/processed/blocks.csv."""
    from scripts.processing.blocks import get_all_blocks, get_documented_stages

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    activities = _load_activities()
    documented = get_documented_stages()
    stage_rows: list[dict] = []

    for doc in documented:
        act = activities.get(doc["date"])
        if act:
            stage_rows.append({
                "stage": doc["stage"],
                "date": doc["date"].isoformat(),
                "block_id": doc["block_id"],
                "activity_id": act["activity_id"],
                "distance_km": round((act["distance_m"] or 0) / 1000, 2),
                "elevation_m": round(act["elevation_m"] or 0),
                "moving_time_s": act["moving_time_s"],
                "avg_hr": act["avg_hr"],
                "suffer_score": act["suffer_score"],
                "depart": doc.get("depart", ""),
                "arrive": doc.get("arrive", ""),
                "source": "strava+itinerary",
            })
        else:
            # No Strava upload for this stage — fill from itinerary CSV.
            stage_rows.append({
                "stage": doc["stage"],
                "date": doc["date"].isoformat(),
                "block_id": doc["block_id"],
                "activity_id": "",
                "distance_km": doc.get("distance_km") or "",
                "elevation_m": doc.get("elevation_m") or "",
                "moving_time_s": "",
                "avg_hr": "",
                "suffer_score": "",
                "depart": doc.get("depart", ""),
                "arrive": doc.get("arrive", ""),
                "source": "itinerary_csv",
            })

    stage_rows.sort(key=lambda r: r["stage"])

    stages_path = PROCESSED_DIR / "stages.csv"
    with stages_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_STAGE_FIELDS)
        w.writeheader()
        w.writerows(stage_rows)
    print(f"  wrote {stages_path} ({len(stage_rows)} stages)")

    all_blocks = sorted(get_all_blocks(), key=lambda b: b["stage_low"])
    blocks_path = PROCESSED_DIR / "blocks.csv"
    with blocks_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=_BLOCK_FIELDS)
        w.writeheader()
        for b in all_blocks:
            w.writerow({
                "block_id": b["block_id"],
                "stage_low": b["stage_low"],
                "stage_high": b["stage_high"],
                "date_start": b["date_start"].isoformat(),
                "date_end": b["date_end"].isoformat(),
                "route_label": b["route_label"],
                "source": b["source"],
            })
    print(f"  wrote {blocks_path} ({len(all_blocks)} blocks)")
