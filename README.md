<div align="center">

<img src="assets/images/avrix_dark_banner.jpg" alt="Avrix"/>

### *A desktop app for downloading YouTube video and audio*

[![License](https://img.shields.io/badge/License-Educational-blue?style=for-the-badge)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?style=for-the-badge)](/)

</div>

---

## Overview

Avrix is an Electron desktop app for downloading YouTube videos and audio.
It's built on [yt-dlp](https://github.com/yt-dlp/yt-dlp) under a Next.js UI,
with a local FastAPI backend doing the actual download work. See
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit
together.

## Features

- **MP4 video or MP3 audio**, quality up to 4K (or "best available")
- **Two download policies**: `strict_quality` (exact format, no fallback,
  requires ffmpeg) or `best_effort` (adds a fallback attempt and a couple of
  YouTube-403 workarounds — good default for flaky streams)
- **Queue system** with configurable concurrency (1–10 simultaneous
  downloads), reordering, retry, and clear-finished/clear-all
  — or a "direct mode" for a single one-off download
- **Subtitles** (multi-language) and **thumbnail embedding**
- **Dark/light theme**
- Settings persist across restarts

## Installation

### End users

Download the latest installer from
[Releases](https://github.com/yassine-krichen/avrix-downloader/releases)
(`Avrix Setup <version>.exe`) and run it. No Python, Node, or ffmpeg
required — they're bundled. Windows only for now.

### Running from source / building your own installer

See [docs/BUILD_INSTRUCTIONS.md](docs/BUILD_INSTRUCTIONS.md).

## Usage

1. Paste a YouTube video, Shorts, or playlist URL.
2. Pick format (video/audio), quality, and download policy.
3. Optionally enable subtitles or thumbnail embedding.
4. **Download** for an immediate single download, or **Add to Queue** to
   batch it with others — queued items run concurrently up to your configured
   limit.

Default download location is `<your Downloads folder>/Avrix`; change it in
Settings.

## Project structure

```
avrix_sidecar_backend/   FastAPI backend — settings, queue, yt-dlp download logic
avrix_desktop_frontend/  Next.js renderer (static export, no server at runtime)
electron/                Electron shell: window, IPC bridge, packaging config
docs/                    Architecture and build docs
assets/                  Icons, banners
```

## Troubleshooting

**Download fails / "Strict quality video download requires ffmpeg in
PATH"** — either switch to `best_effort` mode, or (if running from source)
install ffmpeg and ensure it's on PATH. Packaged installer builds bundle
ffmpeg automatically.

**Downloads fail intermittently with 403s** — use `best_effort` mode; it
retries with a looser format and different extractor client args
specifically to work around this.

**yt-dlp extraction breaks after a YouTube change** — yt-dlp ships fixes
frequently. If running from source, `pip install --upgrade yt-dlp` in
`avrix_sidecar_backend/`.

## Contributing

Issues and PRs welcome. Backend changes should keep
`avrix_sidecar_backend/tests/` passing (`pytest`); frontend changes should
keep `npx tsc --noEmit` clean in `avrix_desktop_frontend/`.

## License

Educational License — personal and educational use only; commercial use
requires permission from the author. This tool is for personal use; users
are responsible for complying with YouTube's Terms of Service and
applicable copyright law.

```
Copyright (c) 2026 Yassine Krichen
```
