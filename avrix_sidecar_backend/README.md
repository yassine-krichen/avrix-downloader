# Avrix Sidecar Backend

Feature 1 foundation is now scaffolded in this folder.

## Run (development)

```bash
cd avrix_sidecar_backend
pip install -r requirements.txt
python -m app.main
```

## Available Endpoints

- GET /health/live
- GET /health/ready
- GET /api/v1/health/live
- GET /api/v1/health/ready

## Notes

- Error responses are standardized with `code`, `message`, `details`, and `trace_id`.
- Trace ID is propagated using `x-trace-id` header.
