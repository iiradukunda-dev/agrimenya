# <img src="assets/wheat.svg" width="32" align="center"> Agri-Menya

**A Data-Driven Decision and Planning Support System for Agricultural Productivity in Rwanda**

Built for the **2026 NISR Big Data Hackathon**

---

## Overview

Agri-Menya helps **planners, agricultural extension officers, and cooperative leaders** make faster, better-informed decisions to improve agricultural productivity across Rwanda. It combines official NISR survey data with machine learning to turn raw agricultural statistics into clear priorities, actionable roadmaps, and real-time alerts.

Rather than leaving planners to manually cross-reference spreadsheets and reports, Agri-Menya surfaces **where to focus, what to do, and how urgent it is** — automatically.

---

## The Problem

Agricultural planning in Rwanda relies on rich survey data (SAS, AHS, EICV, CFSVA) that is powerful but underused in day-to-day decision-making. Turning that data into concrete, local action currently takes significant manual analysis — time that extension officers and planners often don't have. Agri-Menya closes that gap.

---

## Core Pillars

Agri-Menya is organized around four connected capabilities:

| Pillar | What it does |
|---|---|
| <img src="assets/brain.svg" width="18" align="center"> **Decision Making** | Generates precise, automated, and proactive recommendations for specific areas |
| <img src="assets/calendar.svg" width="18" align="center"> **Planification** | Builds planning roadmaps and step-by-step action plans |
| <img src="assets/map.svg" width="18" align="center"> **Segmentation** | Zones and prioritizes areas (Low / Medium / High) based on climate and productivity data |
| <img src="assets/message.svg" width="18" align="center"> **Efficient Communication** | Shares real-time alerts and plans between planners, officers, and cooperatives |

---

## Key Features

- Priority ranking of areas (Low / Medium / High urgency)
- <img src="assets/bot.svg" width="16"> AI-powered recommendations and chat-style assistance
- Yield and impact prediction
- Resource estimation (seeds, irrigation, and related inputs)
- Automated creation of action roadmaps
- <img src="assets/map.svg" width="16"> Interactive maps and zoning based on climate and productivity data
- <img src="assets/bell.svg" width="16"> Real-time alerts and cross-team communication
- Shareable decisions and plans across user groups

---

## Target Users

- **Planners** — national and district-level agricultural planning
- **Extension Officers** — on-the-ground implementation and monitoring
- **Cooperative Leaders** — local resource coordination and decision-sharing

---

## Data Sources

All data comes from **NISR (National Institute of Statistics of Rwanda)**:

| Type | Source |
|---|---|
| **Primary** | Seasonal Agricultural Survey (SAS) — Season A 2026, Season B 2025, Annual 2025 |
| **Supporting** | Agriculture Household Survey (AHS) 2024 |
| **Contextual** | EICV7, Food Balance Sheets / CFSVA |

---

## Architecture

```
┌─────────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│     Frontend         │       │     Backend       │       │     Database      │
│  Streamlit + Folium  │──────▶│     FastAPI       │──────▶│  Supabase          │
│      + Plotly         │◀──────│                   │◀──────│  (PostgreSQL)      │
└─────────────────────┘       └──────────────────┘       └──────────────────┘
                                        │
                                        ▼
                              ┌──────────────────┐
                              │  Machine Learning │
                              │ scikit-learn +    │
                              │     XGBoost        │
                              └──────────────────┘
```

- **Frontend** — Streamlit renders the interface; Folium powers interactive maps; Plotly renders charts.
- **Backend** — FastAPI exposes REST endpoints consumed by the frontend and handles business logic.
- **Database** — Supabase (PostgreSQL, free tier) stores survey data, zones, predictions, and plans.
- **Machine Learning** — scikit-learn and XGBoost models power yield prediction and priority ranking.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Streamlit, Folium, Plotly |
| Backend | FastAPI |
| Database | Supabase (PostgreSQL) |
| Machine Learning | scikit-learn, XGBoost |
| Frontend Hosting | Streamlit Community Cloud |
| Backend Hosting | Render / Railway |
| Version Control | GitHub |

---

## Project Structure

```
agri-menya/
├── frontend/
│   ├── Home.py
│   ├── pages/
│   │   ├── 1_Segmentation.py
│   │   ├── 2_Decision_Making.py
│   │   ├── 3_Planification.py
│   │   └── 4_Communication.py
│   ├── components/
│   ├── utils/
│   └── assets/
├── backend/
│   ├── main.py
│   ├── routers/
│   ├── services/
│   ├── models/
│   └── schemas/
├── ml/
│   ├── notebooks/
│   ├── models/
│   └── training_scripts/
├── database/
│   └── schema.sql
├── docs/
│   ├── API_CONTRACT.md
│   └── BACKEND_GUIDELINES.md
├── .env.example
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- A Supabase account and project
- Git

### 1. Clone the repository
```bash
git clone https://github.com/<your-org>/agri-menya.git
cd agri-menya
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Fill in your Supabase URL, keys, and API base URL
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend
```bash
cd backend
uvicorn main:app --reload
```

### 5. Run the frontend
```bash
cd frontend
streamlit run Home.py
```

The API docs will be available at `http://localhost:8000/docs`, and the app at `http://localhost:8501`.

---

## Branching Strategy

| Branch | Purpose |
|---|---|
| `main` | Always deployable — used for demos |
| `develop` | Integration branch for all completed features |
| `feature/*` | Individual work branches (e.g. `feature/backend-api-routes`) |

All changes go through a pull request into `develop`; `develop` is periodically merged into `main` at milestones. See [`docs/BACKEND_GUIDELINES.md`](docs/BACKEND_GUIDELINES.md) for full contribution rules.

---

## Team

| Role | Responsibility |
|---|---|
| Project Manager & Frontend | Streamlit, Folium, Plotly interface, repo governance |
| Backend Developer | FastAPI, database integration, API contract |
| *(add ML/data role if applicable)* | Model training, data pipeline |

---

## Roadmap

- [x] Requirements defined across all four pillars
- [x] Technology stack finalized
- [x] Architecture diagram created
- [ ] Database schema implemented
- [ ] Backend API endpoints live
- [ ] Frontend pages connected to real data
- [ ] Baseline ML model trained
- [ ] End-to-end demo ready

---

## License

*(Add your chosen license here — e.g. MIT, or "Hackathon submission — all rights reserved" if not yet decided.)*

---

## Acknowledgments

Data provided by the **National Institute of Statistics of Rwanda (NISR)** as part of the 2026 NISR Big Data Hackathon.