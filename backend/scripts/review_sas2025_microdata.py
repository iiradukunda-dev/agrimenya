"""Create a suppressed, weighted QA summary from NISR SAS 2025 ZIP files.

This is an offline review aid only. It does not import records into Agri-Menya,
does not emit row-level data, and deliberately writes a non-importable schema.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
import zipfile


DISTRICTS = {
    "11": "Nyarugenge", "12": "Gasabo", "13": "Kicukiro",
    "21": "Nyanza", "22": "Gisagara", "23": "Nyaruguru", "24": "Huye",
    "25": "Nyamagabe", "26": "Ruhango", "27": "Muhanga", "28": "Kamonyi",
    "31": "Karongi", "32": "Rutsiro", "33": "Rubavu", "34": "Nyabihu",
    "35": "Ngororero", "36": "Rusizi", "37": "Nyamasheke",
    "41": "Rulindo", "42": "Gakenke", "43": "Musanze", "44": "Burera", "45": "Gicumbi",
    "51": "Rwamagana", "52": "Nyagatare", "53": "Gatsibo", "54": "Kayonza",
    "55": "Kirehe", "56": "Ngoma", "57": "Bugesera",
}
DISTRICT_NAMES = {name.casefold(): name for name in DISTRICTS.values()}
DISTRICT_NAMES["nyarugenege"] = "Nyarugenge"  # spelling variant present in the released file
MIN_EFFECTIVE_N = 30.0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="NISR SAS 2025 ZIP file")
    parser.add_argument("--output", type=Path, default=Path("backend/data/nisr_microdata_review/sas2025_weighted_qa.csv"))
    parser.add_argument("--training-table", type=Path, default=Path("backend/data/training_table.csv"))
    parser.add_argument("--report-output", type=Path, default=Path("backend/data/eval/sas2025_microdata_validation.json"))
    args = parser.parse_args()
    buckets: dict[tuple[str, str, str], list[float]] = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    source_files = 0
    with zipfile.ZipFile(args.input) as archive:
        for member in archive.namelist():
            if not member.casefold().endswith("_production.csv"):
                continue
            season_match = next((letter for letter in "ABC" if f"season{letter}2025".casefold() in member.casefold()), None)
            if not season_match:
                continue
            source_files += 1
            with archive.open(member) as binary:
                reader = csv.DictReader(io.TextIOWrapper(binary, encoding="utf-8-sig", newline=""), delimiter="\t")
                fields = {str(name).strip().casefold(): name for name in (reader.fieldnames or [])}
                required = {"s1q2", "cropcategory", "yield"}
                if not required.issubset(fields):
                    raise ValueError(f"Unexpected production file schema: {Path(member).name}")
                weight_field = fields.get("plot_weight") or fields.get("plot_weight ")
                if weight_field is None:
                    raise ValueError(f"Missing plot weight in {Path(member).name}")
                for row in reader:
                    district_code = (row.get(fields["s1q2"]) or "").strip()
                    district = DISTRICT_NAMES.get(district_code.casefold()) or DISTRICTS.get(district_code)
                    crop = (row.get(fields["cropcategory"]) or "").strip()
                    try:
                        value = float((row.get(fields["yield"]) or "").replace(",", ""))
                        weight = float((row.get(weight_field) or "").replace(",", ""))
                    except (ValueError, AttributeError):
                        continue
                    if not district or not crop or not math.isfinite(value) or value <= 0 or not math.isfinite(weight) or weight <= 0:
                        continue
                    bucket = buckets[(f"2025 Season {season_match}", district, crop)]
                    bucket[0] += weight * value
                    bucket[1] += weight
                    bucket[2] += weight * weight
                    bucket[3] += 1
    if source_files != 3:
        raise ValueError(f"Expected three Season A/B/C production CSVs; found {source_files}.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Keep the names distinct from the admin import contract so this diagnostic
    # cannot accidentally be selected as a live NISR release.
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["review_season", "district", "crop_label", "weighted_yield_diagnostic_kg_ha", "effective_sample_size", "disclosure_status"])
        for (season, district, crop), (weighted_sum, weight_sum, squared_weight_sum, _n) in sorted(buckets.items()):
            effective_n = weight_sum * weight_sum / squared_weight_sum if squared_weight_sum else 0
            if effective_n < MIN_EFFECTIVE_N:
                writer.writerow([season, district, crop, "", "", "suppressed_small_effective_sample"])
            else:
                writer.writerow([season, district, crop, round(weighted_sum / weight_sum, 1), round(effective_n, 1), "review_only"])
    published = {}
    with args.training_table.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            if str(row.get("year", "")).strip() != "2025":
                continue
            try:
                target = float(row.get("yield_kg_ha", ""))
            except (TypeError, ValueError):
                continue
            if not math.isfinite(target) or target <= 0:
                continue
            published[(str(row.get("season", "")).strip().casefold(),
                       str(row.get("district", "")).strip().casefold(),
                       str(row.get("crop", "")).strip().casefold())] = target
    differences = []
    comparable_cells = 0
    for (season, district, crop), (weighted_sum, weight_sum, squared_weight_sum, _n) in buckets.items():
        effective_n = weight_sum * weight_sum / squared_weight_sum if squared_weight_sum else 0
        if effective_n < MIN_EFFECTIVE_N or weight_sum <= 0:
            continue
        report_yield = published.get((season.casefold(), district.casefold(), crop.casefold()))
        if report_yield is None:
            continue
        microdata_yield = weighted_sum / weight_sum
        differences.append(abs(microdata_yield - report_yield) / report_yield * 100.0)
        comparable_cells += 1
    report = {
        "source": "NISR Rwanda Seasonal Agricultural Survey 2025 public-use production files",
        "source_zip_sha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
        "published_training_table_sha256": hashlib.sha256(args.training_table.read_bytes()).hexdigest(),
        "comparison": "Plot-weighted arithmetic mean of plot Yield against existing 2025 NISR report-derived district/crop/season yield labels.",
        "comparable_cells": comparable_cells,
        "mean_absolute_percent_difference": round(mean(differences), 4) if differences else None,
        "median_absolute_percent_difference": round(median(differences), 4) if differences else None,
        "cells_within_1_percent": round(100.0 * sum(value <= 1.0 for value in differences) / len(differences), 2) if differences else None,
        "maximum_absolute_percent_difference": round(max(differences), 4) if differences else None,
        "interpretation": "Microdata used for an aggregate QA cross-check, not for fitting or activating a plot-level model. This simple weighted mean is not a design-based variance estimate; material cell differences require review against NISR tabulation methods.",
        "suppression": f"Review output suppresses cells with effective sample size below {MIN_EFFECTIVE_N:g}.",
    }
    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    args.report_output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {len(buckets)} aggregated cells to {args.output}; cells below effective n={MIN_EFFECTIVE_N:g} are suppressed.")
    print(f"Compared {comparable_cells} aggregate cells to published labels; wrote QA metrics to {args.report_output}.")
    print("This weighted-mean diagnostic is not a design-based estimate or confidence interval and is not an import file.")


if __name__ == "__main__":
    main()
