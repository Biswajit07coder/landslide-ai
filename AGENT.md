# AGENT.md — ByteForge Landslide Early Warning Prototype (SIH 2025)

## READ THIS FIRST

You are building a **narrow, working prototype backend** — not the full
product described in the pitch deck. This document is the complete and
final scope. If something is not explicitly listed under "BUILD THIS",
do not build it, scaffold it, or suggest adding it — even if it seems
like an obvious next step or seems required for completeness.

If you believe something outside this scope is genuinely required for
what IS listed to work, STOP and ask before writing code for it. Do not
silently expand scope.

---

## PROJECT CONTEXT

Team: ByteForge, Smart India Hackathon 2025.
Problem statement: AI-Based Early Warning & Natural Disaster Risk
Monitoring System.

For the selection-round prototype, the team scoped down to ONE hazard,
ONE region, ONE working end-to-end flow:

> After sustained rainfall over 5–7 days in a specific Uttarakhand
> location, a model-based risk score crosses a threshold and a push
> notification alert fires to users registered at that location.

A model has already been trained and is provided as an artifact
(`landslide_risk_model.joblib`, XGBoost, trained on rainfall features).
You are NOT training a model. You are building the backend service that
serves it.

---

## PROVIDED ARTIFACTS (already exist, do not regenerate)

- `landslide_risk_model.joblib` — trained XGBoost classifier
  - Input: 4 numeric features, in this exact order:
    `[rain_1d, rain_3d, rain_5d, rain_7d]` (all in mm, floats)
  - Usage: `model.predict_proba([[rain_1d, rain_3d, rain_5d, rain_7d]])[0][1]`
    returns landslide probability (float 0–1)
  - Load with: `joblib.load("landslide_risk_model.joblib")`
- `uttarakhand_landslide_events.csv` — historical event data, used ONLY
  for the "simulate mode" demo data source (see below). Columns include
  `event_id, event_date, latitude, longitude, landslide_trigger,
  landslide_size, fatality_count, location_description`.

---

## BUILD THIS (in-scope, exactly this and nothing more)

### 1. FastAPI backend service

A single FastAPI app with these endpoints ONLY:

- `POST /locations/register`
  - Body: `{ "location_name": str, "latitude": float, "longitude": float, "device_token": str }`
  - Stores the registration (see storage below).
  - Returns the stored record with an assigned id.

- `GET /risk/{location_id}`
  - Pulls current rainfall for that location's coordinates from the
    Open-Meteo free API (see "Live rainfall lookup" below), computes
    1/3/5/7-day cumulative rainfall, runs it through the model, and
    returns:
    `{ "location_id": ..., "risk_score": float, "risk_level": "LOW"|"MEDIUM"|"HIGH"|"CRITICAL", "rain_1d": ..., "rain_3d": ..., "rain_5d": ..., "rain_7d": ... }`
  - Risk level thresholds (use exactly these, do not invent your own):
    - `risk_score < 0.25` → LOW
    - `0.25 <= risk_score < 0.5` → MEDIUM
    - `0.5 <= risk_score < 0.75` → HIGH
    - `risk_score >= 0.75` → CRITICAL

- `POST /risk/check-all`
  - Runs `/risk/{location_id}` logic for every registered location.
  - For any location whose risk_level is HIGH or CRITICAL, send a push
    notification (see "Alert delivery" below).
  - Returns a summary list of `{ location_id, risk_level, alert_sent: bool }`.
  - This endpoint is meant to be called on a schedule (see "Scheduling"
    below) — do not build a separate scheduler service, just make this
    endpoint callable repeatedly.

- `POST /simulate/{event_id}`
  - Looks up the event by `event_id` in `uttarakhand_landslide_events.csv`.
  - Instead of calling the live Open-Meteo API, feeds that historical
    event's date/location through the SAME risk-scoring function used
    by `/risk/{location_id}` (do not duplicate the scoring logic — one
    function, two data sources).
  - Sends a push notification to a single demo device token (passed in
    the request body as `{ "device_token": str }`) if risk_level is
    HIGH or CRITICAL.
  - Purpose: lets the team trigger a convincing live demo without
    waiting for real rain. Must be clearly named/commented as a demo
    endpoint, not part of the "real" pipeline.

### 2. Live rainfall lookup

- Use Open-Meteo's free archive/forecast API (no API key required):
  `https://archive-api.open-meteo.com/v1/archive` for historical dates,
  `https://api.open-meteo.com/v1/forecast` (with `past_days` param) for
  current/recent rainfall.
- Fetch daily `precipitation_sum` for the last 7 days for the given
  lat/lon, then compute the 1/3/5/7-day cumulative sums yourself in
  Python. Do not use any other weather data source.

### 3. Storage

- Use a single local **SQLite** database file (e.g. `app.db`) via
  `sqlite3` or SQLAlchemy — whichever is simpler for you to implement
  correctly. One table: registered locations (id, location_name,
  latitude, longitude, device_token).
- Do NOT set up PostgreSQL, PostGIS, or Redis. Those are future-roadmap
  infrastructure, not needed for this prototype and out of scope here.

### 4. Alert delivery

- Use Firebase Cloud Messaging (FCM) to send a push notification
  containing the location name and risk level.
- Assume Firebase Admin SDK credentials will be provided as a JSON file
  path via an environment variable `FIREBASE_CREDENTIALS_PATH` — read
  it from there, do not hardcode any keys.
- If sending fails (e.g. no credentials configured yet), log the error
  and continue — do not crash the endpoint. This is a hackathon demo;
  a missing FCM config should degrade gracefully, not break the API.

### 5. Scheduling

- Do NOT build a background scheduler, cron job, or task queue.
- `/risk/check-all` is designed to be triggered manually (e.g. via
  Postman, curl, or a simple `while True: sleep` loop in a separate
  throwaway script) during development and demo. That triggering
  mechanism is NOT your responsibility — just make the endpoint work
  correctly when called.

### 6. Project structure

Keep it flat and simple:

```
backend/
  main.py              # FastAPI app + all endpoints
  risk_model.py         # loads model, computes features, scores risk
  weather.py             # Open-Meteo API calls
  notifications.py       # FCM sending logic
  db.py                  # SQLite setup + simple CRUD
  landslide_risk_model.joblib
  uttarakhand_landslide_events.csv
  requirements.txt
  README.md              # how to run it locally
```

### 7. requirements.txt

Pin only what's actually used: `fastapi`, `uvicorn`, `joblib`,
`requests`, `firebase-admin`. Do not add packages "for later."

---

## DO NOT BUILD (explicitly out of scope)

Do not create, scaffold, or start any of the following, even as
placeholders or stubs:

- Any mobile app (React Native or otherwise) — the team is not asking
  a coding agent to build the frontend in this task
- Any web dashboard, admin panel, or authority monitoring UI
- PostgreSQL, PostGIS, or Redis — SQLite only, as specified above
- Multi-hazard support (floods, cyclones, earthquakes) — landslide only
- Satellite imagery ingestion, CNN models, or any image processing
- LSTM or any time-series deep learning model — the trained XGBoost
  model provided is final for this prototype
- User authentication / login system
- Any deployment configuration (Docker, cloud hosting, CI/CD) unless
  explicitly requested later
- Any data outside Uttarakhand
- Retraining, tuning, or modifying `landslide_risk_model.joblib`
- Any additional API endpoints beyond the four listed above

If asked to "make it more complete" or "production-ready" by anyone
other than a direct, explicit new instruction, treat that as out of
scope and flag it instead of building it.

---

## ACCEPTANCE CRITERIA (how the team will check this is done)

1. `uvicorn main:app --reload` starts the server with no errors.
2. `POST /locations/register` successfully stores a test location.
3. `GET /risk/{location_id}` returns a real risk score and level for
   that location using live Open-Meteo data.
4. `POST /simulate/{event_id}` returns a HIGH or CRITICAL risk level
   for at least one known historical event from the CSV (sanity check
   that the pipeline correctly flags real past landslide conditions).
5. When Firebase credentials are configured, a real push notification
   arrives on a test device during `/simulate/{event_id}`.
6. No files, folders, or dependencies exist beyond what's listed in
   "Project structure" and "requirements.txt" above.

---

## IF ANYTHING IS UNCLEAR

Stop and ask the team rather than guessing or defaulting to "the
more thorough option." Scope discipline is the priority for this
prototype — a smaller working system beats a larger half-built one.
