"""
Approximate centroid coordinates (district-town level) for Rwanda's 30
districts, grouped by province. Used to seed one `zones` row per
district when loading real SAS/AHS data - good enough for map markers
and zoning at district granularity; refine to sector-level centroids
later if the frontend needs finer zoom.
"""

RWANDA_DISTRICTS = [
    # Kigali City
    {"district": "Gasabo", "province": "Kigali City", "latitude": -1.9346, "longitude": 30.1044},
    {"district": "Kicukiro", "province": "Kigali City", "latitude": -1.9878, "longitude": 30.1044},
    {"district": "Nyarugenge", "province": "Kigali City", "latitude": -1.9536, "longitude": 30.0605},
    # Southern Province
    {"district": "Gisagara", "province": "Southern Province", "latitude": -2.5833, "longitude": 29.8333},
    {"district": "Huye", "province": "Southern Province", "latitude": -2.5967, "longitude": 29.7392},
    {"district": "Kamonyi", "province": "Southern Province", "latitude": -2.0333, "longitude": 29.8833},
    {"district": "Muhanga", "province": "Southern Province", "latitude": -2.0833, "longitude": 29.7500},
    {"district": "Nyamagabe", "province": "Southern Province", "latitude": -2.4667, "longitude": 29.4667},
    {"district": "Nyanza", "province": "Southern Province", "latitude": -2.3500, "longitude": 29.7500},
    {"district": "Nyaruguru", "province": "Southern Province", "latitude": -2.6167, "longitude": 29.5667},
    {"district": "Ruhango", "province": "Southern Province", "latitude": -2.2167, "longitude": 29.7833},
    # Western Province
    {"district": "Karongi", "province": "Western Province", "latitude": -2.0000, "longitude": 29.3833},
    {"district": "Ngororero", "province": "Western Province", "latitude": -1.8667, "longitude": 29.5667},
    {"district": "Nyabihu", "province": "Western Province", "latitude": -1.6500, "longitude": 29.5000},
    {"district": "Nyamasheke", "province": "Western Province", "latitude": -2.3500, "longitude": 29.1333},
    {"district": "Rubavu", "province": "Western Province", "latitude": -1.6789, "longitude": 29.2661},
    {"district": "Rusizi", "province": "Western Province", "latitude": -2.4846, "longitude": 28.9075},
    {"district": "Rutsiro", "province": "Western Province", "latitude": -1.8833, "longitude": 29.3333},
    # Northern Province
    {"district": "Burera", "province": "Northern Province", "latitude": -1.4667, "longitude": 29.8667},
    {"district": "Gakenke", "province": "Northern Province", "latitude": -1.6833, "longitude": 29.7833},
    {"district": "Gicumbi", "province": "Northern Province", "latitude": -1.5667, "longitude": 30.1000},
    {"district": "Musanze", "province": "Northern Province", "latitude": -1.4995, "longitude": 29.6335},
    {"district": "Rulindo", "province": "Northern Province", "latitude": -1.7500, "longitude": 30.0333},
    # Eastern Province
    {"district": "Bugesera", "province": "Eastern Province", "latitude": -2.2167, "longitude": 30.2500},
    {"district": "Gatsibo", "province": "Eastern Province", "latitude": -1.6000, "longitude": 30.4667},
    {"district": "Kayonza", "province": "Eastern Province", "latitude": -1.8833, "longitude": 30.5333},
    {"district": "Kirehe", "province": "Eastern Province", "latitude": -2.2500, "longitude": 30.7833},
    {"district": "Ngoma", "province": "Eastern Province", "latitude": -2.1667, "longitude": 30.5333},
    {"district": "Nyagatare", "province": "Eastern Province", "latitude": -1.2947, "longitude": 30.3250},
    {"district": "Rwamagana", "province": "Eastern Province", "latitude": -1.9487, "longitude": 30.4347},
]

DISTRICT_LOOKUP = {d["district"]: d for d in RWANDA_DISTRICTS}
