# <img src="assets/wheat.svg" width="32" align="center"> agrimenya

**A Data-Driven Decision and Planning Support System for Agricultural Productivity in Rwanda**

*Proudly built for the **2026 NISR Big Data Hackathon**.*

---

## Overview

Welcome to Agri-Menya! We built this platform to help **planners, agricultural extension officers, and cooperative leaders** make faster, better-informed decisions that actually improve agricultural productivity across Rwanda. 

We take all that incredible (but dense!) official survey data from NISR and combine it with machine learning. The result? A tool that turns raw statistics into clear priorities, actionable roadmaps, and real-time alerts.

Instead of leaving planners to manually cross-reference endless spreadsheets and reports, Agri-Menya automatically surfaces **where to focus, what to do, and how urgent it is**.

---

## The Problem We're Solving

If you've ever looked at agricultural planning in Rwanda, you know it relies on rich, high-quality survey data (like SAS, AHS, EICV, and CFSVA). While this data is powerful, it's often underused in day-to-day decision-making simply because it's hard to digest quickly. 

Turning those datasets into concrete, local action takes significant manual analysis—time that extension officers and busy planners just don't have. We built Agri-Menya to bridge that exact gap.

---

## Core Pillars

We organized Agri-Menya around four main capabilities that talk to each other:

| Pillar | What it does for you |
|---|---|
| <img src="assets/brain.svg" width="18" align="center"> **Decision Making** | Takes the guesswork out by generating precise, automated, and proactive recommendations for specific areas. |
| <img src="assets/calendar.svg" width="18" align="center"> **Planification** | Helps you build clear planning roadmaps and step-by-step action plans so everyone knows what's next. |
| <img src="assets/map.svg" width="18" align="center"> **Segmentation** | Visually zones and prioritizes areas (Low / Medium / High) based on real climate and productivity data. |
| <img src="assets/message.svg" width="18" align="center"> **Efficient Communication** | Keeps everyone in the loop by sharing real-time alerts and plans across planners, officers, and cooperatives. |

---

## Key Features

- Priority ranking of areas so you know what's urgent (Low / Medium / High)
- <img src="assets/bot.svg" width="16"> A friendly, AI-powered assistant ready to chat and offer recommendations
- Yield and impact predictions you can actually trust
- Resource estimation (for things like seeds, irrigation, and related inputs)
- Automated creation of action roadmaps to save you time
- <img src="assets/map.svg" width="16"> Beautiful interactive maps that zone areas based on climate and productivity data
- <img src="assets/bell.svg" width="16"> Real-time alerts and cross-team communication tools
- Easily shareable decisions and plans across different user groups

---

## Who is this for?

- **Planners** — For folks handling national and district-level agricultural planning.
- **Extension Officers** — For the heroes doing on-the-ground implementation and monitoring.
- **Cooperative Leaders** — For local champions coordinating resources and sharing decisions with farmers.

---

## Where does our data come from?

All our core data is proudly sourced from the **National Institute of Statistics of Rwanda (NISR)**:

| Type | Source |
|---|---|
| **Primary** | Seasonal Agricultural Survey (SAS) — Season A 2026, Season B 2025, Annual 2025 |
| **Supporting** | Agriculture Household Survey (AHS) 2024 |
| **Contextual** | EICV7, Food Balance Sheets / CFSVA |

---

## How it works under the hood (Architecture)

```text
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

- **Frontend** — We use Streamlit for a snappy interface, Folium for our interactive maps, and Plotly to make our charts pop.
- **Backend** — A speedy FastAPI backend exposes REST endpoints for the frontend and handles all our heavy business logic.
- **Database** — Supabase (PostgreSQL) securely stores our survey data, zones, predictions, and plans.
- **Machine Learning** — scikit-learn and XGBoost models work behind the scenes to predict yields and rank priorities.

---

## Tech Stack

| Layer | What we use |
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

If you're poking around the code, here's how we've laid things out:

```text
agri-menya/
├── backend/                  # Dev A's domain (FastAPI, ML, Database)
│   ├── app/
│   │   ├── core/
│   │   ├── db/
│   │   ├── ml/
│   │   ├── models/
│   │   ├── routers/
│   │   └── services/
│   ├── data/
│   ├── scripts/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── frontend/                 # Your domain (Streamlit, UI, Maps)
│   ├── Home.py               # Main Streamlit app
│   ├── components/
│   ├── pages/
│   ├── static/
│   ├── tests/
│   ├── requirements.txt      # Frontend specific dependencies
│   └── .env.example          # Frontend specific env vars
├── infra/                    # Deployment configs (Docker, Render, etc.)
├── docs/                     # User & Developer documentation
├── tests/                    # Global/Integration tests
├── .github/                  # CI/CD workflows
├── .gitignore
└── README.md
```

---

## Getting Started

Want to run this yourself? Awesome! Here's how:

### Prerequisites
- Python 3.10 or higher
- A Supabase account and project
- Git

### 1. Clone the repository
```bash
git clone https://github.com/iiradukunda-dev/agri-menya.git
cd agri-menya
```

### 2. Set up environment variables
```bash
cp .env.example .env
# Open up .env and pop in your Supabase URL, keys, and API base URL!
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

The API docs will be ready for you at `http://localhost:8000/docs`, and you can view the app at `http://localhost:8501`.

---

## Branching Strategy

If you're contributing, here's how we keep things tidy:

| Branch | What it's for |
|---|---|
| `main` | Our stable branch. It's always deployable and what we use for demos! |
| `develop` | Where all our completed features come together. |
| `feature/*` | Where the magic happens! Individual work branches (e.g., `feature/backend-api-routes`). |

All changes go through a pull request into `develop`, which we periodically merge into `main` at major milestones. Check out [`docs/BACKEND_GUIDELINES.md`](docs/BACKEND_GUIDELINES.md) for full contribution rules.

---

## The Team

| Role | Responsibility |
|---|---|
| Project Manager & Frontend | Building out the Streamlit, Folium, and Plotly interfaces, plus keeping the repo organized. |
| Backend Developer | Hooking up FastAPI, integrating the database, and defining the API contract. |
| *(add ML/data role if applicable)* | Training models and smoothing out the data pipeline. |

---

## Roadmap

Here's a look at what we've done and where we're heading:

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

A huge thank you to the **National Institute of Statistics of Rwanda (NISR)** for providing the data as part of the 2026 NISR Big Data Hackathon. We couldn't have built this without it!
