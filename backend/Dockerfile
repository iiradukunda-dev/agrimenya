FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data/eval/yield_model_evaluation.json ./data/eval/yield_model_evaluation.json
COPY data/nisr_official_yields_2022_2026.csv ./data/nisr_official_yields_2022_2026.csv

# Database releases take precedence; published NISR SAS observations provide
# a provenance-tracked historical fallback. Training tables remain offline.
RUN test -s app/ml/artifacts/yield_intervals.json
RUN test -s data/nisr_official_yields_2022_2026.csv

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/logs \
    && chown -R app:app /app \
    && chmod -R a-w /app/app/ml/artifacts /app/data

USER app

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import json,os,urllib.request; p=os.getenv('PORT','8000'); r=urllib.request.urlopen(f'http://127.0.0.1:{p}/health/ready', timeout=4); d=json.load(r); raise SystemExit(0 if d.get('status') == 'ready' else 1)"]

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
