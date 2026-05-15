# Web

Vanilla HTML / JS / CSS frontend. No build step, no dependencies.

## Files

- [`index.html`](index.html) — UI shell with the sidebar controls and the two transcript columns.
- [`styles.css`](styles.css) — Light theme.
- [`app.js`](app.js) — Microphone capture (`MediaRecorder`), WebSocket client to the backend, and PCM playback via the Web Audio API.

## Run

These files are served as static assets by the backend (see [../server/](../server/)). Start the server and open <http://localhost:8000> — there is no separate frontend build or dev server.
