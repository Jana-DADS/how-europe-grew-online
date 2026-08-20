# Geospatial

**Jana Dolečková** · Data Analyst
- Defined the research question and scope: how internet access and digital activities have spread across Europe over time
- Selected and vetted the data sources (Eurostat, GISCO, OpenStreetMap)
- Directing the analysis and visualization design through iterative prompt design, reviewing each round of output
- Testing each iteration in Colab and isolating rendering bugs, including the Kosovo/Serbia overlap, where the reported symptom (hover worked *only* in 2007–2016) was what pinned down the actual cause after two wrong hypotheses

**Claude** (Anthropic AI assistant)
- Fetched and decoded the Eurostat datasets, fixed path handling in `scripts/decode.py`
- Fetched, filtered, and merged the country boundary data (GISCO + OpenStreetMap for Kosovo, Iceland, and the UK), with checksum-verified data integrity
- Building the analysis and animated choropleth maps in Google Colab (Python, pandas, plotly), executing on prompted direction
- Models used: Claude Sonnet 4.5 for most of the work; Claude Opus 5 was brought in to diagnose the Kosovo/Serbia hover-and-draw-order bug after the earlier attempts had misdiagnosed it

## About the project

Interactive plotly maps and charts exploring how internet access and digital activities have spread across Europe, 2002–2025. It covers household internet access, individual internet use, and digital activities (by age, by DigComp area, and at the stricter "above basic" level), visualized as animated and clickable choropleth maps, alongside a set of supporting charts and tables that test three hypotheses about how coverage and use relate to each other. Built and prototyped in Google Colab, published as [`geospatial_story.html`](geospatial_story.html): a single self-contained interactive file, ten charts and tables across five chapters plus several "closer look" sub-sections, that opens in any browser with no login or extra software (the interactive maps do need an internet connection, since they fetch their base map layer from Plotly's CDN). The companion notebook, [`notebooks/Story.ipynb`](notebooks/Story.ipynb), builds the same story from the same code and can regenerate the HTML file itself in its last cell.

**Status: complete.** Data collection, analysis, the interactive HTML story, and the companion notebook are all finished and published.

## Data sources

**Statistics**, from [Eurostat](https://ec.europa.eu/eurostat):

| Dataset | Used for | Coverage |
|---|---|---|
| `isoc_ci_in_h` | Household internet access (% of households) | 44 geo entities (38 countries + 6 historical EU/EA aggregates), 2002–2025 |
| `isoc_ci_ifp_iu` | Individuals who used the internet in the last 3 months (% of individuals) | 44 geo entities (38 countries + 6 aggregates), 2002–2025 |
| `isoc_ci_ifp_iu` (by age) | The same indicator split by age group (16–24 / 25–54 / 55–74) | 39 geo entities (37 countries + EU27_2020 + EA), 2021–2025 |
| `isoc_sk_dskl_i21` | Basic or above basic overall digital activities (% of individuals), by age group | 39 geo entities (37 countries + EU27_2020 + EA), 2021 / 2023 / 2025 |
| `isoc_sk_dskl_i21` (by area) | The same, split into the five DigComp areas separately, by age group | 38 geo entities (36 countries + EU27_2020 + EA), 2025 only |
| `isoc_sk_dskl_i21`, `indic_is=I_DSK2_AB` (above basic) | The stricter "above basic" level only (all five DigComp areas at once), by age group | 39 geo entities (37 countries + EU27_2020 + EA), 2021 / 2023 / 2025 |

The age-group split of internet use was added so that use and activities can be compared like for like. Without it, the activity levels of 55–74 year olds were being weighed against internet use across the whole 16–74 population, which flatters the older group's ratio. The three raw files behind it (`data/raw/raw_iu_age_*.json`) are **partial captures**; only the `value` and `status` payloads were retained, not the full JSON-stat document. Each file carries a `_note`, a `_source_url` and the `_shape` needed to decode it; re-fetch the URL for the complete response.

The "above basic" breakdown was fetched separately and later than the other four rows, one country/age-group combination at a time (`indic_is=I_DSK2_AB`, `unit=PC_IND`), and saved to `data/processed/digital_skills_above_basic.csv`. It uses the same 37-country set as the other digital-activities data (missing the UK, which Eurostat doesn't publish this indicator for); the EU27_2020 and EA aggregate rows were added later, once the story's chapter 4b text started quoting them, so the numbers it references are verifiable straight from the file. Sanity-checked against the existing "basic or above" figures at fetch time: above-basic is less than or equal to basic-or-above in every one of the 446 country-year-age values compared, zero violations, which is strong evidence the fetch and the join both came through correctly.

### Why this project says "digital activities", not "digital skills"

Worth reading before interpreting any of these numbers, because the indicator is easy to misread as a competence test. It is not one.

`isoc_sk_dskl_i21` is the **Digital Skills Indicator 2.0**, a composite built on the EU survey on ICT usage in households. Respondents aged 16–74 are not tested and are not asked to rate themselves; they are asked **yes/no whether they performed specific activities**, in the three months before the survey (twelve months for online purchases). Having done the activity is taken as a proxy for having the skill.

Because of this activity-based measurement, this project uses "digital activities" instead of "digital skills" in its own writing (chart titles, code, and the rest of this README), except when naming Eurostat's dataset and indicator directly (`isoc_sk_dskl_i21`, "Digital Skills Indicator 2.0"), where the original name is kept for traceability.

Activities are grouped into the five areas of the [DigComp 2.0](https://joint-research-centre.ec.europa.eu/digcomp_en) competence framework:

| Area | Activities counted | "basic" | "above basic" |
|---|---|---|---|
| Information and data literacy | finding information on goods/services; seeking health information; reading online news; fact-checking online information and its sources | exactly 1 | 2 or more |
| Communication and collaboration | email; internet phone/video calls; instant messaging; social networks; expressing opinions on civic/political issues online; online consultations or voting | exactly 1 | 2 or more |
| Digital content creation | word processor; spreadsheet; editing photo/video/audio; copying or moving files between folders, devices or cloud; creating documents combining text, images, tables, charts; advanced spreadsheet features (formulas, macros); writing code | 1 or 2 | 3 or more |
| Safety | checking a site was secure before giving personal data; reading privacy statements; restricting access to geographical location; limiting access to a social-media profile; refusing use of personal data for advertising; changing browser cookie settings | 1 or 2 | 3 or more |
| Problem solving | installing software/apps; changing device or app settings; online purchases; selling online; using online learning resources; internet banking; job search or applications | 1 or 2 | 3 or more |

Note that "basic" is a *band*, not a floor: the two rightmost columns differ only in where the boundary between the two levels sits, which is calibrated to how demanding each area's activities are. The entry bar is the same everywhere: one activity. Since this project uses the combined **"at least basic"** figure (basic *or* above basic), the effective rule throughout is simply **at least one activity in each of the five areas**, and the basic/above-basic split does not affect any number reported here.

**The headline figure used throughout this project is "at least basic overall digital activities", and it is conjunctive: an individual must reach at least basic level in *all five* areas simultaneously.** Falling short in a single area excludes them from the indicator regardless of how strong the other four are. This is the main reason the 55–74 figures come out so low: someone who emails, reads news and shops online but never installs an app or uses internet banking can still fail the problem-solving area and drop out entirely.

Individuals who did not use the internet at all in the previous three months are classed as "could not be assessed" but **remain in the denominator** (all individuals aged 16–74), so non-use feeds through into a lower digital activities percentage.

**The indicator measures activity, not ability: the inference only runs one way.** Eurostat states the assumption plainly: individuals who performed an activity are taken to have the corresponding skill. Doing implies being able; *not* doing implies nothing. Someone who spent thirty years working in spreadsheets but has had no reason to open one since retiring is counted identically to someone who has never seen one. This does not fall evenly across the five areas: communication and information activities are part of everyday life at any age, whereas digital content creation and problem solving (spreadsheets, documents, installing software, job applications) are tied to working and administrative life. So part of the steep decline in the 55–74 figures may be measuring withdrawal from that life rather than loss of skill. Treat the age gradient (particularly in digital content creation) as an upper bound on the true skills gap, not a direct measurement of it.

A second, smaller caveat on reading the headline figure: because it requires all five areas at once, it sits *below* even the weakest individual area. For 55–74 year olds in 2025 the weakest area (digital content creation) averages 51.8% while the overall figure is 42.6%. Perfect overlap between the areas would have put the overall at 51.8%; statistical independence would have put it at 14.6%. The real 42.6% shows the five areas are strongly but not perfectly correlated: different people are missing different areas.

Because the DSI methodology changed substantially in 2021 to follow DigComp 2.0, 2021 is the start of a new series and figures are not comparable with pre-2021 digital activities data.

Sources: [ESMS metadata for `isoc_sk_dskl_i21`](https://ec.europa.eu/eurostat/cache/metadata/en/isoc_sk_dskl_i21_esmsip2.htm) · [Eurostat DSI glossary entry](https://ec.europa.eu/eurostat/statistics-explained/index.php?title=Glossary:Digital_Skills_Indicator_(DSI)) · [European compiler's manual, 2023 survey (PDF)](https://ec.europa.eu/eurostat/documents/3859598/18369653/KS-GQ-23-019-EN-N.pdf)

### Country boundaries

[GISCO](https://ec.europa.eu/eurostat/web/gisco) (Eurostat's geographic information service), `CNTR_RG_20M_2024_4326`, 1:20M resolution, WGS84. Free to reuse for non-commercial purposes with attribution: © EuroGeographics for the administrative boundaries.

GISCO's own country dataset deliberately excludes Kosovo: five EU member states (Spain, Slovakia, Romania, Greece, Cyprus) do not recognize its independence, so Eurostat/GISCO omits it entirely rather than folding it into Serbia. To keep Kosovo on the map, its boundary was added separately from [OpenStreetMap](https://www.openstreetmap.org) (relation `2088990`), simplified with Douglas-Peucker (ε=0.01°) to match GISCO's generalization level. This is flagged directly in the data via a `SOURCE_NOTE` property on that feature, so the mixed provenance is transparent wherever the boundary file is used, not just here.

Iceland and the United Kingdom also use OpenStreetMap boundaries (relations `299133` and `62149`) instead of GISCO's, for a technical rather than political reason: GISCO's generalized coastline for these two didn't align closely enough with Plotly's own basemap underneath it, leaving visible gaps along jagged coastline (northern Iceland, northern UK/Scottish islands). The OSM boundaries were simplified the same way (Douglas-Peucker, ε=0.01°) to match GISCO's detail level elsewhere.

## Data notes and limitations

- Kosovo's statistics are labeled `Kosovo*` in the Eurostat data (standard notation referencing UN Security Council Resolution 1244/1999) and have gaps: internet access/use figures cover 2017–2020 and 2024–2025 (missing 2021–2023), and digital activities cover only 2025 (missing 2021, 2023).
- The digital activities dataset only has 3 time points (2021, 2023, 2025) since it's biennial and was introduced in 2021, not a continuous yearly series like the internet access/use data.
- Country coverage differs slightly by dataset: the internet datasets include historical EU aggregates (EU28, EU27_2007, etc.) not present in the digital activities dataset.
- **Kosovo's shape overlaps Serbia's by about 99% of Kosovo's area.** GISCO's Serbia boundary has no hole cut out for Kosovo (consistent with GISCO not recognizing its independence; see above), so on the map the two shapes sit almost exactly on top of each other. Within a single plotly trace this is unfixable by ordering alone, because two plotly rules pull in opposite directions: countries are **drawn** in list order, so the last one covers the ones before it, while **hover** walks the same list and stops at the *first* shape containing the cursor. Whichever of the two is listed last is therefore visible but un-hoverable, and whichever is first is hoverable but hidden underneath. The fix is to give Kosovo its own pair of traces, added after the others: later traces both draw on top and take hover priority, so Kosovo ends up correct on both counts. First implemented in the "Map over time" cell of `notebooks/Digitalization.ipynb` and the age-group map cell of `notebooks/DigitalSkills.ipynb`; carried over into every map in the current `notebooks/Story.ipynb` (chapter 1's coverage map and the chapter 4/4b/5c digital-activities maps), each with a comment explaining the reasoning.

  Two related quirks were worked around in the same cell: `plotly express`'s automatic animation controls had to be rebuilt by hand (the slider only follows the Play button when its steps use `method='animate'`), and the "not yet reporting" caption is emitted as a single space rather than an empty string when every country is reporting: during animation an empty string doesn't overwrite the previous frame's text, so the last non-blank year's list would otherwise stay on screen for the rest of the playback.

## Project structure

```
Geospatial/
├── data/
│   ├── raw/         # untouched JSON-stat 2.0 responses from the Eurostat API
│   ├── processed/   # tidy CSVs, decoded from data/raw/, ready for pandas.read_csv()
│   └── geo/         # country boundary GeoJSON (35 GISCO countries + Kosovo/Iceland/UK from OpenStreetMap)
├── notebooks/
│   ├── Story.ipynb          # the current, complete notebook: builds all ten charts/tables and,
│   │                        # in its last cell, exports geospatial_story.html itself
│   ├── DigitalSkills.ipynb  # earlier, single-topic notebook (digital activities only); superseded by Story.ipynb
│   └── Digitalization.ipynb # earlier, single-topic notebook (coverage/use only); superseded by Story.ipynb
├── scripts/
│   └── decode.py    # decodes data/raw/ into data/processed/
├── session_logs/    # dated development notes, newest first
├── geospatial_story.html  # the published, self-contained interactive story (see "About the project")
└── README.md
```

## Tools

Google Colab · plotly for interactive/animated choropleth maps (GeoJSON boundaries loaded and merged with pandas and the standard library's `json` module; geopandas isn't used anywhere in the current pipeline)
