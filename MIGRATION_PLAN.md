# Migration Plan: PyQt to Electron + Next.js + Python

This document outlines the plan to convert the existing PyQt application into a hybrid Desktop Application using Electron, Next.js, and a Python sidecar process.

## Architecture Overview

The application will follow the "Python Sidecar" architecture:
1.  **Electron (Main Process)**: Acts as the application shell. It manages the window, system tray, and spawns the Python background process.
2.  **Python (Background Process)**: Runs a FastAPI server that handles all business logic (downloading, file management, settings). It exposes a REST API and WebSockets for real-time progress.
3.  **Next.js (Renderer Process)**: The user interface. It runs inside the Electron window and communicates with the Python backend via HTTP/WebSockets.

## Step 1: Python Backend Preparation

We need to ensure the Python core is completely decoupled from PyQt and accessible via API.

- [x] **Decouple Core Logic**: Create pure Python versions of services (already started with `downloader_service.py`, `queue_service.py`).
- [x] **Create API Server**: Setup FastAPI to expose core functionality (started in `server/api.py`).
- [ ] **Expand API**:
    -   Add endpoints for Settings management (`GET /settings`, `POST /settings`).
    -   Add endpoints for System info (version, paths).
    -   Add endpoints for File management (open download folder).
- [ ] **Remove PyQt Dependencies**: Ensure `core/` modules used by the server do not import `PySide6`.

## Step 2: Next.js Configuration

The Next.js app needs to be configured to run as a static frontend within Electron.

- [ ] **Static Export**: Update `next.config.mjs` to use `output: 'export'`.
- [ ] **API Client**: Create a centralized API client in the React app to communicate with the Python server (defaulting to `http://localhost:8000`).
- [ ] **WebSocket Hook**: Create a React hook (`useDownloadProgress`) to listen for WebSocket events from the server.
- [ ] **Routing**: Ensure client-side routing works (HashRouter is often preferred in Electron, or just standard Next.js routing with static export).

## Step 3: Electron Setup

We will set up Electron to orchestrate the application.

- [ ] **Initialize Electron**: Create `package.json` and install `electron`, `electron-builder`.
- [ ] **Main Process (`main.js`)**:
    -   Spawn the Python server as a child process on startup.
    -   Find a free port dynamically (optional, or stick to 8000 for dev).
    -   Load the Next.js `out/index.html` (production) or `localhost:3000` (dev).
    -   Kill the Python process when the window closes.
- [ ] **Preload Script**: Expose necessary system capabilities if needed (e.g., opening external links).

## Step 4: Integration & UI Wiring

Connect the React UI to the Python backend.

- [ ] **Connect Forms**: Wire up the "Add Download" form to `POST /download`.
- [ ] **Connect Queue**: Wire up the Queue list to `GET /queue` and WebSocket updates.
- [ ] **Connect Settings**: Wire up the Settings page to read/write from the Python API.
- [ ] **Notifications**: Use HTML5 Notifications API or Electron's Notification module (triggered by WebSocket events).

## Step 5: Packaging & Distribution

Bundle everything into a single installer.

- [ ] **Bundle Python**: Use `pyinstaller` to create a single executable of the Python server (`api.exe`).
- [ ] **Bundle Electron**: Configure `electron-builder` to include the `api.exe` in the resources folder.
- [ ] **Build Scripts**: Create `npm run build:app` scripts to automate the build pipeline (Next build -> Python build -> Electron build).

## Directory Structure Plan

```
root/
├── electron/
│   ├── main.js
│   ├── preload.js
│   └── package.json
├── server/
│   ├── api.py
│   └── ...
├── avrix_react_ui/  (Next.js)
├── core/            (Shared Python Logic)
├── dist/            (Build artifacts)
└── ...
```
