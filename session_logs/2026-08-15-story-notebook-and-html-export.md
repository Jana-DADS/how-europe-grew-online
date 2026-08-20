# 2026-08-15 — Story notebook built, HTML export, restructured chapter order

Continues [[2026-08-14-presentation-story-and-color-scheme]]. That session ended with
chapter 4 (3×3 coverage-bins grid) visually done but nothing assembled, and the output
format still undecided. This session Jani came back with a materially different chapter
plan and the format decision resolved to plotly HTML (a decision that had actually
already been made in [[2026-08-13-notebooks-and-kosovo-render-bug]] — "Presentation
format was settled early as plotly HTML export" — but wasn't in the 08-14 log, so it read
as still-open until Jani reminded me and it turned up in the 08-13 log on a second pass).

## What shipped

- `notebooks/Story.ipynb` (new, 20 cells) — self-contained Colab notebook, Jani's
  `google.colab.files.upload()` pattern for data loading (same convention as the two
  existing notebooks), 5 chapters + a "closer look" + an export cell.
- `geospacific_story.html` (new, repo root, 7.15 MB) — single offline HTML file, all 6
  charts embedded with plotly.js inlined (not CDN-linked — see "HTML self-containment"
  below for why that distinction mattered). Also produced by the notebook's last cell
  when run in Colab (`files.download(...)`).
- Both delivered to Jani and written to her local repo. **Not committed to git** — repo
  is still pre-push per Jani's standing instruction from 08-13.

Both were tested end-to-end in this sandbox before delivery (see "Testing method"), not
just visually spot-checked.

## The new chapter order (supersedes 08-14's plan)

Jani rethought the story shape entirely this session. New order, replacing 08-14's
chapters 1–4:

1. Blue coverage map (unchanged, carried over verbatim from `Digitalization.ipynb`).
2. **New** — coverage-vs-use scatter, 5 key years (2002/2008/2014/2019/2025), grayscale
   by year. Explicitly **replaces** 08-14's 3×3 binned-grid chart
   (`coverage_bins_by_year_grid.py`) — Jani's call, made via AskUserQuestion at the start
   of this session. That script and its predecessors from 08-14 are now fully dead; don't
   resurrect.
3. Use-by-age grouped bar chart, EU27 2021–2025 — same design as 08-14's
   `coverage_vs_age_use_eu27.png` (approved then), just rebuilt in plotly for
   interactivity. No design changes.
4. Purple digital-skills map (unchanged, carried over verbatim from `DigitalSkills.ipynb`).
5. Digital-skills-by-area breakdown (rebuilt from the 08-13 session's
   `digital_skills_by_area_2025.png`, which had never made it into a notebook or the
   repo — only existed as a scratch PNG) + a new "bottleneck" chart, see below.

Chapters 2 and 5 needed full rebuilds from source CSVs since their prior versions only
ever existed as scratch outputs from earlier sessions, never saved to the repo.

## The safety-gap correction — read this before trusting any "young lag in X" claim

08-14's chapter plan said the story would show "young people (16-24) actually lag
*behind* in Safety specifically." **This is not what `digital_skills_by_area.csv`
shows.** Checked directly (EU27_2020, 2025, `pct_basic_or_above`):

| area | 16-24 | 25-54 | 55-74 |
|---|---|---|---|
| Safety | 83.8 | 80.9 | 61.6 |

16-24 scores *highest* of the three groups on Safety, not lowest — they don't lag behind
anyone. What's actually true, and well-supported (matches the 08-13 log's "bottleneck
moves with age" finding): **Safety is the young's and middle-aged's own weakest area**
among their five — a within-person bottleneck, not a between-generation deficit. For
55-74 the bottleneck is Digital content creation (51.8%) instead. Built chapter 5's
second chart (`fig5b` / "Every generation's bottleneck") around this corrected framing —
red/coral dots per area per age group, the minimum per age group highlighted as a
diamond marker. Flagged this to Jani mid-session before building anything on the wrong
premise; she said to continue, so I picked the bottleneck framing myself rather than
re-asking.

**If a future session is tempted to build a "young underperform old at X" chart from
this dataset, verify the exact numbers first** — same CLAUDE.md rule as 08-14's
"skoro všechny" correction, now with a second instance.

## A second number-consistency bug, caught before delivery

Chapter 5a's narrative text originally said "the steep 38.1% overall figure" for 55-74's
composite skills score. **38.1% is the unweighted country-average figure from the 08-13
log's separate table** (`digital_skills_by_area.csv` averaged across 38 countries) — not
what chapter 5a actually plots, which is the EU27_2020 aggregate row (42.6% for that same
cell). Caught by re-deriving every narrative number from the exact dataframe each chart
uses, rather than trusting a number carried over from a different session's different
aggregation method. Fixed in `build_notebook.py`, `build_story_html.py`, and
`export_cell.py` (all three had the same copy-pasted error — they share narrative text by
design, so one `sed` fixed all three). **Lesson for later sessions: EU27_2020-aggregate
numbers and unweighted-38-country-average numbers are different metrics that happen to
be close in magnitude (42.6 vs 38.1) — easy to conflate, always cite the one the chart
actually uses.**

## Deferred color-scheme item, still deferred

08-14 explicitly deferred recoloring `digital_skills_by_area_2025.png`'s five DigComp
areas into the red/coral "individual activity" family (vs. the current green age-based
coloring). Asked Jani about it directly this session (AskUserQuestion) but she moved on
to describing the new story shape without answering that specific question, and by the
time chapter 5a was built the natural design choice was to keep age-as-color (green) since
age is the more central comparison in this chart — area is already on the x-axis as
labels, doesn't need its own color too. Noted this reasoning inline in both the notebook
markdown and said explicitly in `chapter5a_area_breakdown.py`'s docstring. **Still open**
if Jani wants to revisit; not resolved, just deliberately not blocking on it a second time.

## HTML self-containment — CDN vs inline plotly.js

First build of `geospacific_story.html` used `<script src="https://cdn.plot.ly/...">`.
Tested in this sandbox with Playwright and the CDN failed to load (`ERR_TUNNEL_CONNECTION_FAILED`
— this sandbox's network doesn't reach that host), which incidentally caught a real design
flaw: Jani's requirement was "kdokoliv otevře bez speciálního software" (anyone opens it
without special software), which implies no internet dependency either, not just no
installed app. Switched to embedding `plotly.offline.get_plotlyjs()` inline once in a
`<script>` tag (not per-chart, which would have 6×'d the ~1MB library) — file grew from
~2.3MB to ~7.15MB but now verified to render all 6 charts correctly with Playwright's
`offline=True` context (zero network). This is the version delivered; if a future session
regenerates the HTML, keep it inline, don't "optimize" back to a CDN link.

## Testing method used

Extended the 08-13 log's approach (extract non-upload code cells to a `.py`, run against
copies of the real CSVs/GeoJSON, replace `fig.show()` with a print) to also exercise the
new export cell: after building `Story.ipynb`, generated a stripped test script that skips
both `files.upload()` cells, strips the `google.colab` import and `files.download(...)`
call from the export cell, and ran the rest end-to-end in `/tmp`-equivalent scratch dirs
against real data — including regenerating `geospacific_story.html` from inside the
"notebook" run, not just from the standalone `build_story_html.py` script, to make sure
the two code paths (notebook cells vs. the dev script) don't drift. Then loaded the actual
output HTML in headless Chromium (`/opt/pw-browsers/chromium`, offline context) and
asserted 6 `section.chapter` and 6 `.js-plotly-plot` divs render with zero console errors.
This project doesn't have any automated tests beyond this — worth reusing this harness
verbatim for any future notebook/HTML changes rather than only checking visually.

## Where things stand

- Repo: `notebooks/Story.ipynb` and `geospacific_story.html` (root) are new, written to
  Jani's disk, **not committed to git** (still pre-push).
- `notebooks/Digitalization.ipynb` and `notebooks/DigitalSkills.ipynb` are unchanged —
  `Story.ipynb` reuses their map logic but doesn't replace them; kept as-is for whatever
  reason they were split into two notebooks originally (not investigated this session).
- All 5 chapter-building scripts (`chapter1_map.py` … `chapter5b_bottleneck.py`,
  `build_story_html.py`, `build_notebook.py`, `export_cell.py`, plus the 6 `*_cell.py`
  source files the notebook cells are built from) exist only in this session's sandbox
  workspace, not in the repo. If Jani wants to regenerate or tweak the HTML/notebook
  without going through Colab, these would need to be added to `scripts/` or similar —
  currently the only way to reproduce `geospacific_story.html` outside Colab is to re-run
  this session's now-gone sandbox files, or re-derive from `Story.ipynb`'s cells by hand.
- Chapters 1-3 of README's "Status" line ("analysis, notebook, and presentation in
  progress") is now more done than the README reflects — README not updated this session.

## Next steps

1. Jani review of `Story.ipynb` in actual Colab (this session only verified headless —
   the established pattern per 08-13 is that Colab-specific rendering/hover bugs only
   ever surface in real Colab, not in the sandbox harness).
2. Decide whether the standalone chapter scripts should move into the repo (e.g.
   `scripts/story/`) so `geospacific_story.html` is regenerable without Colab.
3. Revisit the deferred digital_skills-by-area red/coral recoloring question if Jani
   still wants it — not resolved this session, see above.
4. Update README's status line and project structure section once Jani signs off on the
   notebook — currently doesn't mention `Story.ipynb` or the HTML export at all.
5. Still gated on Jani's explicit approval before any `git push` (standing instruction
   since 08-13).
