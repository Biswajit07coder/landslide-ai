import requests
import datetime
from typing import List, Dict, Optional
import os


def _fetch_open_meteo(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()
    return resp.json()


def fetch_last_7_days_precipitation(latitude: float, longitude: float, target_date: Optional[datetime.date] = None) -> Dict:
    """Fetch daily precipitation for the 7 days ending on target_date (inclusive).

    If target_date is None, use the recent forecast API to get the last 7 days.
    """
    if target_date:
        end_date = target_date
        start_date = end_date - datetime.timedelta(days=6)
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "daily": "precipitation_sum",
            "timezone": "UTC",
        }
    else:
        # use forecast with past_days=6 to retrieve recent 7 days
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "precipitation_sum",
            "past_days": 6,
            "timezone": "UTC",
        }

    data = _fetch_open_meteo(url, params)
    daily = data.get("daily", {})
    precip = daily.get("precipitation_sum") or []

    # Ensure we have up to 7 values, oldest first
    precip = [float(x) for x in precip]
    if len(precip) > 7:
        precip = precip[-7:]

    # compute cumulative sums
    def safe_sum(last_n):
        return float(sum(precip[-last_n:])) if precip else 0.0

    rain_1d = safe_sum(1)
    rain_3d = safe_sum(3)
    rain_5d = safe_sum(5)
    rain_7d = safe_sum(7)

    return {
        "daily_precip": precip,
        "rain_1d": rain_1d,
        "rain_3d": rain_3d,
        "rain_5d": rain_5d,
        "rain_7d": rain_7d,
    }
