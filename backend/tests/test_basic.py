import requests
import os

API = os.environ.get("LANDSLIDE_API_URL", "http://127.0.0.1:8000")


def test_register_and_risk():
    # register a temporary location
    payload = {"location_name": "test-py", "latitude": 30.0, "longitude": 79.0, "device_token": "tkn"}
    r = requests.post(f"{API}/locations/register", json=payload, timeout=10)
    assert r.status_code == 200
    loc = r.json()
    assert "id" in loc

    # get risk for the created id
    rid = loc["id"]
    r2 = requests.get(f"{API}/risk/{rid}", timeout=10)
    assert r2.status_code == 200
    body = r2.json()
    assert "risk_score" in body


def test_check_all_endpoint():
    r = requests.post(f"{API}/risk/check-all", timeout=10)
    assert r.status_code == 200
    arr = r.json()
    assert isinstance(arr, list)
