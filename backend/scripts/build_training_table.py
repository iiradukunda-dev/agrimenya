"""Build a district-season-crop training table from NISR SAS reports.

Run from backend:
    python -m scripts.build_training_table

Source PDFs are located by their report titles and table titles, not by table
numbers. Paths can be overridden with --sas-2025, --sas-2026-a, and
--sas-2026-b. Unpublished features remain blank and are included in the
missingness report; the script never fills them from another season.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

try:
    import pdfplumber
except ImportError as exc:
    raise SystemExit("pdfplumber is required. Install backend dependencies with `pip install -r requirements.txt`.") from exc

from app.db.rwanda_districts import RWANDA_DISTRICTS

BACKEND = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND / "data"
OUTPUT_PATH = DATA_DIR / "training_table.csv"
OFFICIAL_DISTRICTS = {re.sub(r"\s+", " ", d["district"]).casefold(): d["district"] for d in RWANDA_DISTRICTS}

CROP_ALIASES = {
    "corn": "maize", "bean": "beans", "beans": "beans", "bush beans": "bush bean",
    "climbing beans": "climbing bean", "peas": "pea", "ground nuts": "groundnut",
    "groundnuts": "groundnut", "soya bean": "soybean", "soya beans": "soybean",
    "sweet potatoes": "sweet potato", "irish potatoes": "irish potato",
    "bananas": "banana", "cooking banana": "cooking banana", "dessert banana": "dessert banana",
    "taro & yams": "yams & taro", "yam & taro": "yams & taro", "yarms & taro": "yams & taro",
    "& yams taro": "yams & taro", "& yarms taro": "yams & taro", "taro yams &": "yams & taro",
    "taro yarms &": "yams & taro", "for banana beer": "banana for beer",
    "other cereal": "other cereals", "vegetable": "vegetables",
}

CATEGORY_MAP = {
    "maize": "Cereal", "sorghum": "Cereal", "paddy rice": "Cereal", "wheat": "Cereal",
    "other cereals": "Cereal", "cassava": "Perennial", "sweet potato": "Tuber",
    "irish potato": "Tuber", "yams & taro": "Tuber", "beans": "Legume",
    "bush bean": "Legume", "climbing bean": "Legume", "pea": "Legume",
    "groundnut": "Legume", "soybean": "Legume", "banana": "Perennial",
    "cooking banana": "Perennial", "dessert banana": "Perennial", "banana for beer": "Perennial",
    "vegetables": "Vegetable", "fruits": "Fruit", "fodder crops": "Fodder",
    "other crops": "Other",
}

AREA_HEADERS = {
    "% of agricultural land": "land_agricultural_land_pct",
    "% land of agricultural": "land_agricultural_land_pct",
    "total land area": "land_total_area_share",
    "agricultural land": "land_agricultural_area_share",
    "arable land": "land_arable_area_share",
    "physical cultivated land": "land_physical_cultivated_area_share",
    "area under seasonal crops": "land_seasonal_crop_area_share",
    "area under permanent crops": "land_permanent_crop_area_share",
    "temporary fallow land": "land_temporary_fallow_area_share",
    "temporary meadow and pasture": "land_temporary_pasture_area_share",
    "temporarily meadow and pasture": "land_temporary_pasture_area_share",
    "area permanent under pasture": "land_permanent_pasture_area_share",
}

FEATURE_TITLES = {
    "land_use": "agricultural land use per district",
    "practice_area": "area under agricultural practices",
    "seeds": "use of seeds by farmer type per district",
    "organic_fertilizer": "use of organic fertilizer by farmer type per district",
    "inorganic_fertilizer": "use of inorganic fertilizer by farmer type per district",
    "pesticides": "use of pesticides by farmer type per district",
    "practices": "percentage of farmers who practiced agricultural practices",
    "cropping": "cultivated area by cropping system",
    "sowing": "sowing date",
    "erosion": "percentage of plots by degree of erosion per district",
}


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def key(value: Any) -> str:
    return clean(value).casefold()


def number(value: Any) -> float | None:
    text = clean(value).replace(",", "").replace("\u2212", "-")
    if not text or text in {"..", "..."} or all(char in "-–—−" for char in text):
        return None
    try:
        return float(text)
    except ValueError:
        return None


def header_forms(value: Any) -> list[str]:
    """Normalize normal and NISR's reversed PDF text-layer headings."""
    text = clean(value)
    forms = [text, text[::-1], " ".join(word[::-1] for word in text.split())]
    result = []
    for form in forms:
        normalized = key(form)
        if normalized and normalized not in result:
            result.append(normalized)
        alias = CROP_ALIASES.get(normalized)
        if alias and alias not in result:
            result.append(alias)
    return result


def crop_name(value: Any) -> str | None:
    for candidate in header_forms(value):
        canonical = CROP_ALIASES.get(candidate, candidate)
        if canonical in CATEGORY_MAP:
            return canonical
    return None


def district_name(value: Any) -> str | None:
    return OFFICIAL_DISTRICTS.get(key(value))


def header_rows(table: list[list[Any]]) -> tuple[int, list[str]]:
    """Find first district record and flatten all preceding header levels."""
    first_data = None
    for i, row in enumerate(table):
        if row and (district_name(row[0]) or key(row[0]) == "national"):
            first_data = i
            break
    if first_data is None:
        return len(table), []
    width = max((len(row) for row in table[:first_data]), default=0)
    filled: list[list[str]] = []
    for row in table[:first_data]:
        values = [clean(row[col]) if col < len(row) else "" for col in range(width)]
        last = ""
        for col in range(1, width):
            if values[col]:
                last = values[col]
            elif last:
                values[col] = last
        filled.append(values)
    headers = []
    for col in range(width):
        bits = []
        for row in filled:
            if col < len(row) and clean(row[col]):
                bit = clean(row[col])
                if not bits or key(bits[-1]) != key(bit):
                    bits.append(bit)
        headers.append(" | ".join(bits))
    return first_data, headers


def all_header_forms(header: str) -> set[str]:
    forms = {" ".join(header_forms(part)) for part in header.split(" | ") if part}
    forms.update(header_forms(header))
    return forms


def header_has(header: str, *terms: str) -> bool:
    forms = all_header_forms(header)
    for form in forms:
        compact = re.sub(r"[^a-z0-9]", "", form.casefold())
        if all(re.sub(r"[^a-z0-9]", "", term.casefold()) in compact for term in terms):
            return True
    return False


def report_pages(pdf_path: Path) -> list[tuple[str, list[list[list[Any]]], int]]:
    """Read candidate table pages once; title matching is performed later."""
    if not pdf_path.is_file():
        raise FileNotFoundError(f"NISR report not found: {pdf_path}")
    wanted = tuple(FEATURE_TITLES.values()) + (
        "cultivated area by crop type", "harvested area by crop type",
        "average yield by crop type", "crop production by crop type",
    )
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            lowered = key(text)
            if any(term in lowered for term in wanted):
                tables = page.extract_tables() or []
                if tables:
                    pages.append((text, tables, page_number))
            page.close()
    return pages


def season_matches(text: str, season_code: str) -> bool:
    # A/B titles are explicitly season-tagged; the C title is also explicit.
    return re.search(rf"season\s*{season_code}(?![a-z])", key(text), flags=re.IGNORECASE) is not None


def locate_table(pages, phrase: str, season_code: str | None = None, required: bool = False):
    """Find the table whose printed title contains phrase and season label."""
    matches = []
    for text, tables, page_number in pages:
        normalized = key(text)
        if phrase not in normalized:
            continue
        if season_code and not season_matches(text, season_code):
            continue
        for table in tables:
            if not table:
                continue
            district_rows = sum(1 for row in table if row and (district_name(row[0]) or key(row[0]) == "national"))
            has_national = any(row and key(row[0]) == "national" for row in table)
            if district_rows >= 15 and has_national:
                matches.append((table, page_number, text))
    if not matches:
        if required:
            raise ValueError(f"No district table matching title '{phrase}' for Season {season_code or 'all'} in report")
        return None
    # Prefer actual table-title pages over table-of-contents mentions.
    return matches[0]


def district_table_rows(table: list[list[Any]]):
    data_start, headers = header_rows(table)
    districts: dict[str, list[Any]] = {}
    national: list[Any] | None = None
    for row in table[data_start:]:
        if not row:
            continue
        name = clean(row[0])
        if key(name) == "national":
            national = row
        elif official := district_name(name):
            districts[official] = row
    return headers, districts, national


def extract_crop_table(table, metric: str, season_label: str, report_name: str, validation: list[str]):
    data_start, headers = header_rows(table)
    if not headers:
        return {}, {}, []
    columns: dict[int, str] = {}
    for col, header in enumerate(headers):
        name = crop_name(header)
        if name:
            columns[col] = name
    if not columns:
        raise ValueError(f"No crop headers recognized in {report_name} {season_label} {metric} table")

    values: dict[tuple[str, str], float | None] = {}
    national_values: dict[str, float | None] = {}
    district_values: dict[str, list[float]] = defaultdict(list)
    national_row = None
    for row in table[data_start:]:
        if not row:
            continue
        district = district_name(row[0])
        is_national = key(row[0]) == "national"
        if not district and not is_national:
            continue
        if is_national:
            national_row = row
        for col, crop in columns.items():
            value = number(row[col]) if col < len(row) else None
            if is_national:
                national_values[crop] = value
            elif district:
                values[(district, crop)] = value
                if value is not None:
                    district_values[crop].append(value)
    if national_row is None:
        validation.append(f"{report_name} {season_label} {metric}: National row missing")
    elif metric in {"cultivated_area_ha", "harvested_area_ha", "production_mt"}:
        for crop, national in national_values.items():
            if national is None:
                continue
            total = sum(district_values.get(crop, []))
            tolerance = max(1.0, abs(national) * 0.02)
            if abs(total - national) > tolerance:
                validation.append(f"{report_name} {season_label} {metric}/{crop}: district sum {total:g} vs National {national:g}")
    else:
        # Yield is a ratio, not an additive total. Verify its National value exists.
        absent = [crop for crop in columns.values() if national_values.get(crop) is None]
        if absent:
            validation.append(f"{report_name} {season_label} {metric}: National yield missing for {absent}")
    return values, national_values, list(columns.values())


def feature_slug(text: str) -> str:
    text = re.sub(r"[^a-z0-9]+", "_", key(text)).strip("_")
    return text or "unspecified"


def classify_feature_columns(kind: str, headers: list[str], season_code: str):
    """Map district-table headers to stable feature names and source units."""
    result: dict[int, tuple[str, str]] = {}
    grouped_farmer_table = any(header_has(header, "overall") for header in headers)
    for col, header in enumerate(headers):
        h = key(header)
        area = False
        if kind == "land_use":
            mapping = None
            # Test the percent indicator before the broader agricultural-land
            # phrase so the published percentage is not treated as hectares.
            ordered_headers = sorted(AREA_HEADERS.items(), key=lambda item: item[0] != "% of agricultural land")
            for label, feature in ordered_headers:
                if header_has(header, *label.split()):
                    mapping = feature
                    break
            if mapping is None and header_has(header, "physical", "cultivat", "land"):
                mapping = "land_physical_cultivated_area_share"
            if mapping is None and header_has(header, "manent", "crops"):
                mapping = "land_permanent_crop_area_share"
            if mapping is None and header_has(header, "manent", "pasture"):
                mapping = "land_permanent_pasture_area_share"
            if mapping:
                area = not mapping.endswith("_pct")
                result[col] = (mapping, "thousand_ha" if area else "percent")
        elif kind == "practice_area":
            mapping = None
            if header_has(header, "modern irrigated"):
                mapping = "modern_irrigated_area_share"
            elif header_has(header, "erosion", "control"):
                mapping = "agricultural_area_erosion_control_share"
            elif header_has(header, "agroforestry"):
                mapping = "agricultural_area_agroforestry_share"
            elif header_has(header, "inorganic", "fertilizer"):
                mapping = "agricultural_area_inorganic_fertilizer_share"
            elif header_has(header, "organic", "fertilizer"):
                mapping = "agricultural_area_organic_fertilizer_share"
            if mapping:
                result[col] = (mapping, "ha")
        elif kind in {"seeds", "organic_fertilizer", "inorganic_fertilizer", "pesticides"}:
            targets = {
                "seeds": ("improved seeds", "farmers_using_improved_seeds_pct"),
                "organic_fertilizer": ("organic fertilizer", "farmers_using_organic_fertilizer_pct"),
                "inorganic_fertilizer": ("inorganic fertilizer", "farmers_using_inorganic_fertilizer_pct"),
                "pesticides": ("pesticides", "farmers_using_pesticides_pct"),
            }
            term, feature = targets[kind]
            term_match = header_has(header, *term.split()) or (kind == "seeds" and header_has(header, "improved", "seed"))
            is_overall = header_has(header, "overall") if grouped_farmer_table else True
            if is_overall and term_match and header_has(header, "percentage", "farmers"):
                result[col] = (feature, "percent")
        elif kind == "practices":
            practice_map = {
                "erosion": "farmers_protecting_against_erosion_pct",
                "mechanical": "farmers_using_mechanization_pct",
                "irrigation": "farmers_practicing_irrigation_pct",
                "agroforestry": "farmers_practicing_agroforestry_pct",
            }
            for term, feature in practice_map.items():
                is_overall = header_has(header, "overall") if grouped_farmer_table else True
                if header_has(header, term) and is_overall:
                    result[col] = (feature, "percent")
                    break
        elif kind == "erosion":
            level_map = {
                "severe": "erosion_severe_pct", "moderate": "erosion_moderate_pct",
                "very low": "erosion_very_low_pct", "low": "erosion_low_pct",
            }
            for level, feature in level_map.items():
                if header_has(header, level):
                    result[col] = (feature, "percent")
                    break
        elif kind == "cropping":
            if season_matches(header, season_code) or not re.search(r"season\s*[abc]", h):
                if header_has(header, "pure"):
                    result[col] = ("cultivated_area_pure_pct", "percent")
                elif header_has(header, "mixed"):
                    result[col] = ("cultivated_area_mixed_pct", "percent")
        elif kind == "sowing":
            if season_matches(header, season_code) or not re.search(r"season\s*[abc]", h):
                if not header_has(header, "district") and not header_has(header, "total"):
                    window = h
                    for part in header.split(" | "):
                        forms = header_forms(part)
                        readable = next((f for f in forms if any(t in f for t in ("before", "between", "after", "other season"))), None)
                        if readable:
                            window = readable
                    if any(token in window for token in ("before", "between", "after", "other season")):
                        result[col] = (f"sowing_window_{feature_slug(window)}_pct", "percent")
    return result


def extract_features(table, kind: str, season_code: str, report_name: str, validation: list[str]):
    headers, districts, national = district_table_rows(table)
    if national is None:
        validation.append(f"{report_name} {kind}: National row missing")
        return {}, {}
    columns = classify_feature_columns(kind, headers, season_code)
    features: dict[str, dict[str, float | None]] = defaultdict(dict)
    national_features = {}
    area_kind = kind in {"land_use", "practice_area"}
    for col, (feature, unit) in columns.items():
        national_value = number(national[col]) if col < len(national) else None
        national_features[feature] = national_value
        district_values = []
        for district, row in districts.items():
            value = number(row[col]) if col < len(row) else None
            if value is not None:
                district_values.append(value)
            # Convert area features after merging, once district crop area is known.
            features[district][feature] = value * (1000 if unit == "thousand_ha" else 1) if value is not None else None
        if area_kind and unit != "percent" and national_value is not None:
            total = sum(district_values)
            tolerance = max(1.0, abs(national_value) * 0.02)
            if abs(total - national_value) > tolerance:
                validation.append(f"{report_name} {kind}/{feature}: district total {total:g} vs National {national_value:g}")
    if not columns:
        validation.append(f"{report_name} {kind}: no feature columns recognized from headers")
    return features, national_features


def report_feature_tables(pages, year: int, code: str, report_name: str, validation: list[str]):
    feature_rows: dict[str, dict[str, float | None]] = defaultdict(dict)
    all_national = {}
    missing_sources = []
    required_feature_kinds = list(FEATURE_TITLES)
    for kind in required_feature_kinds:
        # Combined season tables for sowing/cropping have no single-season title.
        phrase = FEATURE_TITLES[kind]
        if year == 2025 and code == "C" and kind in {"land_use", "practice_area"}:
            missing_sources.append(kind)
            continue
        if year == 2026 and kind in {"land_use", "practice_area"}:
            pass
        if kind in {"sowing", "cropping"}:
            found = locate_table(pages, phrase, None, required=False)
        else:
            found = locate_table(pages, phrase, code, required=False)
        if found is None:
            missing_sources.append(kind)
            continue
        table, page_number, _ = found
        extracted, national = extract_features(table, kind, code, report_name, validation)
        for district, values in extracted.items():
            feature_rows[district].update(values)
        all_national.update(national)
    return feature_rows, all_national, missing_sources


def crop_table_phrase(metric: str, season_code: str) -> str:
    if metric == "cultivated_area_ha":
        return "cultivated area by crop type"
    if metric == "harvested_area_ha":
        return "harvested area by crop type"
    if metric == "yield_kg_ha":
        return "average yield by crop type"
    return "crop production by crop type"


def build(args) -> int:
    reports = [
        (2025, "2025", Path(args.sas_2025), ["A", "B", "C"]),
        (2026, "2026 Season A", Path(args.sas_2026_a), ["A"]),
        (2026, "2026 Season B", Path(args.sas_2026_b), ["B"]),
    ]
    crop_values: dict[tuple[int, str, str, str], float | None] = {}
    national_crop_values = {}
    observed_crops: set[str] = set()
    district_features: dict[tuple[int, str, str], dict[str, float | None]] = defaultdict(dict)
    validation: list[str] = []
    missing_sources = []
    print(f"Runtime versions: Python {sys.version.split()[0]}, pdfplumber {pdfplumber.__version__}")

    for year, report_label, pdf_path, seasons in reports:
        print(f"Reading {report_label}: {pdf_path}")
        pages = report_pages(pdf_path)
        for code in seasons:
            season_label = f"{year} Season {code}"
            season_metrics = {}
            for metric in ("cultivated_area_ha", "harvested_area_ha", "yield_kg_ha", "production_mt"):
                found = locate_table(pages, crop_table_phrase(metric, code), code, required=False)
                if found is None and year == 2025 and code == "C":
                    missing_sources.append(f"{season_label} {metric}")
                    continue
                if found is None:
                    raise ValueError(f"Could not find title-matched table '{crop_table_phrase(metric, code)}' for {season_label}")
                table, page_number, _ = found
                values, national, crops = extract_crop_table(table, metric, season_label, report_label, validation)
                observed_crops.update(crops)
                season_metrics[metric] = values
                national_crop_values[(season_label, metric)] = national
            keys = set().union(*(set(v) for v in season_metrics.values())) if season_metrics else set()
            for district, crop in keys:
                for metric, values in season_metrics.items():
                    crop_values[(year, code, district, crop, metric)] = values.get((district, crop))

            features, _, absent = report_feature_tables(pages, year, code, report_label, validation)
            for kind in absent:
                missing_sources.append(f"{season_label} {kind}")
            for district, values in features.items():
                district_features[(year, code, district)].update(values)

    # The sum of source crop areas is the district-season cultivated-area
    # denominator. This keeps absolute district area features scale-neutral.
    area_totals: dict[tuple[int, str, str], float] = defaultdict(float)
    for (year, code, district, crop, metric), value in crop_values.items():
        if metric == "cultivated_area_ha" and value is not None:
            area_totals[(year, code, district)] += value

    records = []
    keys = sorted({k[:4] for k in crop_values})
    for year, code, district, crop in keys:
        record: dict[str, Any] = {
            "season": f"{year} Season {code}", "season_code": code, "year": year,
            "district": district, "crop": crop.title() if crop != "yams & taro" else "Yams & Taro",
            "crop_category": CATEGORY_MAP[crop],
            "yield_kg_ha": crop_values.get((year, code, district, crop, "yield_kg_ha")),
            "cultivated_area_ha": crop_values.get((year, code, district, crop, "cultivated_area_ha")),
            "harvested_area_ha": crop_values.get((year, code, district, crop, "harvested_area_ha")),
            "production_mt": crop_values.get((year, code, district, crop, "production_mt")),
        }
        record.update(district_features.get((year, code, district), {}))
        denominator = area_totals.get((year, code, district), 0.0)
        for feature, value in list(record.items()):
            if feature.endswith("_share") and value is not None:
                record[feature] = value / denominator if denominator > 0 else None
        records.append(record)

    crop_counts = defaultdict(set)
    for row in records:
        if row["yield_kg_ha"] is not None:
            crop_counts[(row["year"], row["season_code"], row["crop"])].add(row["district"])
    for row in records:
        row["n_districts_for_crop"] = len(crop_counts[(row["year"], row["season_code"], row["crop"])])

    columns = ["season", "season_code", "year", "district", "crop", "crop_category",
               "yield_kg_ha", "cultivated_area_ha", "harvested_area_ha", "production_mt"]
    feature_columns = sorted({column for row in records for column in row if column not in columns and column != "n_districts_for_crop"})
    columns += feature_columns + ["n_districts_for_crop"]
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in records:
            writer.writerow({col: "" if row.get(col) is None else row.get(col) for col in columns})

    print(f"Rows written: {len(records)} | features: {len(feature_columns)} | columns: {len(columns)} | output: {OUTPUT_PATH}")
    print("Missing value share by column:")
    for col in columns:
        missing = sum(row.get(col) is None for row in records)
        print(f"  {col}: {missing}/{len(records)} ({missing / len(records):.1%})")
    print(f"Source tables with unavailable coverage: {len(missing_sources)}")
    for source in sorted(set(missing_sources)):
        print(f"  unavailable: {source}")
    print(f"National row checks: {len(validation)} issue(s)")
    for issue in validation[:40]:
        print(f"  CHECK: {issue}")
    if len(validation) > 40:
        print(f"  ... {len(validation) - 40} more checks")
    return 1 if not records else 0


def extract_single_season(pdf_path: Path, year: int, season_code: str) -> list[dict[str, Any]]:
    """Extract one season through the same title/header based M2 routines."""
    code = season_code.upper()
    if code not in {"A", "B", "C"}:
        raise ValueError("season_code must be A, B, or C")
    report_name = f"{year} Season {code}"
    pages = report_pages(pdf_path)
    validation: list[str] = []
    metric_values: dict[str, dict[tuple[str, str], float | None]] = {}
    crops: set[str] = set()
    for metric in ("cultivated_area_ha", "harvested_area_ha", "yield_kg_ha", "production_mt"):
        found = locate_table(pages, crop_table_phrase(metric, code), code, required=True)
        table, _, _ = found
        values, _, names = extract_crop_table(table, metric, report_name, report_name, validation)
        metric_values[metric] = values
        crops.update(names)
    if validation:
        raise ValueError("Header extraction checks failed: " + "; ".join(validation[:20]))
    features, _, missing = report_feature_tables(pages, year, code, report_name, validation)
    if validation:
        raise ValueError("Feature header extraction checks failed: " + "; ".join(validation[:20]))
    area_totals: dict[str, float] = defaultdict(float)
    keys = set().union(*(values.keys() for values in metric_values.values()))
    for district, _crop in keys:
        value = metric_values["cultivated_area_ha"].get((district, _crop))
        if value is not None:
            area_totals[district] += value
    rows = []
    for district, crop in sorted(keys):
        normalized_crop = crop_name(crop) or crop
        if normalized_crop not in CATEGORY_MAP:
            raise ValueError(f"No sourced crop category mapping for {normalized_crop!r}; add it to M2 after review")
        record: dict[str, Any] = {
            "season": report_name, "season_code": code, "year": year, "district": district,
            "crop": normalized_crop.title() if normalized_crop != "yams & taro" else "Yams & Taro",
            "crop_category": CATEGORY_MAP[normalized_crop],
        }
        for metric in metric_values:
            record[metric] = metric_values[metric].get((district, crop))
        record.update(features.get(district, {}))
        denominator = area_totals.get(district, 0.0)
        for name, value in list(record.items()):
            if name.endswith("_share") and value is not None:
                record[name] = value / denominator if denominator > 0 else None
        rows.append(record)
    counts: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        if row.get("yield_kg_ha") is not None:
            counts[row["crop"]].add(row["district"])
    for row in rows:
        row["n_districts_for_crop"] = len(counts[row["crop"]])
    if len({row["district"] for row in rows}) != 30:
        raise ValueError(f"Extracted season has {len({row['district'] for row in rows})} districts; expected 30")
    if missing:
        print(f"Season features not published in source (left blank): {', '.join(sorted(missing))}")
    return rows


def main() -> int:
    downloads = Path.home() / "Downloads"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sas-2025", default=downloads / "SAS 2025 Final report.pdf", type=Path)
    parser.add_argument("--sas-2026-a", default=downloads / "SAS 2026 Season A _Final Report (1).pdf", type=Path)
    parser.add_argument("--sas-2026-b", default=downloads / "SAS 2026B_Main report.pdf", type=Path)
    args = parser.parse_args()
    return build(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, csv.Error) as exc:
        print(f"TRAINING TABLE BUILD FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
