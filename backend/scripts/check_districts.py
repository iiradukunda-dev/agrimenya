import csv
import sys
from pathlib import Path

# Project layout: this script lives in backend/scripts
project_root = Path(__file__).resolve().parents[1]
# Ensure project root on path so we can import app.db.rwanda_districts
sys.path.insert(0, str(project_root))

try:
    from app.db.rwanda_districts import RWANDA_DISTRICTS
except Exception as e:
    print('import_error:', e)
    RWANDA_DISTRICTS = []

csv_path = project_root / 'data' / 'agri_menya_real_data.csv'
if not csv_path.exists():
    print('csv_missing:', csv_path)
    sys.exit(1)

with csv_path.open(newline='') as f:
    reader = csv.DictReader(f)
    districts = sorted({row['district'] for row in reader if row.get('district')})

districts_from_file = sorted(d['district'] for d in RWANDA_DISTRICTS)

print('csv_unique_districts_count:', len(districts))
print('rw_dist_count:', len(districts_from_file))

csv_only = sorted(set(districts) - set(districts_from_file))
rw_only = sorted(set(districts_from_file) - set(districts))

print('csv_only_count:', len(csv_only))
print('csv_only:', csv_only)
print('rw_only_count:', len(rw_only))
print('rw_only:', rw_only)

# show sample of matching names
matches = sorted(set(districts).intersection(districts_from_file))
print('matches_count:', len(matches))
print('matches_sample(10):', matches[:10])
