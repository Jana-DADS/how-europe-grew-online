import json, csv, os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data", "raw"))
PROCESSED_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "data", "processed"))

GEO44 = ["EU27_2020","EU28","EU27_2007","EU25","EU15","EA","BE","BG","CZ","DK","DE","EE","IE","EL","ES","FR","HR","IT","CY","LV","LT","LU","HU","MT","NL","AT","PL","PT","RO","SI","SK","FI","SE","IS","NO","CH","UK","BA","ME","MK","AL","RS","TR","XK"]
GEO44_LABEL = {"EU27_2020":"European Union - 27 countries (from 2020)","EU28":"European Union - 28 countries (2013-2020)","EU27_2007":"European Union - 27 countries (2007-2013)","EU25":"European Union - 25 countries (2004-2006)","EU15":"European Union - 15 countries (1995-2004)","EA":"Euro area","BE":"Belgium","BG":"Bulgaria","CZ":"Czechia","DK":"Denmark","DE":"Germany","EE":"Estonia","IE":"Ireland","EL":"Greece","ES":"Spain","FR":"France","HR":"Croatia","IT":"Italy","CY":"Cyprus","LV":"Latvia","LT":"Lithuania","LU":"Luxembourg","HU":"Hungary","MT":"Malta","NL":"Netherlands","AT":"Austria","PL":"Poland","PT":"Portugal","RO":"Romania","SI":"Slovenia","SK":"Slovakia","FI":"Finland","SE":"Sweden","IS":"Iceland","NO":"Norway","CH":"Switzerland","UK":"United Kingdom","BA":"Bosnia and Herzegovina","ME":"Montenegro","MK":"North Macedonia","AL":"Albania","RS":"Serbia","TR":"Türkiye","XK":"Kosovo*"}
YEARS24 = [str(y) for y in range(2002, 2026)]

GEO39 = ["EU27_2020","EA","BE","BG","CZ","DK","DE","EE","IE","EL","ES","FR","HR","IT","CY","LV","LT","LU","HU","MT","NL","AT","PL","PT","RO","SI","SK","FI","SE","IS","NO","CH","BA","ME","MK","AL","RS","TR","XK"]
GEO39_LABEL = {"EU27_2020":"European Union - 27 countries (from 2020)","EA":"Euro area","BE":"Belgium","BG":"Bulgaria","CZ":"Czechia","DK":"Denmark","DE":"Germany","EE":"Estonia","IE":"Ireland","EL":"Greece","ES":"Spain","FR":"France","HR":"Croatia","IT":"Italy","CY":"Cyprus","LV":"Latvia","LT":"Lithuania","LU":"Luxembourg","HU":"Hungary","MT":"Malta","NL":"Netherlands","AT":"Austria","PL":"Poland","PT":"Portugal","RO":"Romania","SI":"Slovenia","SK":"Slovakia","FI":"Finland","SE":"Sweden","IS":"Iceland","NO":"Norway","CH":"Switzerland","BA":"Bosnia and Herzegovina","ME":"Montenegro","MK":"North Macedonia","AL":"Albania","RS":"Serbia","TR":"Türkiye","XK":"Kosovo*"}
YEARS3 = ["2021", "2023", "2025"]
YEARS5 = ["2021", "2022", "2023", "2024", "2025"]

# Sanity checks on the hand-transcribed geo lists, run once at import time:
# catches a typo'd/missing label before any file gets touched, rather than a
# bare KeyError mid-write leaving a partial CSV in place.
assert set(GEO44) <= set(GEO44_LABEL), f"GEO44 codes missing a label: {set(GEO44) - set(GEO44_LABEL)}"
assert set(GEO39) <= set(GEO39_LABEL), f"GEO39 codes missing a label: {set(GEO39) - set(GEO39_LABEL)}"

STATUS_LABEL = {
    "b": "break in time series", "e": "estimated", "u": "low reliability",
    "bu": "break in time series, low reliability",
    "d": "definition differs", "p": "provisional", "c": "confidential",
    "n": "not significant", "f": "forecast", "s": "Eurostat estimate",
}
_unmapped_flags_warned = set()


def _status_desc(flag, source_label):
    """Look up a human-readable label for an Eurostat status flag. Warns
    once per unmapped flag instead of silently returning a blank
    description (a future re-fetch could introduce a flag combination not
    in STATUS_LABEL, e.g. 'du')."""
    if not flag:
        return ""
    if flag in STATUS_LABEL:
        return STATUS_LABEL[flag]
    if flag not in _unmapped_flags_warned:
        print(f"  WARNING: {source_label} has unmapped status flag {flag!r} "
              f"(add it to STATUS_LABEL); leaving its description blank for now.")
        _unmapped_flags_warned.add(flag)
    return ""


def _check_axis_length(raw, dim_name, expected_len, source_label):
    """If the raw response carries full JSON-stat dimension metadata (not
    all of this project's raw files do - the dskl/iu_age files are partial
    captures with no 'dimension' key), assert the named dimension's
    category count matches what the flat-index arithmetic below assumes.
    This is what catches a silent index shift the next time Eurostat adds a
    year to the series: without it, the decoder happily reads every value
    one slot off with no error (confirmed by reconstructing a 25-year
    version of raw_isoc_ci_in_h.json and re-running this script: 695 of 714
    overlapping values came back wrong, silently)."""
    dim = raw.get("dimension", {}).get(dim_name)
    if dim is None:
        return  # partial capture, no dimension metadata available to check
    actual_len = len(dim["category"]["index"])
    assert actual_len == expected_len, (
        f"{source_label}: expected {expected_len} categories in dimension "
        f"'{dim_name}', but the raw response has {actual_len}. The flat-index "
        f"arithmetic in this script assumes the old length - update GEO44/"
        f"GEO39/YEARS24/YEARS3/YEARS5 above before trusting the decoded output.")


def _check_no_leftover_values(raw, consumed_indices, source_label):
    """Fallback for the partial-capture raw files (dskl/iu_age), which carry
    no dimension metadata to check against: confirm every key actually
    present in raw['value'] is one this decoder consumed. If the source
    dataset ever grows a dimension (e.g. a new year added on re-fetch),
    indices beyond what GEO/YEARS currently expect will show up here, and
    this trips instead of silently shifting every value one slot over."""
    present = set(int(k) for k in raw.get("value", {}))
    leftover = present - consumed_indices
    assert not leftover, (
        f"{source_label}: raw response has values at indices {sorted(leftover)[:5]}"
        f"{'...' if len(leftover) > 5 else ''} that this decoder never reads. "
        f"The data's shape has grown (new year/category?) - update GEO/YEARS "
        f"above before trusting the decoded output.")


def _unit_block_offset(raw, geo_len, time_len, source_label, prefer="PC_IND"):
    """Most of this project's flat-index arithmetic assumes geo and time are
    the last two dimensions and every other dimension has exactly one
    category, which is true for raw_isoc_ci_in_h.json. raw_isoc_ci_ifp_iu.json
    is the one exception: its 'unit' dimension has two categories (PC_IND
    and PC_IND_ILT12), so reading it with plain geo_i*time_len+time_i only
    happens to work today because PC_IND is category index 0 there. This
    computes the correct block offset from the response's own dimension
    metadata instead of relying on that coincidence, and raises rather than
    guessing if any OTHER dimension besides geo/time/unit ever gets a
    second category."""
    ids, sizes = raw.get("id"), raw.get("size")
    if ids is None or sizes is None:
        return 0  # partial capture, no metadata - nothing to adjust for
    dim_size = dict(zip(ids, sizes))
    for name, size in dim_size.items():
        if name in ("geo", "time", "unit"):
            continue
        assert size == 1, (
            f"{source_label}: dimension '{name}' has {size} categories, "
            f"expected exactly 1. This decoder's flat-index math only "
            f"accounts for 'unit' having more than one category; extend it "
            f"before trusting the decoded output.")
    if dim_size.get("unit", 1) <= 1:
        return 0
    unit_index = raw["dimension"]["unit"]["category"]["index"]
    assert prefer in unit_index, (
        f"{source_label}: expected a {prefer!r} category in the 'unit' "
        f"dimension, got {sorted(unit_index)}.")
    return unit_index[prefer] * geo_len * time_len


def decode_44x24(raw, colname, source_label):
    _check_axis_length(raw, "geo", len(GEO44), source_label)
    _check_axis_length(raw, "time", len(YEARS24), source_label)
    offset = _unit_block_offset(raw, len(GEO44), len(YEARS24), source_label)
    # Only run the leftover-values check when there really is exactly one
    # geo/time block in the response (unit dimension size 1, e.g.
    # raw_isoc_ci_in_h.json). raw_isoc_ci_ifp_iu.json has a second, currently
    #-empty 'unit' block (PC_IND_ILT12) that this decoder deliberately
    # never reads; flagging its indices as "leftover" would be a false
    # alarm the day Eurostat actually starts populating it.
    dim_size = dict(zip(raw.get("id", []), raw.get("size", []))) if raw.get("id") else {}
    single_block = dim_size.get("unit", 1) <= 1
    rows = []
    consumed = set()
    for geo_i, geo in enumerate(GEO44):
        for time_i, year in enumerate(YEARS24):
            idx = offset + geo_i * len(YEARS24) + time_i
            consumed.add(idx)
            v = raw["value"].get(str(idx))
            flag = raw.get("status", {}).get(str(idx), "")
            if v is None and not flag:
                continue  # nothing reported at all for this cell
            rows.append({
                "geo_code": geo, "geo_label": GEO44_LABEL[geo], "year": year,
                colname: v if v is not None else "",
                "flag": flag, "flag_desc": _status_desc(flag, source_label),
            })
    if single_block:
        _check_no_leftover_values(raw, consumed, source_label)
    return rows


def decode_39x3(raw, colname, source_label, breakdown=None):
    _check_axis_length(raw, "geo", len(GEO39), source_label)
    _check_axis_length(raw, "time", len(YEARS3), source_label)
    rows = []
    consumed = set()
    for geo_i, geo in enumerate(GEO39):
        for time_i, year in enumerate(YEARS3):
            idx = geo_i * len(YEARS3) + time_i
            consumed.add(idx)
            v = raw["value"].get(str(idx))
            flag = raw.get("status", {}).get(str(idx), "")
            if v is None and not flag:
                continue
            row = {
                "geo_code": geo, "geo_label": GEO39_LABEL[geo], "year": year,
                colname: v if v is not None else "",
                "flag": flag, "flag_desc": _status_desc(flag, source_label),
            }
            if breakdown is not None:
                row["age_group"] = breakdown
            rows.append(row)
    _check_no_leftover_values(raw, consumed, source_label)
    return rows


def decode_44x5(raw, colname, source_label, breakdown=None):
    """Same 44 countries as decode_44x24, but only 2021-2025 (five years).

    Used for the age-group breakdown of internet use, which was fetched with
    sinceTimePeriod=2021 rather than the full series."""
    _check_axis_length(raw, "geo", len(GEO44), source_label)
    _check_axis_length(raw, "time", len(YEARS5), source_label)
    rows = []
    consumed = set()
    for geo_i, geo in enumerate(GEO44):
        for time_i, year in enumerate(YEARS5):
            idx = geo_i * len(YEARS5) + time_i
            consumed.add(idx)
            v = raw["value"].get(str(idx))
            flag = raw.get("status", {}).get(str(idx), "")
            if v is None and not flag:
                continue
            row = {
                "geo_code": geo, "geo_label": GEO44_LABEL[geo], "year": year,
                colname: v if v is not None else "",
                "flag": flag, "flag_desc": _status_desc(flag, source_label),
            }
            if breakdown is not None:
                row["age_group"] = breakdown
            rows.append(row)
    _check_no_leftover_values(raw, consumed, source_label)
    return rows


# Order and labels match the _indicators mapping embedded in each
# raw_dskl_area_*.json file (IL/CC/DCC/SF/PS = the five DigComp areas at
# "basic or above", BAB_OVERALL = the composite across all five). Unlike
# the other partial captures, these files store values already resolved to
# country codes (values_by_country[indicator][geo_code]), not flat indices,
# so no index arithmetic is needed here.
AREA_LABELS = {
    "IL_BAB": "Information and data literacy",
    "CC_BAB": "Communication and collaboration",
    "DCC_BAB": "Digital content creation",
    "SF_BAB": "Safety",
    "PS_BAB": "Problem solving",
    "BAB_OVERALL": "Overall (all five areas)",
}
AREA_ORDER = ["IL_BAB", "CC_BAB", "DCC_BAB", "SF_BAB", "PS_BAB", "BAB_OVERALL"]


def decode_area_breakdown(raw, age_label, source_label, year="2025"):
    values_by_country = raw["values_by_country"]
    missing_areas = set(AREA_ORDER) - set(values_by_country)
    assert not missing_areas, f"{source_label}: missing area indicator(s) {missing_areas}"
    rows = []
    for area_key in AREA_ORDER:
        country_values = values_by_country[area_key]
        for geo in GEO39:
            if geo not in country_values:
                continue  # this dataset doesn't cover Iceland; skip it like every other geo not reporting
            rows.append({
                "geo_code": geo, "geo_label": GEO39_LABEL[geo], "year": year,
                "age_group": age_label, "skill_area": AREA_LABELS[area_key],
                "pct_basic_or_above": country_values[geo],
            })
    return rows


def derive_comparison_csv(iu_rows, dskl_rows):
    """digitalization_vs_skills_comparison.csv isn't decoded from its own raw
    file - there isn't one. It's a wide-format merge of two CSVs this script
    already produces: individual_internet_use.csv (all-individuals internet
    use) and digital_skills_by_age.csv, filtered to the 'All individuals
    (16-74)' age group, for 2021/2023/2025, EU27_2020 and EA aggregates
    dropped, sorted by country name. Verified against the committed file:
    every value reproduces exactly (max abs difference 0.0) once rows with
    no match in one of the two source datasets are kept as blanks rather
    than dropped, matching the committed file's own gaps (Iceland has no
    2025 skills figure, North Macedonia and Kosovo* have gaps too)."""
    years = ("2021", "2023", "2025")
    iu_by_geo_year = {(r["geo_code"], r["year"]): r["pct_individuals_used_internet_3m"] for r in iu_rows}
    dskl_by_geo_year = {
        (r["geo_code"], r["year"]): r["pct_basic_or_above_digital_skills"]
        for r in dskl_rows if r.get("age_group") == "All individuals (16-74)"
    }
    geo_labels = {r["geo_code"]: r["geo_label"] for r in dskl_rows}
    geos = sorted(
        (g for g in geo_labels if g not in ("EU27_2020", "EA")),
        key=lambda g: geo_labels[g])
    rows = []
    for geo in geos:
        row = {"geo_code": geo, "geo_label": geo_labels[geo]}
        for year in years:
            row[f"internet_use_{year}"] = iu_by_geo_year.get((geo, year), "")
            row[f"digital_skills_{year}"] = dskl_by_geo_year.get((geo, year), "")
        rows.append(row)
    return rows


def write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"Wrote {path} ({len(rows)} rows)")


def main():
    # Every dataset is fully read and decoded before anything is written, so
    # a failure partway through (missing input file, shape mismatch caught
    # by the assertions above, ...) never leaves some CSVs freshly rewritten
    # and others stale from a previous run - either everything below updates
    # together, or nothing does.
    outputs = []  # list of (path, rows, fieldnames), written only at the end

    # 1. Household internet access at home (isoc_ci_in_h), TOTAL household type
    with open(os.path.join(RAW_DIR, "raw_isoc_ci_in_h.json"), encoding="utf-8") as f:
        raw_in_h = json.load(f)
    rows_in_h = decode_44x24(raw_in_h, "pct_households_with_internet", "raw_isoc_ci_in_h.json")
    outputs.append((
        os.path.join(PROCESSED_DIR, "household_internet_access.csv"), rows_in_h,
        ["geo_code", "geo_label", "year", "pct_households_with_internet", "flag", "flag_desc"]))

    # 2. Individuals - internet use in last 3 months (isoc_ci_ifp_iu), all individuals
    with open(os.path.join(RAW_DIR, "raw_isoc_ci_ifp_iu.json"), encoding="utf-8") as f:
        raw_ifp_iu = json.load(f)
    rows_ifp_iu = decode_44x24(raw_ifp_iu, "pct_individuals_used_internet_3m", "raw_isoc_ci_ifp_iu.json")
    outputs.append((
        os.path.join(PROCESSED_DIR, "individual_internet_use.csv"), rows_ifp_iu,
        ["geo_code", "geo_label", "year", "pct_individuals_used_internet_3m", "flag", "flag_desc"]))

    # 3. Digital skills (isoc_sk_dskl_i21), basic-or-above overall digital skills, by age group + total
    dskl_files = [
        ("raw_dskl_total.json", "All individuals (16-74)"),
        ("raw_dskl_y16_24.json", "16-24"),
        ("raw_dskl_y25_54.json", "25-54"),
        ("raw_dskl_y55_74.json", "55-74"),
    ]
    all_dskl_rows = []
    for fname, label in dskl_files:
        with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
            raw = json.load(f)
        all_dskl_rows.extend(decode_39x3(raw, "pct_basic_or_above_digital_skills", fname, breakdown=label))
    outputs.append((
        os.path.join(PROCESSED_DIR, "digital_skills_by_age.csv"), all_dskl_rows,
        ["geo_code", "geo_label", "year", "age_group", "pct_basic_or_above_digital_skills", "flag", "flag_desc"]))

    # 4. Internet use in last 3 months (isoc_ci_ifp_iu) broken down BY AGE GROUP.
    #    Added so that internet use and digital skills can be compared like for
    #    like: before this, the skills of 55-74 year olds were being weighed
    #    against internet use across the whole 16-74 population.
    #    NOTE: these three raw files are partial captures (value + status only) -
    #    see the _note field inside each one, and the session log.
    iu_age_files = [
        ("raw_iu_age_y16_24.json", "16-24"),
        ("raw_iu_age_y25_54.json", "25-54"),
        ("raw_iu_age_y55_74.json", "55-74"),
    ]
    all_iu_age_rows = []
    for fname, label in iu_age_files:
        with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
            raw = json.load(f)
        all_iu_age_rows.extend(
            decode_44x5(raw, "pct_individuals_used_internet_3m", fname, breakdown=label))
    outputs.append((
        os.path.join(PROCESSED_DIR, "internet_use_by_age.csv"), all_iu_age_rows,
        ["geo_code", "geo_label", "year", "age_group",
         "pct_individuals_used_internet_3m", "flag", "flag_desc"]))

    # 5. Digital skills (isoc_sk_dskl_i21), basic-or-above, split into the five
    #    DigComp areas separately (plus the overall composite), by age group.
    #    2025 only - this breakdown isn't available for earlier years.
    dskl_area_files = [
        ("raw_dskl_area_ind_total.json", "All individuals (16-74)"),
        ("raw_dskl_area_y16_24.json", "16-24"),
        ("raw_dskl_area_y25_54.json", "25-54"),
        ("raw_dskl_area_y55_74.json", "55-74"),
    ]
    all_dskl_area_rows = []
    for fname, label in dskl_area_files:
        with open(os.path.join(RAW_DIR, fname), encoding="utf-8") as f:
            raw = json.load(f)
        all_dskl_area_rows.extend(decode_area_breakdown(raw, label, fname))
    outputs.append((
        os.path.join(PROCESSED_DIR, "digital_skills_by_area.csv"), all_dskl_area_rows,
        ["geo_code", "geo_label", "year", "age_group", "skill_area", "pct_basic_or_above"]))

    # 6. Not decoded from a raw file - derived from datasets 2 and 3 above.
    #    See derive_comparison_csv()'s docstring.
    comparison_rows = derive_comparison_csv(rows_ifp_iu, all_dskl_rows)
    outputs.append((
        os.path.join(PROCESSED_DIR, "digitalization_vs_skills_comparison.csv"), comparison_rows,
        ["geo_code", "geo_label", "internet_use_2021", "digital_skills_2021",
         "internet_use_2023", "digital_skills_2023", "internet_use_2025", "digital_skills_2025"]))

    # NOTE: data/processed/digital_skills_above_basic.csv is still not fully
    # reproducible from data/raw/ - most of its rows (the 37 individual
    # countries) were fetched one country/age-group combination at a time and
    # the raw responses were never saved (see README's data-sources section).
    # Only the EU27_2020 and EA aggregate rows added later have a saved raw
    # capture (raw_dskl_ab_eu27.json, raw_dskl_ab_ea.json); decoding just
    # those two would silently suggest the file is fully covered when most of
    # it isn't, so this script deliberately leaves the whole CSV alone rather
    # than partially regenerating it.

    os.makedirs(PROCESSED_DIR, exist_ok=True)
    for path, rows, fieldnames in outputs:
        write_csv(path, rows, fieldnames)
    print("Done.")


if __name__ == "__main__":
    main()
