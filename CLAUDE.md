# Geospatial

Jani's personal data-visualization project: interactive plotly maps/charts of Europe, built in Google Colab (which already has geopandas/shapely preinstalled, no extra setup needed there).

Start here, then read the latest file in `session_logs/` for full context of where things stand.

## Global rules apply here too

`Github/CLAUDE.md` (one level up from this repo, in `Documents\Claude\Github\`) holds cross-project rules that apply to Geospatial as well: language, writing style (no em dashes), chart-axis conventions, "discuss before rewriting code," and more. If that folder isn't among your connected folders this session, ask Jana for access to it (or to the whole `Documents\Claude\Github\` folder) before assuming those rules don't apply, rather than waiting for her to remind you.

## Layout

- `data/raw/`: untouched JSON-stat 2.0 responses as fetched from the Eurostat API (kept for reproducibility / re-decoding if the CSV schema needs to change).
- `data/processed/`: tidy CSVs ready to load in Colab with `pandas.read_csv()`.
- `scripts/decode.py`: decodes the JSON-stat 2.0 files in `data/raw/` into the CSVs in `data/processed/`. Run with `python3 scripts/decode.py` from the repo root (it resolves paths relative to its own location... actually currently hardcoded to its own directory, see note in session log).
- `session_logs/`: dated notes on what happened each session, in reverse-chronological relevance (read the newest first).

## Current topic

First theme: Eurostat data on internet access and digital activities across Europe (2002–2025), for maps/charts of "how connectivity and digital participation have spread over time." Eurostat's own name for the skills dataset is "digital skills," but the project deliberately says "digital activities" in its own writing; see the README's data-sources section for why. See `session_logs/2026-08-12-eurostat-digital-data.md` for dataset details, exact API queries used, and what's still open (country/NUTS boundary GeoJSON for the map join hasn't been fetched yet).
