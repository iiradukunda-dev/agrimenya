Agri-Menya Backend

Lightweight FastAPI backend for district-level agricultural recommendations.

Getting started

1. Create a Python venv and install requirements:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

2. Seed real data and (optionally) train model:

```powershell
python -m scripts.seed_real_data
python -m app.ml.train_yield_model
```

3. Run the dev server:

```powershell
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Artifacts

- `app/ml/artifacts/yield_model.pkl` — trained model bundle (optional)
- `app/ml/artifacts/yield_baselines.json` — fallback baselines (recommended)

Tests

```powershell
pip install -r requirements.txt
pytest -q
```
