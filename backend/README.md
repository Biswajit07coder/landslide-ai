# Landslide Risk Prototype (backend)

Run the FastAPI backend from the `backend/` directory:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Environment:

- `FIREBASE_CREDENTIALS_PATH` (optional): path to Firebase service account JSON. If not set or invalid, push notifications are skipped and logged.

Endpoints:

- `POST /locations/register` — register a device location
- `GET /risk/{location_id}` — compute current risk using Open-Meteo
- `POST /risk/check-all` — check all registered locations and send alerts
- `POST /simulate/{event_id}` — demo endpoint using the provided CSV (sends to a demo device token)
