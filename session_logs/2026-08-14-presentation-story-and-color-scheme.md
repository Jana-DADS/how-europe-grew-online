# 2026-08-14 — Presentation story: coverage/use/skills correlations, color scheme

## Context

Following on from [[2026-08-13-notebooks-and-kosovo-render-bug]] (Kosovo hover bug fixed
and verified in both notebooks, UI polish done). Jani opened this session with a concrete
plan for a **presentation story** built on the existing analysis:

1. Show internet coverage growing over time (existing animated map).
2. Explain how "digital skills" is measured per generation — the conjunctive
   all-five-areas rule, which makes seniors look bad.
3. Immediately soften that: break skills down by individual activity/area, showing the
   generational gaps are less dramatic than the headline number suggests, and that young
   people (16-24) actually lag *behind* in Safety specifically.
4. Show that coverage doesn't guarantee activity — no 1:1 relationship.

**Nothing in the repo changed this session** — no notebook or script edits, no README
changes. This was pure exploratory chart-building for chapter 4 of the story, done in
scratch outputs and shown to Jani via `present_files`. Working tree is clean/unchanged.

## Chapter 4 exploration: coverage vs. individual use

### First pass: country-level correlations (2025 snapshot) — superseded

Computed Pearson correlations on 2025 data, 36 real countries (EU/EA aggregates excluded):

- Individual internet use vs. overall digital skills: **r = 0.753, r² = 0.567**
  (p < 0.0001). Notable residuals: HR, PT, CZ, FI, LT score higher on skills than their
  usage rate predicts; MK, RO, ME, TR, LV score lower.
- Household coverage vs. individual use: **r = 0.635, r² = 0.403** (p < 0.0001).

Built scatter charts for both (`corr_use_vs_skills.py`, `corr_hh_vs_use.py`). **Problem:**
internet use is nearly saturated everywhere in 2025 (86-100%), so on a full 0-100 axis
almost every point crams into the rightmost fifth of the chart. Tried country flags as
markers — unreadable, badly overlapping (and no Kosovo flag available — the custom-drawn
one from a prior session's chart wasn't saved anywhere, would need to be redrawn from the
GeoJSON silhouette if needed again). Jani correctly called both draft charts "hard to read
for a layperson" and asked for a completely different approach — these two scripts and
their outputs are dead ends, not part of the final story.

### Second pass: EU27 grouped bar, coverage + use-by-age, 2021-2025 — approved

Jani's ask: one chart, x-axis = year, y-axis 0-100%, 4 bars per year (household coverage,
then individual use for ages 16-24 / 25-54 / 55-74, lightest green = youngest). Built from
`household_internet_access.csv` + `internet_use_by_age.csv`, EU27_2020 aggregate. **Only 5
years available** (2021-2025) since the age breakdown only starts in 2021 — flagged this
constraint to Jani before building, she accepted it.

Script: `coverage_vs_age_use.py` → `coverage_vs_age_use_eu27.png`. Had to move data labels
inside the bars (white bold text) instead of above them — with values in the high 90s and
a full 0-100 axis, above-bar labels collided with the title. Jani's takeaway, unprompted:
"seniors are catching up to the young in usage, that's good — but only over 5 years."

### Third pass: coverage-binned distribution of use, all countries, all years pooled — approved, then reworked

Jani then asked to use the full 2002-2025 history: bin countries by household-coverage
decile (0-10%, 10-20%, ... 90-100%), and for each bin compute min/max/mean/median of
individual use **pooling every country-year observation across 2002-2025** (n=749,
38 countries). Built as a min-max band + mean/median lines + a y=x reference line
(`coverage_bins_vs_use.py` → `coverage_bins_vs_use.png`). Clean monotonic relationship,
consistently *above* the 1:1 reference line (individual use outpaces home coverage,
most visibly at low coverage — people get online via work/school even without a home
connection).

Jani noticed the 50-60% bin's minimum dipped below the 40-50% bin's minimum and asked why.
Traced it to a single point: **Cyprus, 2004** (53% coverage, only 32% individual use) — an
outlier, not a pattern; every other country in that bin scores 38-73%. Worth keeping as a
one-off callout if this chart resurfaces, but don't generalize from it.

Jani then asked for country flags at each bin's min and max (20 flags total) —
added via `flagpy`, with a name-mapping dict for the handful of countries flagpy expects
different names for (`CZ`→"The Czech Republic", `NL`→"The Netherlands"; full map is in the
script). No Kosovo hit a min/max, so the missing-flag problem from pass 1 didn't recur here.

**Then Jani caught a misunderstanding**: she'd actually wanted this binned min/max/mean/
median breakdown *per individual year*, not pooled across all 24 years. This produced the
final version of chapter 4's chart — see below. `coverage_bins_vs_use.py` and
`coverage_bins_vs_use_flags.py` (pooled-years versions) are superseded; kept in scratch
outputs but not the deliverable.

### Final version: 3×3 grid, one panel per year — approved

`coverage_bins_by_year_grid.py` → `coverage_bins_by_year_grid.png`. Same binning logic,
but computed **separately for each of 9 snapshot years** (2002, 2005, 2008, 2011, 2014,
2017, 2020, 2023, 2025), one subplot per year, shared 0-100 axes on both dimensions for
visual comparability across panels. Each bin's min/max flagged with the actual country
(now genuinely one country per flag, no duplicates, since within a single year a bin often
holds very few countries).

This is the chart that landed the point Jani was after: in 2002 countries were spread from
0% to 60% coverage; by 2023 **every single country in the dataset is in the 80-100%
coverage bin** (34/34), same in 2025 (36/36) — not "almost all", literally all. (I first
described 2025/2023 as "skoro všechny" / "almost all" — Jani asked me to check, and it was
wrong in the conservative direction: verified via `pct_households_with_internet<80`, count
is exactly 0 in both years. 2020 still had 3 countries under 80%: BG 78.85%, BA 72.84%,
MK 79.39%. Corrected in chat. This is the kind of claim CLAUDE.md's "don't state conclusions
the data doesn't support" rule is about — check the exact count, don't eyeball it.)

## Color scheme decision (project-wide, not just this chart)

Triggered by a legend-legibility complaint (the pale green range-fill swatch was nearly
invisible against the legend's white background) plus a design question — Mean and Median
lines were almost overlapping, worth dropping one.

Worked out the color convention through several rounds with Jani, landing on:

- **Blue** — household coverage.
- **Purple** — composite/overall digital skills, "at least basic" across all five DigComp
  areas at once. Already established on the `DigitalSkills.ipynb` map.
- **Red/coral** (`#C0392B` line / `#EFB6AD` fill) — any *individual* skill or activity,
  as opposed to the composite. Jani's framing: she treats "using the internet" itself as
  an individual skill/activity, conceptually parallel to the five DigComp areas, so
  internet-use charts get this color too, not a brand new one and not purple (purple is
  reserved for the composite metric specifically — using it for a single activity would
  visually imply it's the same kind of thing).
- **Green** — distinguishes age groups *within* whichever of the above metrics is being
  shown (lightest = youngest, darkest = oldest; darkest shade fixed last session at
  `#1A7A47`).
- **Amber** — "not yet reporting" / missing data on the animated maps (established prior
  session, unchanged).

Applied to `coverage_bins_by_year_grid.py`: dropped the Median line entirely, Mean line
and the min-max range fill recolored to the red/coral pair above, legend trimmed to 3
items (Mean, Range, Reference). Jani approved the result.

**Explicitly deferred**: recoloring `digital_skills_by_area_2025.png` (the 5-DigComp-area
breakdown chart from the previous session, currently colored by age only, green shades) to
put each of the five *areas* in its own red/coral-family shade. This interacts with the
existing age-based green shading in that chart and needs its own discussion — not done
yet, don't assume the scheme above has been retrofitted onto it.

## Where things stand / state of deliverables

- Repo: clean, nothing changed on disk under `Geospacific/`.
- All charts from this session live only in scratch outputs, delivered via `present_files`,
  **not copied into the repo**. Scripts (in case any are worth resurrecting or reference):
  `corr_use_vs_skills.py`, `corr_hh_vs_use.py` (dead ends — don't reuse),
  `coverage_vs_age_use.py` (approved, EU27 4-bar chart),
  `coverage_bins_vs_use.py` / `coverage_bins_vs_use_flags.py` (superseded pooled-year
  version — kept for reference only),
  `coverage_bins_by_year_grid.py` (**final, approved** — this is chapter 4's chart),
  `purple_options.py` / `fourth_color_options.py` (swatch pickers, disposable).
- Chapter 4 of the story is now visually done: the 3×3 convergence grid.
- Chapters 1-3 already exist from the previous session (map, skills-criteria writeup +
  quadrant chart, area-breakdown + safety-gap chart) but are similarly still loose
  chart files, not assembled into one deliverable.

## Next steps

1. Decide the actual output format for the story (new notebook? slide deck? single
   long-form doc?) — asked once, Jani hadn't decided yet when the session ended.
2. Apply the new color convention to `digital_skills_by_area_2025.png` (deferred, see
   above) if/when that chart is revisited.
3. Once a format is chosen, move the approved chart scripts (and re-run them) somewhere
   durable in the repo rather than scratch outputs — right now a fresh session has nothing
   to regenerate them from except this log.
4. Session ended because chat performance degraded from conversation length, not because
   the work was finished — pick up directly with the story-assembly question above.
