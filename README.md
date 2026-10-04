<div align="center">
  <img src="frontend/assets/logo.jpg" alt="agrimenya logo" width="120" style="border-radius: 20px;"/>
  <h1>agrimenya</h1>
  <p><b>A Data-Driven Decision and Planning Support System for Agricultural Productivity in Rwanda</b></p>
  <p><i>Proudly built for the <b>2026 NISR Big Data Hackathon</b></i></p>
</div>

---

## Overview

**agrimenya** is an intelligent platform designed to help **planners, agricultural extension officers, and cooperative leaders** make faster, better-informed decisions to improve agricultural productivity across Rwanda.

By aggregating dense official survey data from the National Institute of Statistics of Rwanda (NISR) and augmenting it with machine learning, agrimenya transforms raw statistics into clear priorities, actionable roadmaps, and real-time alerts.

Instead of leaving planners to manually cross-reference complex spreadsheets and reports, agrimenya automatically surfaces **where to focus, what to do, and how urgent the action is**.

---

## The Problem We Are Solving

Agricultural planning in Rwanda relies on rich, high-quality survey data (SAS, AHS, EICV, and CFSVA). While this data is powerful, it is often underutilized in day-to-day decision-making simply because it is difficult to digest quickly.

Turning those datasets into concrete, local action takes significant manual analysis—time that extension officers and busy planners lack. We built agrimenya to bridge this exact gap, ensuring that data directly drives operational action.

---

## Core Pillars

agrimenya is organized around four core capabilities that communicate seamlessly with each other:

| Pillar | Capability | Description |
|:---|:---|:---|
| **Decide** | Decision Engine | Generates precise, automated, and proactive recommendations for specific agricultural zones based on predictive models. |
| **Plan** | Roadmapping | Facilitates the creation of clear planning roadmaps and step-by-step action plans to coordinate stakeholder activities. |
| **Segment** | Geographic Analysis | Visually zones and prioritizes areas (Low / Medium / High) based on climate, yield, and productivity metrics. |
| **Communicate** | Alert System | Maintains operational alignment by sharing real-time alerts and plans across planners, officers, and cooperatives. |

---

## Key Features

- **Priority Ranking:** Automatic classification of agricultural areas to highlight urgent intervention needs.
- **AI-Powered Insights:** A conversational AI assistant designed to offer contextual recommendations and answer data-driven agronomic questions.
- **Yield & Impact Predictions:** Reliable forecasts powered by XGBoost ML models and optimized caching via FastAPI lifespan events.
- **Resource Estimation:** Forecasting capability for agricultural inputs such as seeds and fertilizer.
- **Interactive Zoning:** Interactive geographic maps (powered by Folium and CartoDB) that zone areas based on environmental and productivity data.
- **Unified Alerting:** Real-time notifications and cross-team communication modules.
- **Seamless Internationalization (i18n):** Native multi-language support (English, Kinyarwanda, French) powered by a robust GNU `gettext` architecture, dynamically managed via Streamlit session state.
- **Liquid Glass Design System:** A premium, immersive user interface featuring refractive translucency and a nature-forward color palette for a frictionless user experience.

---

## Target Audience

- **Planners:** Government and district-level officials handling national and regional agricultural strategy.
- **Extension Officers:** Frontline agronomists executing on-the-ground implementation, training, and monitoring.
- **Cooperative Leaders:** Local community champions coordinating resources and translating decisions to farmers.

---

## Data Sources

Our core analytical data is strictly sourced from the **National Institute of Statistics of Rwanda (NISR)**:

- **Primary:** Seasonal Agricultural Survey (SAS) — Season A 2026, Season B 2025, Annual 2025
- **Supporting:** Agriculture Household Survey (AHS) 2024
- **Contextual:** Integrated Household Living Conditions Survey (EICV7), Food Balance Sheets / Comprehensive Food Security and Vulnerability Analysis (CFSVA)

---

## Architecture & Technology Stack

agrimenya employs a modern, scalable microservices architecture orchestrated via Docker.

```text
┌─────────────────────────┐       ┌────────────────────────┐       ┌─────────────────────┐
│       Frontend          │       │        Backend         │       │      Database       │
│  Streamlit + React      │──────▶│   FastAPI (Python)     │──────▶│     PostgreSQL      │
│  Folium + Plotly        │◀──────│                        │◀──────│     (Supabase)      │
└─────────────────────────┘       └────────────────────────┘       └─────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────┐       ┌────────────────────────┐
│ GNU gettext (i18n)      │       │    Machine Learning    │
│ English / Kinyarwanda   │       │ scikit-learn + XGBoost │
└─────────────────────────┘       └────────────────────────┘
```