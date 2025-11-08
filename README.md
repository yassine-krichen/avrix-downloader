# YouTube Downloader

A modern, clean desktop application for downloading YouTube videos and playlists as MP3 or MP4 files, built with Python and PySide6.

## Features

✨ **Core Functionality:**
- Download single YouTube videos or entire playlists
- Choose between MP3 (audio) or MP4 (video) formats
- Select video quality: HD (1080p) or SD (480p)
- Real-time progress tracking with speed and ETA
- Dual progress bars for playlist downloads
- Persistent settings (remembers your preferences)
- Clean, user-friendly interface

## Installation

### Prerequisites

1. **Python 3.8 or higher**
   - Download from [python.org](https://www.python.org/downloads/)

2. **FFmpeg** (Required for MP3 conversion and video merging)
   - **Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
   - **macOS:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg` (Ubuntu/Debian) or `sudo yum install ffmpeg` (Fedora)

### Setup

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   cd youtube_downloader
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main.py
```

### How to Use

1. **Paste URL:** Enter a YouTube video or playlist URL in the input field
2. **Choose Format:** Select MP3 (audio only) or MP4 (video)
3. **Select Quality:** If MP4, choose between HD (1080p) or SD (480p)
4. **Choose Destination:** Select where to save downloaded files (default: `Downloads/YoutubeDownloader`)
5. **Start Download:** Click "Start Download" and watch the progress
6. **Open Folder:** After completion, click "Open Folder" to view downloaded files

### Features in Action

- **URL Detection:** The app automatically detects if you've pasted a video or playlist link
- **Progress Tracking:** Watch real-time download speed, file size, and estimated time
- **Playlist Support:** For playlists, see both individual video progress and overall playlist progress
- **Settings Persistence:** Your format, quality, and folder preferences are saved automatically

## Project Structure

```
youtube_downloader/
├── main.py                 # Application entry point
├── core/                   # Backend logic
│   ├── downloader.py      # yt-dlp integration and download management
│   └── utils.py           # URL validation, config, formatting utilities
├── ui/                     # User interface
│   ├── main_window.py     # Main application window
│   └── progress_widget.py # Progress display widget
├── config/                 # Configuration
│   └── settings.json      # User settings (auto-generated)
├── assets/                 # Assets (reserved for future use)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Architecture

The application follows a clean, modular architecture:

- **Core Module:** Handles all download logic using yt-dlp's Python API (not shell commands)
- **UI Module:** PySide6-based interface with signal/slot communication
- **Configuration:** JSON-based settings persistence
- **Threading:** Downloads run in background threads to keep UI responsive

## Troubleshooting

### "FFmpeg not found" error
- Ensure FFmpeg is installed and added to your system PATH
- Restart the application after installing FFmpeg

### Downloads fail or hang
- Check your internet connection
- Verify the YouTube URL is valid and accessible
- Some videos may be restricted or unavailable in your region

### Quality options don't work
- FFmpeg must be installed for quality selection to work properly
- Some videos may not have the requested quality available

## Future Enhancements

The architecture is designed to support future features:
- Download queue system
- Pause/resume functionality
- Subtitle downloads
- Metadata tagging
- Theme customization
- Download history
- Auto yt-dlp updates
- Multi-threaded downloads

## Requirements

- Python 3.8+
- PySide6 6.6.0+
- yt-dlp 2023.10.13+
- FFmpeg (external dependency)

## License

This project is for educational purposes. Respect YouTube's Terms of Service and copyright laws.

## Credits

Built with:
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube download library
- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [FFmpeg](https://ffmpeg.org/) - Media processing

---

**Note:** This is a Phase 1 implementation focusing on core functionality. The codebase is designed to be modular and maintainable for future enhancements.
