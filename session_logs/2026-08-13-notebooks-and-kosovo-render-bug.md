# 2026-08-13 — Colab notebooks built, Kosovo render/hover bug solved

Continues [[2026-08-12-eurostat-digital-data]] (data collection, GeoJSON assembly).
That log still holds for anything about the Eurostat API, `scripts/decode.py`, or how
the boundary file was originally built.

## Where things stand

Nothing is in git yet — **the repo has still never been pushed**, at Jana's explicit
instruction ("zatím nedávej na GitHub, až bude vše hotové a odsouhlasíme si to"). Everything
below is on local disk only, all of it reviewed and accepted by Jana in Colab.

Working tree, all current and tested end-to-end:

- `notebooks/Digitalization.ipynb` — household internet access, animated 2002–2025 (17 cells)
- `notebooks/DigitalSkills.ipynb` — digital skills, 3×4 button grid year × age group (11 cells)
- `data/geo/europe_countries_boundaries.geojson` — 38 features, **Iceland and UK geometry replaced this session** (see below)
- `data/processed/digitalization_vs_skills_comparison.csv` — new this session
- `README.md` — updated with the boundary provenance and the Kosovo render-bug writeup
- Leftover `data_test*` scratch folders in the repo root — Jana said she'll delete them herself at the end, deliberately not cleaned up

Testing method used throughout, worth reusing: extract every code cell except the
`google.colab` upload cells into a plain `.py`, replace `fig.show()` with a print,
run it against copies of the real CSVs/GeoJSON in `/tmp`. Catches import errors,
NameErrors, and lets you assert on figure structure (`fig.frames[i].data[t].z`) —
but **cannot catch rendering or hover behaviour**, which is exactly where this
session's hardest bug lived. Jana testing in real Colab was the only way to see it.

## The Kosovo bug — three hypotheses, two of them wrong

Highest-value section of this log. The symptom went through several disguises and
two confident-but-wrong diagnoses before the real cause surfaced.

**Root fact underneath all of it:** GISCO draws Serbia with *no hole cut out for
Kosovo* (it doesn't recognise Kosovo's independence — same reason Kosovo is absent
from GISCO entirely and had to come from OSM). Verified with shapely:
Kosovo's polygon overlaps Serbia's by **99.2%** of Kosovo's area. Kosovo is the only
country in the dataset whose shape lies inside another country's — every other
border in Europe merely touches. So Kosovo is the only country that can exhibit this
class of bug, which is why "why only Kosovo?" was the right question to keep asking.

### Hypothesis 1 (wrong): the invisible overlay trace was blocking hover

Theory: the amber "no data yet" trace sits on top and swallows hover even where
it's transparent. **Disproven** — it doesn't explain why hover worked fine in
2007–2016, and the amber trace is present in all years.

### Hypothesis 2 (wrong): animation frames changing their `locations` list

Theory: because the data trace omitted countries before their first data year, the
`locations` array changed length between frames, and plotly lost track of which
polygon was which. Rebuilt both traces to use one fixed, constant country list in
every frame (values become `None` instead of the country being dropped).
**Disproven by Jana's testing** — behaviour was completely unchanged.

That rebuild was kept anyway; it's cleaner and it's what the current code does. But
it was not the fix.

### Hypothesis 3 (correct): draw order and hover order run in opposite directions

Jana's precise bug report is what cracked it. Hover on Kosovo:

| years | Serbia | Kosovo | hover showed |
|---|---|---|---|
| 2002–2006 | no data | no data | **Serbia** |
| 2007–2016 | has data | no data | **Kosovo** ✓ |
| 2017–2025 | has data | has data | **Serbia** |

It works *only* when the two countries are in **different traces**. Within one
trace, Serbia always wins. Reading plotly's `choropleth/hover.js` confirms why:

```js
for(i = 0; i < cd.length; i++) {
    ...
    if(isInside) break;   // first match in locations order wins
}
```

Hover walks `locations` in order and **stops at the first** polygon containing the
cursor. Fill, meanwhile, draws in the same order, so the **last** one wins and
covers everything before it. Sorted alphabetically, `RS` (index 31) precedes
`XK` (index 37) — so Serbia was reached first by hover, and Kosovo, drawn last,
was visible but unreachable.

Moving `XK` to the front of the list fixed hover — **and immediately broke the
fill**: Kosovo was now drawn first, so Serbia painted over it. Jana caught this in
one round ("Kosovo splyne se Srbskem a dokonce přebírá jeho hodnoty"). There is
**no ordering within a single trace that satisfies both rules.**

**The fix:** give Kosovo its own pair of traces (data + amber), added *after* the
main ones. Later traces both draw on top and take hover priority, so Kosovo is
correct on both counts. Main traces now carry the other 37 countries; `MAIN_COUNTRIES`
/ `countries_age` explicitly exclude `XK`. Implemented in both notebooks.

## Other bugs fixed this session

- **Grey slivers on Iceland/UK coastline.** GISCO's 1:20M outlines are generalised
  enough that plotly's own basemap showed through along jagged coast. Fixed by
  swapping both countries' geometry for OSM (relations `299133`, `62149`), simplified
  with the same Douglas–Peucker ε=0.01° used for Kosovo — Iceland 804→92 points,
  UK 38,356→551 points across 5 landmasses (Shetland/Orkney/Hebrides retained, bbox
  reaches 61.06°N). Both came out counter-clockwise and were reversed to match GISCO's
  clockwise convention, avoiding the "fills the whole world" bug hit with Kosovo earlier.
  Note the sandbox **cannot** `curl` `gisco-services.ec.europa.eu` or
  `polygons.openstreetmap.fr`; both had to be fetched through the browser tool.
- **UK rendered as "not tracked" in DigitalSkills.** UK has zero rows in
  `digital_skills_by_age.csv` (it does have rows in both internet datasets). The
  country list was derived from the data, so UK fell out entirely. Now derived from
  the GeoJSON, so UK correctly shows as tracked-but-missing. UK is the *only*
  country on the map with no rows in that dataset.
- **Slider didn't follow the Play button.** Slider steps had been switched to
  `method='update'`; they only track the animation when they use `method='animate'`
  with matching frame names. Reverted.
- **Stale "not yet reporting" list during playback.** Frames merge annotations by
  position, and an **empty string doesn't overwrite** the previous frame's text —
  so the last non-blank year's country list stayed on screen for the rest of the
  animation. Emitting a single space `' '` instead of `''` fixes it. (Jumping
  between years worked fine, which is what made this look like a different bug.)

## Design decisions, with reasons

- **"No data yet" colour is amber `rgb(246,217,168)`, not grey.** Grey was ambiguous
  against both the purple scale and the "not tracked" land. Amber is outside both
  colour families so it can never read as a data value. Jana picked the lightest of
  five candidate shades. Same colour in both notebooks, deliberately.
- **Age-group map is a static 3×4 button grid, not an animation.** Year and age
  group aren't a continuous sequence; animating between them would imply a trend
  that isn't there.
- **No forward-filling in the digital skills data** (unlike the internet data, which
  does forward-fill). The skills series is biennial with only 3 points — a 2-year gap
  is too big to assume nothing changed. Missing stays missing. This follows Jana's
  stated principle against "fingování nebo odvozování dat".
- **Only Kosovo, Iceland, UK use OSM.** Jana asked whether to just load the whole map
  from OSM since "everything gets fixed with OSM". No — the other 35 GISCO countries
  have no problem, and swapping them would be work and risk for no gain. The OSM
  swaps were each for a specific, diagnosed defect.

## Analysis done (exploratory, not yet in any notebook)

Jana's hypothesis was that rising connectivity drives digital literacy. Findings:

- Correlation internet use vs. digital skills: **r ≈ 0.81 / 0.80 / 0.75** (2021/2023/2025).
  Real but far from 1:1 — she read this correctly as "ten vztah tam není tak markantní".
- Follow-up question — is the *ratio* skills/use constant across countries? **No.**
  2025 range is **0.31 (North Macedonia) to 0.84 (Netherlands)**, CV ≈ 0.25.
- The ratio itself correlates with coverage level (r ≈ 0.66–0.70) and clusters
  geographically: Nordic/Western Europe 0.79–0.84, Balkans/South-East 0.31–0.47 —
  countries with near-identical internet coverage (85–93%) but very different skills.
  Suggested story: **the digital divide has moved from access to skills.**
  Kosovo is a notable outlier at 0.77, closer to the Nordics than its neighbours.

Artifacts: `data/processed/digitalization_vs_skills_comparison.csv` (37 countries ×
2021/2023/2025) is in the repo. Two charts were generated to the scratch outputs
folder only and are **not** in the repo — a 34-country small-multiples grid
(Iceland/Kosovo/North Macedonia dropped, per Jana: "pokud data chybí, tak ty země
vynech") and a ranked bar chart of the 2025 ratio. Regenerate from the CSV if wanted.

Two ranked spreadsheets were also delivered to Jana's Vizualizace folder (not the
repo): household internet ranking 2025, and digital skills 2025 across all four age groups.

## Late addition: internet use by age group

Jana asked whether internet use also has an age breakdown (it does — for *individuals*;
household internet access has no age dimension, since the unit is the dwelling). Pulled
`isoc_ci_ifp_iu` three more times, one per `ind_type` value (`Y16_24`, `Y25_54`, `Y55_74`),
with `sinceTimePeriod=2021`. New `data/processed/internet_use_by_age.csv` (547 rows),
`scripts/decode.py` extended with `decode_44x5` and a fourth section. Verified: re-running
decode.py reproduces all three pre-existing CSVs byte-identically.

**Caveat on the raw files.** `data/raw/raw_iu_age_*.json` are **not** faithful API dumps like
the others. The fetch tool returns the response into the conversation rather than to disk, and
only the `value`/`status` payloads were carried across; the `dimension`/`id`/`size`/`extension`
blocks were not. Each file therefore carries `_note`, `_source_url`, `_fetched` and `_shape`
(dimension order, geo/time ordering, flat-index formula) so it can still be decoded and
re-fetched. If byte-faithful raws matter later, re-fetch the three `_source_url`s.

Also fixed while in there: `STATUS_LABEL["bu"]` said "break+estimated", which is wrong — this
dataset defines `bu` as "break in time series, low reliability".

**What the like-for-like comparison shows (2025):**

| age | uses internet | has basic skills | gap | skills/use | corr across countries |
|---|---|---|---|---|---|
| 16–24 | 99.3% | 74.7% | 24.6 pp | 0.75 | 0.48 |
| 25–54 | 98.1% | 66.5% | 31.6 pp | 0.68 | 0.66 |
| 55–74 | 84.9% | 38.1% | 46.8 pp | 0.43 | 0.84 |

The decisive number: among 16–24 year olds, internet use spans only **96.5–100%** across the
36 countries (std 0.8) while their skills span **44.5–93.1%** (std 13.1). A variable with a
3.5-point range cannot explain a 49-point one — which kills Jana's original "more coverage →
more literacy" hypothesis far more cleanly than the earlier correlation numbers did.

Careful with the flip side: the 0.84 correlation for 55–74 is not proof that access drives
skills for them either. It partly reflects that both variables still genuinely vary in that
age group (use 66–100%), whereas the young sit at a ceiling that mechanically suppresses
correlation. Don't report the young/old correlation difference as if it were a causal finding.

Extreme cases among 55–74, online but unskilled: Romania 84.7% online vs 12.8% skilled (71.8 pp
gap), North Macedonia 80.7/10.1, Albania 71.8/4.8. Smallest gap: Ireland 99.2/75.6 (23.6 pp).

Chart written to the scratch outputs folder only (not the repo):
`internet_use_vs_skills_by_age_2025.png` — scatter of use vs skills, one dot per country,
coloured by age group, with the y=x reference line. The young form a near-vertical stripe at
x≈99, which is the whole argument in one picture.

## Second late addition: the five DigComp areas separately

Jana asked whether the individual skill areas could be pulled too. They can — `isoc_sk_dskl_i21`
carries 24 `indic_is` values, including each DigComp area at basic-or-above (`I_DSK2_IL_BAB`,
`I_DSK2_CC_BAB`, `I_DSK2_DCC_BAB`, `I_DSK2_SF_BAB`, `I_DSK2_PS_BAB`).

**API trick worth remembering: omit `indic_is` entirely and the response contains all 24
indicators at once.** That turned a planned 20 calls (5 areas × 4 age groups) into 4 (one per
`ind_type`, with `time=2025`). Note the dimension order for this dataset is
`["freq","ind_type","indic_is","unit","geo","time"]` — *different* from `isoc_ci_ifp_iu` — so
with `time` pinned the flat index is `indic_index * 39 + geo_index`, over `GEO39`.

New `data/processed/digital_skills_by_area.csv` (912 rows), raw in
`data/raw/raw_dskl_area_*.json`. Same partial-capture caveat as the age files, plus these keep
only 6 of the 24 indicators and are already resolved to country codes. **Validation used
throughout: the overall indicator `I_DSK2_BAB` was transcribed alongside the five areas and
checked against `digital_skills_by_age.csv` — exact match on all 38 countries for all four age
groups.** Any transcription slip would have shown up there.

**What it shows (European averages, 2025):**

| area | 16–24 | 25–54 | 55–74 |
|---|---|---|---|
| Communication and collaboration | 99 | 97 | 82 |
| Information and data literacy | 92 | 93 | 76 |
| Problem solving | 96 | 92 | 68 |
| Safety | 83 | 78 | 56 |
| Digital content creation | 89 | 79 | 50 |
| **Overall (all five at once)** | **75** | **67** | **38** |

Two things fall out of this. First, **the bottleneck moves with age**: for the young and
middle-aged the weakest area is Safety, but for 55–74 it is Digital content creation (50%) —
spreadsheets, editing files, combining text and images. Communication is near-universal at
every age, so "seniors can't use the internet" is wrong; they message and read news fine.

Second, **the conjunctive rule costs a lot on its own**. Averaged across countries, the weakest
single area for 55–74 sits at 46%, but the overall figure is 38% — needing *all five*
simultaneously removes a further 8 points beyond simply failing the hardest area. The same
penalty is 7 points for 16–24 and 8 for 25–54, so it isn't an age effect; it's the indicator's
construction. Worth stating whenever the headline number is quoted.

Country illustrations: Czechia's 55–74 are fine on information (82%) and communication (81%)
but collapse on content creation (47%), giving an overall 42%. Romania's 55–74 reach 82% on
communication yet 19% on content creation and 36% on safety, giving 13% overall. Ireland is
the only country where seniors clear 83% in every single area.

Chart in the scratch outputs folder: `digital_skills_by_area_2025.png`.

## Next steps

1. Jana wants to keep exploring the data for more relationships before wrapping up.
2. Session log + README are current; repo still awaiting her final review.
3. **Then push to GitHub** — still gated on her explicit approval.
4. **After the push:** replace the manual `files.upload()` cells in both notebooks
   with `pd.read_csv(<github raw url>)`. Deliberately deferred — Jana declined an
   interim Google Drive mount so the migration only has to happen once.
5. Presentation format was settled early as **plotly HTML export** (works for anyone
   without special tools, unlike the original PowerPoint idea) but nothing has been
   exported yet.
