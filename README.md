# North American Epic 2025 (NAE25)

Jupyter Book documenting a bicycle journey from Puerto Vallarta, Mexico to Panama City, Panama —
Stages 83–128 of the TDA Global Cycling North American Epic, ridden as a sectional participant
from 25 October to 21 December 2025.

46 riding days · 12 rest days · 7 countries · ~4,600 km

## Build

```bash
pip install -r requirements.txt

# Download Strava activity data
python -m scripts.processing.strava_sync

# Regenerate maps and elevation profiles
python -m scripts.visualization.render_blocks

# Regenerate section pages
python -m scripts.build_pages

# Build the book
jupyter-book build .
```

## Project layout

```
data/raw/activities/     # per-activity JSON from Strava (gitignored)
data/processed/          # stages.csv, blocks.csv
content/sections/        # generated block pages (one per block)
content/maps/            # generated folium maps and elevation PNGs
scripts/processing/      # strava_sync, blocks, stages
scripts/visualization/   # render_blocks
scripts/build_pages.py   # page generator
_config.yml / _toc.yml  # Jupyter Book config
```

## Credentials

Strava OAuth token is read from `~/.strava_mcp_token.json` (shared with the Strava MCP server).
`STRAVA_CLIENT_ID` and `STRAVA_CLIENT_SECRET` must be set in `.env`.
