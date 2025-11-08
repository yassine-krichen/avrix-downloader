# YouTube Downloader - Architecture Documentation

## Overview

This is a desktop YouTube downloader application built with a clean, modular architecture that separates concerns between the backend download logic and the frontend UI.

## Design Principles

1. **Modular Structure**: Clear separation between core logic and UI
2. **Maintainability**: Easy to understand, extend, and debug
3. **Scalability**: Architecture supports future enhancements
4. **User Experience**: Responsive UI with real-time feedback
5. **Reliability**: Proper error handling and state management

## Architecture Layers

### 1. Core Layer (`core/`)

**Purpose**: Backend business logic, independent of UI

#### `downloader.py`
- **DownloadWorker**: QObject-based worker that runs in a separate thread
  - Handles actual download via yt-dlp Python API
  - Implements progress hooks for real-time updates
  - Detects and handles both videos and playlists
  - Emits signals for progress, completion, and errors
  
- **DownloadManager**: Main interface for starting/managing downloads
  - Creates and manages worker threads
  - Routes signals between worker and UI
  - Handles cleanup and cancellation
  - Thread-safe operation

**Key Features**:
- Uses yt-dlp's Python API (not shell commands)
- Thread-based to keep UI responsive
- Signal/slot pattern for loose coupling
- Configurable format (MP3/MP4) and quality (HD/SD)

#### `utils.py`
- **ConfigManager**: JSON-based settings persistence
  - Saves/loads user preferences
  - Handles default values
  - Graceful error handling
  
- **URLValidator**: YouTube URL validation
  - Pattern matching for various YouTube URL formats
  - Detects video vs playlist
  - Returns validation status
  
- **Helper Functions**:
  - `format_bytes()`: Human-readable file sizes
  - `format_speed()`: Download speed formatting
  - `format_time()`: ETA formatting
  - `ensure_directory_exists()`: Safe directory creation

### 2. UI Layer (`ui/`)

**Purpose**: User interface components using PySide6 (Qt)

#### `main_window.py`
- **MainWindow**: Main application window
  - URL input with real-time validation
  - Format selection (MP3/MP4 radio buttons)
  - Quality selection (HD/SD dropdown)
  - Folder browser dialog
  - Control buttons (Start/Cancel/Open Folder)
  - State management for UI elements
  - Settings persistence via ConfigManager
  
**Signal Connections**:
- Connected to DownloadManager signals
- Updates UI based on download state
- Handles user interactions

#### `progress_widget.py`
- **ProgressWidget**: Reusable progress display component
  - Current video progress bar
  - Playlist progress bar (shown for playlists)
  - Real-time stats: speed, size, ETA
  - Status messages (success/error)
  - Dynamic title updates
  
**Features**:
- Clean, readable progress information
- Conditional display (playlist bar only when needed)
- Color-coded status messages

### 3. Configuration Layer (`config/`)

**Purpose**: Persistent user settings

#### `settings.json`
```json
{
    "download_path": "path/to/folder",
    "format_type": "mp4",
    "quality": "hd",
    "last_url": ""
}
```

- Auto-created on first run
- Updated when user changes settings
- Loaded on app startup

### 4. Entry Point

#### `main.py`
- Application initialization
- QApplication setup
- MainWindow creation and display
- Event loop management

## Data Flow

### Download Workflow

```
User Input (URL) 
    ↓
MainWindow validates URL
    ↓
User clicks "Start Download"
    ↓
MainWindow → DownloadManager.start_download()
    ↓
DownloadManager creates DownloadWorker + QThread
    ↓
Worker runs in background thread:
    - Extracts video/playlist info
    - Downloads with progress hooks
    - Emits progress signals
    ↓
Signals flow back:
    Worker → DownloadManager → MainWindow → ProgressWidget
    ↓
UI updates in real-time
    ↓
Download completes → Worker emits completion signal
    ↓
MainWindow shows success message
    ↓
User clicks "Open Folder"
```

### Signal Flow

```
DownloadWorker signals:
    - progress_updated(dict)
    - download_started(str)
    - download_completed(dict)
    - download_error(str)
    - playlist_progress(int, int)
        ↓
DownloadManager (forwards signals)
        ↓
MainWindow (receives signals)
        ↓
ProgressWidget (updates UI)
```

## Threading Model

- **Main Thread**: UI operations (Qt event loop)
- **Worker Thread**: Download operations (yt-dlp)
- **Communication**: Qt signals/slots (thread-safe)

**Why Threading?**
- Prevents UI freezing during downloads
- Allows real-time progress updates
- Enables cancellation without blocking

## Error Handling

1. **URL Validation**: Before starting download
2. **Path Validation**: Ensures destination exists
3. **Download Errors**: Caught and reported via signals
4. **User Cancellation**: Graceful cleanup
5. **Thread Cleanup**: Proper resource disposal

## State Management

### UI States

1. **Ready**: Waiting for user input
   - Download button enabled
   - All inputs editable
   
2. **Downloading**: Active download
   - Download button disabled
   - Cancel button enabled
   - Inputs locked
   - Progress updates visible
   
3. **Completed**: Download finished
   - Open Folder button enabled
   - Ready for next download

### State Transitions

```
Ready → [Start Download] → Downloading
Downloading → [Complete/Error] → Completed → Ready
Downloading → [Cancel] → Ready
```

## Extensibility Points

The architecture is designed for easy extension:

### Future Queue System
- Add `DownloadQueue` class in `core/`
- Manages multiple DownloadWorkers
- Priority queue support

### Pause/Resume
- Add state tracking in DownloadWorker
- Use yt-dlp's resume capabilities
- Store partial download state

### Metadata Tagging
- Add `metadata.py` module in `core/`
- Use mutagen library
- Tag MP3 files with ID3 info

### Themes
- Add `themes.py` in `ui/`
- QSS stylesheets in `assets/`
- Theme switcher in settings

### Download History
- Add `database.py` in `core/`
- SQLite for history storage
- History widget in `ui/`

## Dependencies

### Core Dependencies
- **yt-dlp**: YouTube download engine
- **PySide6**: Qt framework for Python
- **FFmpeg**: External dependency for media processing

### Why These Choices?

- **yt-dlp**: Most reliable YouTube downloader, active development
- **PySide6**: Official Qt bindings, mature, cross-platform
- **FFmpeg**: Industry standard for media processing

## File Organization

```
youtube_downloader/
├── main.py                     # Entry point (23 lines)
├── check_dependencies.py       # Dependency checker (70 lines)
├── requirements.txt            # Python dependencies
├── README.md                   # User documentation
├── QUICK_START.md             # Quick start guide
├── ARCHITECTURE.md            # This file
├── .gitignore                 # Git ignore rules
│
├── core/                      # Backend (530+ lines)
│   ├── __init__.py
│   ├── downloader.py          # Download engine (243 lines)
│   └── utils.py               # Utilities (201 lines)
│
├── ui/                        # Frontend (620+ lines)
│   ├── __init__.py
│   ├── main_window.py         # Main window (438 lines)
│   └── progress_widget.py     # Progress display (186 lines)
│
├── config/                    # Configuration
│   └── settings.json          # User settings
│
└── assets/                    # Assets (reserved)
    ├── icons/
    └── styles.qss
```

## Code Quality

- **Type Hints**: Used throughout for clarity
- **Docstrings**: All classes and public methods documented
- **Comments**: Explain complex logic
- **Error Handling**: Try-except blocks where needed
- **Resource Management**: Proper cleanup of threads

## Testing Strategy (Future)

Recommended test structure:

```
tests/
├── test_downloader.py         # Download logic tests
├── test_utils.py              # Utility function tests
├── test_url_validator.py      # URL validation tests
└── test_ui.py                 # UI component tests
```

## Performance Considerations

1. **Threading**: Non-blocking downloads
2. **Progress Updates**: Throttled to avoid UI spam
3. **Memory**: Streaming downloads (yt-dlp handles this)
4. **Resource Cleanup**: Proper thread termination

## Security Considerations

1. **URL Validation**: Only YouTube URLs accepted
2. **Path Validation**: Safe file path handling
3. **No Shell Injection**: Uses Python API, not shell commands
4. **Error Messages**: No sensitive info exposed

## Platform Support

- **Windows**: Fully tested
- **macOS**: Should work (Qt is cross-platform)
- **Linux**: Should work (Qt is cross-platform)

## Known Limitations (Phase 1)

1. No download queue (single download at a time)
2. No pause/resume
3. No subtitle downloads
4. No metadata tagging
5. No download history
6. Basic error messages
7. No retry logic

## Conclusion

This architecture provides a solid foundation for a YouTube downloader application. The modular design makes it easy to add features, fix bugs, and maintain code quality. The separation of concerns ensures that backend and frontend can evolve independently.

The code is production-ready for Phase 1 requirements and provides clear extension points for future enhancements.
