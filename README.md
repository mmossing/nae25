# North American Epic 2025 (NAE25)

A Jupyter Book documenting a 17,000+ km bicycle journey from Tuktoyaktuk, Canada to Panama City, Panama.

**Journey:** July 10 - December 21, 2025  
**Stages:** 128 riding days + 33 rest days  
**Tour Operator:** TDA Global Cycling

## Project Structure

```
nae25/
├── content/              # Jupyter Book content
│   ├── sections/        # Geographic sections (Arctic Canada, Yukon, etc.)
│   ├── stages/          # Individual stage pages (auto-generated)
│   ├── maps/            # Interactive and static maps
│   ├── analysis/        # Data analysis notebooks
│   └── media/           # Photo galleries and videos
├── data/
│   ├── raw/             # Raw data from Strava, photos, GPX files
│   └── processed/       # Processed daily/weekly summaries
├── scripts/
│   ├── agents/          # Claude Code agents for automation
│   ├── processing/      # Data processing utilities
│   └── visualization/   # Mapping and chart generation
├── assets/              # Static assets
└── notebooks/           # Jupyter notebooks for analysis
```

## Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy `.env.example` to `.env` and add your credentials:
```bash
cp .env.example .env
```

Required API keys:
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`

### 3. Build the Book

```bash
# Clean build
jupyter-book clean content/
jupyter-book build content/

# Serve locally
cd content/_build/html && python -m http.server
```

## Daily Workflow (with Claude Code)

The agent-based workflow processes daily ride data:

```bash
# Run daily agent (processes latest Strava activity)
python scripts/agents/daily_processor.py

# Or manual processing
python scripts/processing/strava_sync.py --date 2025-10-29
python scripts/processing/generate_stage.py --stage 86
```

## Features

- **Real-time updates**: Build the book progressively as the tour progresses
- **Strava integration**: Automatic activity sync and analysis
- **Interactive maps**: Folium maps with route visualization
- **Photo galleries**: Organized by stage and section
- **Statistical analysis**: Distance, elevation, weather, and performance metrics
- **Agent automation**: Claude Code agents for daily processing

## Development

```bash
# Watch mode for development
jupyter-book build content/ --builder html --all

# Deploy to GitHub Pages (automated via Actions)
git push origin main
```

## Current Status

**Last Updated:** October 29, 2025  
**Current Location:** Ocotlán, Jalisco, Mexico  
**Stage Completed:** 86/128  
**Distance Covered:** ~9,500 km

## Links

- **Live Book:** [Coming Soon]
- **GitHub Repository:** [Coming Soon]
- **Previous Tour (SAE24):** [Link to SAE24 book]

## License

MIT License - see LICENSE file for details
