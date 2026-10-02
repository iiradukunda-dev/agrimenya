"""
Build yield baseline JSON used by `app.ml.predict`.
Produces `app/ml/artifacts/yield_baselines.json` with keys:
- district_crop_averages: {"District|Crop": avg_kg_ha}
- crop_averages: {"Crop": avg_kg_ha}
- overall_average: number

Usage:
    cd backend
    python -m scripts.build_yield_baseline [path/to/agri_menya_real_data.csv]
"""
from pathlib import Path
import sys
import json
import statistics
import csv

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "agri_menya_real_data.csv"
ARTIFACT_DIR = ROOT / "app" / "ml" / "artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PATH = ARTIFACT_DIR / "yield_baselines.json"

# read CSV and aggregate yields per district|crop and per crop
rows = []
with open(DATA_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for r in reader:
        try:
            y = float(r.get('yield_kg_ha') or 0)
        except Exception:
            continue
        if y <= 0:
            continue
        district = r.get('district')
        crop = r.get('crop')
        if not district or not crop:
            continue
        rows.append({'district': district.strip(), 'crop': crop.strip(), 'yield': y})

# collect
from collections import defaultdict
by_district_crop = defaultdict(list)
by_crop = defaultdict(list)
all_vals = []
for r in rows:
    key = f"{r['district']}|{r['crop']}"
    by_district_crop[key].append(r['yield'])
    by_crop[r['crop']].append(r['yield'])
    all_vals.append(r['yield'])

district_crop_avg = {k: round(statistics.mean(v), 1) for k, v in by_district_crop.items()}
crop_avg = {k: round(statistics.mean(v), 1) for k, v in by_crop.items()}
overall = round(statistics.mean(all_vals), 1) if all_vals else None

payload = {
    'district_crop_averages': district_crop_avg,
    'crop_averages': crop_avg,
    'overall_average': overall,
}

with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(payload, f, indent=2, ensure_ascii=False)

print(f"Wrote {len(district_crop_avg)} district|crop entries and {len(crop_avg)} crop entries to {OUT_PATH}")
