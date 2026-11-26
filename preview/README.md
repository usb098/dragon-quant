# Temporary dashboard deployment

This branch deploys the repository React + FastAPI dashboard. It uses the cloud-side TDX / THS collectors and stores its own SQLite files under /data on a Railway persistent volume.

- Public HTTP Basic Auth is required.
- Only /health is unauthenticated for Railway health checks.
- Web workspace writes remain disabled.
- Run scan and prep manually from the dashboard; no brokerage order endpoint is exposed.
- Cloud storage starts empty; local databases are not copied from a user's computer.
