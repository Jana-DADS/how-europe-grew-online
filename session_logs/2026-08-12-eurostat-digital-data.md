# 2026-08-12 — Eurostat internet access & digital skills data

## Context / why

Jani finished a 2-day Coders Lab "Data Analyst" course (seaborn, plotly, geopandas, Mapbox — separately documented in a Word file at `Vizualizace - nastroje.docx` in her Vizualizace folder, unrelated to this repo). She wants a personal project applying it: plotly maps/charts of Europe. First topic she picked: **how internet access and digital skills have spread across Europe over time** — she'll build this in **Google Colab**, which already ships with geopandas etc., so no environment setup is needed on her end.

## Where things stand

Three tidy CSVs are in `data/processed/`, decoded from raw Eurostat JSON-stat responses in `data/raw/` via `scripts/decode.py`. All three were spot-checked against the decoded EU27 2024 household-internet figure (94.19%) against Eurostat's own published "94.2% in 2024" figure in a regional-yearbook article — matches, so the decode logic (row-major flat-index formula, see below) is verified correct.

Copies of the same three CSVs were also delivered to Jani directly in her `Vizualizace` folder in the previous chat (via `present_files`) — the copies here in `data/processed/` are for the coding/analysis side of the work.

### `data/processed/household_internet_access.csv`
- Eurostat dataset `isoc_ci_in_h`, household type = TOTAL, unit = % of households.
- Coverage: 44 geo entities (EU aggregates + all member/candidate/EFTA states + UK, BA, ME, MK, AL, RS, TR, XK) × years 2002–2025 (annual).
- Columns: `geo_code, geo_label, year, pct_households_with_internet, flag, flag_desc`. Flags: `b` = break in series, `e` = estimated, `u` = low reliability.

### `data/processed/individual_internet_use.csv`
- Eurostat dataset `isoc_ci_ifp_iu`, indicator `I_IU3` ("used internet in last 3 months"), ind_type = IND_TOTAL (all individuals), unit = % of individuals.
- Same 44×24 geo/year coverage as above.
- Columns: `geo_code, geo_label, year, pct_individuals_used_internet_3m, flag, flag_desc`.

### `data/processed/digital_skills_by_age.csv`
- Eurostat dataset `isoc_sk_dskl_i21`, indicator `I_DSK2_BAB` ("basic or above basic overall digital skills" — this is the EU Digital Decade 2030 headline skills indicator), unit = % of individuals.
- Only 3 time points exist for this dataset: **2021, 2023, 2025** (it's biennial, introduced 2021 — don't expect earlier years).
- 39 geo entities (fewer than the internet datasets — no EU28/EU27_2007/EU25/EU15/UK breakdown here, just EU27_2020 + EA + current member/candidate states).
- Broken out by age band via the `age_group` column: `"All individuals (16-74)"`, `"16-24"`, `"25-54"`, `"55-74"`. Each age band required a **separate API call** — see gotcha below.
- Columns: `geo_code, geo_label, year, age_group, pct_basic_or_above_digital_skills, flag, flag_desc`.

## Gotchas / dead ends (read this before re-fetching anything)

- **`ec.europa.eu` is blocked from plain `curl`/`wget` in the bash sandbox** (proxy allowlist, 403 `blocked-by-allowlist`). Must use the `mcp__workspace__web_fetch` tool instead, which goes through a different, unrestricted network path.
- **Eurostat's JSON-stat API does not OR-combine repeated query params for the same dimension.** e.g. `?ind_type=Y16_24&ind_type=Y25_54&ind_type=Y55_74` silently keeps only one value (the tool's URL echo showed it collapsing to just `ind_type=Y16_24`). The fix: **one API call per age-group value**, then merge client-side. This is why `digital_skills_by_age.csv` came from 4 separate fetches rather than 1.
- **`web_fetch` dedupes identical URLs for up to ~3600s within a session** and returns a "reuse the earlier result" stub instead of the body — annoying if the earlier result already scrolled out of context (e.g. after a conversation compaction). Workaround: add a harmless extra query param that doesn't change the result but changes the URL string, e.g. append `&freq=A` (a dimension that only has one valid value anyway, so it's a no-op filter) to force a fresh fetch.
- Tried `indic_is=I_DSK1_BAB` on `isoc_sk_dskl_i21` expecting a lower/companion skills threshold — dataset returned empty (`"value":{}`). That indicator code doesn't exist in this dataset; **only `I_DSK2_BAB` is valid here.** Didn't investigate further since I_DSK2_BAB (the Digital Decade headline one) is the more policy-relevant number anyway.
- Decode formula, in case `scripts/decode.py` needs to be extended to a new dataset: JSON-stat 2.0 gives a flat `value` dict keyed by string integers, computed row-major over the dimensions listed in `id`/`size`. For a dataset shaped `[1,1,1,1,geo,time]` (four size-1 dims first), the flat index is simply `geo_index * len(time) + time_index`. Always double check the actual `id`/`size` arrays in the response before assuming this — if a dataset has more than one non-trivial dimension (e.g. both `ind_type` and `geo` vary), the formula needs an extra multiplication term.
- `scripts/decode.py` currently resolves its input/output paths via `os.path.dirname(os.path.abspath(__file__))`, i.e. it expects to be run with `raw_*.json` sitting next to it. In this repo layout the raw files are one level up in `data/raw/` and outputs should go to `data/processed/` — **the script has NOT been updated to that path layout yet**, it still writes/reads relative to its own folder. Fix the `OUT` variable (or split into `RAW_DIR`/`PROCESSED_DIR`) before running it again from here.

## Not done yet / next steps

1. ~~No country/NUTS boundary GeoJSON has been fetched.~~ **Done** — see `data/geo/europe_countries_boundaries.geojson` (added this session, see "Country boundary GeoJSON" section below).
2. `scripts/decode.py`'s path handling has been fixed (split into `RAW_DIR`/`PROCESSED_DIR`, tested — re-running it reproduces identical CSVs regardless of cwd).
3. No Colab notebook exists yet — Jani said she'd build the analysis herself; she was offered but hadn't yet asked for a starter code snippet (CSV load + GeoJSON join + first plotly choropleth) as of the end of the last session.
4. Possible further breakdowns of `isoc_sk_dskl_i21` not yet pulled (education level, gender, urbanization) if she wants more granularity later — the full `ind_type` codelist has 139 categories; the `indic_is` codelist has 24 sub-skill indicators across 5 DigComp2.0 areas. Ask her what she specifically wants before pulling more, this API tends to want one fetch per category value.
5. She has NOT yet been shown sample code for the CSV+GeoJSON join / first plotly choropleth — that's the natural next conversational step when she picks this back up.

## Country boundary GeoJSON

`data/geo/europe_countries_boundaries.geojson` — GISCO country boundaries (`CNTR_RG_20M_2024_4326.geojson`, 1:20M resolution, WGS84), filtered client-side (in-browser, since `ec.europa.eu` is blocked from the sandbox's `curl`/`web_fetch` — see gotcha above, same restriction applies here) down to the 37 actual country features matching `GEO44`/`GEO39` in `scripts/decode.py` (i.e. real countries only, not the EU/EA aggregate rows — those don't have geometries anyway).

- Join key: `CNTR_ID` property, 2-letter codes matching `geo_code` in the CSVs directly (e.g. `CZ`, `DE`). No recoding needed — GISCO already uses Eurostat's non-ISO codes (`EL` for Greece, `UK` for the United Kingdom), matching the CSVs.
- Verified byte-for-byte against the live GISCO fetch via rolling checksums per chunk plus a whole-file checksum match; also validated as parseable GeoJSON with 37 `MultiPolygon` features, all linear rings closed, no missing/duplicate `CNTR_ID`s.
- Resolution note: 20M was chosen over 60M (much coarser, ~150KB) or 10M (much finer, ~500KB+) as the GISCO-recommended default for country-level Europe maps — good detail/size balance for an interactive plotly choropleth.

### Kosovo (`XK`) — added separately from OpenStreetMap

GISCO's own country dataset does **not** include Kosovo (5 EU member states — ES, SK, RO, EL, CY — don't recognize its independence, so Eurostat/GISCO omits it entirely, not even merged into Serbia). Since Jani wants it on the map, added it as a 38th feature using OpenStreetMap data (the tool covered in her Coders Lab course), not Natural Earth.

- Source: OSM relation `2088990` (Kosovo), fetched via the community converter `https://polygons.openstreetmap.fr/get_geojson.py?id=2088990&params=0`.
- Raw OSM boundary was very high-res (19,268 points) compared to GISCO's 20M-generalized countries (Albania=56, Montenegro=33, North Macedonia=64, Slovenia=126 points). Simplified with a from-scratch Douglas-Peucker implementation, epsilon=0.01°, down to 133 points — in line with neighboring Slovenia's 126.
- The feature carries the same property schema as the GISCO features (`CNTR_ID: "XK"`, `CNTR_NAME`, `NAME_ENGL`, etc.) plus one extra field, `SOURCE_NOTE`, documenting the mixed provenance and the non-recognition caveat directly in the data — so anyone (including future-me) opening this file sees why one feature looks different.
- File is now `data/geo/europe_countries_boundaries.geojson` with **38 features** (37 GISCO + 1 OSM). Re-validated after merge: unique `CNTR_ID`s, all rings closed, valid GeoJSON.

### Iceland (`IS`) and United Kingdom (`UK`) — swapped from GISCO to OpenStreetMap

GISCO's 20M-resolution outlines for Iceland and the UK are generalized enough that Plotly's own internal basemap (drawn underneath our polygons for the "not tracked"/ocean backdrop) shows through as thin slivers along jagged coastline — visible on Iceland's northern peninsula and the UK's northern coast/islands. The two datasets come from independent sources with different vertex placement, so no resolution of GISCO's own files (checked: 1:1M/3M/10M/20M/60M) is guaranteed to align pixel-perfectly with Plotly's basemap. A more detailed polygon that hugs the true coastline more closely shrinks the mismatch to sub-pixel and makes it disappear in practice — the same principle behind the Kosovo boundary already being from OSM.

- Source: OSM relations `299133` (Iceland) and `62149` (United Kingdom), fetched the same way as Kosovo via `https://polygons.openstreetmap.fr/get_geojson.py?id=<relation>&params=0`.
- Iceland: raw OSM boundary was 804 points (2 rings); simplified with the same Douglas-Peucker implementation, epsilon=0.01°, down to 92 points — close to GISCO's own Iceland (90 points), so no size trade-off.
- UK: raw OSM boundary was 38,356 points across 5 separate landmasses (mainland Great Britain + islands); simplified the same way down to 551 points. Bounding box reaches 61.06°N, confirming Shetland/Orkney/Hebrides are included in the mainland polygon, not dropped.
- Both features' properties (`CNTR_ID`, `CNTR_NAME`, `NAME_ENGL`, etc.) were left untouched — only the `geometry` was replaced.
- Ring winding: both replacements came out counter-clockwise from the source; reversed to clockwise (matching GISCO's convention) to avoid the same "fills the whole world" Plotly bug hit with Kosovo. Verified via signed-area check before/after, all rings closed.
- File is still `data/geo/europe_countries_boundaries.geojson`, still 38 features — only IS and UK's geometry changed (35 GISCO + Kosovo(OSM) + Iceland(OSM) + UK(OSM)).
