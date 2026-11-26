# Temporary leader dashboard preview

Standalone read-only static demo for reviewing the leader dashboard layout.

- All dates, prices, market figures, stock codes and scores are synthetic.
- No SQLite database, local files, market provider credentials, user account or broker connection is included.
- The container only serves the static HTML file with Python's standard HTTP server.
- Deploy branch: `preview/leader-dashboard-demo`; Railway reads `railway.toml` and `preview/Dockerfile`.
- Delete the temporary Railway service once the visual review is complete.
