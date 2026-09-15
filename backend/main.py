from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict
import logging
import datetime

import db
import weather
import risk_model
import notifications
import csv
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')

app = FastAPI(title="Landslide Risk Prototype")

# Allow CORS during development so the demo page can be served from a
# separate static server or ngrok and still call the backend endpoints.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the lightweight FCM token tool as static files at /demo
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobapp", "fcm-token-tool"))
if os.path.isdir(static_dir):
    app.mount("/demo", StaticFiles(directory=static_dir, html=True), name="demo")


@app.get("/demo/config")
def demo_config(request: Request):
    """Return the public Firebase config and VAPID key for the demo tool.

    This reads the `mobapp/fcm-token-tool/.env` file (if present) and exposes
    only the public Firebase config and VAPID key. The `backendUrl` is
    derived from the incoming request so the demo can POST back to the same
    backend (useful when the backend is exposed via ngrok).
    """
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mobapp", "fcm-token-tool", ".env"))
    env = {}
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
                        v = v[1:-1]
                    env[k] = v
        except Exception:
            pass

    firebaseConfig = None
    vapidKey = None
    if env:
        firebaseConfig = {
            "apiKey": env.get("FIREBASE_API_KEY"),
            "authDomain": env.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": env.get("FIREBASE_PROJECT_ID"),
            "messagingSenderId": env.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": env.get("FIREBASE_APP_ID"),
        }
        vapidKey = env.get("FIREBASE_VAPID_KEY")

    backend_url = os.environ.get("BACKEND_URL") or str(request.base_url).rstrip("/")

    return {"firebaseConfig": firebaseConfig, "vapidKey": vapidKey, "backendUrl": backend_url}


class LocationIn(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    device_token: str


class DeviceTokenIn(BaseModel):
    device_token: str


def _risk_level_from_score(score: float) -> str:
    if score < 0.25:
        return "LOW"
    if score < 0.5:
        return "MEDIUM"
    if score < 0.75:
        return "HIGH"
    return "CRITICAL"


@app.post("/locations/register")
def register_location(loc: LocationIn):
    rec = db.add_location(loc.location_name, loc.latitude, loc.longitude, loc.device_token)
    return rec


@app.get("/risk/{location_id}")
def get_risk(location_id: int):
    loc = db.get_location(location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="location not found")
    try:
        result = compute_risk_for_coords(loc["latitude"], loc["longitude"])
        result.update({"location_id": location_id})
        return result
    except Exception:
        logging.exception("Error computing risk for location %s", location_id)
        raise HTTPException(status_code=500, detail="error computing risk")


@app.post("/risk/check-all")
def check_all():
    results = []
    locs = db.list_locations()
    for l in locs:
        try:
            res = compute_risk_for_coords(l["latitude"], l["longitude"])
            level = res.get("risk_level")
            alert_sent = False
            if level in ("HIGH", "CRITICAL"):
                title = f"Landslide risk: {level}"
                body = f"{l['location_name']} risk level {level} (score={res.get('risk_score'):.2f})"
                alert_sent = notifications.send_push(l["device_token"], title, body)
            results.append({"location_id": l["id"], "risk_level": level, "alert_sent": alert_sent})
        except Exception:
            logging.exception("Error checking location %s", l.get("id"))
            results.append({"location_id": l.get("id"), "risk_level": "ERROR", "alert_sent": False})
    return results


@app.post("/simulate/{event_id}")
def simulate_event(event_id: str, token: DeviceTokenIn):
    # Demo endpoint: uses historical CSV data instead of live weather
    csv_path = os.path.join(os.path.dirname(__file__), "..", "uttarakhand_landslide_events.csv")
    csv_path = os.path.abspath(csv_path)
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=500, detail="events CSV not found")
    found = None
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if str(row.get("event_id")) == str(event_id):
                found = row
                break
    if not found:
        raise HTTPException(status_code=404, detail="event not found")
    # CSV uses formats like '06/29/2011 12:00:00 AM' — try parsing common formats
    date_str = found.get("event_date")
    event_date = None
    for fmt in ("%m/%d/%Y %I:%M:%S %p", "%Y-%m-%d"):
        try:
            event_date = datetime.datetime.strptime(date_str, fmt).date()
            break
        except Exception:
            continue
    if event_date is None:
        raise HTTPException(status_code=500, detail="invalid event date format in CSV")

    lat = float(found.get("latitude"))
    lon = float(found.get("longitude"))
    res = compute_risk_for_coords(lat, lon, target_date=event_date)
    level = res.get("risk_level")
    alert_sent = False
    if level in ("HIGH", "CRITICAL"):
        title = f"[DEMO] Landslide risk: {level}"
        body = f"Demo event {event_id} at {found.get('location_description','unknown')} -> {level} (score={res.get('risk_score'):.2f})"
        alert_sent = notifications.send_push(token.device_token, title, body)
    return {"event_id": event_id, "risk_score": res.get("risk_score"), "risk_level": level, "alert_sent": alert_sent}


def compute_risk_for_coords(latitude: float, longitude: float, target_date: Optional[datetime.date] = None) -> Dict:
    """Centralized risk computation used by endpoints. Returns dict with rain sums, score and level."""
    try:
        data = weather.fetch_last_7_days_precipitation(latitude, longitude, target_date=target_date)
        rain_1d = data.get("rain_1d", 0.0)
        rain_3d = data.get("rain_3d", 0.0)
        rain_5d = data.get("rain_5d", 0.0)
        rain_7d = data.get("rain_7d", 0.0)
        score = risk_model.score_from_features(rain_1d, rain_3d, rain_5d, rain_7d)
        level = _risk_level_from_score(score)
        return {
            "risk_score": score,
            "risk_level": level,
            "rain_1d": rain_1d,
            "rain_3d": rain_3d,
            "rain_5d": rain_5d,
            "rain_7d": rain_7d,
        }
    except Exception:
        logging.exception("Failed to compute risk for coords %s,%s", latitude, longitude)
        # return a safe default rather than raising so callers can choose how to react
        return {"risk_score": 0.0, "risk_level": "LOW", "rain_1d": 0.0, "rain_3d": 0.0, "rain_5d": 0.0, "rain_7d": 0.0}
