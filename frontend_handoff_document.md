# Agri-Menya Frontend Handoff Document

## 1. Product overview

Agri-Menya is an agricultural decision-support platform for Rwanda. It helps planners, extension officers, cooperative leaders, and field teams understand crop productivity, risk, intervention needs, and recommended actions across districts and zones.

The product combines:
- yield prediction
- district and zone segmentation
- agricultural benchmarking
- alignment and readiness analysis
- AI-guided recommendations
- crop disease detection
- planning and communication
- live field/weather context

The frontend should behave like a decision-support dashboard, not a generic admin dashboard. The user experience should make it easy to understand what is happening, why it matters, and what action should be taken next.

---

## 2. Product goals

The system supports the following core goals:
- identify high-priority zones
- predict expected yield for a crop and season
- highlight risk factors and crop stress
- recommend interventions and resource planning
- guide extension workers with clear actions
- support communication to farmers and stakeholders
- integrate AI assistance grounded in real agronomic data

---

## 3. Core user groups

### 3.1 Planners
Need: district overview, crop planning, intervention prioritization.

### 3.2 Extension officers
Need: zone-level diagnosis, disease detection, recommendation generation, action planning.

### 3.3 Cooperative leaders
Need: field-level overview, communication, priority ranking, plan sharing.

### 3.4 Admins
Need: zone management, alert management, system health, configuration access.

---

## 4. Main product flows

### Flow 1: Zone overview and prediction
User selects a district or zone, then views:
- current zone metadata
- predicted yield
- priority classification
- yield gap and benchmark comparison
- recommended actions

### Flow 2: Segmentation and district analysis
User filters by district, season, and crop to view:
- agri metrics
- crop comparison rankings
- map-based zone data
- where intervention might be needed most

### Flow 3: Alignment and readiness review
User checks whether a zone is:
- ready for credit/insurance
- nutritionally at risk
- exposed to climate risk
- export-readiness eligible

### Flow 4: AI assistance
User asks a question about a zone, such as:
- What is the current status of this zone?
- Why is this crop underperforming?
- What intervention is recommended?

The AI response should be grounded in the zone’s prediction, risk, and alert data.

### Flow 5: Disease detection
User provides crop, symptom description, and optionally an image, to receive:
- probable disease
- confidence score
- risk level
- recommended treatment actions

### Flow 6: Planning and communication
User creates a plan based on recommendation data, then:
- see estimated resource needs
- save a roadmap
- share or communicate the plan to stakeholders

---

## 5. Core backend modules and frontend relevance

### 5.1 Decision module
Purpose: yield prediction and recommendation engine.

API group:
- /decision

Key endpoints:
- POST /decision/predict
- GET /decision/crops
- GET /decision/district-ranking
- GET /decision/priority-ranking
- GET /decision/recommendations/{zone_id}
- POST /decision/disease-risk

Frontend usage:
- zone forecast card
- district ranking table
- priority list
- recommendation panel

### 5.2 Segmentation module
Purpose: zone and district context, map data, agri metrics.

API group:
- /segmentation

Key endpoints:
- GET /segmentation/zones
- POST /segmentation/zones
- GET /segmentation/map-data
- GET /segmentation/zones/{zone_id}
- GET /segmentation/agri-metrics
- GET /segmentation/crop-comparison/{district}

Frontend usage:
- map page
- district filters
- crop comparison chart
- agricultural table

### 5.3 Alignment module
Purpose: macro-level national alignment and risk review.

API group:
- /alignment

Key endpoints:
- POST /alignment/compute/{zone_id}
- GET /alignment/finance-readiness/{zone_id}
- GET /alignment/nutrition-risk/{zone_id}
- GET /alignment/export-flags
- GET /alignment/dashboard

Frontend usage:
- readiness cards
- score overview dashboard
- nutrition/climate risk widgets
- export-readiness summary

### 5.4 Chat and AI module
Purpose: grounded assistant and disease detection.

API group:
- /chat

Key endpoints:
- POST /chat
- POST /chat/disease-detect
- POST /chat/disease-detect-upload

Frontend usage:
- AI advisor panel
- question-answer interface
- disease detection form
- image upload support

### 5.5 Planning module
Purpose: resource and intervention planning.

API group:
- /planification

Key endpoints:
- GET /planification/resources/{zone_id}
- POST /planification/roadmap
- GET /planification/plans/{zone_id}
- POST /planification/disease-plan

Frontend usage:
- plan creation form
- roadmap timeline widget
- saved plan list

### 5.6 Communication module
Purpose: notifications and communication actions.

API group:
- /communication

Key endpoints:
- POST /communication/notify
- POST /communication/alerts
- GET /communication/alerts
- GET /communication/share/{plan_id}

Frontend usage:
- alert list
- message center
- share summary

### 5.7 Live data module
Purpose: weather, reports, contextual data freshness.

API group:
- /live

Key endpoints:
- GET /live/weather/{district}
- POST /live/field-report
- GET /live/field-reports/{zone_id}
- POST /live/context

Frontend usage:
- live weather widget
- recent field updates
- context summary near decision cards

### 5.8 Farmer community and satellite map context

The farmer community provides individually authenticated text posts and
comments, content reports, and administrator moderation. The pilot does not
verify email addresses or farmer roles and has no account recovery yet; do not
present community posts as official advice.

API group:
- /community

Key endpoints:
- POST /community/register and /community/login
- GET/POST /community/posts
- GET/POST /community/posts/{post_id}/comments
- POST /community/posts/{post_id}/report
- Admin-only community moderation endpoints

The zone priority map includes an optional Rwanda Space Agency orthomosaic
layer. It is visual context only, covers a limited mapped area near Kigali, and
does not feed yield predictions or priority levels.

---

## 6. Recommended frontend pages and wireframe outline

## Page 1: Dashboard
Purpose: high-level operational overview.

Sections:
1. Top navigation bar
   - Dashboard
   - Zones
   - Segmentation
   - AI Assistant
   - Planning
   - Communication
   - Admin

2. KPI summary cards
   - total zones
   - high priority zones
   - average credit readiness score
   - zones export-ready
   - total estimated jobs supported

3. Map panel
   - district or zone markers
   - color-coded status by risk level

4. Alerts panel
   - recent system warnings
   - critical alerts

5. Performance chart panel
   - yield by district or crop
   - priority breakdown

6. Quick actions panel
   - predict zone
   - new plan
   - disease check
   - contact stakeholders

### Suggested layout
- header at top
- left or top nav
- main content grid with 2-3 columns on large screens

---

## Page 2: Zones list and detail
Purpose: explore all zones and inspect a single zone.

### Zones list page
Sections:
- district filter
- crop filter
- season filter
- search bar
- zone table with columns:
  - zone name
  - district
  - sector
  - cell
  - priority
  - predicted yield
  - risk status

### Zone detail page
Sections:
- zone metadata header
- yield prediction card
- priority status card
- climate/nutrition risk card
- credit readiness card
- recommendation panel
- plan history section
- recent alerts section

---

## Page 3: Segmentation page
Purpose: district-level analytics and comparison.

Sections:
- district selector
- crop selector
- season selector
- map or chart view
- agri metrics table
- crop comparison ranking list

Focus:
- what crop should this zone grow?
- what is performing best in this district?
- what is underperforming?

---

## Page 4: AI assistant page
Purpose: question-answer and diagnosis.

Sections:
- chat input box
- zone selector
- conversation area
- grounded answer cards
- source summary and context chips

Additional section:
- disease detection panel
  - crop selector
  - symptoms textarea
  - image upload
  - submit button
  - result card with disease, confidence, risk, actions

---

## Page 5: Planning page
Purpose: turn recommendations into actions.

Sections:
- select zone
- select season
- choose intervention type
- resource estimate summary
- roadmap builder
- list of saved plans

Plan item structure:
- title
- zone
- objective
- steps
- resource summary
- creation date

---

## Page 6: Communication page
Purpose: alerts and plan sharing.

Sections:
- alert feed
- notification form
- channel selector
- recipient list
- message preview
- plan share view

---

## Page 7: Admin page
Purpose: operations and governance.

Sections:
- zone management list
- plan management list
- alert management
- system health indicator
- environment and secret status (non-sensitive summary only)

---

## 7. Recommended UI behavior patterns

### Data presentation patterns
- Use cards for high-level metrics
- Use badges for priority levels
- Use color-coded risk indicators
- Use simple tables for raw data
- Use charts for district and crop ranking
- Use map markers for geospatial status

### Interaction patterns
- Filters should cascade from district to zone to crop to season
- Auto-refresh data when filters change
- Show empty states clearly
- Show AI output with context trace or source summary
- Require confirmation before sending alerts or creating plans

---

## 8. Exact API calls per screen

### Dashboard screen
- GET /segmentation/map-data
- GET /alignment/dashboard
- GET /decision/priority-ranking
- GET /communication/alerts

### Zones list screen
- GET /segmentation/zones
- GET /segmentation/agri-metrics

### Zone detail screen
- GET /segmentation/zones/{zone_id}
- GET /decision/recommendations/{zone_id}
- GET /alignment/finance-readiness/{zone_id}
- GET /alignment/nutrition-risk/{zone_id}
- GET /planification/plans/{zone_id}

### Segmentation screen
- GET /segmentation/agri-metrics
- GET /segmentation/crop-comparison/{district}
- GET /segmentation/map-data?district=...

### AI assistant screen
- POST /chat
- POST /chat/disease-detect
- POST /chat/disease-detect-upload

### Planning screen
- GET /planification/resources/{zone_id}
- POST /planification/roadmap
- GET /planification/plans/{zone_id}
- POST /planification/disease-plan

### Communication screen
- GET /communication/alerts
- POST /communication/notify
- GET /communication/share/{plan_id}

### Admin screen
- GET /admin/zones
- GET /admin/plans
- GET /admin/alerts

---

## 9. Suggested product tone and experience

The frontend should be:
- professional
- practical
- agricultural and evidence-based
- clear for non-technical users
- decision-oriented rather than data-heavy for its own sake

Important UX principle:
The system should help the user answer three questions quickly:
1. What is happening?
2. Why is it happening?
3. What should we do next?

That is the core product experience.

---

## 10. Final recommendation

The frontend should be built as a dashboard-driven decision platform with:
- map-first overview
- zone-level intelligence
- AI assistance panel
- action-oriented planning modules
- live alerts and communication controls

This aligns well with the backend’s architecture and gives the product a strong operational identity for Rwanda-focused agricultural planning and extension work.

---

## 11. Short conclusion

Agri-Menya is best viewed as an agricultural intelligence and action platform. It is not only a data viewer; it turns agronomic and operational information into recommendations, decisions, and action plans. The frontend should be designed around decision clarity, risk visibility, and actionable outcomes.
