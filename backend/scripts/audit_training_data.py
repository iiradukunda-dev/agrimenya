"""Audit the SAS 2026 district/crop CSV against its NISR source reports.

Run from backend with:
    python -m scripts.audit_training_data

Optional PDF paths can be supplied with --season-a-pdf and --season-b-pdf.
The audit writes data/audit_flags.csv and exits non-zero for missing source
tables, schema problems, duplicate records, or source/CSV value mismatches.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
from functools import lru_cache
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

try:
    import pdfplumber
except ImportError as exc:  # fail loudly; source validation is mandatory
    raise SystemExit("pdfplumber is required; install it with `pip install pdfplumber`.") from exc

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "agri_menya_real_data.csv"
FLAGS_PATH = ROOT / "data" / "audit_flags.csv"
SEASONS = ("2026 Season A", "2026 Season B")
METRICS = {
    "cultivated_area_ha": ("cultivated area by crop type and district", "cultivated area"),
    "harvested_area_ha": ("harvested area by crop type and district", "harvested area"),
    "yield_kg_ha": ("average yield by crop type and district", "yield"),
    "production_mt": ("crop production by crop type and district", "production"),
}
DISTRICTS = {
    "bugesera", "burera", "gakenke", "gasabo", "gatsibo", "gicumbi", "gisagara",
    "huye", "kamonyi", "karongi", "kayonza", "kicukiro", "kirehe",
    "muhanga", "musanze", "nyabihu", "nyagatare", "nyamagabe", "nyamasheke",
    "nyanza", "nyarugenge", "nyaruguru", "ngoma", "ngororero", "rusizi",
    "rulindo", "rutsiro", "rubavu", "ruhango", "rwamagana",
}


def norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip().casefold()


def number(value: Any) -> float | None:
    text = str(value or "").strip().replace(",", "").replace("\u2212", "-")
    if not text or text in {"-", "–", "—"}:
        return None
    try:
        return float(text)
    except ValueError:
        return None


@lru_cache(maxsize=4)
def _report_tables(pdf_path: Path) -> dict[str, tuple[list[list[str]], str]]:
    """Extract the four required NISR tables in a single pass over each PDF."""
    if not pdf_path.is_file():
        raise ValueError(f"Source PDF does not exist: {pdf_path}")
    targets = {phrase for phrase, _ in METRICS.values()}
    extracted: dict[str, tuple[list[list[str]], str]] = {}
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = norm(page.extract_text() or "")
            matching = [phrase for phrase in targets if phrase in text]
            if not matching:
                continue
            tables = page.extract_tables()
            for phrase in matching:
                for table in tables:
                    if table and table[0]:
                        extracted[phrase] = (table, f"{pdf_path.name}, page {page_number}")
                        break
            if targets.issubset(extracted):
                break
    return extracted


def pdf_table(pdf_path: Path, table_phrase: str, crop_names: list[str]) -> tuple[dict[tuple[str, str], str], str]:
    """Return district/crop cells from the table identified by its printed title."""
    source = _report_tables(pdf_path).get(table_phrase)
    if source is None:
        raise ValueError(f"Could not locate a table titled with '{table_phrase}' in {pdf_path}")
    table, location = source
    crop_lookup = {norm(name): name for name in crop_names}
    aliases = {
        "sweet potatoes": "sweet potato",
        "irish potatoes": "irish potato",
        "bananas": "banana",
        "taro & yams": "yams & taro",
        "yam & taro": "yams & taro",
        "yarms & taro": "yams & taro",
        "ground nuts": "groundnut",
        "groundnuts": "groundnut",
        "peas": "pea",
        "soya beans": "soybean",
        "soya bean": "soybean",
        "for banana beer": "banana for beer",
        "& yams taro": "yams & taro",
        "& yarms taro": "yams & taro",
        "taro yams &": "yams & taro",
        "taro yarms &": "yams & taro",
    }
    headers = [str(cell or "").replace("\n", " ").strip() for cell in table[0]]
    crop_columns: dict[int, str] = {}
    for index, header in enumerate(headers):
        # NISR's PDF text layer stores the crop headings in reverse
        # character order; reverse the extracted header, not the data.
        words_reversed = " ".join(word[::-1] for word in norm(header).split())
        candidates = (norm(header), norm(header[::-1]), norm(words_reversed))
        crop = next((crop_lookup[key] for key in candidates if key in crop_lookup), None)
        if crop is None:
            alias = next((aliases[key] for key in candidates if key in aliases), None)
            crop = crop_lookup.get(norm(alias)) if alias else None
        if crop:
            crop_columns[index] = crop
    if not crop_columns:
        raise ValueError(f"No CSV crop names matched the PDF headers for '{table_phrase}' ({location})")
    missing_crops = set(crop_names) - set(crop_columns.values())
    if missing_crops:
        raise ValueError(f"PDF table '{table_phrase}' is missing CSV crop headers {sorted(missing_crops)} ({location})")
    cells: dict[tuple[str, str], str] = {}
    for row in table[1:]:
        if not row or not row[0]:
            continue
        district = norm(row[0])
        if district not in DISTRICTS:
            continue
        for index, crop in crop_columns.items():
            cells[(district, norm(crop))] = str(row[index] or "").strip() if index < len(row) else ""
    return cells, location


def add_flag(flags: list[dict[str, Any]], row: dict[str, Any] | None, flag: str, detail: str) -> None:
    item = dict(row or {})
    item.update(flag=flag, detail=detail)
    flags.append(item)


def audit(csv_path: Path, pdf_paths: dict[str, Path]) -> int:
    hard_failures: list[str] = []
    flags: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"season", "district", "crop", "cultivated_area_ha", "yield_kg_ha", "production_mt"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            missing = sorted(required - set(reader.fieldnames or []))
            raise ValueError(f"CSV is missing required columns: {missing}")
        rows = list(reader)

    crops = sorted({r["crop"].strip() for r in rows if r.get("crop", "").strip()})
    districts = sorted({r["district"].strip() for r in rows if r.get("district", "").strip()})
    season_counts = Counter(r["season"].strip() for r in rows)
    district_counts = Counter(r["district"].strip() for r in rows)
    crop_counts = Counter(r["crop"].strip() for r in rows)
    print("SAS 2026 TRAINING DATA AUDIT")
    print(f"Runtime: Python {sys.version.split()[0]} | pdfplumber {pdfplumber.__version__} | CSV: {csv_path}")
    print(f"Rows: {len(rows)} | Districts: {len(districts)} (expected 30) | Crops: {len(crops)}")
    print("Rows by season: " + ", ".join(f"{s}={season_counts[s]}" for s in SEASONS))
    print("Rows by district: " + ", ".join(f"{d}={district_counts[d]}" for d in districts))
    if len(districts) != 30:
        hard_failures.append(f"Expected 30 districts; found {len(districts)}")
    duplicates = Counter((r["season"], r["district"], r["crop"]) for r in rows)
    for key, count in duplicates.items():
        if count > 1:
            hard_failures.append(f"Duplicate district/crop/season record: {key} ({count} rows)")

    season_pairs: dict[str, set[tuple[str, str]]] = {}
    for season in SEASONS:
        season_pairs[season] = {(r["district"].strip(), r["crop"].strip()) for r in rows if r["season"].strip() == season}
    only_a = sorted(season_pairs[SEASONS[0]] - season_pairs[SEASONS[1]])
    only_b = sorted(season_pairs[SEASONS[1]] - season_pairs[SEASONS[0]])
    print(f"District/crop pairs in A only: {len(only_a)} {only_a}")
    print(f"District/crop pairs in B only: {len(only_b)} {only_b}")
    for season, pairs in ((SEASONS[0], only_a), (SEASONS[1], only_b)):
        for district, crop in pairs:
            add_flag(flags, {"season": season, "district": district, "crop": crop}, "season_pair_missing", "Pair absent in other season")

    # Match the four source tables by their printed titles, then compare every
    # district/crop value to the corresponding CSV cell.
    row_by_key = {(r["season"].strip(), norm(r["district"]), norm(r["crop"])): r for r in rows}
    source_table_locations: dict[str, dict[str, str]] = defaultdict(dict)
    source_harvested_area: dict[tuple[str, str, str], float | None] = {}
    source_markers: dict[tuple[str, str], Counter] = defaultdict(Counter)
    for season in SEASONS:
        pdf_path = pdf_paths[season]
        for column, (title, _) in METRICS.items():
            try:
                cells, location = pdf_table(pdf_path, title, crops)
                source_table_locations[season][column] = location
            except Exception as exc:
                hard_failures.append(str(exc))
                continue
            for row in rows:
                if row["season"].strip() != season:
                    continue
                source_key = (norm(row["district"]), norm(row["crop"]))
                if source_key not in cells:
                    detail = f"Source table omitted {row['district']} / {row['crop']} ({location})"
                    hard_failures.append(detail)
                    add_flag(flags, row, "source_cell_missing", detail)
            for (district_norm, crop_norm), source_value in cells.items():
                source_markers[(season, column)][source_value.strip() or "<blank>"] += 1
                if column == "harvested_area_ha":
                    source_harvested_area[(season, district_norm, crop_norm)] = number(source_value)
                    continue  # harvested area is absent from this CSV schema
                row = row_by_key.get((season, district_norm, crop_norm))
                if row is None:
                    continue
                csv_value = number(row.get(column))
                pdf_value = number(source_value)
                # NISR uses '-' to mean no reported value. Blank extracted cells
                # are also treated as missing; a literal 0 remains numeric zero.
                if csv_value is None and pdf_value is None:
                    continue
                if csv_value is None or pdf_value is None or not math.isclose(csv_value, pdf_value, rel_tol=0, abs_tol=0.51):
                    detail = f"{column}: CSV={row.get(column)!r}, PDF={source_value!r} ({location})"
                    hard_failures.append(f"Source mismatch: {row['season']} / {row['district']} / {row['crop']} / {detail}")
                    add_flag(flags, row, "source_value_mismatch", detail)

    source_zeros = Counter()
    for season in SEASONS:
        for column, (_, label) in METRICS.items():
            location = source_table_locations.get(season, {}).get(column)
            if location:
                print(f"Source {season} {label}: {location}")
                markers = source_markers[(season, column)]
                print(f"  Source cell conventions: hyphen={markers['-']}, literal_zero={markers['0'] + markers['0.0']}, blank={markers['<blank>']}")

    # Missing and literal zeros are reported separately, retaining all records.
    missing = Counter()
    zeros = Counter()
    for row in rows:
        for col in ("cultivated_area_ha", "yield_kg_ha", "production_mt"):
            if not str(row.get(col, "")).strip():
                missing[col] += 1
                add_flag(flags, row, "missing_value", col)
            elif number(row.get(col)) == 0:
                zeros[col] += 1
                add_flag(flags, row, "literal_zero", col)
    print(f"Missing values: {dict(missing)} | Literal zeros: {dict(zeros)}")
    # Production consistency uses harvested area extracted from the NISR
    # harvested-area table, never cultivated area (wrong for perennial crops).
    checked_consistency = 0
    for row in rows:
        key = (row["season"].strip(), norm(row["district"]), norm(row["crop"]))
        production, yield_value = number(row.get("production_mt")), number(row.get("yield_kg_ha"))
        harvested_area = source_harvested_area.get(key)
        if production is None or yield_value is None or harvested_area is None:
            continue
        expected_mt = yield_value * harvested_area / 1000
        if expected_mt > 0:
            checked_consistency += 1
            relative_error = abs(production - expected_mt) / expected_mt
            if relative_error > 0.10:
                detail = f"production={production}, yield×source harvested area/1000={expected_mt:.3f}, error={relative_error:.1%}"
                add_flag(flags, row, "production_consistency_over_10pct", detail)

    outliers: list[dict[str, Any]] = []
    by_crop: dict[str, list[tuple[float, dict[str, Any]]]] = defaultdict(list)
    for row in rows:
        value = number(row.get("yield_kg_ha"))
        if value is not None:
            by_crop[row["crop"].strip()].append((value, row))
    for crop, observations in by_crop.items():
        values = [value for value, _ in observations]
        median = statistics.median(values)
        mad = statistics.median(abs(value - median) for value in values)
        robust_sd = 1.4826 * mad
        if robust_sd == 0:
            continue
        for value, row in observations:
            if abs(value - median) / robust_sd > 3:
                detail = f"yield={value:g}, crop median={median:g}, robust_sd={robust_sd:.3f}"
                add_flag(flags, row, "yield_outlier_3_robust_sd", detail)
                outliers.append(row)
    print(f"Yield outliers (>3 robust SD): {len(outliers)}")
    for row in outliers:
        print(f"  {row['season']} | {row['district']} | {row['crop']} | {row['yield_kg_ha']}")

    district_observations = defaultdict(set)
    for row in rows:
        district_observations[row["crop"].strip()].add(row["district"].strip())
    print("District observations per crop:")
    for crop in crops:
        count = len(district_observations[crop])
        print(f"  {crop}: {count}{' THIN' if count < 10 else ''}")
        if count < 10:
            add_flag(flags, {"crop": crop}, "thin_crop", f"{count} districts (<10)")

    FLAGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys([*(reader.fieldnames or []), "flag", "detail"]))
    with FLAGS_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(flags)
    print(f"Flagged rows: {len(flags)} -> {FLAGS_PATH}")
    print(f"Production consistency: checked {checked_consistency} rows using source harvested area; >10% discrepancies are flagged.")
    if hard_failures:
        print(f"HARD FAILURES: {len(hard_failures)}")
        for failure in hard_failures[:30]:
            print(f"  - {failure}")
        if len(hard_failures) > 30:
            print(f"  ... and {len(hard_failures) - 30} more")
        return 1
    print("HARD FAILURES: 0")
    return 0


def audit_new_season(csv_path: Path, pdf_path: Path, season_label: str, flags_path: Path | None = None) -> int:
    """Audit one freshly extracted season against its source PDF using M1 readers."""
    hard_failures: list[str] = []
    with csv_path.open(newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        required = {"season", "district", "crop", "cultivated_area_ha", "yield_kg_ha", "production_mt"}
        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(f"CSV missing required columns: {sorted(required - set(reader.fieldnames or []))}")
        rows = list(reader)
    if any(row["season"].strip() != season_label for row in rows):
        hard_failures.append(f"Extracted CSV must contain only {season_label}")
    districts = {norm(row["district"]) for row in rows}
    if len(districts) != 30 or not districts.issubset(DISTRICTS):
        hard_failures.append(f"Expected 30 recognized Rwanda districts; found {len(districts)}")
    seen = set()
    for row in rows:
        key = (norm(row["district"]), norm(row["crop"]))
        if key in seen:
            hard_failures.append(f"Duplicate district/crop row: {key}")
        seen.add(key)
    crops = sorted({row["crop"].strip() for row in rows})
    row_map = {(norm(row["district"]), norm(row["crop"])): row for row in rows}
    source_harvest = {}
    for column, (title, _) in METRICS.items():
        try:
            cells, location = pdf_table(pdf_path, title, crops)
        except Exception as exc:
            hard_failures.append(str(exc))
            continue
        missing_csv = set(cells) - set(row_map)
        for district_crop in sorted(missing_csv):
            hard_failures.append(f"CSV omitted source row {district_crop} for {column} ({location})")
        for key, row in row_map.items():
            if key not in cells:
                hard_failures.append(f"Source omitted {row['district']} / {row['crop']} ({location})")
                continue
            source_value, csv_value = number(cells[key]), number(row.get(column))
            if column == "harvested_area_ha":
                source_harvest[key] = source_value
                continue
            if source_value is None and csv_value is None:
                continue
            if source_value is None or csv_value is None or not math.isclose(source_value, csv_value, abs_tol=0.51, rel_tol=0):
                hard_failures.append(f"Mismatch {row['district']} / {row['crop']} / {column}: CSV={csv_value}, PDF={source_value}")
    checked = 0
    for key, row in row_map.items():
        y, production, harvested = number(row.get("yield_kg_ha")), number(row.get("production_mt")), source_harvest.get(key)
        if y is not None and production is not None and harvested is not None and harvested > 0:
            checked += 1
            expected = y * harvested / 1000
            if expected > 0 and abs(production - expected) / expected > 0.10:
                print(f"CHECK: production consistency >10% for {row['district']} / {row['crop']}")
    print(f"M1 new-season audit: {season_label}, {len(rows)} rows, {len(districts)} districts, {checked} production checks")
    if flags_path:
        flags_path.parent.mkdir(parents=True, exist_ok=True)
        with flags_path.open("w", newline="", encoding="utf-8") as output:
            writer = csv.DictWriter(output, fieldnames=["season", "district", "crop", "flag", "detail"])
            writer.writeheader()
            for failure in hard_failures:
                writer.writerow({"season": season_label, "flag": "hard_failure", "detail": failure})
    for failure in hard_failures:
        print(f"HARD FAILURE: {failure}")
    print(f"HARD FAILURES: {len(hard_failures)}")
    return 1 if hard_failures else 0


def main() -> int:
    downloads = Path.home() / "Downloads"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    parser.add_argument("--season-a-pdf", type=Path, default=downloads / "SAS 2026 Season A _Final Report (1).pdf")
    parser.add_argument("--season-b-pdf", type=Path, default=downloads / "SAS 2026B_Main report.pdf")
    args = parser.parse_args()
    return audit(args.csv, {SEASONS[0]: args.season_a_pdf, SEASONS[1]: args.season_b_pdf})


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error) as exc:
        print(f"AUDIT COULD NOT COMPLETE: {exc}", file=sys.stderr)
        raise SystemExit(2)
