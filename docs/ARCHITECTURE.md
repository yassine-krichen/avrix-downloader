# Architecture

Avrix is an Electron desktop app with a Python "sidecar" backend. Electron
hosts a Next.js renderer and spawns a local FastAPI process; the renderer
talks to it over plain HTTP on `127.0.0.1:8000`.

```
┌─────────────────────────────────────────────────────────┐
│ Electron (electron/main.js)                              │
│  ┌───────────────────────┐   spawns    ┌───────────────┐ │
│  │ BrowserWindow          │◄───────────►│ FastAPI       │ │
│  │ (Next.js static export)│   HTTP      │ sidecar       │ │
│  │ avrix_desktop_frontend │  :8000      │ avrix_sidecar_│ │
│  └───────────────────────┘             │ backend       │ │
│           │ preload.js (contextBridge)  └───────┬───────┘ │
│           │ IPC: folder picker, open-folder      │ yt-dlp │
└───────────┴─────────────────────────────────────┴────────┘
```

## Processes

- **Electron main** (`electron/main.js`) creates the window, spawns/kills the
  sidecar process, and exposes a narrow set of OS operations (pick a folder,
  open a folder, get the default Downloads path) to the renderer via
  `electron/preload.js`'s `contextBridge`. The renderer runs with
  `nodeIntegration: false` / `contextIsolation: true` — it has no direct
  Node or Electron API access.
- **FastAPI sidecar** (`avrix_sidecar_backend/`) owns all download logic:
  settings persistence, the download queue, and driving yt-dlp. It's a
  regular HTTP server; Electron just manages its lifecycle.
- **Renderer** (`avrix_desktop_frontend/`) is a Next.js app built as a static
  export (`next build`, `output: "export"`) and loaded via `loadFile` — there
  is no Next.js server at runtime, only static HTML/JS talking to the sidecar
  over `fetch`.

In dev mode, the renderer instead loads from the Next.js dev server
(`http://localhost:3000`) and the sidecar runs as `python -m app.main`. See
[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for both paths.

## Backend layout (`avrix_sidecar_backend/`)

```
app/
├── main.py                 # FastAPI app, middleware, error handlers
├── api/v1/                 # Routers: health, settings, queue, download
├── contracts/               # Pydantic request/response models
├── core/
│   ├── config.py           # Settings (env-overridable, prefix AVRIX_)
│   └── errors.py           # AppError -> structured JSON error mapping
└── services/
    ├── settings_service.py     # GET/PATCH /settings, persisted to JSON
    ├── queue_service.py        # Queue CRUD/ordering, JSON-file persisted
    ├── download_engine_service.py  # Queue-driven concurrent downloads
    ├── current_download_service.py # Single "direct mode" download
    └── download_options.py     # Shared yt-dlp option/attempt builder
```

### API surface (`/api/v1`)

| Area | Endpoints |
|---|---|
| Health | `GET /health/live`, `GET /health/ready` |
| Settings | `GET /settings`, `PATCH /settings` |
| Queue | `GET/POST /queue`, `DELETE /queue`, `DELETE /queue/finished`, `DELETE /queue/{id}`, `POST /queue/{id}/move`, `GET/POST /queue/execution`, `POST /queue/stop` |
| Direct download | `GET /download/current`, `POST /download/start`, `POST /download/cancel` |

Errors follow a standard envelope: `{code, message, details, trace_id}`
(see `app/core/errors.py` and the exception handlers in `app/main.py`).

### Download policies

Every download (queue or direct) picks one of two policies
(`app/services/download_options.py`):

- **`strict_quality`** — exactly one yt-dlp attempt at the requested
  format/height, no fallback. Requires ffmpeg (raises if unavailable).
- **`best_effort`** — same first attempt, plus a looser `best[ext=mp4]/best`
  fallback attempt, `skip_unavailable_fragments`, and
  `player_client: [android, web]` extractor args to work around YouTube 403s
  on the primary stream.

Both services (queue engine and direct download) build their yt-dlp options
through the same `build_ydl_attempts()` function — kept as one shared
function specifically so this logic isn't duplicated and so it's covered by
`tests/test_download_options.py` as pure-function unit tests, with no yt-dlp
or thread mocking required.

### Queue execution

`download_engine_service.py` runs a single dispatcher thread that pulls
pending items from `queue_service` into a `ThreadPoolExecutor` sized by
`max_concurrent_downloads` (from settings). It excludes both in-flight item
IDs and in-flight URLs when picking the next item, so the same video can't be
downloaded twice concurrently (a real 403 source if two yt-dlp processes hit
the same stream at once).

### Data persistence

No database — settings and the queue are each a single JSON file under
`config_root` (default `<repo>/config` in dev; see the packaging note below
for the installed build). `queue_service.py` and `settings_service.py` each
hold a `threading.Lock` around read-modify-write cycles since multiple
requests/threads can touch the same file.

## Packaging

The installed build bundles two things Python and Node code depend on so
the end user needs neither preinstalled:

1. **The sidecar itself**, frozen with PyInstaller (`sidecar.spec`, onedir
   build) into `avrix_sidecar_backend/dist/avrix_sidecar/`.
2. **ffmpeg**, fetched by `scripts/fetch-ffmpeg.ps1` into
   `electron/build-resources/ffmpeg/` (not committed — fetched at build
   time).

`electron-builder` (config in `electron/package.json`'s `"build"` key) wires
both in as `extraResources`, alongside the Next.js static export. In a
packaged build, `electron/main.js` spawns the frozen sidecar exe instead of
`python -m app.main`, and sets two env vars the sidecar reads via
`pydantic-settings`' `AVRIX_` prefix:

- `FFMPEG_PATH` — path to the bundled ffmpeg binary (checked before PATH,
  see `resolve_ffmpeg_location()` in `download_options.py`).
- `AVRIX_CONFIG_ROOT` — `app.getPath('userData')/config`. Without this, the
  sidecar's default `config_root` resolves relative to its own frozen
  source location, which lands inside the install directory — not reliably
  writable, and wiped on reinstall/uninstall.

See [BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md) for the full build steps.
