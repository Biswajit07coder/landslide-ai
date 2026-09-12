"""Small demo script to call POST /risk/check-all and print the summary.

Usage:
  python demo_check_all.py
"""
import requests
import os

URL = os.environ.get("LANDSLIDE_API_URL", "http://127.0.0.1:8000")


def main():
    resp = requests.post(f"{URL}/risk/check-all", timeout=30)
    resp.raise_for_status()
    data = resp.json()
    print("Check-all results:")
    for r in data:
        print(f" - location_id={r.get('location_id')} level={r.get('risk_level')} alert_sent={r.get('alert_sent')}")


if __name__ == "__main__":
    main()
