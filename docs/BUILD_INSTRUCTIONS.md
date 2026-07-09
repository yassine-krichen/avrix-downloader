# Build Instructions

## Running from source (development)

Three pieces, each in its own terminal:

```bash
# 1. Backend — install deps and run the dev server
cd avrix_sidecar_backend
pip install -r requirements-dev.txt   # includes runtime + test deps
python -m app.main                    # http://127.0.0.1:8000

# 2. Frontend — Next.js dev server
cd avrix_desktop_frontend
npm install
npm run dev                           # http://localhost:3000

# 3. Electron shell
cd electron
npm install
NODE_ENV=development npm start
```

In dev mode, Electron loads the renderer from the Next.js dev server (hot
reload works) and spawns the backend via `python -m app.main` — you need a
Python 3.10+ interpreter and `ffmpeg` on PATH locally.

Run the backend test suite from `avrix_sidecar_backend/`:

```bash
pytest
```

## Building the installer (production)

This produces a single NSIS installer that bundles the frontend, a frozen
copy of the Python backend, and ffmpeg — the target machine needs none of
those preinstalled. Windows only (see [ARCHITECTURE.md](ARCHITECTURE.md) for
why: PyInstaller + electron-builder are both configured for a Windows/NSIS
target today).

```bash
# 1. Fetch ffmpeg (downloads a static build into electron/build-resources/,
#    gitignored, ~100MB, skips if already present)
powershell -File scripts/fetch-ffmpeg.ps1

# 2. Freeze the Python backend with PyInstaller
cd avrix_sidecar_backend
pip install -r requirements-build.txt
pyinstaller sidecar.spec --noconfirm
# -> avrix_sidecar_backend/dist/avrix_sidecar/avrix_sidecar.exe

# 3. Build the installer (also builds the Next.js static export first,
#    via the predist/prepack npm script)
cd ../electron
npm install
npm run dist
# -> electron/dist/Avrix Setup <version>.exe
```

`npm run pack` (instead of `dist`) produces an unpacked build in
`electron/dist/win-unpacked/` without going through NSIS — faster for
checking the resource layout without producing a full installer.

### What goes where

electron-builder's `build` config (in `electron/package.json`) wires:

- `avrix_desktop_frontend/out` (the static export) into the packaged app
  root as `avrix_desktop_frontend/out`.
- `avrix_sidecar_backend/dist/avrix_sidecar` (the PyInstaller output) into
  `resources/sidecar/avrix_sidecar/`.
- `electron/build-resources/ffmpeg` into `resources/ffmpeg/`.

`electron/main.js` picks between the dev and packaged spawn paths via
`app.isPackaged`.

### Verifying a build

```bash
cd electron/dist/win-unpacked
./Avrix.exe
```

Confirm: the window opens, the settings/queue tabs load without errors (the
sidecar responded), and a real download completes with `strict_quality`
selected (this is the policy that requires ffmpeg — it's the one that
exercises the bundled binary rather than silently falling back).

## Updating yt-dlp before a release

yt-dlp ships fixes for YouTube extraction breakage frequently. Before
cutting a release, bump the pin in `avrix_sidecar_backend/requirements.txt`
(`requirements-dev.txt` and `requirements-build.txt` both inherit it via
`-r requirements.txt`) and rerun the backend test suite.
