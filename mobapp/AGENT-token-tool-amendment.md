# AGENT.md — Amendment: User-Friendly Token + Registration Flow

## CONTEXT

The existing `fcm-token-tool/` (index.html + firebase-messaging-sw.js)
works and produces valid tokens, but requires manually copying the
token into Swagger/Postman to call `/locations/register`. This
amendment removes that manual step by merging the tool into the
backend and adding a simple form directly on the page.

This is still a lightweight demo tool, NOT the real mobile app. Do not
add a framework, build step, or styling library.

---

## CHANGES TO MAKE

### 1. Serve the token tool from the FastAPI backend (single origin)

In `main.py`, mount `fcm-token-tool/` as static files, e.g.:

```python
from fastapi.staticfiles import StaticFiles

app.mount("/demo", StaticFiles(directory="../fcm-token-tool", html=True), name="demo")
```

(Adjust the relative path to wherever `fcm-token-tool/` actually sits
relative to `backend/`.) The page will now be reachable at
`http://localhost:8000/demo/` instead of a separate `python -m
http.server` process. Only ONE ngrok tunnel is now needed:
`ngrok http 8000`.

Do not add CORS middleware — same-origin serving makes it unnecessary.
Do not change any existing endpoint behavior.

### 2. Add a simple registration form to `index.html`

Add, in this order, on the same page:

- A text input: **Location Name** (e.g. "Test Phone 1")
- A button: **"Use My Location"** — on click, calls
  `navigator.geolocation.getCurrentPosition()` and fills two
  (otherwise-hidden or read-only) latitude/longitude fields
  automatically. This is the user-friendly part — no manual lat/lon
  typing needed.
- A single button: **"Get Token & Register"** — replaces the old
  "Get Notification Token" button. On click, it should, in order:
  1. Request notification permission and retrieve the FCM token
     (existing logic, unchanged).
  2. If the token is retrieved successfully, immediately `fetch()`
     `POST /locations/register` (relative URL, same origin) with
     `{ location_name, latitude, longitude, device_token }`.
  3. Show a clear success message on the page (e.g. "Registered!
     Location ID: 3") or a clear error message if either step fails.
     Do not silently fail — the whole point is removing guesswork.

Do not remove the raw token display — keep it visible below the form
(still useful for debugging), just make it secondary to the new flow.

### 3. Do not touch

- `/simulate/{event_id}`, `/risk/{location_id}`, `/risk/check-all`,
  `notifications.py`, `risk_model.py`, `weather.py`, `db.py` — none of
  these need any changes for this amendment.
- Do not add authentication, rate limiting, or input validation beyond
  what FastAPI/Pydantic already does by default on the existing
  `/locations/register` model.

---

## ACCEPTANCE CRITERIA

1. `ngrok http 8000` is the only tunnel needed for the full demo flow.
2. Opening the ngrok URL + `/demo/` on a phone shows the form.
3. Tapping "Use My Location" fills in real coordinates.
4. Tapping "Get Token & Register" results in a visible success message
   and a new row in the SQLite locations table — no manual Swagger or
   Postman step required anywhere in this flow.

If anything here conflicts with existing backend behavior, stop and
ask rather than changing endpoint logic to make it fit.
