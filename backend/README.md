# Landslide Risk Prototype (backend)

Run the FastAPI backend from the `backend/` directory:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

Environment:

- `FIREBASE_CREDENTIALS_PATH` (optional): path to Firebase service account JSON. If not set or invalid, push notifications are skipped and logged.

Firebase test:

- Place your service account JSON in a safe location (example: `.env/credentials/service.json`).
- Set the environment variable and start the server, for example:

```bash
cd backend
export FIREBASE_CREDENTIALS_PATH=../.env/credentials/landslide-ai-50735-firebase-adminsdk-fbsvc-e32690f3be.json
uvicorn main:app --reload
```

- To trigger a demo notification (using a real device token), call:

```bash
curl -X POST http://127.0.0.1:8000/simulate/4924 -H "Content-Type: application/json" -d '{"device_token":"<YOUR_DEVICE_TOKEN>"}'
```

Note: Do NOT commit the service account JSON to version control; `.gitignore` includes `.env/` by default.

Endpoints:

- `POST /locations/register` — register a device location
- `GET /risk/{location_id}` — compute current risk using Open-Meteo
- `POST /risk/check-all` — check all registered locations and send alerts
- `POST /simulate/{event_id}` — demo endpoint using the provided CSV (sends to a demo device token)
