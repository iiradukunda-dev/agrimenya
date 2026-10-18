# Agri-Menya API Reference for Frontend Integration

This document describes the HTTP API currently registered by the backend. It is intended as a practical contract for frontend implementation. When a detail is not fixed by a response model, use the endpoint behavior and examples below as guidance and confirm actual values against the running API.

## 1. Connection setup

### Local development

Run the backend from the `backend` directory:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Set the frontend API base URL to:

```text
http://127.0.0.1:8000
```

In development, interactive API documentation is available at `http://127.0.0.1:8000/docs`; the generated OpenAPI document is at `http://127.0.0.1:8000/openapi.json`. These are disabled when `APP_ENV=production`.

Do not add an `/api` or `/v1` prefix: the routes below are mounted directly at the root.

### Deployed environment and CORS

Set `API_BASE_URL`, `USER_API_KEY`, and (for admin screens) `ADMIN_API_KEY` in the Streamlit server environment. The backend CORS allowlist is controlled by `ALLOWED_ORIGINS`; allowed API hostnames are controlled by `ALLOWED_HOSTS`. Configure both for the deployed environment, then restart/redeploy the backend.

The Streamlit frontend reads these values from its server environment. It sends the user key on production POST requests and the admin key only on admin requests:

```python
import os
import requests

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
USER_API_KEY = os.getenv("USER_API_KEY", "")

response = requests.post(
    f"{API_BASE_URL}/decision/predict",
    json=prediction_payload,
    headers={"X-API-Key": USER_API_KEY} if USER_API_KEY else {},
    timeout=15,
)
response.raise_for_status()
result = response.json()
```

For image uploads, pass file bytes using Python `requests` `files=` and let the library set the multipart boundary. The backend accepts JPEG, PNG, and WebP images up to `MAX_UPLOAD_SIZE_MB` (10 MB by default).

## 2. General contract

- JSON endpoints accept and return JSON unless explicitly marked multipart.
- Query parameters are URL-encoded. Some POST operations below use query parameters, not JSON bodies.
- UUID values must be valid UUID strings.
- Most database-backed routes can return `503` when Supabase is unavailable. Show a recoverable service error rather than treating this as an empty result.
- FastAPI validation failures normally return `422` with a `detail` array.
- Not-found responses commonly return `404` with `{"detail":"..."}`.
- Read-only data routes are public. In production, write and AI routes require `X-API-Key` set to the provisioned `USER_API_KEY`; configure it in the Streamlit server environment, never in a browser bundle.
- Admin routes require `X-Admin-Key` set to `ADMIN_API_KEY`.
- No login/token-issuance endpoint is registered in this API. Admin credentials/tokens must be provisioned separately; never put a service-role database key in browser code.

## 3. Health and root

### `GET /`
Returns basic service links.

Example response:

```json
{
  "message": "Agri-Menya API is running.",
  "docs": "/docs",
  "health": "/health"
}
```

### `GET /health`
Returns service, database, and yield-artifact status. `status` is `degraded` when the database probe fails. The health endpoint remains HTTP 200 for orchestrator liveness checks.

Example response:

```json
{
  "status": "ok",
  "database_status": "ok",
  "env": "development",
  "model_present": true,
  "model_version": "xgboost-v1-sas2026",
  "baselines_present": true,
  "baselines_overall_average": 5754.7
}
```

The model fields can be false/null if artifacts are unavailable; the endpoint can still return `status: ok`.

## 4. Segmentation and zones

### `GET /segmentation/zones`
Optional query: `district`.

Example: `GET /segmentation/zones?district=Gasabo`

Returns an array of zone records, typically including `id`, `district`, `sector`, `cell`, `latitude`, `longitude`, `crop_type`, `season`, and `created_at`.

### `POST /segmentation/zones`
Creates a zone. JSON body:

```json
{
  "district": "Gasabo",
  "sector": "Kimihurura",
  "cell": "Rugando",
  "latitude": -1.9441,
  "longitude": 30.0928,
  "crop_type": "Maize",
  "season": "Season A 2026"
}
```

`sector`, `cell`, `crop_type`, and `season` are optional; `district`, `latitude`, and `longitude` are required. Returns the inserted zone record.

### `GET /segmentation/zones/{zone_id}`
Returns one zone record. Returns `404` if the zone does not exist.

### `GET /segmentation/map-data`
Optional query: `district`.

Returns zone records enriched with the latest prediction fields:

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "district": "Gasabo",
    "sector": "Kimihurura",
    "cell": "Rugando",
    "latitude": -1.9441,
    "longitude": 30.0928,
    "predicted_yield": 2100.0,
    "priority_level": "Medium"
  }
]
```

`predicted_yield` and `priority_level` are `null` if no prediction exists.

### `GET /segmentation/agri-metrics`
Optional query parameters: `district`, `crop`, `season`.

Returns an array of metric records, normally with `zone_id`, `season`, `crop`, `yield_actual`, `production_mt`, `rainfall_mm`, `soil_type`, `area_cultivated`, `household_size`, and joined zone location data where available. An empty array means there are no matching metrics.

### `GET /segmentation/crop-comparison/{district}`
Optional query: `season`.

Returns matching agricultural metric rows sorted by `yield_actual` descending. Returns `404` if there are no matching rows.

## 5. Decision and yield prediction

### `GET /decision/crops`
Returns an array of crop names supported by the prediction pipeline. Use these returned values in crop selectors rather than hard-coding a separate list.

### `POST /decision/predict`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "season": "Season A 2026",
  "crop": "Maize",
  "rainfall_mm": 850,
  "area_cultivated": 1.2,
  "soil_type": "loam",
  "household_size": 5
}
```

Required: `zone_id`, `season`. `crop` defaults to `All crops`; other input fields are optional numbers/strings.

Example response:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "season": "Season A 2026",
  "crop": "Maize",
  "predicted_yield": 2100.0,
  "priority_level": "Medium",
  "confidence": 0.78,
  "model_version": "xgboost-v1-sas2026",
  "yield_per_ha": 2100.0,
  "benchmark_yield_per_ha": 2600.0,
  "yield_gap_kg_ha": 500.0,
  "yield_index": 0.81
}
```

Numeric results above are illustrative. The response includes `predicted_yield`, `priority_level` (`Low`, `Medium`, or `High`), `confidence`, `model_version`, and nullable analysis fields. A successful prediction is also saved by the backend. Returns `404` if `zone_id` is unknown.

### `GET /decision/district-ranking?crop={crop}&season={season}`
Required query: `crop`. Optional query: `season`.

Returns an array of district rows, sorted by `yield_index` ascending:

```json
[
  {
    "district": "Gasabo",
    "yield_per_ha": 2100.0,
    "benchmark_yield_per_ha": 2600.0,
    "yield_gap_kg_ha": 500.0,
    "yield_index": 0.81,
    "cultivated_area_ha": 120.0,
    "potential_gain_mt": 60.0
  }
]
```

The numeric fields may be `null` where no estimate is available. Unknown crops return `404`.

### `GET /decision/priority-ranking`
Optional query: `season`.

Returns prediction records joined with zone location fields, sorted High, Medium, then Low priority. The endpoint does not promise pagination.

### `GET /decision/recommendations/{zone_id}`
Optional query parameters: `rainfall_mm`, `soil_type`.

Returns:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "priority_level": "High",
  "recommendations": ["..."]
}
```

The recommendations are based on the latest saved prediction for the zone. Returns `404` if the zone has no predictions.

### `POST /decision/disease-risk`
Despite being a POST, this endpoint currently accepts query parameters, not a JSON body.

Required query: `zone_id`, `crop`, `symptoms`. Optional query: `image_description`.

Example:

```text
POST /decision/disease-risk?zone_id=123e4567-e89b-12d3-a456-426614174000&crop=Maize&symptoms=yellow%20leaves
```

Returns:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "crop": "Maize",
  "predicted_disease": "...",
  "confidence": 0.72,
  "risk_level": "Medium",
  "recommended_actions": ["..."]
}
```

Returns `404` if the zone does not exist.

## 6. National alignment

### `POST /alignment/compute/{zone_id}`
This POST currently takes all inputs as query parameters, not as a JSON body.

Required query: `season`, `predicted_yield`. Optional: `area_cultivated`, `rainfall_mm`, `priority_level` (defaults to `Medium`), `crop`, `district`.

Example:

```text
POST /alignment/compute/123e4567-e89b-12d3-a456-426614174000?season=Season%20A%202026&predicted_yield=2100&area_cultivated=1.2&rainfall_mm=850&priority_level=Medium&crop=Maize&district=Gasabo
```

Returns the saved alignment metric row, including fields such as `credit_insurance_score`, `nutrition_risk_level`, `climate_risk_level`, `export_readiness_flag`, `estimated_jobs_supported`, `irrigation_ha`, and `terraces_ha`. Returns `404` if the zone is unknown.

### `GET /alignment/finance-readiness/{zone_id}`
Returns:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "credit_insurance_score": 71.5
}
```

Returns `404` if alignment metrics have not been computed for the zone.

### `GET /alignment/nutrition-risk/{zone_id}`
Returns:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "nutrition_risk_level": "Medium"
}
```

Returns `404` if alignment metrics have not been computed for the zone.

### `GET /alignment/export-flags`
Returns an array of alignment metric records whose `export_readiness_flag` is true.

### `GET /alignment/dashboard`
Returns national summary fields:

```json
{
  "total_zones": 12,
  "avg_irrigation_ha": 0.0,
  "avg_terraces_ha": 0.0,
  "avg_credit_insurance_score": 71.5,
  "zones_high_nutrition_risk": 2,
  "zones_high_climate_risk": 3,
  "zones_export_ready": 4,
  "total_estimated_jobs": 24
}
```

When no metrics exist, it returns an object with a `message` explaining that alignment must be computed first.

## 7. AI assistant and disease detection

### `POST /chat`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "What should we prioritize for this zone?"
}
```

`question` must contain 1-500 characters.

Response:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "question": "What should we prioritize for this zone?",
  "answer": "...",
  "source": "grounded-context"
}
```

Returns `404` if the zone does not exist. The assistant may use local grounded context if an external LLM is not configured or unavailable; the frontend should display the answer and source rather than assume every answer came from an external model.

### `POST /chat/disease-detect`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "crop": "Maize",
  "symptoms": "Yellowing leaves and brown lesions",
  "image_description": "Optional description of visible symptoms",
  "image_url": null
}
```

Required: `zone_id`, `crop` (1-50 characters), `symptoms` (1-1000 characters). `image_description` and `image_url` are optional; the current handler passes symptoms and description to the detector and does not use `image_url` to fetch an image.

Response:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "crop": "Maize",
  "predicted_disease": "...",
  "confidence": 0.72,
  "risk_level": "Medium",
  "recommended_actions": ["..."],
  "source": "trained-disease-model"
}
```

### `POST /chat/disease-detect-upload`
Multipart `FormData`, not JSON:

| Field | Type | Required |
|---|---|---|
| `zone_id` | UUID string | Yes |
| `crop` | string | Yes |
| `symptoms` | string | Yes |
| `image_description` | string | No |
| `image` | file | No |

Python `requests` example:

```python
with open(image_path, "rb") as image_file:
    response = requests.post(
        f"{API_BASE_URL}/chat/disease-detect-upload",
        data={"zone_id": zone_id, "crop": crop, "symptoms": symptoms},
        files={"image": ("field.png", image_file, "image/png")},
        headers={"X-API-Key": USER_API_KEY} if USER_API_KEY else {},
        timeout=30,
    )
response.raise_for_status()
result = response.json()
```

The response has the same fields as `/chat/disease-detect`. Disease inference depends on available model artifacts and may use the safe fallback path; do not label results as clinically confirmed.

## 8. Planning

### `GET /planification/resources/{zone_id}`
Optional query parameters: `area_cultivated`, `rainfall_mm`.

Returns a resource estimate. The current route accepts `zone_id` for the path but derives the estimate from the optional query inputs.

### `POST /planification/roadmap`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Season A maize support plan",
  "roadmap": [
    {
      "step_number": 1,
      "title": "Prepare land",
      "description": "Prepare the field before planting.",
      "timeframe": "Week 1"
    }
  ],
  "resources": {
    "seeds_kg": 20,
    "fertilizer_kg": 50,
    "irrigation_liters": 1000,
    "estimated_cost_rwf": 75000
  },
  "created_by": "extension-officer"
}
```

Required: `zone_id`, `title`, `roadmap`, `resources`. Step `timeframe`, resource numbers, and `created_by` are optional. Returns the inserted plan record with `roadmap_json` and `resources_json`. Returns `404` for an unknown zone.

### `GET /planification/plans/{zone_id}`
Returns an array of saved plan records for the zone. A database `503` is currently converted to an empty array by this route, so an empty response may mean either no plans or a temporarily unavailable database.

### `POST /planification/disease-plan`
This POST currently accepts query parameters rather than a JSON body.

Required query: `zone_id`, `crop`, `symptoms`. Optional: `image_description`.

Returns:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "crop": "Maize",
  "predicted_disease": "...",
  "risk_level": "Medium",
  "recommended_actions": ["..."],
  "roadmap": ["...", "...", "..."]
}
```

## 9. Communication and alerts

### `POST /communication/notify`
JSON body:

```json
{
  "phone": "+2507XXXXXXXX",
  "email": "farmer@example.rw",
  "message": "Field visit scheduled for tomorrow.",
  "channels": ["sms", "whatsapp", "email"]
}
```

`message` is required (1-1000 characters). `phone`, `email` are optional. Channels can include `sms`, `whatsapp`, `email`, `voice`, and `ussd`; if omitted/empty, the backend defaults to `sms` and `whatsapp`.

Response contains `status`, `channels`, `deliveries`, `message`, `simulated`, and `recipient`. Delivery may be queued/simulated if provider credentials are not configured; the frontend must distinguish `queued` from `sent`.

### `POST /communication/alerts`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Heavy rainfall risk reported.",
  "severity": "Warning",
  "created_by": "extension-officer"
}
```

`severity` is one of `Info`, `Warning`, `Critical` and defaults to `Info`. Returns the saved alert record. The route also attempts configured SMS, WhatsApp, and email delivery using backend defaults.

### `GET /communication/alerts`
Optional query: `zone_id`. Returns alert records, newest first.

### `GET /communication/share/{plan_id}`
Returns the plan record for sharing, or `{"error":"Plan not found"}` when no matching plan exists. This endpoint currently returns JSON, not a generated PDF or public link.

## 10. Live data and field reports

### `GET /live/weather/{district}`
Returns weather context for the district. Provider/fallback fields depend on weather service availability; treat the response as contextual data and show any freshness/source metadata returned.

### `POST /live/field-report`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "district": "Gasabo",
  "crop": "Maize",
  "rainfall_mm": 35,
  "soil_moisture_pct": 42,
  "symptoms": "Some leaves are yellowing",
  "notes": "Observed during the morning visit"
}
```

Required: `zone_id`, `district` (1-100 characters), `crop` (1-50 characters). Other fields are optional; `symptoms` max 500 characters and `notes` max 1000 characters. Returns the submitted report/result from the field-report service.

### `GET /live/field-reports/{zone_id}`
Returns up to 20 reports for the zone.

### `POST /live/context`
JSON body:

```json
{
  "zone_id": "123e4567-e89b-12d3-a456-426614174000",
  "district": "Gasabo",
  "crop": "Maize",
  "rainfall_mm": 35,
  "notes": "Recent field observation"
}
```

At least one of `zone_id` or `district` is required. Returns a combined live context result. Returns `400` if both are absent.

## 11. Admin API and credentials

All `/admin` endpoints require an admin credential. Supported request forms are:

```http
Authorization: Bearer <admin-token>
```

or, for API-key mode:

```http
X-Admin-Key: <ADMIN_API_KEY>
```

`X-API-Key` is also accepted by the backend auth dependency. The API key must be configured on the server; do not embed it in a public browser bundle. If the frontend needs admin workflows, use a trusted server-side proxy/backend-for-frontend rather than exposing a shared secret to every browser user.

### `GET /admin/zones?district={district}`
Optional query: `district`. Returns zones. Requires admin auth.

### `PATCH /admin/zones/{zone_id}`
JSON object containing only fields to update, for example:

```json
{"season":"Season B 2026","crop_type":"Beans"}
```

Returns the updated zone, or `404` if missing.

### `DELETE /admin/zones/{zone_id}`
Returns the deleted record with `deleted: true`, or `404` if missing.

### `GET /admin/plans`
Returns all plan records. Requires admin auth.

### `PATCH /admin/plans/{plan_id}`
JSON object containing fields to update. Returns the updated plan or `404` if missing.

### `DELETE /admin/plans/{plan_id}`
Deletes a plan; returns the deleted record with `deleted: true`, or `404` if missing.

### `GET /admin/alerts`
Returns all alert records. Requires admin auth.

### `PATCH /admin/alerts/{alert_id}`
JSON object containing fields to update. Returns the updated alert or `404` if missing.

### `DELETE /admin/alerts/{alert_id}`
Deletes an alert; returns the deleted record with `deleted: true`, or `404` if missing.

Admin actions are audited by the backend.

## 12. Debug endpoint

In non-production environments only:

### `GET /debug/logs?lines=200`
Returns the last requested number of application log lines. It is not registered when `APP_ENV=production`. Do not expose this endpoint as a normal frontend feature.

## 13. Frontend integration checklist

1. Configure one base URL from the frontend environment; do not hard-code localhost in deployed builds.
2. Confirm backend `ALLOWED_ORIGINS` includes the exact frontend origin, including scheme and port.
3. Use JSON bodies for documented JSON endpoints and query parameters for endpoints explicitly marked query-based.
4. Use `requests` multipart `files=` for disease image upload.
5. Handle `422`, `404`, `401`, and `503` separately; show actionable errors.
6. Distinguish empty arrays from errors, especially for `/planification/plans/{zone_id}`.
7. Treat message delivery as queued unless the delivery object reports `sent`; provider credentials may not be configured.
8. Do not expose `SUPABASE_SERVICE_ROLE_KEY`, `ADMIN_API_KEY`, or other server secrets in browser code.
9. Use `/docs` and `/openapi.json` on the running backend as the final source of truth if the API changes.

## 14. Endpoint index

| Method | Path | Input style | Auth |
|---|---|---|---|
| GET | `/` | none | No |
| GET | `/health` | none | No |
| GET | `/segmentation/zones` | query | No |
| POST | `/segmentation/zones` | JSON | User (production) |
| GET | `/segmentation/map-data` | query | No |
| GET | `/segmentation/zones/{zone_id}` | path | No |
| GET | `/segmentation/agri-metrics` | query | No |
| GET | `/segmentation/crop-comparison/{district}` | path + query | No |
| GET | `/decision/crops` | none | No |
| POST | `/decision/predict` | JSON | User (production) |
| GET | `/decision/district-ranking` | query | No |
| GET | `/decision/priority-ranking` | query | No |
| GET | `/decision/recommendations/{zone_id}` | path + query | No |
| POST | `/decision/disease-risk` | query | User (production) |
| POST | `/alignment/compute/{zone_id}` | path + query | User (production) |
| GET | `/alignment/finance-readiness/{zone_id}` | path | No |
| GET | `/alignment/nutrition-risk/{zone_id}` | path | No |
| GET | `/alignment/export-flags` | none | No |
| GET | `/alignment/dashboard` | none | No |
| POST | `/chat` | JSON | User (production) |
| POST | `/chat/disease-detect` | JSON | User (production) |
| POST | `/chat/disease-detect-upload` | multipart | User (production) |
| GET | `/planification/resources/{zone_id}` | path + query | No |
| POST | `/planification/roadmap` | JSON | User (production) |
| GET | `/planification/plans/{zone_id}` | path | No |
| POST | `/planification/disease-plan` | query | User (production) |
| POST | `/communication/notify` | JSON | User (production) |
| POST | `/communication/alerts` | JSON | User (production) |
| GET | `/communication/alerts` | query | No |
| GET | `/communication/share/{plan_id}` | path | No |
| GET | `/live/weather/{district}` | path | No |
| POST | `/live/field-report` | JSON | User (production) |
| GET | `/live/field-reports/{zone_id}` | path | No |
| POST | `/live/context` | JSON | User (production) |
| GET | `/admin/zones` | query | Admin |
| PATCH | `/admin/zones/{zone_id}` | JSON | Admin |
| DELETE | `/admin/zones/{zone_id}` | path | Admin |
| GET | `/admin/plans` | none | Admin |
| PATCH | `/admin/plans/{plan_id}` | JSON | Admin |
| DELETE | `/admin/plans/{plan_id}` | path | Admin |
| GET | `/admin/alerts` | none | Admin |
| PATCH | `/admin/alerts/{alert_id}` | JSON | Admin |
| DELETE | `/admin/alerts/{alert_id}` | path | Admin |
| GET | `/debug/logs` | query | Non-production only |
