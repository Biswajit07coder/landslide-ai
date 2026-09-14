# AGENT.md — FCM Token Grabber (throwaway tool, NOT the product frontend)

## READ THIS FIRST

This is a temporary, disposable utility used ONCE to obtain a real FCM
device token for testing the ByteForge backend's push notifications.
It is NOT the mobile app, NOT a UI for the product, and should never be
expanded into one. Keep this as small and ugly as possible — it exists
to be deleted later.

Location: create a NEW top-level folder `fcm-token-tool/` in the repo,
sitting next to `backend/`, not inside it. Do not touch anything in
`backend/`.

---

## BUILD THIS (exactly this, nothing more)

Two files only:

```
fcm-token-tool/
  index.html
  firebase-messaging-sw.js
```

### `index.html`

- Loads the Firebase JS SDK (v9+ compat or modular, your choice) via
  CDN script tags — no npm, no build step, no framework.
- On page load, shows a single button: "Get Notification Token".
- On click:
  1. Requests browser notification permission
     (`Notification.requestPermission()`).
  2. If granted, initializes Firebase with the config object (see
     "Config placeholders" below) and calls `getToken()` from Firebase
     Messaging, passing the VAPID key.
  3. Displays the returned token as plain selectable text on the page
     (e.g. inside a `<textarea readonly>` so it's easy to copy) —
     do NOT just console.log it.
  4. If permission is denied or token retrieval fails, show the error
     message plainly on the page.
- No styling beyond basic readability. No routing, no other pages, no
  additional buttons or features.

### `firebase-messaging-sw.js`

- Standard Firebase Cloud Messaging service worker file — initializes
  Firebase in the service worker scope and sets up background message
  handling per Firebase's documented pattern for this exact file name.
- This file MUST be served from the root of the site (same level as
  `index.html`), or the browser will not register it for scope reasons.

### Config placeholders

Do NOT invent or guess any Firebase config values. Use clearly marked
placeholders that I will fill in myself:

```js
const firebaseConfig = {
  apiKey: "PLACEHOLDER_API_KEY",
  authDomain: "PLACEHOLDER.firebaseapp.com",
  projectId: "PLACEHOLDER_PROJECT_ID",
  messagingSenderId: "PLACEHOLDER_SENDER_ID",
  appId: "PLACEHOLDER_APP_ID",
};
const vapidKey = "PLACEHOLDER_VAPID_KEY";
```

These come from the Firebase Console (Web app config + Cloud Messaging
web push certificate), not from you. Leave them as placeholders and
tell me exactly which line to edit.

---

## DO NOT BUILD

- No backend/server component for this tool — it's static HTML served
  by ngrok directly off the local filesystem (e.g. via
  `python -m http.server` or `npx serve`), nothing more.
- No framework (React, Vue, etc.), no CSS library, no build tooling.
- No integration with the ByteForge backend's `/locations/register` or
  any other endpoint — this tool only produces a token; registering it
  is a separate manual step done by the team afterward.
- No additional pages, styling polish, or "nice to have" features.
- Do not add this folder's dependencies to `backend/requirements.txt`
  or touch `backend/` in any way.

---

## ACCEPTANCE CRITERIA

1. Serving `fcm-token-tool/` with a static file server and opening it
   over HTTPS (via ngrok) shows one button.
2. Clicking it prompts for notification permission in the browser.
3. On success, a token string appears on the page, selectable/copyable.
4. On failure, a readable error message appears on the page instead of
   a blank screen or console-only error.

If anything beyond this is unclear, stop and ask rather than guessing.
