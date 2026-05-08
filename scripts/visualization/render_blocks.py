"""
Generate route maps and elevation profiles for each NAE25 block.

Outputs written to content/maps/:
  block_<low>_<high>_map.html      — interactive folium route map (topo tiles)
  block_<low>_<high>_elevation.png — single-panel sequential elevation profile

Gap handling: between consecutive stages the haversine distance from stage N's
last GPS point to stage N+1's first GPS point is drawn as a dashed gray
connector. For complete stages this gap is a few hundred metres and nearly
invisible; for partial stages (e.g. joined mid-ride) it is proportional to
the unridden distance.

Usage:
    python -m scripts.visualization.render_blocks
    python -m scripts.visualization.render_blocks --block block_083_085
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.processing.blocks import get_all_blocks

RAW_DIR    = Path("data/raw/activities")
MAPS_DIR   = Path("content/maps")
STAGES_CSV = Path("data/processed/stages.csv")

# ColorBrewer Set1 — good categorical contrast on both map and chart
PALETTE = [
    "#e41a1c", "#377eb8", "#4daf4a", "#984ea3",
    "#ff7f00", "#a65628", "#f781bf", "#666666",
]

TOPO_TILES = "https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"
TOPO_ATTR  = (
    'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
    'contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | '
    'Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a> '
    '(<a href="https://creativecommons.org/licenses/by-sa/3.0/">CC-BY-SA</a>)'
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_km(p1: list, p2: list) -> float:
    R = 6371.0
    lat1, lon1 = math.radians(p1[0]), math.radians(p1[1])
    lat2, lon2 = math.radians(p2[0]), math.radians(p2[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.asin(math.sqrt(a))


def _load_stages_by_block() -> dict[str, list[dict]]:
    by_block: dict[str, list[dict]] = {}
    with STAGES_CSV.open() as f:
        for row in csv.DictReader(f):
            by_block.setdefault(row["block_id"], []).append(row)
    return by_block


def _activity_file(row: dict) -> Path | None:
    aid = (row.get("activity_id") or "").strip()
    if aid:
        hits = list(RAW_DIR.glob(f"*_{aid}.json"))
        if hits:
            return hits[0]
    hits = list(RAW_DIR.glob(f"{row['date']}_*.json"))
    return max(hits, key=lambda p: p.stat().st_size) if hits else None


def _streams(path: Path) -> dict:
    return json.loads(path.read_text()).get("streams") or {}


def _stage_streams(row: dict) -> tuple[list, list, list] | None:
    """Return (dist_m, alt, latlng) arrays for a stage row, or None."""
    f = _activity_file(row)
    if not f:
        return None
    s = _streams(f)
    dist_m = (s.get("distance") or {}).get("data") or []
    alt    = (s.get("altitude")  or {}).get("data") or []
    latlng = (s.get("latlng")   or {}).get("data") or []
    n = min(len(dist_m), len(alt), len(latlng))
    if not n:
        return None
    return dist_m[:n], alt[:n], latlng[:n]


# ---------------------------------------------------------------------------
# Route map (folium, OpenTopoMap tiles)
# ---------------------------------------------------------------------------

def build_map(block: dict, stages: list[dict]) -> folium.Map | None:
    tracks: list[tuple] = []
    all_coords: list[list] = []

    for i, row in enumerate(stages):
        result = _stage_streams(row)
        if not result:
            continue
        _, _, latlng = result
        color = PALETTE[i % len(PALETTE)]
        all_coords.extend(latlng)
        tracks.append((row, latlng, color))

    if not tracks:
        return None

    lats = [c[0] for c in all_coords]
    lngs = [c[1] for c in all_coords]

    m = folium.Map(tiles=TOPO_TILES, attr=TOPO_ATTR)

    for row, latlng, color in tracks:
        tip = f"Stage {row['stage']}: {row['depart']} → {row['arrive']}"
        # White stroke underneath makes the colored line pop against topo background
        folium.PolyLine(latlng, color="white", weight=7, opacity=0.9).add_to(m)
        folium.PolyLine(latlng, color=color, weight=4.5, opacity=0.95, tooltip=tip).add_to(m)
        folium.CircleMarker(
            latlng[0], radius=6, color="white", weight=2, fill=True,
            fill_color=color, fill_opacity=1.0, tooltip=row["depart"],
        ).add_to(m)
        folium.CircleMarker(
            latlng[-1], radius=6, color="white", weight=2, fill=True,
            fill_color="white", fill_opacity=0.9, tooltip=row["arrive"],
        ).add_to(m)

    m.fit_bounds([[min(lats), min(lngs)], [max(lats), max(lngs)]])
    return m


# ---------------------------------------------------------------------------
# Sequential elevation profile (single panel)
# ---------------------------------------------------------------------------

def build_elevation(block: dict, stages: list[dict]) -> plt.Figure:
    """
    Single-panel profile with stages plotted sequentially.
    Gaps between stage end and next stage start are shown as dashed gray
    connectors spanning the haversine distance between the two GPS points.
    """
    fig, ax = plt.subplots(figsize=(14, 4))
    fig.suptitle(block["route_label"], fontsize=13, fontweight="bold")

    x_cursor      = 0.0
    prev_latlng_end = None
    prev_alt_end    = None
    legend_handles  = []

    for i, row in enumerate(stages):
        color  = PALETTE[i % len(PALETTE)]
        result = _stage_streams(row)

        if result is None:
            continue

        dist_m, alt, latlng = result

        # --- Gap connector from previous stage end to this stage start ---
        if prev_latlng_end is not None:
            gap_km = _haversine_km(prev_latlng_end, latlng[0])
            if gap_km >= 0.1:
                ax.plot(
                    [x_cursor, x_cursor + gap_km],
                    [prev_alt_end, alt[0]],
                    color="#888888", linewidth=1.0, linestyle="--",
                    alpha=0.7, zorder=1,
                )
                x_cursor += gap_km

        # --- Vertical stage separator (skip first) ---
        if i > 0:
            ax.axvline(x=x_cursor, color="#aaaaaa", linestyle=":", linewidth=0.8, zorder=1)

        # --- Stage label just above the x-axis ---
        ax.text(
            x_cursor + 0.3, 0, f"S{row['stage']}",
            fontsize=7, color=color, va="bottom", ha="left",
            transform=ax.get_xaxis_transform(), clip_on=True,
        )

        # --- Plot stage elevation ---
        step = max(1, len(dist_m) // 2000)
        d = [x_cursor + m / 1000 for m in dist_m[::step]]
        a = alt[::step]

        line, = ax.plot(d, a, color=color, linewidth=1.5, zorder=2)

        dist_km   = dist_m[-1] / 1000
        elev_gain = float(row["elevation_m"]) if row.get("elevation_m") else 0
        legend_handles.append((
            line,
            f"S{row['stage']}  {row['depart']} → {row['arrive']}  "
            f"({dist_km:.0f} km  +{elev_gain:.0f} m)",
        ))

        x_cursor       += dist_m[-1] / 1000
        prev_latlng_end = latlng[-1]
        prev_alt_end    = alt[-1]

    ax.legend(
        [h for h, _ in legend_handles],
        [l for _, l in legend_handles],
        fontsize=7.5, loc="upper left",
        framealpha=0.85, ncol=max(1, len(legend_handles) // 4),
    )
    ax.set_xlabel("Cumulative distance (km)", fontsize=9)
    ax.set_ylabel("Elevation (m)", fontsize=9)
    ax.grid(True, alpha=0.18, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--block", metavar="BLOCK_ID",
                    help="Render only this block (e.g. block_083_085)")
    args = ap.parse_args()

    MAPS_DIR.mkdir(parents=True, exist_ok=True)
    blocks = get_all_blocks()
    stages_by_block = _load_stages_by_block()

    for block in blocks:
        bid = block["block_id"]
        if args.block and bid != args.block:
            continue
        stages = stages_by_block.get(bid, [])
        if not stages:
            print(f"  {bid}: no stages — skipping")
            continue

        print(f"\n{bid}  {block['route_label']}")

        m = build_map(block, stages)
        if m:
            out = MAPS_DIR / f"{bid}_map.html"
            m.save(str(out))
            print(f"  map  → {out}")

        fig = build_elevation(block, stages)
        out = MAPS_DIR / f"{bid}_elevation.png"
        fig.savefig(out, dpi=150, bbox_inches="tight")
        plt.close(fig)
        print(f"  elev → {out}")

    print("\nDone.")


if __name__ == "__main__":
    main()
