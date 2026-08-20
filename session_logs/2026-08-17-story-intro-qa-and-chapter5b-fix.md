# 2026-08-17: Story intro section, bulleted chart intros, question/answer for every
chart, and a real data bug caught in chapter 5b

Jani's request had four parts: add a detailed data-source/intro section at the start of the
story; convert every chart's narrative intro text into bullet points (the format chapter2b/2c
already used); give every chart a question above and a concise, non-speculative answer below;
and open a discussion about what else the data could contribute to the story's conclusion.

## New "About the data" intro section

Added right after the page header, before chapter 1, in both `geospacific_story.html` and
`Story.ipynb`. Adapted (not copied verbatim) from the README's existing "Why this project says
'digital activities', not 'digital skills'" section, condensed for a general-audience story but
keeping real detail as asked:

- What each of the three Eurostat datasets measures, its country coverage, and its year range
  (household coverage and individual use go back to 2002; digital activities only exist for
  2021/2023/2025, a newer biennial indicator).
- The full "why activities, not skills" explanation: respondents self-report yes/no on specific
  activities rather than taking a skills test; the headline figure is conjunctive (all five
  DigComp areas at once); the inference only runs one way (doing implies being able, not doing
  implies nothing); non-users stay in the denominator; the 2021 methodology break.

`build_story_html.py` and `export_cell.py` both got a new `INTRO_HTML` block plus matching
`.intro` CSS (headings, bullet lists, an inline `<code>` style for the dataset IDs).
`build_notebook.py` got the same content as a new markdown cell, right after the title cell and
before the data-upload cells.

## Bulleted chart intros + question/answer for every chart

Chapters 1, 3, 4, 5a and 5b previously had plain prose `text` blocks and no `answer` at all
(only chapter2a/2b/2c had gone through this treatment already). Converted all five to bullet
lists, and added a `question` (new, styled bold above the chart) and a verified `answer` (below
the chart, reusing the existing `.answer` styling) to each, matching the chapter 2 pattern.

Every answer was checked against the actual CSVs before writing it down, not written from
memory:

- **Chapter 1** (coverage map): 2002 ranged 3.0% (Latvia) to 58.0% (Netherlands), 15 reporting
  countries, all below 90%. 2025 ranged 87.9% (Croatia) to 99.4% (Kosovo*), 36 countries, only
  5 below 90% (Croatia, Montenegro, Bosnia and Herzegovina, Greece, Lithuania).
- **Chapter 3** (age bars): EU27 16-24-to-55-74 use gap narrowed from 21.8 points (2021) to
  12.6 points (2025), driven almost entirely by the 55-74 group rising from 75.9% to 86.2%.
- **Chapter 4** (composite activities map): EU27 2025, internet use minus composite
  digital-activities score grows with age: 24.3 points for 16-24, 29.0 for 25-54, 43.6 for
  55-74. Being online is close to universal at every age; the composite figure is not.
- **Chapter 5a** (area breakdown bars): widest 16-24-to-55-74 gap by area is digital content
  creation (36.7 points), more than double the narrowest, communication and collaboration
  (15.5 points).
- **Chapter 5b** (least-common-activity scatter): see the bug fix below.

QUESTION/ANSWER constants were added directly to each chapter's own build script
(`chapter1_map.py`, `chapter3_age_bars.py`, `chapter4_map.py`, `chapter5a_area_breakdown.py`,
`chapter5b_bottleneck.py`), imported into `build_story_html.py`, and mirrored by hand into
`export_cell.py` and `build_notebook.py`'s markdown cells, following the same
two-build-paths-kept-in-sync convention already used for chapter 2.

## Real bug caught while verifying chapter 5b: the "safety for young and middle-aged" claim was wrong

While pulling the verified numbers for chapter 5b's new answer, re-checked which area is each
age group's own least common one, area by area, straight from
`digital_skills_by_area.csv` (EU27, 2025):

| Age group | Least common area | Value |
|---|---|---|
| 16-24 | Safety | 83.8% |
| 25-54 | **Digital content creation** | 78.3% |
| 55-74 | Digital content creation | 51.8% |

The chart's own dot placement was always correct (it computes `idxmin()` straight from the
data), but the chart's *subtitle* and every piece of surrounding prose (in
`chapter5b_bottleneck.py`'s docstring, `chapter5b_cell.py`, and the heading/text in all three
build scripts) claimed safety was the least common area for **both** the young and the
middle-aged group. That's only true for 16-24; for 25-54, digital content creation (78.3%) is
actually lower than safety (80.9%) for that group too. This was an assumption from an earlier
round that never got re-checked against the data once the chart existed.

Fixed everywhere: chart subtitle now reads "Content creation is least common for 25 and up;
safety for the youngest," the docstring explains the correction explicitly (so this doesn't
silently regress again), and the new question/answer/bullets all state the corrected version:
digital content creation is the least common area for both 25-54 and 55-74, and only 16-24 is
the exception (with safety, still their own strongest safety score of the three age groups).

`chapter5b_cell.py` had never been mirrored from `chapter5b_bottleneck.py` after last round's
per-dot-label rework (still had the old "bottleneck" language, no `cliponaxis`, no per-dot
labels, smaller figure size). Rewrote it to match exactly, including the fix above.

Also renamed the section heading everywhere from "Every generation has its own bottleneck" to
"Each generation's least common activity," to fully retire "bottleneck" language outside of the
one deliberate explanatory mention (the bullet that explains *why* it's not called that).

## Verification

- Rebuilt `geospacific_story.html` and `Story.ipynb` from all updated scripts; both built clean.
- Synced `/root/geospacific_work/` to `/root/geospacific_test/`, regenerated `test_notebook.py`
  from the rebuilt notebook, ran it standalone: all 16 code cells executed without errors,
  including the export cell.
- Full-page Playwright scroll-and-screenshot sweep of the rebuilt HTML: only the known,
  pre-existing benign `world_110m.json` console errors (unrelated to this project, which uses
  its own GeoJSON), nothing new.
- Confirmed via direct HTML inspection: intro section present, 5 new question blocks, zero
  em dashes, and the one remaining "bottleneck" text is the intentional explanatory mention,
  not a leftover.
- Visually confirmed the corrected chapter 5b chart: the 25-54 diamond now reads "Digital
  content creation 78.3%" instead of the old, wrong "Safety."
- Delivered both files to Jani (SendUserFile + `device_commit_files`, mtime-guarded) to
  `geospacific_story.html` (repo root) and `notebooks/Story.ipynb`.

## Open items

1. The chapter2b flag-rendering report from the 08-16 round is still unconfirmed by Jani; not
   reproducible in this sandbox.

## Round 2: new "Where each activity stands across countries" map + conclusion section

Jani liked the "access is solved, activity is not, and that's true both across ages and across
countries" framing and asked what the two unused ranking spreadsheets
(`household_internet_ranking.xlsx`, `digital_skills_ranking_2025.xlsx`) contain, and whether
they could help. Checked: both are static, single-year leaderboards (rank/country/%) of numbers
already present in `data/processed/`, already superseded by this project's own interactive maps
(chapter 1 and chapter 4 already let you find any country's exact rank via hover), so nothing
new to add there. Told her this plainly rather than repurposing them just because they existed.

She then proposed a better, genuinely new idea: reuse the map format (like chapter 4) but drill
into individual DigComp areas instead of the composite, with buttons to pick an activity area
and age group, purple to match chapter 4 (her call: "same topic, different angle," which fits
the project's existing color language). This uses country-level detail from
`digital_skills_by_area.csv` that had ONLY ever been shown as an EU27 aggregate (chapter 5a/5b)
- genuinely unused country-level data, a better find than the ranking spreadsheets.

Built it as `chapter5c_area_map.py` (+ `chapter5c_cell.py` mirror), reusing chapter 4's
per-button-menu recoloring trick and Kosovo dedicated-trace pattern almost verbatim. One layout
change from chapter 4's grid: chapter 4 puts years (short labels) in rows and age groups in
columns; here there's no year dimension (the area-level dataset only has 2025), so age group
(short labels: 16-24 etc.) went in rows and the 5 activity areas in columns instead, since area
names ("Digital content creation") are too long to fit as row labels in the narrow left margin
next to the buttons, but work fine as (abbreviated) button labels spread across the map's full
width. 20 buttons total (4 age groups x 5 areas), same color-flip mechanism as chapter 4's 12.

While picking a default view, checked all 20 area/age-group combinations for their country-level
spread and found the widest in the whole dataset: digital content creation among 55-74 year
olds ranges from 9.4% (Albania) to 92.0% (Kosovo*), an 82.7-point spread. Set that as the map's
default view instead of an arbitrary top-left combination, since it's the single sharpest
illustration of the story's closing thesis in the whole project.

Added as a new "closer look" section after chapter 5b (same unnumbered pattern as 2b/2c and
5b), with its own bulleted intro, question, and verified answer, then a short text-only
**Conclusion** section at the very end (no new chart) synthesizing all five chapters: coverage
is close to solved (87.9%-99.4% by 2025), the composite activity figure is not and splits by
age (42.6% vs 74.6%, 55-74 vs 16-24), and splits even more sharply by country within one age
group and one activity (the 82.7-point spread above). Ends by explicitly stating what the data
can't answer (why the gaps are so large) rather than speculating about causes.

### A real rendering limitation surfaced, unrelated to any of today's changes

While checking chapter 5c's map render, discovered that in THIS sandbox, choropleth maps never
actually draw their country shapes at all (0 SVG path elements in the DOM), not just an
occasional visual glitch. Root cause: `showland`/`showocean` in `update_geos()` require plotly.js
to fetch a base world topojson from `cdn.plot.ly`, which this sandbox cannot reach
(`ERR_TUNNEL_CONNECTION_FAILED`); the fetch failure aborts the entire geo subplot's rendering,
even though our own country data is supplied directly via a local GeoJSON and doesn't itself
need the network. Confirmed this is NOT new and NOT specific to chapter 5c: chapter 1's and
chapter 4's maps, both already-shipped and working chapters, show the exact same blank result
here. This matches (and now explains precisely) the "benign, pre-existing" console error noted
in earlier session logs - it's benign for Jani (her real browser has real internet, so the
fetch succeeds and the map draws normally), but it does mean this sandbox can never visually
screenshot-verify actual map coloring, only the surrounding layout, data, and button behavior.
Verified chapter 5c the same way chapter 4's buttons were verified previously in this project:
confirmed the correct default z-values/hover text via direct Python inspection, confirmed all
20 buttons render with correct labels/positions/colors via screenshot, and confirmed the
color-flip click logic works via a live click test reading the actual SVG `fill` attributes
before and after (button 0 flipped from selected dark purple to unselected light purple; the
clicked button flipped the other way).

### Verification

- `chapter5c_area_map.py` rendered standalone cleanly; data spot-checked against
  `digital_skills_by_area.csv` (82.7-point spread confirmed: Albania 9.35%, Kosovo* 92.01%).
- Rebuilt `geospacific_story.html` (8.3 MB, up from 7.2 MB) and `Story.ipynb` (45 cells, up from
  41) from all updated scripts.
- Synced to `/root/geospacific_test/`, regenerated and ran `test_notebook.py`: all 17 code cells
  executed cleanly, including the new chapter 5c cell and the export cell.
- Full-page Playwright sweep: only the known `world_110m.json` errors, now 3 instances (one per
  map: chapters 1, 4, 5c) instead of 2, exactly as expected, nothing unexpected.
- Confirmed via direct HTML inspection: new chapter 5c section present, conclusion section
  present, 6 question blocks total, zero em dashes, no stray "bottleneck" text.
- Delivered both files to Jani (SendUserFile + `device_commit_files`, mtime-guarded).

## Open items

1. The chapter2b flag-rendering report from the 08-16 round is still unconfirmed by Jani; not
   reproducible in this sandbox.
2. The actual choropleth country coloring (chapters 1, 4, 5c) has never been visually confirmed
   from within this sandbox, for the network reason explained above; it relies on the underlying
   data being correct (which is checked directly) and on Jani's own real-internet browser to
   render it, same as it always has for chapters 1 and 4.
