"""Download Strava ride activities for the NAE25 date range.

Usage:
    python -m scripts.processing.strava_sync
    python -m scripts.processing.strava_sync --start 2025-10-25 --end 2025-12-21
    python -m scripts.processing.strava_sync --refresh       # re-download existing files
    python -m scripts.processing.strava_sync --skip-streams  # summaries only (no GPS/HR)
"""

from __future__ import annotations

import argparse
import asyncio
import json
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path

import httpx

from scripts.strava_auth import strava_get

DATA_DIR = Path(__file__).parents[2] / "data"
RAW_DIR = DATA_DIR / "raw" / "activities"
PROCESSED_DIR = DATA_DIR / "processed"

RIDE_TYPES = {"Ride", "VirtualRide", "EBikeRide", "GravelRide", "MountainBikeRide"}
STREAM_KEYS = "time,latlng,altitude,heartrate,velocity_smooth,cadence"

# 10 s between calls keeps us well under Strava's 100 req / 15 min limit.
CALL_DELAY = 10


async def _get(path: str, params: dict | None = None) -> object:
    """Strava GET with one automatic retry on 429."""
    for attempt in range(2):
        try:
            return await strava_get(path, params)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 429 and attempt == 0:
                print("  Rate limited — sleeping 15 min …")
                await asyncio.sleep(900)
            else:
                raise


async def _list_rides(after_ts: int, before_ts: int) -> list[dict]:
    rides: list[dict] = []
    page = 1
    while True:
        batch = await _get("/athlete/activities", {
            "after": after_ts, "before": before_ts,
            "per_page": 200, "page": page,
        })
        if not batch:
            break
        for act in batch:
            sport = act.get("sport_type") or act.get("type") or ""
            if sport in RIDE_TYPES:
                rides.append(act)
        page += 1
        await asyncio.sleep(CALL_DELAY)
    return rides


async def _download_one(act: dict, refresh: bool, skip_streams: bool) -> None:
    activity_id = act["id"]
    act_date = act["start_date_local"][:10]
    out_path = RAW_DIR / f"{act_date}_{activity_id}.json"

    if out_path.exists() and not refresh:
        print(f"  skip  {out_path.name}")
        return

    print(f"  fetch {out_path.name} …", end=" ", flush=True)

    await asyncio.sleep(CALL_DELAY)
    detail = await _get(f"/activities/{activity_id}", {"include_all_efforts": "false"})

    streams: dict = {}
    if not skip_streams:
        await asyncio.sleep(CALL_DELAY)
        try:
            streams = await _get(
                f"/activities/{activity_id}/streams",
                {"keys": STREAM_KEYS, "key_by_type": "true"},
            )
        except httpx.HTTPStatusError as exc:
            print(f"(streams {exc.response.status_code}) ", end="")

    out_path.write_text(json.dumps({"summary": detail, "streams": streams}, indent=2))
    gps_pts = len((streams.get("latlng") or {}).get("data") or [])
    print(f"ok ({gps_pts} GPS pts)")


async def _run(start: date, end: date, refresh: bool, skip_streams: bool) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    after_ts = int(datetime.combine(start, time(), tzinfo=timezone.utc).timestamp())
    before_ts = int(datetime.combine(end + timedelta(days=1), time(), tzinfo=timezone.utc).timestamp())

    print(f"Listing rides {start} → {end} …")
    rides = await _list_rides(after_ts, before_ts)
    print(f"Found {len(rides)} ride(s)\n")

    for act in sorted(rides, key=lambda a: a["start_date_local"]):
        await _download_one(act, refresh, skip_streams)

    print("\nBuilding stage/block index …")
    from scripts.processing.stages import build_mapping
    build_mapping()
    print("Done.")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--start", default="2025-10-25", metavar="YYYY-MM-DD",
                    help="First day to fetch, inclusive (default: 2025-10-25)")
    ap.add_argument("--end", default="2025-12-21", metavar="YYYY-MM-DD",
                    help="Last day to fetch, inclusive (default: 2025-12-21)")
    ap.add_argument("--refresh", action="store_true",
                    help="Re-download files that already exist")
    ap.add_argument("--skip-streams", action="store_true",
                    help="Skip GPS/HR stream download (summaries only)")
    args = ap.parse_args()

    asyncio.run(_run(
        date.fromisoformat(args.start),
        date.fromisoformat(args.end),
        args.refresh,
        args.skip_streams,
    ))


if __name__ == "__main__":
    main()
