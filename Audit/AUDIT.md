# Geospatial: code and content audit

Read-only audit of `notebooks/`, `scripts/`, and the story pipeline. Nothing was
changed. Every claim below was verified directly against the data, the built
files, or a rendered browser, not inferred from reading code.

Scope: `Story.ipynb`, `Digitalization.ipynb`, `DigitalSkills.ipynb`,
`scripts/decode.py`, the 13 chapter modules and their 17 notebook mirrors, both
build scripts, and all seven processed CSVs plus the boundary GeoJSON.

---

## Summary

The project is in unusually good shape. Two independently hand-written build
pipelines produce byte-identical output, every number quoted in the prose
reproduces from the shipped CSVs to two decimals, and `decode.py` regenerates
its four CSVs byte-for-byte. That is a stronger baseline than most published
data projects have.

There are six real defects. One of them stops anyone else from running the
notebook at all. The rest are a visible layout bug, an unverifiable set of
numbers, a mismatch between two maps and the text below them, and two
reproducibility holes in the data pipeline.

---

## 1. Blocking: the notebook cannot be run by anyone, including you

**Verified.** `Story.ipynb` reads six CSVs. The upload instructions name five.

Code cells call `pd.read_csv` on:

```
household_internet_access.csv     individual_internet_use.csv
internet_use_by_age.csv           digital_skills_by_age.csv
digital_skills_by_area.csv        digital_skills_above_basic.csv   <-- not in the instructions
```

Cell 2 says "Upload all five CSVs" and lists five. Cell 3's comment repeats the
same five. Cell 40 then calls
`pd.read_csv('digital_skills_above_basic.csv')` and raises `FileNotFoundError`.
Cell 44, the export cell, then fails with `NameError: fig4b`.

It is worse than a documentation gap: **`digital_skills_above_basic.csv` is not
in the repository at all.** `data/processed/` on disk contains six files, and
that file is not among them. It exists only in the cloud working directory where
it was fetched. So there is currently no way for a reader to obtain it.

Three things need to happen together:

1. Commit `digital_skills_above_basic.csv` into `data/processed/`.
2. Change "all five CSVs" to "all six" in cells 2 and 3 and add the filename to
   both lists (`build_notebook.py`).
3. Add it to the "About the data" dataset list in cell 1, and to the README's
   data-sources table, which already documents the dataset but not the file.

This is the only finding that makes something fail outright. Everything else
below is a defect in something that works.

## 2. The chapter 2 chart is clipped, and the clipped part is unreachable

**Verified in a headless browser at three viewport widths, with a screenshot.**

`chapter2a_yearly_bars.py:91` sets `width=1500`. The page container is
`max-width: 1100px` with `padding: 48px 24px` (`build_story_html.py:376`),
giving a 1052 px content box, and `.figure-wrap` has no overflow handling.

| viewport | page overflow | chapter 2 chart position |
|---|---|---|
| 1440 | 30 px | left edge at **-30 px** |
| 1280 | 110 px | left edge at **-110 px** |
| 1024 | 238 px | left edge at **-238 px** |

Because the chart is centered, the overflow is split across both edges. The
right side sits behind a horizontal page scrollbar; **the left side is at a
negative coordinate and cannot be scrolled to at all.** At 1280 px the y-axis
tick labels, the axis title, the first bar's year label and part of the chart
title and legend are simply not reachable. The chart loses its value scale
entirely.

1440 px is a common laptop width, so this is not an edge case. Every other
figure fits, though the four 1050 px maps clear the 1052 px box by 2 px and also
overflow below 1050 px viewport width.

Two candidate fixes: bring `width` down to 1000 to match the other charts, or
give `.figure-wrap` `overflow-x: auto` so wide figures scroll inside their own
box instead of the page. The first is simpler and keeps the page tidy; the
second preserves the chart at full size. The notebook is unaffected, since
Colab output cells are not width-constrained.

## 3. Chapter 4b's headline numbers cannot be verified from anything in the project

**Verified.** The ANSWER quotes EU27 above-basic figures of 43.1% (16-24),
38.0% (25-54) and 17.1% (55-74). The comment directly above it
(`chapter4b_above_basic_map.py:52-59`) says these were

> Verified against data/processed/digital_skills_above_basic.csv and
> digital_skills_by_age.csv, EU27_2020, 2025

That file contains **zero `EU27_2020` rows**, and zero aggregate rows of any
kind. It holds 37 individual countries only, exactly as the README states. The
unweighted 37-country means for 2025 are 39.0 / 34.4 / 14.4, which are not the
quoted figures, so they are not a plain average either.

The numbers are almost certainly correct: they are population-weighted EU27
aggregates straight from Eurostat, which is the right figure to quote. The
problem is that the project cannot prove them. Every other ANSWER in the story
carries a comment naming a CSV that actually contains the numbers, and a reader
can check any of them. This one cannot be checked.

The second half of the same sentence is fine: 74.6 / 68.6 / 42.6 does reproduce
from `digital_skills_by_age.csv`, `EU27_2020`, 2025.

Cheapest fix: re-fetch the three EU27_2020 above-basic values and append them to
`digital_skills_above_basic.csv`, then the comment becomes true as written. If
you would rather not change the file, correct the comment to say the aggregate
came directly from the Eurostat API and was not saved.

## 4. Chapters 4 and 4b open on 2021 while their text talks only about 2025

**Verified.** `chapter4_map.py:117` and `chapter4b_above_basic_map.py:111` both
set `default_year = YEARS[0]`, and `YEARS` is `[2021, 2023, 2025]`. So both maps
land on 2021.

The answer paragraph immediately below each map quotes 2025 and nothing else:
"In 2025, EU27 internet use exceeded it by 24.3 points for 16-24" and "EU27
above-basic skills in 2025 ran from 43.1%". A reader who tries to find those
figures on the map is looking at the wrong year and has no reason to suspect it.

Chapter 5c gets this right and documents the reasoning in a five-line comment:
it deliberately opens on "Digital content creation, 55-74" rather than the
arbitrary top-left cell, because that is the view the text discusses. Chapters 4
and 4b should do the same with `YEARS[-1]`.

## 5. `decode.py` will silently corrupt every value when Eurostat publishes 2026

**Verified by reconstruction.** Line 23:

```python
idx = geo_i * 24 + time_i
```

The `24` is a literal, matching `YEARS24 = range(2002, 2026)`. JSON-stat 2.0
flattens its dimensions into a single index, so this arithmetic only holds while
the time axis has exactly 24 periods.

Rebuilding `raw_isoc_ci_in_h.json` onto a 25-year axis (2002-2026, as Eurostat
will return next year) and re-running the script produces: exit code 0, no
warning, a well-formed CSV, and **695 of 714 overlapping values wrong**, each
shifted one year earlier. EU28 2008 reads 60.13 instead of 54.65, and so on.
There is nothing in the output that would look suspicious on a map.

Line 38 (`geo_i * 3 + time_i`) has the same problem for the biennial skills
series, which breaks on the 2027 wave. Line 60 already does it correctly with
`len(YEARS5)`, which suggests the literals are drift rather than intent.

The fix is free, because the information is already in the file: both full
JSON-stat responses carry `size` and `dimension[...].category.index`. Reading
the axis lengths from the response, and asserting the geo and time axes match
what the script expects, removes the whole class of failure.

Related, same file: `raw_isoc_ci_ifp_iu.json` has a `unit` dimension of size 2
(`PC_IND`, `PC_IND_ILT12`), which the index arithmetic ignores. It is harmless
today only because the second block is entirely empty and `PC_IND` happens to be
index 0.

## 6. Two reproducibility holes in the data pipeline

`decode.py` regenerates four of the seven processed CSVs, byte-identically. The
other three:

- **`digital_skills_by_area.csv`** (912 rows): the four `raw_dskl_area_*.json`
  files are sitting in `data/raw/` and are not read by anything. A short decode
  block reproduces all 912 rows with zero mismatches; the indicator-to-area
  mapping is already inside the raw files under `_indicators`. This is the
  cheapest of the three to close.
- **`digitalization_vs_skills_comparison.csv`** (38 rows): derivable from
  `decode.py`'s own two outputs by merging on 2021/2023/2025, pivoting, and
  dropping `EU27_2020` and `EA`. Maximum difference against the committed file:
  0.0. The recipe exists nowhere in code, so the "drop the aggregates" decision
  would have to be re-derived by inspection.
- **`digital_skills_above_basic.csv`**: no raw response was kept anywhere. This
  one directly contradicts the rule stated in `CLAUDE.md`, that `data/raw/`
  holds untouched responses "kept for reproducibility". If the CSV is ever lost
  or questioned it can only be recovered by re-querying Eurostat and
  reconstructing the query. Worth saving the raw response now while the query is
  still known.

## 7. Smaller consistency issues

**One chart in the notebook has no heading.** Cell 25, the 2025 chart, is the
only chart cell in `Story.ipynb` without a preceding markdown heading. Both HTML
assemblers supply `heading="One more year: 2025"`, but `build_notebook.py` has
no matching `md()` call, so notebook readers hit an unlabelled chart. Confirmed
by walking all 14 chart cells; every other one has a heading.

**Chapter 1's map uses a different grey from the other three maps.**
`chapter1_map.py:15` has `UNTRACKED_COLOR = '#E7E5DB'` = rgb(231,229,219);
chapters 4, 4b and 5c all use `rgb(211,209,199)`. Twenty levels apart in every
channel, on both the landmass fill and the legend swatch labelled "Not tracked",
which appears in all four maps. `OCEAN_COLOR` is the same colour written two
ways in the same files, which is what makes the grey mismatch look accidental
rather than deliberate. It came in from the two legacy notebooks, which each had
their own value, and was never reconciled at the merge.

**Chapter 5c's legend is styled differently from the identical legends in 4 and
4b.** Half-height swatches (`y0=_y_pos - 0.018` vs `- 0.035`) and "No data"
instead of "No data yet". Same three items, same position, same map size,
everything else in the block character-identical.

**Two strings break the project's own naming rule.** The README states the
project says "digital activities", never "digital skills", except when naming
Eurostat's dataset. `chapter4b_above_basic_map.py:120` has
`colorbar=dict(title='% above<br>basic skills')` and line 62 says "EU27
above-basic skills in 2025". These are the only two occurrences in the published
story that are not quoting Eurostat. Chapter 4's equivalent colorbar gets it
right: `'% with basic+<br>digital activities'`.

**Three `QUESTION` constants are defined and never rendered**, in
`chapter2d_gap.py:26`, `chapter3_age_bars.py:25`, and `chapter4_map.py:68`. Only
5c's and 4b's questions actually appear (`class="question"` occurs exactly twice
in the built HTML). Dead prose rots quietly; either render them or delete them.

**`decode.py` drops three real data points.** Lines 24-26 skip a cell when the
value is missing, before line 27 ever reads its status flag. Eurostat emits
status-without-value for suppressed cells, and three such cells exist in the
current raw data, all Ireland: household access 2022 (`u`, low reliability) and
internet use 16-24 for 2021 (`bu`) and 2022 (`u`). A downstream consumer cannot
tell "never surveyed" from "suppressed for low reliability". For a map that
draws grey holes, that distinction matters. Emitting the row with an empty value
and a populated flag would preserve it.

**`chapter2d_gap.py:40` filters aggregates differently from every other chapter.**
It uses `c.startswith('EU') or c in ('EA','EA19','EA20')` where the other four
chapter 2 modules use an explicit `AGG` set. It selects the same six codes on
today's data, but it derives the list from `hh` only and applies it to `iu`, so
an aggregate present only in `iu` would leak through as a country, and any
future real geo code beginning "EU" would be swallowed.

**Chapter 4b's "closer look" sits under Chapter 5 in the heading hierarchy.**
Its own first bullet says "Same map as chapter 4", but as an `h3` after
`## Chapter 5` it reads as a Chapter 5 subsection. Reading order is
4, 5, 5-detail, 4-detail. If the placement at the end is deliberate, giving it
its own `##` would stop it reading as a child of chapter 5.

---

## 8. Optimization opportunities

None of these are defects. They are places where the current structure costs
more maintenance than it needs to.

**The drift risk is the one worth acting on.** Every narrative block exists in
up to four hand-maintained copies: the chapter module, `export_cell.py`,
`build_notebook.py`'s markdown, and the `*_cell.py` figure mirror. Chapter 4's
answer text alone lives in three independently edited places. Editing a number
in `chapter4_map.py` updates `geospatial_story.html` (a real import) but
silently leaves `export_cell.py` and `build_notebook.py` stale, and every build
command still reports success. The published HTML and the published notebook
would then disagree, with nothing to catch it.

They are currently in perfect sync. This was checked properly: both HTML
pipelines were rebuilt from source and diffed end to end, including every
figure's serialized plotly JSON, after normalizing whitespace and plotly's
random div ids. Result, 4,603,348 characters against 4,603,348, identical. The
committed `geospatial_story.html`, `Story.ipynb` and `test_notebook.py` all
match freshly built output too.

That same comparison is the guard the pipeline is missing, and it can be added
today as a passing baseline: build both HTML files, strip the div ids, normalize
whitespace, assert equality. One assertion catches prose drift, figure drift,
chapter-ordering drift, CSS drift and stale deliverables in a single check.

Chapter ordering in particular is defined in three hand-synchronised places
(`build_story_html.py:145`, `export_cell.py:126`, and the sequence of calls in
`build_notebook.py:154`), with nothing enforcing that they agree.

**Around 330 lines are duplicated across the three button-grid maps.**
`chapter4b_above_basic_map.py` is a literal copy of `chapter4_map.py`; excluding
comments the entire functional difference is five lines (the CSV, the value
column, `zmax`, the colorbar title, the function name). Everything else, the
`combo_data` builder, the four `add_trace` calls, `update_geos`, the legend
loop, the 12-menu button grid, the row labels, is byte-identical, including the
docstring on `_pad_button_labels`. `chapter5c_area_map.py` shares the same
blocks with one grid axis swapped. A single
`build_button_grid_map(csv, value_col, colorbar_title, row_dim, col_dim, zmax)`
would collapse those 330 lines to about 120 and would have made the legend and
colour mismatches in section 7 mechanically impossible. `chapter2c_present.py`
already demonstrates the pattern: 38 lines that parameterize
`build_chapter2b_figure` instead of copying it.

**The exported HTML carries the boundary file 16 times.** Each of the four maps
attaches `geojson=` to all four of its choropleth traces, so `pio.to_html`
serializes all 38 features 16 times: 624 `CNTR_ID` occurrences, roughly 4.4 MB
of the 9.46 MB file. Eight of those copies are on Kosovo traces that draw a
single country. Two cheap wins: strip the 11 unused properties from the GeoJSON
(only `CNTR_ID` and `NAME_ENGL` are ever read, out of 13 fields including
`NAME_FREN`, `NAME_GERM`, `COUNTRY_URI`), and check whether the amber overlay
trace can share geometry with the data trace.

**Constants are duplicated rather than shared.** `#1F5FA6` appears under four
different names plus two hardcoded literals plus a CSS variable. The `AGG`
aggregate set exists in four copies (and a fifth mechanism, see section 7).
`MISSING_COLOR` / `OCEAN_COLOR` / `UNTRACKED_COLOR` and the 10-line legend loop
appear four times each. `_pad_button_labels` exists three times with two
different docstrings. A small `story_style.py` holding the palette, `AGG` and
the tick arrays, imported by every chapter, would remove all of it.

**Data is re-read rather than loaded once.** A full build parses the 271 KB
GeoJSON four times, `household_internet_access.csv` eight times and
`individual_internet_use.csv` six times, and rebuilds the same
coverage/use merge in five separate modules. Total build time is 1.4 seconds, so
this is a readability issue, not a performance one; worth doing as part of a
shared-loader refactor, not on its own. The notebook, notably, gets the
expensive half right: it loads the GeoJSON exactly once and reuses it across all
four maps.

**Two cells build tables at import time.** `build_story_html.py:197` and `:210`
call `compute_country_table()` inside the `CHAPTERS` list literal, so merely
importing the module reads four CSVs and computes both tables. Every figure uses
`build=lambda:` to defer; these two should too.

**Sixteen scratch `.py` files are dead** (seven `chapter2_*` prototypes and nine
`check_ch*` Playwright probes), alongside 118 screenshots and 18 stale HTML
builds, roughly 35 MB. These live only in the cloud working directory, not the
repo, so this is housekeeping rather than risk. Note that five files that look
like scratch are actually live and must not be deleted: `chapter1_cell.py`,
`chapter2b_country_table_cell.py`, `chapter5a_cell.py`, the four
`appendix_*_cell.py`, and `chapter2_shared.py` (imported transitively by
`chapter2b_binned_detail.py`).

**`Story.ipynb` has empty metadata**, no `kernelspec` or `language_info`. Both
legacy notebooks have them. Colab tolerates it; some viewers and `nbconvert`
lose syntax highlighting.

**Four dead variables** in the notebook: `ANSWER_CH2A` (cell 11),
`QUESTION_CH5C` and `ANSWER_CH5C` (cell 37), `YEAR_LABEL_COLOR_CH2` (cell 23).
No unused imports anywhere, which is a good ratio across 20 code cells.

---

## 9. The two legacy notebooks

Both still run, both reference files that still exist, and both are essentially
fully superseded by `Story.ipynb`. Three differences are deliberate improvements
in Story and should not be copied back: the button-title-on-click that triggered
the Plotly.js relayout bug, the `active=-1` row-reset trick that could not
colour the selected button, and the older row/column orientation.

One thing was genuinely lost in the merge, and it is worth restoring: **the
country-code legend table.** Chapter 1's map still renders "Not yet reporting:
BA, ME, XK" as bare two-letter codes, and there is now nowhere in `Story.ipynb`
or in the exported HTML to look them up. `Digitalization.ipynb` even says so
explicitly, that the codes "can be looked up in the legend table right after the
map". A small markdown table would close it.

Also lost, less important, are four developer diagnostics: a join sanity check
confirming the unmatched geo codes are exactly the EU/EA aggregates, a per-year
missing-data printout, a countries-reporting-per-year count with the invariant
that it should only ever rise, and a year dtype check. Those are developer
tools, not reader content, and the appendix would be the natural home if you
want them.

Two stale notes to clean up if the notebooks are kept: both say a boundary file
"was corrected this session, re-upload a fresh copy", which no longer means
anything, and both say "this notebook uses four files" then list three.

---

## 10. What is done well

This is not padding, and it is worth being specific about, because several of
these are things that are normally got wrong.

**The two pipelines agree byte for byte.** For a story maintained as two
independently hand-written HTML assemblers plus twelve hand-written notebook
mirrors, having zero drift across roughly forty prose blocks and every figure is
an unusual amount of discipline.

**The numbers hold.** Every quantitative claim in the story was recomputed from
the CSVs and reproduces: 749 country-year observations, median gap 2.72,
90.7% within 10 points, mean +3.90 for 2002-2011 and -1.73 for 2012-2025, era
medians 4.90 and 1.87, minimum country correlation 0.940, Switzerland 0.59 over
6 years, Albania 14.84 at r=0.963, Bulgaria 63.41 and 67.33 in 2017, the 21.8 to
12.6 point age gap, the 82.7-point 5c spread. Even a passing comment in the code
checks out: "actual max is 70.6% (FI, 16-24, 2023)" is 70.58, Finland, 16-24,
2023. The single exception is section 3.

**`decode.py` reproduces its four CSVs byte-identically**, from three different
working directories. Its `GEO44` list, `GEO44_LABEL` dict and `YEARS24` order
were checked against `dimension.geo.category.index` and `.label` in both raw
files and match exactly. Hand-rolled decoders against a flat-index API format
usually do not survive that check. Its path handling is correct and
cwd-independent; the note in `CLAUDE.md` calling it "hardcoded to its own
directory" is stale and should be corrected, since it will send the next reader
hunting a bug that was already fixed.

**Eurostat status flags are carried through rather than discarded**, with a
human-readable expansion alongside the code. Most ad-hoc Eurostat pipelines drop
`status` entirely and quietly present break-in-series points as continuous.

**The partial captures are documented honestly.** Each `raw_iu_age_*.json`
carries a `_note` stating plainly that it is not a byte-faithful dump, plus
`_source_url`, `_fetched`, and a `_shape` block giving the literal flat-index
formula. Labelling your own shortcuts that precisely is rare, and it is what
made this audit possible at all.

**The builders fail loudly.** No `try`/`except` anywhere in either build script,
so a broken chapter aborts before the output file is opened. A stale-but-valid
deliverable is never half-overwritten with a broken one.

**The notebook loads the 277 KB GeoJSON exactly once** and reuses it across all
four maps, and the chapter 1 animation attaches the geometry only to the first
frame, so 24 animation frames carry z and hover arrays rather than 24 copies of
the boundaries. Both legacy notebooks load it themselves; the merge got this
right.

**Comments explain why, not what.** The Kosovo fix explains the fill-order
versus hover-order conflict rather than just asserting a workaround. Cell 8
explains why Play and Pause need two separate `updatemenus`. The
`reporting_annotation` explains why it emits a single space instead of an empty
string. `_cluster_flags` justifies its 5.0 threshold with a concrete example.
Chapters 4 and 4b record the Plotly.js relayout bug that killed the map titles.
These are the notes that normally get lost.

**Accessibility is measured, not asserted.** "Contrast-checked at 4.21:1 (WCAG),
comfortably above the 3:1 floor for button-sized text" and "7.47:1, clear of the
4.5:1 text floor" are real numbers on real colour pairs.

**Every ANSWER is preceded by a comment naming the CSV and the exact figures it
was verified against.** That single convention is what made the numbers in
section 10 checkable at all, and it is the reason section 3 stands out as an
anomaly rather than blending in.

**Chapter 2's argument is well built.** The intro promises six looks and lists
them; the six sections that follow map onto those bullets in the stated order.
The three hypotheses are introduced once and then referenced by number in five
later sections. And the text explicitly declines to confirm hypotheses 1 and 2
from the mean-gap curve alone rather than overselling it.

**The appendix keeps a documented mistake.** It preserves a chart whose title
was wrong and explains the error in the comment: the title reads "From lagging
to caught up", that is backwards, caught by checking the per-country numbers
before publishing the claim. Keeping a documented wrong turn is better practice
than deleting it, and it is rare.

**The regression harness is real and green**, and `make_test_notebook.py`
correctly strips the Colab-only upload calls rather than trying to stub them.

**The notebook ships with zero outputs and no execution counts.** 149 KB of pure
source, diffable in git, no base64 bloat.

---

## Suggested order of work

1. Commit `digital_skills_above_basic.csv` and fix the "five CSVs" instructions
   (section 1). Nothing else matters until the notebook runs.
2. Fix the chapter 2 chart width (section 2). Visible to every reader.
3. Default chapters 4 and 4b to 2025 (section 4). One line each.
4. Resolve the EU27 above-basic provenance (section 3), either by saving the
   three values or by correcting the comment.
5. Add the missing "One more year: 2025" heading, unify the two greys, and fix
   the two "skills" strings (section 7).
6. Read the axis lengths from the JSON-stat response in `decode.py`
   (section 5), and save the raw response for the above-basic fetch.
7. Add the two-pipeline equality assertion (section 8). It passes today, so it
   can go in as a green baseline and will catch the next drift.
8. Everything else is housekeeping.
