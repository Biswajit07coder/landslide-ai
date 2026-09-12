import datetime
import os
import sys
import importlib

# Import main module robustly whether tests are run from repo root or backend/ directory
try:
    import main as mainmod
except Exception:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
    mainmod = importlib.import_module('main')


def test_features_from_daily_list_short():
    vals = [1.0, 2.0]
    # import risk_model module relative to main
    rm = importlib.import_module('risk_model')
    r1, r3, r5, r7 = rm.features_from_daily_list(vals)
    assert r1 == 2.0
    assert r3 == 3.0
    assert r5 == 3.0
    assert r7 == 3.0


def test_compute_risk_handles_weather_failure(monkeypatch):
    # make weather.fetch raise
    weather = importlib.import_module('weather')
    monkeypatch.setattr(weather, 'fetch_last_7_days_precipitation', lambda *a, **k: (_ for _ in ()).throw(Exception('fail')))
    res = mainmod.compute_risk_for_coords(0.0, 0.0)
    assert res['risk_score'] == 0.0
    assert res['risk_level'] == 'LOW'


def test_compute_risk_uses_score(monkeypatch):
    # Ensure compute_risk uses risk_model.score_from_features
    rm = importlib.import_module('risk_model')
    weather = importlib.import_module('weather')
    monkeypatch.setattr(rm, 'score_from_features', lambda a, b, c, d: 0.8)
    monkeypatch.setattr(weather, 'fetch_last_7_days_precipitation', lambda *a, **k: {
        'rain_1d': 10.0, 'rain_3d': 20.0, 'rain_5d': 30.0, 'rain_7d': 40.0
    })
    res = mainmod.compute_risk_for_coords(0.0, 0.0)
    assert res['risk_score'] == 0.8
    assert res['risk_level'] == 'CRITICAL'
