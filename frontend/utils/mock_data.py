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
