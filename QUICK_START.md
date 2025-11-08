# Quick Start Guide

## Installation (First Time Setup)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python check_dependencies.py
   ```

## Running the Application

```bash
python main.py
```

## Basic Usage

### Downloading a Single Video

1. Copy a YouTube video URL (e.g., `https://www.youtube.com/watch?v=dQw4w9WgXcQ`)
2. Paste it in the URL field - you'll see "📹 Video" indicator
3. Choose format:
   - **MP3**: Audio only (good for music)
   - **MP4**: Video with audio
4. For MP4, choose quality:
   - **HD**: 1080p (better quality, larger file)
   - **SD**: 480p (lower quality, smaller file)
5. Click "Browse..." to choose where to save (optional)
6. Click "Start Download"
7. Watch the progress bar update in real-time
8. When done, click "Open Folder" to view the file

### Downloading a Playlist

1. Copy a YouTube playlist URL (e.g., `https://www.youtube.com/playlist?list=...`)
2. Paste it in the URL field - you'll see "📋 Playlist" indicator
3. Choose format and quality (same as single video)
4. Click "Start Download"
5. Watch both progress bars:
   - Top bar: Current video progress
   - Bottom bar: Overall playlist progress
6. The app will download all videos one by one
7. All videos save to the same folder

## Tips

- **Settings are saved:** Your format, quality, and folder choices are remembered
- **Cancel anytime:** Click "Cancel" to stop a download in progress
- **Check URL first:** The app validates URLs and shows video/playlist/invalid status
- **FFmpeg required:** Must be installed for MP3 conversion and HD video downloads

## Troubleshooting

### App won't start
- Make sure Python 3.8+ is installed
- Run: `pip install -r requirements.txt`

### Downloads fail
- Check internet connection
- Verify YouTube URL is valid
- Some videos may be region-restricted

### MP3 conversion fails
- Install FFmpeg: https://ffmpeg.org/download.html
- Add FFmpeg to system PATH
- Restart the application

### Quality options don't work
- FFmpeg must be installed
- Some videos don't have HD available

## Keyboard Shortcuts

- **Alt+F4**: Close application
- **Esc**: Close any dialog

## Default Settings

- **Format:** MP4 (Video)
- **Quality:** HD (1080p)
- **Save Location:** `C:\Users\YourName\Downloads\YoutubeDownloader\`

---

Enjoy downloading! 🎵🎬
