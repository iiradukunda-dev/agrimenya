"""Append official SAS 2022-2024 district yield tables to a local experiment.

Only published aggregate tables are used. Output is written under the ignored
microdata-review directory and is not an admin import or production dataset.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath
import xml.etree.ElementTree as ET

BACKEND = Path(__file__).resolve().parents[1]
DATA = BACKEND / "data"
OUTPUT = DATA / "nisr_microdata_review" / "training_table_sas2024_2026_experiment.csv"
REPORT = DATA / "eval" / "sas2024_2026_official_table_qa.json"
NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
REL_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
DISTRICTS = {
    "nyarugenge", "gasabo", "kicukiro", "nyanza", "gisagara", "nyaruguru", "huye",
    "nyamagabe", "ruhango", "muhanga", "kamonyi", "karongi", "rutsiro", "rubavu",
    "nyabihu", "ngororero", "rusizi", "nyamasheke", "rulindo", "gakenke", "musanze",
    "burera", "gicumbi", "rwamagana", "nyagatare", "gatsibo", "kayonza", "kirehe",
    "ngoma", "bugesera",
}
CROP_ALIASES = {
    "corn": "maize", "bean": "beans", "bush beans": "bush bean", "climbing beans": "climbing bean",
    "peas": "pea", "ground nuts": "groundnut", "groundnuts": "groundnut", "soya bean": "soybean",
    "soya beans": "soybean", "sweet potatoes": "sweet potato", "irish potatoes": "irish potato",
    "bananas": "banana", "taro & yams": "yams & taro", "yam & taro": "yams & taro",
    "yarms & taro": "yams & taro", "for banana beer": "banana for beer",
    "other cereal": "other cereals", "vegetable": "vegetables",
}
CATEGORIES = {
    "maize": "Cereal", "sorghum": "Cereal", "paddy rice": "Cereal", "wheat": "Cereal",
    "other cereals": "Cereal", "cassava": "Perennial", "sweet potato": "Tuber",
    "irish potato": "Tuber", "yams & taro": "Tuber", "beans": "Legume", "bush bean": "Legume",
    "climbing bean": "Legume", "pea": "Legume", "groundnut": "Legume", "soybean": "Legume",
    "banana": "Perennial", "cooking banana": "Perennial", "dessert banana": "Perennial",
    "banana for beer": "Perennial", "vegetables": "Vegetable", "fruits": "Fruit",
    "fodder crops": "Fodder", "other crops": "Other",
}
GROUP_HEADERS = {"cereals", "tubers and roots", "legumes and pulses", "vegetables and fruits", "bananas"}


def normalized(value: str) -> str:
    return re.sub(r"\s+", " ", value.replace("\u00a0", " ").strip()).casefold()


def crop_name(value: str) -> str | None:
    key = normalized(value)
    key = CROP_ALIASES.get(key, key)
    if key not in CATEGORIES:
        return None
    return key.title()


def numeric(value: str) -> float | None:
    try:
        result = float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None
    return result if math.isfinite(result) else None


def col_number(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    value = 0
    for char in letters.group(0) if letters else "A":
        value = value * 26 + ord(char) - 64
    return value - 1


def read_rows(archive: zipfile.ZipFile, path: str, shared: list[str]) -> list[list[str]]:
    root = ET.fromstring(archive.read(path))
    result = []
    for row in root.findall(".//m:sheetData/m:row", NS):
        cells: dict[int, str] = {}
        for cell in row.findall("m:c", NS):
            value = cell.find("m:v", NS)
            text = value.text if value is not None else ""
            if cell.attrib.get("t") == "s" and text:
                text = shared[int(text)]
            inline = cell.find("m:is", NS)
            if inline is not None:
                text = "".join(node.text or "" for node in inline.findall(".//m:t", NS))
            cells[col_number(cell.attrib.get("r", "A1"))] = text
        if cells:
            result.append([cells.get(i, "") for i in range(max(cells) + 1)])
        else:
            result.append([])
    return result


def workbook_sheets(path: Path) -> list[tuple[str, list[list[str]]]]:
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {item.attrib["Id"]: item.attrib["Target"] for item in relationships}
        shared: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            strings = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared = ["".join(node.text or "" for node in item.findall(".//m:t", NS))
                      for item in strings.findall("m:si", NS)]
        result = []
        for sheet in workbook.findall("m:sheets/m:sheet", NS):
            target = targets[sheet.attrib[REL_ID]].lstrip("/")
            target = target if target.startswith("xl/") else str(PurePosixPath("xl") / target)
            result.append((sheet.attrib["name"], read_rows(archive, target, shared)))
        return result


def district_yield_tables(path: Path, required_year: int) -> tuple[dict, dict, list[str]]:
    """Return district/crop/season rows by reading detailed (not grouped) tables."""
    yields: dict[tuple[str, str, str], float] = {}
    harvested: dict[tuple[str, str, str], float] = {}
    cultivated: dict[tuple[str, str, str], float] = {}
    matched_yield_sheets, matched_harvest_sheets, matched_cultivated_sheets = [], [], []
    for sheet_name, rows in workbook_sheets(path):
        preview = " ".join(value for row in rows[:5] for value in row if value).casefold()
        season_match = re.search(
            r"season\s*([abc])\s*[_ ]*" + str(required_year)
            + r"|" + str(required_year) + r"\s*season\s*([abc])", preview)
        if not season_match:
            continue
        season = (season_match.group(1) or season_match.group(2)).upper()
        kind = None
        if re.search(r"average yield by crop type (?:and|per) district", preview) and "large-scale" not in preview and "site" not in preview:
            kind = "yield"
        elif re.search(r"harvested area by crop type (?:and|per) district", preview):
            kind = "harvested"
        elif re.search(r"cultivated area by crop type (?:and|per) district", preview):
            kind = "cultivated"
        if kind is None:
            continue
        header_index = None
        for index, row in enumerate(rows):
            if any(normalized(value) in {"district", "district/crop", "district/crop category"}
                   for value in row[:4] if value):
                header_index = index
                break
        if header_index is None:
            raise ValueError(f"No district/crop header found in {sheet_name}")
        header = rows[header_index]
        target = {"yield": yields, "harvested": harvested, "cultivated": cultivated}[kind]
        count = 0
        for row in rows[header_index + 1:]:
            if not row:
                continue
            district_col = next((i for i, value in enumerate(header[:4])
                                 if normalized(value) in {"district", "district/crop", "district/crop category"}), None)
            if district_col is None or district_col >= len(row):
                continue
            district = re.sub(r"\s+", " ", row[district_col].strip()).title()
            if normalized(district) not in DISTRICTS:
                continue
            for col, heading in enumerate(header):
                if col == district_col or not heading or normalized(heading) in GROUP_HEADERS:
                    continue
                crop = crop_name(heading)
                value = numeric(row[col]) if col < len(row) else None
                if not crop or value is None or value <= 0:
                    continue
                key = (season, district, crop)
                if key in target:
                    raise ValueError(f"Duplicate {kind} value for {key} in {sheet_name}")
                target[key] = value
                count += 1
        if count:
            {"yield": matched_yield_sheets, "harvested": matched_harvest_sheets,
             "cultivated": matched_cultivated_sheets}[kind].append(sheet_name)
    if required_year in {2022, 2023, 2024} and len(matched_yield_sheets) != 3:
        raise ValueError(f"Expected 3 overall yield sheets for {required_year}; found {matched_yield_sheets}")
    sources = matched_yield_sheets + matched_harvest_sheets + matched_cultivated_sheets
    combined = {}
    for key, yield_value in yields.items():
        if key not in harvested:
            continue
        combined[key] = {"yield_kg_ha": yield_value, "harvested_area_ha": harvested[key],
                         "cultivated_area_ha": cultivated.get(key)}
    return combined, {"yield_cells": len(yields), "harvested_area_cells": len(harvested),
                      "cultivated_area_cells": len(cultivated), "matched_cells": len(combined)}, sources


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sas-2022", type=Path, required=True)
    parser.add_argument("--sas-2023", type=Path, required=True)
    parser.add_argument("--sas-2024", type=Path, required=True)
    parser.add_argument("--sas-2025", type=Path, required=True)
    parser.add_argument("--sas-2026-a", type=Path, required=True)
    parser.add_argument("--sas-2026-b", type=Path, required=True)
    parser.add_argument("--training-table", type=Path, default=DATA / "training_table.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--report", type=Path, default=REPORT)
    args = parser.parse_args()

    with args.training_table.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        current_rows = list(reader)
    required = {"season", "season_code", "year", "district", "crop", "crop_category",
                "yield_kg_ha", "cultivated_area_ha", "harvested_area_ha", "production_mt"}
    if not required.issubset(columns):
        raise ValueError(f"Training table missing required columns: {sorted(required - set(columns))}")

    hashes = {str(year): hashlib.sha256(path.read_bytes()).hexdigest() for year, path in (
        (2022, args.sas_2022), (2023, args.sas_2023), (2024, args.sas_2024),
        (2025, args.sas_2025), ("2026-A", args.sas_2026_a),
        ("2026-B", args.sas_2026_b))}
    official_2022, coverage_2022, sheets_2022 = district_yield_tables(args.sas_2022, 2022)
    official_2023, coverage_2023, sheets_2023 = district_yield_tables(args.sas_2023, 2023)
    official_2024, coverage_2024, sheets_2024 = district_yield_tables(args.sas_2024, 2024)

    # Cross-check current report-derived labels against the independently supplied
    # official tables. The experiment keeps existing labels unchanged.
    official_checks = []
    for year, path in ((2025, args.sas_2025), (2026, args.sas_2026_a), (2026, args.sas_2026_b)):
        official, coverage, source_sheets = district_yield_tables(path, year)
        for row in current_rows:
            try:
                row_year = int(row["year"])
                target = float(row["yield_kg_ha"])
            except (ValueError, TypeError):
                continue
            if row_year != year or (year == 2026 and row["season_code"] != ("A" if "Season A" in path.name else "B")):
                continue
            key = (row["season_code"].upper(), row["district"].strip().title(), crop_name(row["crop"]) or row["crop"].strip().title())
            official_value = official.get(key)
            if official_value and target > 0:
                difference = abs(official_value["yield_kg_ha"] - target) / target * 100.0
                official_checks.append({"year": row_year, "season_code": row["season_code"],
                                        "district": row["district"], "crop": row["crop"],
                                        "training_table_yield_kg_ha": target,
                                        "official_workbook_yield_kg_ha": official_value["yield_kg_ha"],
                                        "absolute_percent_difference": difference})

    exact_crop = {normalized(row["crop"]): row["crop"] for row in current_rows if row.get("crop")}
    added = []
    added_by_year = {}
    for year, official in ((2022, official_2022), (2023, official_2023), (2024, official_2024)):
        for (season, district, crop), values in sorted(official.items()):
            yield_value = values["yield_kg_ha"]
            harvested_area = values["harvested_area_ha"]
            if yield_value <= 0 or harvested_area <= 0:
                continue
            canonical_crop = exact_crop.get(normalized(crop), crop)
            category = CATEGORIES.get(normalized(crop))
            if not category:
                raise ValueError(f"No Agri-Menya crop category mapping for official crop {crop}")
            record = {column: "" for column in columns}
            record.update({"season": f"{year} Season {season}", "season_code": season, "year": str(year),
                           "district": district, "crop": canonical_crop, "crop_category": category,
                           "yield_kg_ha": f"{yield_value:.6f}", "harvested_area_ha": f"{harvested_area:.6f}",
                           "production_mt": f"{yield_value * harvested_area / 1000.0:.9f}"})
            cultivated_area = values.get("cultivated_area_ha")
            if cultivated_area:
                record["cultivated_area_ha"] = f"{cultivated_area:.6f}"
            added.append(record)
            added_by_year[year] = added_by_year.get(year, 0) + 1

    combined = added + current_rows
    key_fields = ("district", "crop", "season_code", "year")
    seen = set()
    for row in combined:
        key = tuple(row[name].strip().casefold() for name in key_fields)
        if key in seen:
            raise ValueError(f"Duplicate district/crop/season/year key: {key}")
        seen.add(key)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(combined)

    diffs = [item["absolute_percent_difference"] for item in official_checks]
    report = {
        "purpose": "Offline model experiment and source QA only; output is not an admin import or production table.",
        "added_seasons": [f"{year} Season {season}" for year in (2022, 2023, 2024)
                          for season in ("A", "B", "C") if any(r["year"] == str(year) and r["season_code"] == season for r in added)],
        "official_table_sheets": {"2022": sheets_2022, "2023": sheets_2023, "2024": sheets_2024},
        "coverage_by_year": {"2022": coverage_2022, "2023": coverage_2023, "2024": coverage_2024},
        "added_rows_by_year": added_by_year,
        "added_rows": len(added), "existing_training_rows": len(current_rows),
        "combined_rows": len(combined),
        "matched_existing_labels_against_official_2025_2026_rows": len(official_checks),
        "existing_label_comparison_mean_absolute_percent_difference":
            sum(diffs) / len(diffs) if diffs else None,
        "existing_label_comparison_max_absolute_percent_difference": max(diffs) if diffs else None,
        "source_workbook_sha256": hashes,
        "source_note": "SAS 2022-2024 overall district tables supply yield (kg/ha), harvested area (ha), and cultivated area (ha) separately. Production_mt is computed as official yield times official harvested area / 1000 to preserve the table's yield-area identity. SITE subgroup tables are excluded.",
        "limitations": [
            "Historical auxiliary practice and land features are left blank; the pipeline does not fill them from newer seasons.",
            "The 2022-2024 output is for grouped offline evaluation; it is not activated in serving or the database.",
        ],
        "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Added {len(added)} official SAS 2022-2024 district/crop/season rows; combined input has {len(combined)} rows.")
    print(f"Compared {len(official_checks)} existing 2025/2026 labels with the supplied official workbooks.")
    print(f"Local experiment input: {args.output}\nQA report: {args.report}")


if __name__ == "__main__":
    main()
