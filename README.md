<div align="center">
  <img src="frontend/assets/logo.jpg" alt="agrimenya logo" width="120" style="border-radius: 20px;"/>
  <h1>agrimenya</h1>
  <p><b>A Data-Driven Decision and Planning Support System for Agricultural Productivity in Rwanda</b></p>
  <p><i>Proudly built for the <b>2026 NISR Big Data Hackathon</b></i></p>
</div>

---

## 🌾 Overview

**agrimenya** is an intelligent platform designed to help **planners, agricultural extension officers, and cooperative leaders** make faster, better-informed decisions to improve agricultural productivity across Rwanda.

By aggregating dense official survey data from the National Institute of Statistics of Rwanda (NISR) and augmenting it with machine learning, agrimenya transforms raw statistics into clear priorities, actionable roadmaps, and real-time alerts.

Instead of leaving planners to manually cross-reference endless spreadsheets and reports, agrimenya automatically surfaces **where to focus, what to do, and how urgent it is**.

---

## 🎯 The Problem We're Solving

Agricultural planning in Rwanda relies on rich, high-quality survey data (SAS, AHS, EICV, and CFSVA). While this data is powerful, it is often underutilized in day-to-day decision-making simply because it is difficult to digest quickly.

Turning those datasets into concrete, local action takes significant manual analysis—time that extension officers and busy planners just don't have. We built agrimenya to bridge that exact gap.

---

## 🏗️ Core Pillars

agrimenya is organized around four core capabilities that communicate seamlessly with each other:

| Pillar | Capability | Description |
|:---:|:---|:---|
| 🧠 | **Decide** | Takes the guesswork out by generating precise, automated, and proactive recommendations for specific agricultural zones. |
| 📅 | **Plan** | Helps you build clear planning roadmaps and step-by-step action plans so stakeholders know exactly what's next. |
| 🗺️ | **Segment** | Visually zones and prioritizes areas (Low / Medium / High) based on real climate, yield, and productivity data. |
| 📡 | **Communicate** | Keeps everyone in the loop by sharing real-time alerts and plans across planners, officers, and cooperatives. |

---

## ✨ Key Features

- **Priority Ranking:** Automatic classification of agricultural areas so you know what's urgent.
- **AI-Powered Insights:** A conversational AI assistant ready to offer contextual recommendations and answer data-driven questions.
- **Yield & Impact Predictions:** Reliable forecasts powered by XGBoost ML models.
- **Resource Estimation:** Forecasting needs for seeds, irrigation, and related inputs.
- **Interactive Zoning:** Beautiful interactive maps (powered by Folium and CartoDB) that zone areas based on climate and productivity.
- **Unified Alerting:** Real-time alerts and cross-team communication tools.

---

## 👥 Target Audience

- **Planners:** For officials handling national and district-level agricultural planning.
- **Extension Officers:** For the frontline workers doing on-the-ground implementation and monitoring.
- **Cooperative Leaders:** For local champions coordinating resources and sharing decisions with farmers.

---

## 📊 Data Sources

All our core data is proudly sourced from the **National Institute of Statistics of Rwanda (NISR)**:

- **Primary:** Seasonal Agricultural Survey (SAS) — Season A 2026, Season B 2025, Annual 2025
- **Supporting:** Agriculture Household Survey (AHS) 2024
- **Contextual:** EICV7, Food Balance Sheets / CFSVA

---

## 🛠️ Architecture & Tech Stack

agrimenya uses a modern, scalable microservices architecture orchestrated via Docker.

```text
┌─────────────────────────┐       ┌────────────────────────┐       ┌─────────────────────┐
│       Frontend          │       │        Backend         │       │      Database       │
│  Streamlit + React      │──────▶│   FastAPI (Python)     │──────▶│     PostgreSQL      │
│  Folium + Plotly        │◀──────│                        │◀──────│     (Supabase)      │
└─────────────────────────┘       └────────────────────────┘       └─────────────────────┘
                                             │
                                             ▼
                                  ┌────────────────────────┐
                                  │    Machine Learning    │
                                  │ scikit-learn + XGBoost │
                                  └────────────────────────┘
```

### The Stack
- **Frontend:** Streamlit, React (custom components), Folium, Plotly, GSAP
- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL (via Supabase)
- **Machine Learning:** scikit-learn, XGBoost
- **Infrastructure:** Docker, Docker Compose

---

## 🚀 Getting Started (Docker Setup)

The easiest way to run the full stack locally is using Docker Compose. This ensures the frontend and backend microservices communicate securely on isolated networks.

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed and running
- Git

### 1. Clone the repository
```bash
git clone https://github.com/iiradukunda-dev/agrimenya.git
cd agrimenya
```

### 2. Run with Docker Compose
```bash
docker-compose up --build
```
*Note: Add the `-d` flag to run in detached mode.*

### 3. Access the Application
- **Frontend UI:** [http://localhost:8501](http://localhost:8501)
- **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🌿 Branching Strategy

If you're contributing, here's how we keep things tidy:

- `main` — Stable branch. Always deployable and used for live demos.
- `develop` — Staging branch where all completed features come together.
- `feature/*` — Individual work branches (e.g., `feature/ai-assistant`).

All changes go through a pull request into `develop`. Check out `docs/BACKEND_GUIDELINES.md` for full contribution rules.

---

## 📝 License

This project was built for the 2026 NISR Big Data Hackathon. All rights reserved.

---

## 🙏 Acknowledgments

A huge thank you to the **National Institute of Statistics of Rwanda (NISR)** for providing the data as part of the 2026 NISR Big Data Hackathon. We couldn't have built this without it!