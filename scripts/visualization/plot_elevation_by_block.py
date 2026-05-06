#!/usr/bin/env python3
"""Plot cumulative elevation profiles grouped by expedition block.

Reads a blocks CSV (must have columns: id, Block, name, start_date_local),
loads per-activity stream JSON files, and saves one elevation PNG per block.

Stream JSON files are expected at: <streams_dir>/activity_<id>.json
Output files are written to: <output_dir>/block_<N>_elevation.png

Stream files written by strava_client.py are valid JSON.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = ["red", "blue", "green", "purple", "orange", "darkred"]
MIN_ELEVATION_AXIS = 1000  # metres; applied when block max is below this


def load_stream(path: Path) -> dict | None:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(raw)
    except (SyntaxError, ValueError) as exc:
        print(f"  warning: could not parse {path.name}: {exc}")
        return None


def plot_block(block_id: int | str, group: pd.DataFrame, streams_dir: Path, output_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6))
    cumulative_km = 0.0
    all_elevations: list[float] = []

    for idx, row in enumerate(group.itertuples()):
        stream_path = streams_dir / f"activity_{row.id}.json"
        if not stream_path.exists():
            print(f"  missing: {stream_path.name}")
            continue

        data = load_stream(stream_path)
        if data is None or "altitude" not in data or "distance" not in data:
            print(f"  skipping {stream_path.name}: altitude/distance data not found")
            continue

        elevation = np.array(data["altitude"]["data"])
        distances = np.array(data["distance"]["data"]) / 1000.0  # m → km
        distances += cumulative_km
        cumulative_km = float(distances[-1])

        all_elevations.extend(elevation.tolist())
        color = COLORS[idx % len(COLORS)]
        ax.plot(distances, elevation, color=color, alpha=0.7, linewidth=2.5, label=row.name)

    if all_elevations and max(all_elevations) < MIN_ELEVATION_AXIS:
        ax.set_ylim(0, MIN_ELEVATION_AXIS)

    ax.set_title(f"Elevation Profile — Block {block_id}", fontsize=16)
    ax.set_xlabel("Cumulative Distance (km)", fontsize=14)
    ax.set_ylabel("Elevation (m)", fontsize=14)
    ax.legend(fontsize="large", loc="best")
    ax.grid(True)

    out_path = output_dir / f"block_{block_id}_elevation.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  saved {out_path}")


def run(csv_path: Path, streams_dir: Path, output_dir: Path, blocks: list[int] | None) -> int:
    df = pd.read_csv(csv_path)
    df["start_date_local"] = pd.to_datetime(df["start_date_local"])

    output_dir.mkdir(parents=True, exist_ok=True)

    grouped = df.groupby("Block")
    targets = blocks if blocks else sorted(grouped.groups.keys())

    for block_id in targets:
        if block_id not in grouped.groups:
            print(f"block {block_id}: not found in CSV, skipping")
            continue
        group = grouped.get_group(block_id)
        print(f"block {block_id}: {len(group)} rides")
        plot_block(block_id, group, streams_dir, output_dir)

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--csv", default="data/blocks.csv", help="Blocks CSV file (default: data/blocks.csv)")
    p.add_argument("--streams-dir", default="data/raw/strava/streams", help="Directory containing activity_<id>.json files (default: data/raw/strava/streams)")
    p.add_argument("--output-dir", default="assets/exports/elevation", help="Directory for output PNGs (default: assets/exports/elevation)")
    p.add_argument("--blocks", nargs="*", type=int, metavar="N", help="Only plot these block numbers (default: all)")
    return p


def main() -> int:
    args = build_parser().parse_args()
    return run(
        csv_path=Path(args.csv),
        streams_dir=Path(args.streams_dir),
        output_dir=Path(args.output_dir),
        blocks=args.blocks or [],
    )


if __name__ == "__main__":
    raise SystemExit(main())
