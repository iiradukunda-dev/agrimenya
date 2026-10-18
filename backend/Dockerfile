FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data/eval/yield_model_evaluation.json ./data/eval/yield_model_evaluation.json

# Baseline estimates come from database observations. The interval calibration
# is a compact evaluation artifact; training tables remain in the offline job.
RUN test -s app/ml/artifacts/yield_intervals.json

RUN groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /app/logs \
    && chown -R app:app /app \
    && chmod -R a-w /app/app/ml/artifacts /app/data

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import json,urllib.request; r=urllib.request.urlopen('http://127.0.0.1:8000/health/ready', timeout=4); d=json.load(r); raise SystemExit(0 if d.get('status') == 'ready' else 1)"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
