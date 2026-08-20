# 2026-08-16: Chapter 2 redesign, question/answer format, README + button polish

## Context

Continuing from the previous session's presentation-story work. This session focused on
reworking chapter 2 (coverage vs. individual use) end to end, establishing a question/answer
format for the whole story, and clearing the remaining TODO items (chapter 4 button colors,
README/CLAUDE.md em-dash and terminology sweep).

## Chapter 2: from one scatter chart to three question/answer charts

Started from a single binned scatter chart with a red/coral color scheme (matching the
project's "individual activity" color convention). Jani flagged that the red fill was
clashing with the red in several country flags used as data labels, making them hard to
see. Switched that chart's fill/line to gray (`TIER_LIGHT` = `#E5E5E5` fill / `#767676`
line, `TIER_DARK` = `#B8B8B8` fill / `#333333` line) as a deliberate one-off exception to
the blue/purple/red/green convention, specific to this chart's flag-legibility problem.

### Title accuracy catch

The chart originally had a statement title along the lines of "From lagging to caught up."
Jani checked it against the data and caught that it was backwards: at the very start, with
coverage around 5%, individual use was already close to 20%, i.e. use *led* coverage, not
lagged behind it. Verified this held for nearly all of the 2002 data (10 of 11 countries had
use > coverage) and for 2025 too. Dropped the title.

### Speculation catch

While discussing why use might exceed coverage at low-coverage bins, I offered an explanation
along the lines of "people got online at work, school, or internet cafés." Jani pushed back:
were internet cafés even a real feature of 2002 in these countries? I checked the schemas of
every CSV in this project and confirmed none of them break down *where* people used the
internet: there's no place-of-use data at all. Dropped the explanation entirely rather than
speculate; this is a direct instance of the CLAUDE.md rule "don't state conclusions the data
doesn't support."

### Format decision: question titles + bullet methodology + answer below chart

Jani asked to replace statement titles with question titles, with the explanatory text moved
to an answer paragraph *below* the chart instead of in the title. I proposed five candidate
questions; she picked "Does home internet come before people start using it, or after?" and
asked for the methodology caption to be reformatted as bullet points for readability. This
became the format for every remaining chart in chapter 2: question as title, bulleted
methodology as subtitle, chart, then a verified-against-data answer paragraph underneath.

Jani was explicit about *why*: she wants every chart to visibly represent a real step in an
investigation, including any that turned out to be a dead end (e.g. an early assumption that
coverage would simply predict activity); nothing gets deleted just because it didn't pan
out, so the notebook reads as a systematic walkthrough rather than a highlight reel.

### New chart: yearly bars across the full 2002-2025 span

Jani asked for an additional chart showing the coverage/use relationship across *all* years
at once (not binned into deciles), plain country-average per year, coverage and use as
side-by-side bars. This produced `chapter2a_yearly_bars.py`: blue bars for household coverage,
gray bars for individual use, one pair per year, 2002-2025. It revealed a clear crossover
around 2012 (use overtakes coverage as the higher of the two and stays there). Jani liked this
enough to make it the *first* chart in chapter 2 (the year-by-year overview), with the binned
detail chart repositioned as a closer, second look.

### Year selection for the binned detail chart

Iterated through several year combinations for the binned/flags chart before landing on a
final pair:
- 2002 vs. 2025 (confirmed working, but sparse in the middle bins).
- 2002 vs. 2017 (richer spread, includes a clear below-the-60%-line example in 2017: Turkey).
- 2025 alone (too sparse on its own).
- All three years together (2002/2017/2025): visibly overlapping and crowded; Jani was
  decisive here: "urcite pojdme zpatky" (definitely let's go back) to the two-year version.

Final: **2002 vs. 2017** for the "closer look" chart, with **2025 alone** promoted to its own
third chart answering "what does the present look like?", reusing the same binning/flag/tier
logic via a thin wrapper (`chapter2c_present.py` calls `chapter2b_binned_detail`'s
`build_chapter2b_figure` with different year/question/bullet arguments).

### Axis ticks

Jani asked for minor tick marks every 5% with only the tens labeled, on both axes, on both
the binned chart and the yearly-bars chart. Hit a plotly bug along the way: `minor=dict(dtick=5)`
starting at `tick0=0` also lands on every major tick position (multiples of 10), drawing a
minor tick on top of the major one and corrupting the label glyph. Fixed by switching to
explicit `tickvals` lists that exclude the major positions (`[5, 15, 25, ..., 95]` instead of
`dtick=5`).

### Data-verified answer text

For the 2002-vs-2017 chart: confirmed 2002 had 8 of 11 reporting countries below 60%
individual use (minimum 14.67%, Greece), while 2017 had 0 of 36 countries below 60% (minimum
63.41%, Bulgaria). Answer text: "Fifteen years later, every reporting country had crossed the
60% mark for individual use: the lowest, Bulgaria, stood at 63.4%, up from a low of just 14.7%
(Greece) in 2002."

For the 2025-present-day chart: confirmed all 36 countries above 85% individual use, minimum
85.9% (Croatia), maximum 99.78% (Ireland). Answer text: "By 2025, every country was above 85%
individual use. The lowest, Croatia, stood at 85.9%, just 14 points behind the highest,
Ireland at 99.8%."

### Small fixes along the way

- A stray red dot in the legend: a `fill='toself'` trace with `line=dict(width=0)` and no
  explicit color falls back to plotly's default categorical color cycle for its legend
  swatch. Fixed by setting `line=dict(width=0, color=FILL_COLOR)` and
  `marker=dict(color=FILL_COLOR)` explicitly.
- Ireland's flag (use = 99.78%, right at the y-axis ceiling) was getting clipped at the top of
  the plot. Fixed by extending the y-axis range to `[-5, 118]` and switching flag text
  position to `top center` / `bottom center` instead of centering on the point.
- Discussed (not implemented) merging both binned charts into a single panel with a year label
  per region: Jani asked my opinion first; agreed two separate panels stay clearer than one
  merged one given the flag density, so this was not pursued further.

### Chapter 2's final structure

Three charts, in this order:
1. `chapter2a_yearly_bars.py`: plain yearly bars, 2002-2025, still has its original plain
   descriptive title (not yet converted to the question/answer format, see Open items below).
2. `chapter2b_binned_detail.py`: "Does home internet come before people start using it, or
   after?", years 2002 vs. 2017.
3. `chapter2c_present.py`: "And what does the present look like?", year 2025, reusing
   chapter2b's helpers.

New shared helper module `chapter2_shared.py` factors out the flag-emoji and decile-binning
logic used by both chapter2b and chapter2c. Superseded iteration files
(`chapter2_scatter.py`, `chapter2_coverage_use_bins.py`, `chapter2_binned_grid_preview.py`,
`chapter2_merged_preview.py`, `chapter2_yearly_bars_preview.py`) are left in the working
directory but not referenced by any build script; only `chapter2_scatter.py` has an explicit
"SUPERSEDED" docstring so far.

## Chapter 4 button colors

Previously flagged as unresolved (plotly styles `updatemenus` at the menu level, not per
button, so per-button color differentiation isn't straightforward). Jani resolved it herself
with a simple direction: one uniform light purple background with dark purple labels across
all 12 buttons in the year x age-group grid, matching the map's own Purples colorscale.
Implemented as `BUTTON_BG_PURPLE = '#E5D8F0'` / `BUTTON_TEXT_PURPLE = '#54278F'`
(contrast-checked at 7.47:1, well above the 4.5:1 floor), applied uniformly via `bgcolor`,
`bordercolor`, and `font.color` on each of the three `updatemenus` entries.

One caveat remains and is now just documented rather than chased further: plotly's
`showactive=True` gives the *currently active* button its own built-in highlight style
(white background, light blue border) that no `Updatemenu` attribute can override (confirmed
via `dir()` inspection, no `activecolor` attribute exists). Every button except the active one
in its row shows the intended purple; the active one shows plotly's default highlight.

**Caught during testing**: this fix was applied to `chapter4_map.py` (used by
`build_story_html.py`) but initially missed in `chapter4_cell.py` (the notebook-cell version,
used by both `Story.ipynb` and `export_cell.py`): the two files carry the same chart logic
independently since the notebook uses flat, shared-namespace cells rather than importable
functions. Caught this via a full-page regression pass on the notebook-exported HTML (see
Testing below), which showed the chapter 4 buttons still white/default. Ported the fix to
`chapter4_cell.py` and re-verified.

## README and CLAUDE.md sweep

Two standing rules applied across the whole project this session: no em dashes anywhere
(replaced contextually with commas, colons, semicolons, periods, or parentheses depending on
what read best in each spot), and "digital skills" → "digital activities" in this project's
own descriptive writing (kept unchanged wherever the text names Eurostat's own dataset/
indicator directly, e.g. `isoc_sk_dskl_i21` / "Digital Skills Indicator 2.0", or is explicitly
contrasting activity-based measurement against the idea of a tested skill).

- `README.md`: full sweep, all em dashes removed, "digital skills" → "digital activities" in
  the About section, the data-sources table, the age-group-split paragraph, and the data-notes
  bullets. Retitled a section from `### What "digital skills" actually measures` to
  `### Why this project says "digital activities", not "digital skills"`, and added an
  explicit terminology-choice paragraph explaining the exception for Eurostat's own naming.
- `CLAUDE.md`: fixed the remaining 4 em dashes in the Layout section's bullet list.

**Process note**: before editing `CLAUDE.md`, re-staged both files fresh from Jani's actual
device and discovered my locally cached copy was stale, missing a "Global rules apply here
too" section and a terminology note that had already been added to the real file earlier in
this session (before a context compaction). Discarded the risky edit and redid it against the
freshly-fetched real content, so nothing was lost. Both files delivered via `device_commit_files`
with an `expectedMtimeMs` guard; both writes succeeded.

Old notebooks (`Digitalization.ipynb`, `DigitalSkills.ipynb`) and historical session logs still
contain em dashes and the old "digital skills" phrasing in places; deliberately left alone as
historical record, not swept, unless Jani asks otherwise.

## Testing

- Fixed a bug in the notebook-regression test harness (`make_test_notebook.py` in the sandbox,
  not part of the repo): the script that extracts `Story.ipynb`'s code cells for headless
  execution was stripping `google.colab`/`files.upload()` lines but leaving the trailing
  `print("Uploaded:", ...)` line behind, causing a `NameError` on the now-undefined upload
  variable. Fixed by skipping upload cells entirely (they have nothing left to run headlessly
  once the upload call is removed) rather than partially stripping them.
- Rebuilt `Story.ipynb` (25 cells) and `geospacific_story.html` (~7.17 MB) from the updated
  cell/build scripts and ran the fixed test harness: all 10 code cells with executable content
  ran cleanly end to end, including chapter 1 through chapter 5b.
- Full-page Playwright pass over the rebuilt `geospacific_story.html`: scrolled and
  screenshotted the entire page top to bottom, checked console/page errors. Only error present
  is the pre-existing, harmless `https://cdn.plot.ly/un/world_110m.json` fetch failure (no
  internet access in the sandbox; irrelevant since this project's choropleths use their own
  GeoJSON, not plotly's built-in world atlas).
- Verified chapter 4's button colors directly in the rendered SVG (`fill`/`stroke` on
  `.updatemenu-item-rect` elements) rather than relying on a screenshot alone, since this is
  what caught the `chapter4_cell.py` gap described above: confirmed `rgb(229, 216, 240)`
  (`#E5D8F0`) on 11 of 12 buttons, with the 12th (currently active) showing plotly's
  unavoidable default active-state highlight as expected.

## Round 2: chapter 2a/2b questions finalized, appendix system, chapter 1 caption fix

After the first delivery, Jani reviewed the notebook and asked for several more changes,
resolved in this order.

### Chapter 2a's title, finalized

Picked from the three candidates: "As household coverage grew, did individual use simply
follow behind it?" (option 2), with a shortened answer: "Not at first: individual use led
coverage for the whole first decade (2002-2011). Coverage overtook use in 2012 and has stayed
narrowly ahead since." Wired into `chapter2a_yearly_bars.py`, `chapter2a_cell.py`, and all
three build scripts.

### Chapter 2b's question and heading reassigned

Jani flagged that the original binned-chart question, "Does home internet come before people
start using it, or after?", actually fits chapter2a (the year-by-year crossover chart) better
than chapter2b (the two-year country comparison), since chapter2a is what actually shows the
before/after temporal ordering across all 24 years. She confirmed chapter2a's chosen wording
(option 2) already covers that idea in reformulated form, so chapter2b needed a new, different
question. Replaced it with "Once a country has some coverage, does everyone catch up on use,
or are some left behind?", kept the existing (already-verified) answer text. Also changed the
section heading from "A closer look, country by country" to "A more detailed look at the
relationship between coverage and individual use" per Jani's suggested phrasing. Updated in
`chapter2b_binned_detail.py`, `chapter2b_cell.py`, and all three build scripts.

### Chapter 1's caption corrected

Jani caught that the caption ("countries with no data yet for a given year are shown in amber
rather than blending into the low end of the blue scale") didn't match the actual behavior.
Checked `chapter1_map.py`: it does `groupby('geo_code')['pct_households_with_internet'].ffill()`
before computing which countries are "missing" for a given year, so a country that has reported
before and then has a gap year keeps the shade of its last known value; only a country with
literally no data yet (never reported, nothing to forward-fill from) gets amber. The code was
already correct, only the caption was misleading. Rewrote it to state the actual rule, and
added a mention of hover behavior (country name + coverage %) that the caption never described
at all. Applied to `build_notebook.py`, `build_story_html.py`, and `export_cell.py`.

### Dead ends: HTML story stays clean, notebook gets a full appendix

Jani initially said she wanted every dead end kept as full graphs, then reconsidered: the
polished HTML story should stick to the agreed chapter lineup only, no dead-end charts, but
she liked the idea of at least a short textual mention. Landed on: a one-line note appended to
chapter 2c's answer in the HTML story ("Along the way we also tried a straight correlation
scatter and a 9-panel year-by-year grid before landing on this three-chart format; those are
kept in the notebook as a record of the paths we didn't take."), and a full **Appendix** section
at the very end of the notebook only (not exported into the HTML), covering the full project
history of dead ends, not just this session's:

1. `appendix_scatter_cell.py`: the very first chapter 2 design, a raw per-country scatter
   across 5 key years, no binning.
2. `appendix_wrongtitle_cell.py`: the binned 2002-vs-2025 pair kept exactly as first built,
   original red/coral coloring, including the title later found to be backwards ("From lagging
   to caught up"), with an in-chart note explaining the correction and pointing to chapter 2a.
3. `appendix_grid_cell.py`: the 9-snapshot-year grid approved in the 2026-08-14 session, then
   dropped in 08-15's chapter replan.
4. `appendix_corr_cell.py`: the 08-14 session's straight Pearson-correlation scatters
   (coverage vs. use, r=0.635, r²=0.403; use vs. composite digital activities, r=0.753,
   r²=0.567; both verified fresh against 2025 data, matching the 08-14 log's numbers exactly).
   The original version used country flags as markers and was unreadable (crowded, saturated
   values); rebuilt here with plain dots since the point is to document the correlation
   finding, not to reproduce the specific readability failure.

`build_notebook.py` now produces 35 cells (up from 25); the appendix isn't referenced by
`build_story_html.py` or `export_cell.py`, so `geospacific_story.html` is unaffected in scope,
only in the chapter2a/2b text changes above.

### Flag-rendering check, prompted by a Jani report

Jani reported the 2002-vs-2017 chart (chapter2b) was missing its country flags. Re-rendered
`build_chapter2b_figure()` fresh and confirmed via a Playwright screenshot of the actual
rebuilt `geospacific_story.html` that flags ARE present and rendering correctly (Lithuania,
Portugal, Greece, Finland, Denmark, Italy, Germany in the 2002 cluster; Croatia, Latvia,
Bulgaria, Romania, Turkey, Estonia, Iceland, Germany in 2017). Could not reproduce "missing" in
this sandbox's headless Chromium. Flagged back to Jani to clarify whether she was looking at a
Colab live run (which has historically shown its own rendering quirks not reproducible in this
sandbox, per the 08-15 log) or the exported HTML file, and asked her to double check against
the redelivered file before assuming a real regression.

### Chapter 4's selected button reversed (dark bg / light text)

Jani asked for the currently-selected button in chapter 4's year x age-group grid to reverse
colors, dark purple background with light purple text, mirroring chapter 1's reversed
Play/Pause pair, instead of plotly's default (uncontrollable) active-button highlight that was
still showing before this fix.

Plotly has no per-button color attribute: `bgcolor`/`font` only exist at the whole-menu level
(confirmed via the `Button` object's schema directly, not just `dir()` on `Updatemenu`), so a
shared 4-button-per-row menu can't give one button a different color than its siblings. Fixed
by restructuring the grid from 3 row-menus (4 buttons each) into 12 individual single-button
menus, one per year x age-group cell, each with its own `bgcolor`/`bordercolor`/`font.color`.
On click, the `layout_update` args now flip every menu's colors: the clicked button's menu goes
dark purple (`BUTTON_BG_ACTIVE` = the same `#54278F` already used as the unselected text color)
with light purple text (`BUTTON_TEXT_ACTIVE` = the same `#E5D8F0` already used as the unselected
background), and all 11 other menus reset to the normal light-bg/dark-text pair. Same technique
already in use for keeping only one row's `active` state true at a time, just extended to
color attributes. `showactive` set to `False` on every menu now, since selection state is
conveyed entirely through the custom colors rather than plotly's built-in highlight.

Per-button x positions had to be set manually (`col_x_positions`), since splitting one
multi-button menu into separate single-button menus loses plotly's automatic side-by-side
layout; tuned by eye against a rendered screenshot, "All (16-74)" gets a wider slot than the
other three shorter labels. Verified two ways: reading the actual `fill`/`bgcolor` values off
the rendered figure (not just eyeballing a screenshot), and clicking a button in a live render
to confirm the dark-purple state actually moves to the newly-clicked button and the previous
one reverts. Applied to both `chapter4_map.py` and `chapter4_cell.py`.

### Confusion cleared up: the "old iteration scripts" question

Asked Jani whether the superseded chapter-2 draft scripts should be deleted from the repo. She
didn't understand the question, reasonably: those scripts only ever existed in this session's
own sandbox workspace and were never delivered to her computer or repo, so there was nothing
on her end to decide. Cleared as a non-issue, no action needed.

## Open items

1. The flag-rendering report from earlier in this round (chapter2b's 2002-vs-2017 chart)
   still needs Jani's confirmation against the redelivered file, or a screenshot of wherever
   she's seeing it missing, before treating it as a real bug; not reproducible in this sandbox.
2. `Story.ipynb` and `geospacific_story.html` need to be redelivered to Jani with this round's
   full set of changes (chapter2a/2b questions and heading, chapter1 caption, appendix,
   chapter 4 button reversal); the most recent delivery in this session predates the button fix.
