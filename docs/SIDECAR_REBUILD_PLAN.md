# Avrix Sidecar Rebuild Plan

## Naming And Structure Decisions

To keep the repository clean and explicit:

- New frontend name: `avrix_desktop_frontend/` (renamed from `avrix_react_ui/`)
- New backend target: `avrix_sidecar_backend/` (brand new implementation)
- Legacy label: `legacy_backend_pyside/` (legacy architecture reference)

Current legacy implementation is now grouped under `legacy_backend_pyside/` as migration reference until full cutover.

## Product Goal

Build a production-ready desktop application where:

1. Electron hosts the desktop shell.
2. Next.js provides the full renderer UI.
3. Python sidecar exposes API + realtime events.
4. Frontend and backend are strongly contract-driven and versioned.

## Non-Negotiable Engineering Rules

- Contract-first development: frontend never calls ad-hoc endpoints.
- One feature at a time, each feature must be fully complete before moving on.
- Add observability from day one (structured logs, health endpoints, clear errors).
- Every feature has a Definition of Done (DoD) and manual verification steps.
- No hidden coupling to PySide/Qt in new backend code.

## Ordered Feature Roadmap (Execution Sequence)

## Feature 1: Foundation And API Contract

Objective:
Create the new backend foundation and stable contract layer so all future features integrate safely.

Why first:
Everything else depends on stable request/response models, health checks, error format, and event schema.

Includes:
- Backend app scaffold in `avrix_sidecar_backend/`.
- Config loader and environment profile (`dev` / `prod`).
- API versioning (`/api/v1/...`).
- Global response/error model.
- Health endpoints (`/health/live`, `/health/ready`).
- Event envelope schema for websocket/SSE.
- Frontend shared API client skeleton (typed) against this contract.

DoD:
- Frontend can call health endpoint reliably from Electron.
- All backend errors return structured JSON with stable codes.
- Contract document exists and is versioned.

## Feature 2: Settings Service (Read/Write + Validation)

Objective:
Migrate settings as first real business capability and establish persistent config flow.

Why second:
Settings are low-risk but touch persistence, validation, defaults, and frontend data binding.

Includes:
- `GET /api/v1/settings`
- `PATCH /api/v1/settings`
- Strict schema validation and defaults
- Persistence to JSON (or SQLite if chosen in Feature 1 decision)
- Frontend settings hydration and save actions

DoD:
- Settings persist across restarts.
- Invalid payloads return detailed field-level errors.

## Feature 3: Queue Domain (CRUD + Ordering)

Objective:
Rebuild queue as backend-first domain without download execution yet.

Why third:
Queue operations are the backbone for both single and batch workflows.

Includes:
- Add queue item
- List queue
- Remove queue item
- Move item up/down or absolute reorder
- Clear finished / clear all policies
- Queue persistence and state recovery rules

DoD:
- UI queue tab is fully backed by API, no mock state.
- Reorder and cleanup actions are deterministic.

## Feature 4: Download Execution Engine Adapter

Objective:
Bridge/port yt-dlp execution into sidecar service workers.

Why fourth:
Execution depends on stable queue and settings semantics.

Includes:
- Start job worker from queue item
- Progress hooks normalized to event schema
- Stop/cancel behavior
- Retry safety and idempotency guards
- Concurrency controls

DoD:
- Real downloads run from UI actions.
- Progress updates map correctly to active queue items.

## Feature 5: Realtime Updates Channel

Objective:
Ship robust realtime updates for queue/download state.

Why fifth:
Needs event schemas and execution state from prior features.

Includes:
- Websocket channel in sidecar backend
- Event fan-out manager
- Reconnect strategy in frontend hook
- Backfill sync on reconnect

DoD:
- UI updates in realtime without refresh.
- Reconnect does not duplicate or corrupt state.

## Feature 6: Desktop Integrations (Electron Bridge)

Objective:
Add desktop-specific capabilities through Electron safely.

Why sixth:
Core app must function first; desktop extras come after stable domain flow.

Includes:
- Open download folder
- Shell operations via preload IPC only
- Notification bridge (optional backend-triggered event -> electron notify)
- Security hardening (disable insecure nodeIntegration path)

DoD:
- All desktop actions are routed through vetted IPC.
- Renderer has no direct unsafe node access.

## Feature 7: Legacy Cutover And Cleanup

Objective:
Complete migration and retire old runtime paths.

Why seventh:
Only safe when all functional features are validated on sidecar stack.

Includes:
- Switch all runtime scripts to new backend folder.
- Mark legacy modules read-only archive.
- Remove orphan code paths and stale docs.

DoD:
- App runs only on Electron + Next + sidecar backend.
- Legacy stack no longer required for runtime.

## Feature 8: Packaging And Release Pipeline

Objective:
Build reproducible distribution pipeline.

Why eighth:
Packaging should lock only after architecture is stable.

Includes:
- Backend bundling strategy (PyInstaller or embeddable Python runtime)
- Electron builder config with sidecar assets
- One-command build pipeline
- Smoke tests for packaged build

DoD:
- Fresh machine install works with no manual patching.

## Implementation Strategy For Feature 1 (Best Approach)

### Recommended Architecture

Use FastAPI with a strict layered backend inside `avrix_sidecar_backend/`:

- `app/main.py`: app bootstrap and route registration
- `app/api/v1/`: REST routers
- `app/contracts/`: pydantic request/response/event models
- `app/core/`: config, logging, error mapping
- `app/services/`: domain services (empty placeholders for now)

### Why this is best for your project

1. You already have a complex UI and queue/download logic expectations.
2. Contract-first FastAPI gives fast iteration and explicit schemas.
3. Pydantic models will let us generate stable TS types for frontend integration.
4. It cleanly decouples from legacy PySide signal-driven architecture.

### Feature 1 Technical Decisions

- API base path: `/api/v1`
- Error shape:
  - `code` (machine-readable)
  - `message` (human-readable)
  - `details` (field errors / context)
  - `trace_id` (log correlation)
- Health endpoints:
  - `live`: process is alive
  - `ready`: dependencies and storage are available
- Event envelope (for future realtime):
  - `event_type`
  - `event_version`
  - `occurred_at`
  - `payload`

### Frontend Prep In Feature 1

Only foundations, no feature behavior yet:
- Add `lib/api/client.ts` in `avrix_desktop_frontend/`.
- Add base URL strategy (`http://127.0.0.1:{port}` with fallback).
- Add a `pingBackend()` function wired to startup status indicator.

### Risks And Mitigations For Feature 1

Risk: Contract churn while building later features.
Mitigation: Freeze v1 envelope and evolve using additive fields only.

Risk: Electron starts before backend is ready.
Mitigation: readiness polling with timeout and clear UI error state.

Risk: Hidden PySide coupling leaks into new backend.
Mitigation: zero imports from legacy modules in new sidecar scaffolding.

## Per-Feature Delivery Mode

For each feature, we will follow this exact cycle:

1. Clarify functional boundary.
2. Confirm/lock API contract for that feature.
3. Implement backend endpoints/services.
4. Implement frontend integration.
5. Verify manually in Electron runtime.
6. Update docs and mark feature complete.

## Status

- Planning complete.
- Feature 1 completed: foundation, contracts, health endpoints, and frontend API client skeleton.
- Ready to begin Feature 2.
