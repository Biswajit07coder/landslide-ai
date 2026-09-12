import os
from typing import Tuple

_MODEL = None


def _get_asset_path(filename: str) -> str:
    # Look in the backend directory first, then the workspace root
    base = os.path.dirname(__file__)
    p1 = os.path.join(base, filename)
    if os.path.exists(p1):
        return p1
    p2 = os.path.join(base, "..", filename)
    return os.path.abspath(p2)


def load_model():
    global _MODEL
    if _MODEL is not None:
        return _MODEL
    try:
        from joblib import load

        model_path = _get_asset_path("landslide_risk_model.joblib")
        _MODEL = load(model_path)
    except Exception:
        _MODEL = None
    return _MODEL


def score_from_features(rain_1d: float, rain_3d: float, rain_5d: float, rain_7d: float) -> float:
    """Return a risk probability (0-1) using the supplied model.

    If the model cannot be loaded, returns 0.0 and does not raise.
    """
    model = load_model()
    features = [[float(rain_1d), float(rain_3d), float(rain_5d), float(rain_7d)]]
    if model is None:
        return 0.0
    try:
        proba = model.predict_proba(features)[0][1]
        return float(proba)
    except Exception:
        return 0.0


def features_from_daily_list(daily_precip: list) -> Tuple[float, float, float, float]:
    """Given a list of up to 7 daily precipitation values (oldest first),
    compute cumulative 1/3/5/7 day sums where available.
    """
    vals = list(daily_precip)[-7:]
    # pad left if fewer than 7
    if len(vals) < 7:
        vals = [0.0] * (7 - len(vals)) + vals
    # most recent last
    rain_1d = sum(vals[-1:])
    rain_3d = sum(vals[-3:])
    rain_5d = sum(vals[-5:])
    rain_7d = sum(vals[-7:])
    return rain_1d, rain_3d, rain_5d, rain_7d
