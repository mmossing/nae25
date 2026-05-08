"""
Generate Jupyter Book section pages from blocks.csv and stages.csv.

Writes:
  content/sections/block_*.md   — one page per block
  content/intro.md              — introduction with tour totals

Usage:
    python -m scripts.build_pages
"""

from __future__ import annotations

import csv
import re
from datetime import date
from pathlib import Path

BLOCKS_CSV   = Path("data/processed/blocks.csv")
STAGES_CSV   = Path("data/processed/stages.csv")
SECTIONS_DIR = Path("content/sections")
CONTENT_DIR  = Path("content")


def _clean_label(label: str) -> str:
    """Strip 'Stages NNN-MMM: ' prefix present in some POI-sourced labels."""
    return re.sub(r"^Stages \d+[\-–]\d+:\s*", "", label).strip()


def _fmt_date_range(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day}–{end.day} {start.strftime('%B %Y')}"
    elif start.year == end.year:
        return f"{start.strftime('%-d %B')} – {end.strftime('%-d %B %Y')}"
    return f"{start.strftime('%-d %B %Y')} – {end.strftime('%-d %B %Y')}"


def _fmt_moving(seconds: str) -> str:
    if not seconds:
        return "—"
    s = int(float(seconds))
    h, m = s // 3600, (s % 3600) // 60
    return f"{h}:{m:02d}"


def _load_blocks() -> list[dict]:
    with BLOCKS_CSV.open() as f:
        return list(csv.DictReader(f))


def _load_stages_by_block() -> dict[str, list[dict]]:
    by_block: dict[str, list[dict]] = {}
    with STAGES_CSV.open() as f:
        for row in csv.DictReader(f):
            by_block.setdefault(row["block_id"], []).append(row)
    return by_block


def _block_page(block: dict, stages: list[dict]) -> str:
    bid        = block["block_id"]
    title      = _clean_label(block["route_label"])
    date_start = date.fromisoformat(block["date_start"])
    date_end   = date.fromisoformat(block["date_end"])
    date_range = _fmt_date_range(date_start, date_end)
    n          = len(stages)
    total_km   = sum(float(s["distance_km"]) for s in stages if s.get("distance_km"))
    total_elev = sum(float(s["elevation_m"]) for s in stages if s.get("elevation_m"))
    total_s    = sum(int(float(s["moving_time_s"])) for s in stages if s.get("moving_time_s"))
    tot_h, tot_min = total_s // 3600, (total_s % 3600) // 60
    low, high  = block["stage_low"], block["stage_high"]

    rows = []
    for s in stages:
        d_str = date.fromisoformat(s["date"]).strftime("%-d %b")
        km    = f"{float(s['distance_km']):.0f}" if s.get("distance_km") else "—"
        elev  = f"+{float(s['elevation_m']):.0f}" if s.get("elevation_m") else "—"
        hr    = f"{float(s['avg_hr']):.0f}" if s.get("avg_hr") else "—"
        rows.append(
            f"| {s['stage']} | {d_str} | {s['depart']} | {s['arrive']}"
            f" | {km} km | {elev} m | {_fmt_moving(s.get('moving_time_s', ''))} | {hr} |"
        )

    table = "\n".join(rows)

    return f"""\
# {title}

**Stages {low}–{high} · {date_range} · {n} riding days · {total_km:.0f} km · +{total_elev:.0f} m · {tot_h}h {tot_min:02d}m**

## Route Map

```{{raw}} html
<iframe
  src="../../{bid}_map.html"
  width="100%" height="520px"
  frameborder="0" style="border:none; border-radius:6px;"
></iframe>
```

## Elevation Profile

```{{figure}} ../maps/{bid}_elevation.png
:width: 100%
:alt: Elevation profile for stages {low}–{high}
Sequential elevation profile. Dashed grey lines indicate unrecorded sections.
```

## Stages

| Stage | Date | Depart | Arrive | Distance | Elevation | Moving time | Avg HR |
|------:|------|--------|--------|:--------:|:---------:|:-----------:|:------:|
{table}

**Block totals:** {total_km:.0f} km · +{total_elev:.0f} m · {tot_h}h {tot_min:02d}m riding time

## Notes

*Add narrative here.*
"""


def _intro_page(blocks: list[dict], stages_by_block: dict) -> str:
    all_stages = [s for stages in stages_by_block.values() for s in stages]
    total_km   = sum(float(s["distance_km"]) for s in all_stages if s.get("distance_km"))
    total_elev = sum(float(s["elevation_m"]) for s in all_stages if s.get("elevation_m"))
    total_s    = sum(int(float(s["moving_time_s"])) for s in all_stages if s.get("moving_time_s"))
    tot_h      = total_s // 3600

    return f"""\
# Introduction

*North American Epic 2025* documents a bicycle journey from Puerto Vallarta, Mexico
to Panama City, Panama — Stages 83 through 128 of the
[TDA Global Cycling North American Epic](https://www.tdaglobalcycling.com/north-american-epic).

## The Sectional Ride

The full NAE tour spans ~17,000 km from Tuktoyaktuk in Canada’s Arctic to Panama City,
covering 128 stages across 9 countries. This book covers the southern section,
ridden as a sectional participant from 25 October to 21 December 2025.

|  |  |
|---|---|
| **Start** | Puerto Vallarta, Mexico · Stage 83 · 25 October 2025 |
| **Finish** | Panama City, Panama · Stage 128 · 21 December 2025 |
| **Riding days** | 46 stages across 11 blocks |
| **Rest days** | 12 |
| **Countries** | Mexico · Guatemala · El Salvador · Honduras · Nicaragua · Costa Rica · Panama |
| **Distance** | {total_km:.0f} km |
| **Elevation gain** | +{total_elev:.0f} m |
| **Riding time** | {tot_h} hours |

## Structure

The ride is organised into **11 blocks** — groups of consecutive stages between rest days,
grouped in the sidebar by country. Each chapter includes:

- An **interactive route map** on a topographic background
- A **sequential elevation profile** across all stages in the block
- A **stage-by-stage table** with distance, elevation, and riding time

## Data

GPS tracks, heart rate, and effort data from [Strava](https://www.strava.com).
Stage routes and dates follow the TDA Global Cycling official itinerary.
Map tiles © [OpenTopoMap](https://opentopomap.org) (CC-BY-SA).
"""


def _strava_page(blocks: list[dict], stages_by_block: dict) -> str:
    sections = []
    for block in blocks:
        bid    = block["block_id"]
        stages = [s for s in stages_by_block.get(bid, []) if s.get("activity_id")]
        if not stages:
            continue
        title  = _clean_label(block["route_label"])
        embeds = []
        for s in stages:
            aid = s["activity_id"]
            d   = date.fromisoformat(s["date"]).strftime("%-d %b")
            embeds.append(
                f"**Stage {s['stage']} · {d} · {s['depart']} → {s['arrive']}**\n\n"
                f"```{{raw}} html\n"
                f'<iframe allowtransparency="true" frameBorder="0" scrolling="no"'
                f' src="https://www.strava.com/activities/{aid}/embed/{aid}"'
                f' width="100%" height="405"></iframe>\n'
                f"```"
            )
        sections.append(f"## {title}\n\n" + "\n\n".join(embeds))

    return "# Strava Rides\n\n" + "\n\n".join(sections) + "\n"


def main() -> None:
    SECTIONS_DIR.mkdir(parents=True, exist_ok=True)
    blocks          = _load_blocks()
    stages_by_block = _load_stages_by_block()

    for block in blocks:
        bid     = block["block_id"]
        stages  = stages_by_block.get(bid, [])
        content = _block_page(block, stages)
        out     = SECTIONS_DIR / f"{bid}.md"
        out.write_text(content)
        print(f"  {out}")

    intro = _intro_page(blocks, stages_by_block)
    out   = CONTENT_DIR / "intro.md"
    out.write_text(intro)
    print(f"  {out}")

    strava = _strava_page(blocks, stages_by_block)
    out    = CONTENT_DIR / "strava_rides.md"
    out.write_text(strava)
    print(f"  {out}")

    print("Done.")


if __name__ == "__main__":
    main()
