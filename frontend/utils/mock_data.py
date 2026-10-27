import random

import pandas as pd

# Realistic mock data for Rwandan districts/sectors
DISTRICTS = [
    {"province": "Kigali City", "district": "Gasabo", "lat": -1.8906, "lon": 30.0898},
    {"province": "Kigali City", "district": "Kicukiro", "lat": -2.0000, "lon": 30.1250},
    {"province": "Kigali City", "district": "Nyarugenge", "lat": -1.9567, "lon": 30.0460},
    {"province": "Northern", "district": "Musanze", "lat": -1.5000, "lon": 29.6333},
    {"province": "Northern", "district": "Burera", "lat": -1.4167, "lon": 29.8000},
    {"province": "Southern", "district": "Huye", "lat": -2.5833, "lon": 29.7167},
    {"province": "Southern", "district": "Muhanga", "lat": -2.0833, "lon": 29.7500},
    {"province": "Eastern", "district": "Bugesera", "lat": -2.2000, "lon": 30.1333},
    {"province": "Eastern", "district": "Nyagatare", "lat": -1.3000, "lon": 30.3333},
    {"province": "Western", "district": "Rubavu", "lat": -1.6833, "lon": 29.2500},
]

CROPS = ["Maize", "Beans", "Cassava", "Irish Potatoes", "Rice"]
SEASONS = ["Season A", "Season B", "Season C"]

def generate_mock_priority_data():
    data = []
    for d in DISTRICTS:
        for crop in CROPS:
            priority = random.choice(["Low", "Medium", "High"])
            yield_val = random.uniform(1.0, 5.0)
            data.append({
                "District": d["district"],
                "Province": d["province"],
                "Crop": crop,
                "Priority": priority,
                "Yield_MT_ha": round(yield_val, 2),
                "Lat": d["lat"] + random.uniform(-0.05, 0.05),
                "Lon": d["lon"] + random.uniform(-0.05, 0.05)
            })
    return pd.DataFrame(data)

def _get_lang():
    try:
        from utils.i18n import get_current_language
        return get_current_language()
    except Exception:
        return "en"

def generate_mock_recommendations():
    lang = _get_lang()
    if lang == "rw":
        return [
            {"area": "Musanze", "crop": "Ibirayi", "priority": "High", "text": "Gukwirakwiza ifumbire ifite nkunganire byihuse mbere y'itangira ry'Igihembwe A.", "status": "Birategerejwe"},
            {"area": "Nyagatare", "crop": "Ibigori", "priority": "Medium", "text": "Gutegura amahugurwa ku mbuto zihanganira amapfa ku bayobozi b'amakoperative.", "status": "Birakomeje"},
            {"area": "Bugesera", "crop": "Imyumbati", "priority": "Low", "text": "Kugenzura ubuziranenge bw'ubutaka muri gahunda isanzwe.", "status": "Byararangiye"},
        ]
    elif lang == "fr":
        return [
            {"area": "Musanze", "crop": "Pommes de terre", "priority": "High", "text": "Distribuer immédiatement les engrais subventionnés avant le début de la Saison A.", "status": "En attente"},
            {"area": "Nyagatare", "crop": "Maïs", "priority": "Medium", "text": "Programmer une formation sur les semences résistantes à la sécheresse pour les coopératives.", "status": "En cours"},
            {"area": "Bugesera", "crop": "Manioc", "priority": "Low", "text": "Analyse de sol de routine recommandée.", "status": "Terminé"},
        ]
    return [
        {"area": "Musanze", "crop": "Irish Potatoes", "priority": "High", "text": "Distribute subsidized fertilizer immediately before Season A onset.", "status": "Pending"},
        {"area": "Nyagatare", "crop": "Maize", "priority": "Medium", "text": "Schedule drought-resistant seed training for cooperative leaders.", "status": "In Progress"},
        {"area": "Bugesera", "crop": "Cassava", "priority": "Low", "text": "Routine soil testing recommended.", "status": "Completed"},
    ]

def generate_mock_roadmap():
    lang = _get_lang()
    if lang == "rw":
        return pd.DataFrame([
            {"Task": "Gutumiza Imbuto", "Start": "2026-09-01", "End": "2026-09-15", "Phase": "Imyiteguro"},
            {"Task": "Gukwirakwiza Ifumbire", "Start": "2026-09-10", "End": "2026-09-25", "Phase": "Imyiteguro"},
            {"Task": "Amahugurwa yo Gutera", "Start": "2026-09-20", "End": "2026-10-05", "Phase": "Gushyira mu Bikorwa"},
            {"Task": "Gukurikirana Imihindagurikire", "Start": "2026-10-01", "End": "2026-12-01", "Phase": "Gukurikirana"}
        ])
    elif lang == "fr":
        return pd.DataFrame([
            {"Task": "Approvisionnement en Semences", "Start": "2026-09-01", "End": "2026-09-15", "Phase": "Préparation"},
            {"Task": "Distribution d'Engrais", "Start": "2026-09-10", "End": "2026-09-25", "Phase": "Préparation"},
            {"Task": "Formation aux Semis", "Start": "2026-09-20", "End": "2026-10-05", "Phase": "Exécution"},
            {"Task": "Suivi des Cultures", "Start": "2026-10-01", "End": "2026-12-01", "Phase": "Suivi & Évaluation"}
        ])
    return pd.DataFrame([
        {"Task": "Procure Seeds", "Start": "2026-09-01", "End": "2026-09-15", "Phase": "Preparation"},
        {"Task": "Distribute Fertilizer", "Start": "2026-09-10", "End": "2026-09-25", "Phase": "Preparation"},
        {"Task": "Planting Training", "Start": "2026-09-20", "End": "2026-10-05", "Phase": "Execution"},
        {"Task": "Monitoring", "Start": "2026-10-01", "End": "2026-12-01", "Phase": "Monitoring"}
    ])

def generate_mock_alerts():
    lang = _get_lang()
    if lang == "rw":
        return [
            {"type": "Warning", "message": "Imvura nyinshi iteganyijwe i Rubavu mu cyumweru gitaha. Inama yo gusarura hakiri kare ibihingwa bishobora kwangirika.", "timestamp": "Amasaha 2 ashize"},
            {"type": "Info", "message": "Ifumbire igejejwe ku cyicaro cy'Akarere ka Huye.", "timestamp": "Umunsi 1 ushize"},
            {"type": "Urgent", "message": "Icyorezo cy'imyate cyagaragaye muri Bugesera. Kohereza itsinda ryo gusuzuma byihuse.", "timestamp": "Iminsi 3 ishize"},
        ]
    elif lang == "fr":
        return [
            {"type": "Warning", "message": "Fortes pluies attendues à Rubavu la semaine prochaine. Récolte précoce conseillée pour les cultures vulnérables.", "timestamp": "Il y a 2 heures"},
            {"type": "Info", "message": "Cargaison d'engrais arrivée au siège du district de Huye.", "timestamp": "Il y a 1 jour"},
            {"type": "Urgent", "message": "Épidémie de chenilles légionnaires signalée à Bugesera. Déployer les équipes d'inspection.", "timestamp": "Il y a 3 jours"},
        ]
    return [
        {"type": "Warning", "message": "Heavy rainfall expected in Rubavu next week. Advise early harvest of vulnerable crops.", "timestamp": "2 Hours Ago"},
        {"type": "Info", "message": "Fertilizer shipment arrived in Huye district headquarters.", "timestamp": "1 Day Ago"},
        {"type": "Urgent", "message": "Fall armyworm outbreak reported in Bugesera. Deploy inspection teams.", "timestamp": "3 Days Ago"},
    ]


def generate_mock_zones() -> list[dict]:
    """Generate realistic mock zones for the zone list page."""
    zones = []
    zone_id = 1
    priorities = ["High", "Medium", "Low"]
    for d in DISTRICTS:
        for crop in CROPS[:3]:
            zones.append({
                "id": zone_id,
                "name": f"{d['district']} - {crop} Zone",
                "district": d["district"],
                "province": d["province"],
                "sector": f"Sector {zone_id % 5 + 1}",
                "cell": f"Cell {zone_id % 8 + 1}",
                "crop": crop,
                "priority": random.choice(priorities),
                "predicted_yield": round(random.uniform(800, 4500), 1),
                "latitude": d["lat"] + random.uniform(-0.03, 0.03),
                "longitude": d["lon"] + random.uniform(-0.03, 0.03),
                "risk_status": random.choice(["Stable", "At Risk", "Critical"]),
                "area_ha": round(random.uniform(5, 120), 1),
            })
            zone_id += 1
    return zones


def generate_mock_agri_metrics() -> list[dict]:
    """Generate realistic mock agri metrics for the segmentation page."""
    metrics = []
    for d in DISTRICTS:
        for crop in CROPS[:3]:
            metrics.append({
                "district": d["district"],
                "province": d["province"],
                "crop": crop,
                "yield_per_ha": round(random.uniform(800, 5000), 1),
                "area_cultivated_ha": round(random.uniform(50, 500), 0),
                "total_production_mt": round(random.uniform(100, 2500), 1),
                "rainfall_mm": round(random.uniform(600, 1400), 0),
                "season": random.choice(SEASONS),
            })
    return metrics


def generate_mock_weather(district: str) -> dict:
    """Generate mock weather data for a district."""
    return {
        "district": district,
        "temperature_c": round(random.uniform(18, 28), 1),
        "humidity_pct": round(random.uniform(55, 85), 0),
        "rainfall_mm_week": round(random.uniform(5, 60), 1),
        "condition": random.choice(["Clear", "Partly Cloudy", "Rainy", "Overcast"]),
        "wind_speed_kmh": round(random.uniform(5, 25), 1),
        "forecast_summary": f"Moderate rainfall expected in {district} over the next 7 days.",
    }



def generate_mock_model_info() -> dict:
    """Generate mock diagnostic and provenance metadata for the yield model."""
    return {
        "active_basis": "baseline",
        "model_version": "nisr-database-plus-official-sas-baseline",
        "winner": "BASELINE (XGBoost R2=0.83, MAE=214 kg/ha)",
        "metrics": {
            "validation": {"r2": 0.83, "mae": 214.2, "rmse": 298.5},
            "test": {"r2": 0.81, "mae": 228.0, "rmse": 312.1},
        },
        "training_data_span": "2018-2025 Seasonal Agricultural Survey (SAS)",
        "features": ["district", "crop", "season", "historical_yield_trend", "soil_zone", "rainfall_tier"],
        "known_limitations": [
            "Baseline predictions are observational aggregates and do not account for unmeasured micro-climate shifts.",
            "Exact district/crop/season/year coverage varies; missing seasons use clearly labeled pooled historical evidence.",
            "Bundled official tables cover overall district estimates; SITE subgroup estimates are excluded.",
        ],
        "official_evidence_years": ["2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    }


def generate_mock_district_ranking(crop: str = "Maize", season: str | None = None) -> list[dict]:
    """Generate mock evidence ranking comparing districts for a crop."""
    rankings = []
    base_yield = 2800.0
    for idx, d in enumerate(DISTRICTS, start=1):
        yield_val = round(base_yield + (len(DISTRICTS) - idx) * 120 - random.uniform(10, 50), 1)
        national_ref = 3200.0
        gap = round(max(0.0, national_ref - yield_val), 1)
        rankings.append({
            "district": d["district"],
            "yield_per_ha": yield_val,
            "benchmark_yield_per_ha": national_ref,
            "yield_gap_kg_ha": gap,
            "yield_index": round(yield_val / national_ref, 3),
            "observation_count": random.randint(12, 45),
            "seasons": [season] if season else ["Season A", "Season B"],
            "sources": ["NISR SAS"],
            "rank": idx,
        })
    return rankings
