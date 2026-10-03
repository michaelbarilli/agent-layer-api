# Deploy Agent Layer API to Railway

## Recommended: GitHub → Railway

1. Create a new GitHub repository, e.g. `agent-layer-api`.
2. Upload every file in this folder to the repository root, including `agent_layer.db` and `railway.json`.
3. In Railway choose **New Project → Deploy from GitHub repo**.
4. Select `agent-layer-api` and deploy.
5. Railway should read `railway.json` and start:
   `uvicorn app:app --host 0.0.0.0 --port $PORT`
6. In Railway **Settings → Networking**, generate a public domain.
7. Test:
   - `/v1/health`
   - `/v1/sources/status`
   - `/v1/commercial-property/changes?event_type=RATEPAYER_CHANGED&limit=5`
   - `/docs`
   - `/openapi.json`

## Database note

For this first read-only proof, the bundled SQLite database can ship with the application.
Because the API does not modify it, a persistent volume is not required yet.

Before automated snapshot ingestion writes new data in production, move the database to a Railway volume or migrate to a managed database.

## Expected health result

The health endpoint should report:
- 3,686 current properties
- 7,352 snapshot records
- 156 field-level change events
