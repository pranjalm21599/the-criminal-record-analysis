# CrimeNet AI — Frontend Dashboard (Member 5)

Investigator-facing web console for the Criminal Network Analysis System.
Dark "intelligence console" visual identity — IBM Plex Mono for data/labels,
Inter for UI text, electric-blue signal accent, risk-tiered reds/ambers/greens.

## Pages
- **Overview** (`/`) — live stats, network graph search, top-risk suspects, detected groups
- **Network Graph** (`/graph`) — full-screen Cytoscape.js graph exploration
- **Cases** (`/cases`) — case list, case detail, timeline
- **Crime Map** (`/map`) — Leaflet-based geographic view of incidents
- **Ingest Data** (`/upload`) — drag-and-drop FIR / call record / transaction upload
- **AI Assistant** (`/chat`) — chat UI wired to Member 6's `/chat/` endpoints

## Setup

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Before your demo

Check `src/api/apiClient.js` — the base URLs there (ports 8000–8004) must
match where each teammate's service is actually running. If you're using
`docker compose up` from the `ai_service/integration/docker-compose.yml`,
these already line up.

## Notes on library choices

- **Timeline**: implemented as a lightweight custom component
  (`components/timeline/EventTimeline.jsx`) instead of `vis-timeline`, to
  keep the dependency surface smaller and avoid version-mismatch bugs before
  a demo. Swap in `vis-timeline` later if you need zoom/pan on long timelines.
- **Map**: uses `react-leaflet` with a dark CARTO basemap tile layer, wired
  to accept `[{ lat, lng, label, severity }]` — connect this to real geocoded
  evidence once the backend exposes coordinates.
- **AIChat.jsx** is a drop-in component — it manages its own conversation ID
  and talks directly to `POST /chat/`, `POST /chat/reset`, and
  `GET /chat/sample-questions` (Member 6's API). No extra wiring needed
  beyond making sure port 8004 is reachable.
