"""
YouTube downloader core module using yt-dlp.
Handles single videos and playlists with progress tracking.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any, Callable
import yt_dlp
from PySide6.QtCore import QObject, Signal, QThread


class DownloadWorker(QObject):
    """Worker class to handle downloads in a separate thread."""
    
    # Signals for progress updates
    progress_updated = Signal(dict)  # Progress info dictionary
    download_started = Signal(str)   # Video title
    download_completed = Signal(dict)  # Result info
    download_error = Signal(str)     # Error message
    playlist_progress = Signal(int, int)  # Current index, total count
    
    def __init__(self, url: str, download_path: str, format_type: str, quality: str = "best"):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.format_type = format_type  # 'mp3' or 'mp4'
        self.quality = quality  # 'sd' or 'hd'
        self.is_cancelled = False
        self.current_video_index = 0
        self.total_videos = 1
        
    def progress_hook(self, d: Dict[str, Any]):
        """Hook called by yt-dlp to report download progress."""
        if self.is_cancelled:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            progress_info = {
                'status': 'downloading',
                'downloaded_bytes': d.get('downloaded_bytes', 0),
                'total_bytes': d.get('total_bytes') or d.get('total_bytes_estimate', 0),
                'speed': d.get('speed', 0),
                'eta': d.get('eta', 0),
                'filename': d.get('filename', ''),
                'percent': 0.0
            }
            
            # Calculate percentage
            if progress_info['total_bytes'] > 0:
                progress_info['percent'] = (progress_info['downloaded_bytes'] / progress_info['total_bytes']) * 100
            
            self.progress_updated.emit(progress_info)
            
        elif d['status'] == 'finished':
            self.progress_updated.emit({
                'status': 'finished',
                'filename': d.get('filename', ''),
                'percent': 100.0
            })
    
    def cancel(self):
        """Cancel the current download."""
        self.is_cancelled = True
    
    def run(self):
        """Main download execution method."""
        try:
            print(f"\n{'*'*60}")
            print(f"DEBUG: Starting download")
            print(f"  URL: {self.url}")
            print(f"  Download Path: {self.download_path}")
            print(f"  Format: {self.format_type}")
            print(f"  Quality: {self.quality}")
            print(f"{'*'*60}\n")
            
            # Create download directory if it doesn't exist
            Path(self.download_path).mkdir(parents=True, exist_ok=True)
            
            # Configure yt-dlp options
            ydl_opts = self._get_ydl_options()
            
            # Start download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to check if it's a playlist
                print(f"DEBUG: Extracting video information...")
                info = ydl.extract_info(self.url, download=False)
                
                if 'entries' in info:
                    # It's a playlist
                    self.total_videos = len(info['entries'])
                    self.playlist_progress.emit(0, self.total_videos)
                    print(f"DEBUG: Detected playlist with {self.total_videos} videos\n")
                    
                    # Download each video
                    for idx, entry in enumerate(info['entries'], 1):
                        if self.is_cancelled:
                            break
                            
                        if entry:
                            self.current_video_index = idx
                            video_title = entry.get('title', f'Video {idx}')
                            print(f"\nDEBUG: Downloading video {idx}/{self.total_videos}: {video_title}")
                            self.download_started.emit(video_title)
                            self.playlist_progress.emit(idx, self.total_videos)
                            
                            # Download single video
                            ydl.download([entry['webpage_url']])
                else:
                    # Single video
                    video_title = info.get('title', 'Video')
                    video_height = info.get('height', 'unknown')
                    video_width = info.get('width', 'unknown')
                    print(f"DEBUG: Single video detected")
                    print(f"  Title: {video_title}")
                    print(f"  Available resolution: {video_width}x{video_height}")
                    print(f"  Starting download...\n")
                    self.download_started.emit(video_title)
                    ydl.download([self.url])
            
            # Emit completion signal
            if not self.is_cancelled:
                print(f"\n{'+'*60}")
                print(f"DEBUG: Download completed successfully!")
                print(f"  Type: {'Playlist' if self.total_videos > 1 else 'Single video'}")
                print(f"  Count: {self.total_videos}")
                print(f"  Path: {self.download_path}")
                print(f"{'+'*60}\n")
                self.download_completed.emit({
                    'success': True,
                    'path': self.download_path,
                    'type': 'playlist' if self.total_videos > 1 else 'video',
                    'count': self.total_videos
                })
        
        except Exception as e:
            if not self.is_cancelled:
                print(f"\n{'!'*60}")
                print(f"DEBUG: Download ERROR!")
                print(f"  Error: {str(e)}")
                print(f"{'!'*60}\n")
                self.download_error.emit(str(e))
    
    def _get_ydl_options(self) -> Dict[str, Any]:
        """Get yt-dlp configuration options based on format and quality."""
        base_opts = {
            'progress_hooks': [self.progress_hook],
            'outtmpl': os.path.join(self.download_path, '%(title)s.%(ext)s'),
            'quiet': False,
            'no_warnings': False,
        }
        
        print(f"\n{'='*60}")
        print(f"DEBUG: Configuring download options")
        print(f"  Format Type: {self.format_type}")
        print(f"  Quality: {self.quality}")
        
        if self.format_type == 'mp3':
            # Audio download options
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
            })
            print(f"  Format String: bestaudio/best")
            print(f"  Mode: Audio extraction (MP3)")
        else:
            # Video download options with proper audio merging
            # Use flexible format selection that falls back gracefully
            if self.quality == 'best':
                # Best available quality with audio
                base_opts['format'] = 'bestvideo+bestaudio/best'
                print(f"  Format String: bestvideo+bestaudio/best")
                print(f"  Mode: Best available quality")
            else:
                # Specific quality with multiple fallback options
                # IMPORTANT: Always include audio in all fallback options
                height = self.quality.replace('p', '')
                format_string = (
                    # Option 1: Best video at quality + best audio (separate streams)
                    f'bestvideo[height<={height}]+bestaudio[ext=m4a]/bestvideo[height<={height}]+bestaudio/'
                    # Option 2: Combined format that already has audio at quality
                    f'best[height<={height}][vcodec^=avc1]/'
                    # Option 3: Any video at quality + any audio
                    f'worstvideo[height<={height}]+bestaudio/'
                    # Option 4: Last resort - best combined format at quality
                    f'best[height<={height}]'
                )
                base_opts['format'] = format_string
                print(f"  Height Limit: {height}p")
                print(f"  Format String: {format_string}")
                print(f"  Mode: Quality-limited video with audio in all fallbacks")
            
            # Merge video and audio if separate
            base_opts['merge_output_format'] = 'mp4'
            
            # CRITICAL: Ensure FFmpeg merges audio properly
            base_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            
            # Add audio codec preference to ensure audio is included
            base_opts['prefer_ffmpeg'] = True
            
            print(f"  Output Format: MP4 (with FFmpeg audio merging)")
            print(f"  Audio: Guaranteed in all options")
        
        print(f"{'='*60}\n")
        return base_opts


class DownloadManager(QObject):
    """
    Main download manager that coordinates download operations.
    Manages worker threads and provides a clean interface for the UI.
    """
    
    # Signals
    progress_updated = Signal(dict)
    download_started = Signal(str)
    download_completed = Signal(dict)
    download_error = Signal(str)
    playlist_progress = Signal(int, int)
    
    def __init__(self):
        super().__init__()
        self.worker: Optional[DownloadWorker] = None
        self.thread: Optional[QThread] = None
    
    def start_download(self, url: str, download_path: str, format_type: str, quality: str = "best"):
        """
        Start a new download operation.
        
        Args:
            url: YouTube video or playlist URL
            download_path: Directory to save downloaded files
            format_type: 'mp3' for audio, 'mp4' for video
            quality: 'sd' or 'hd' (only for video)
        """
        # Clean up any existing download
        self.cleanup()
        
        # Create worker and thread
        self.worker = DownloadWorker(url, download_path, format_type, quality)
        self.thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self.worker.progress_updated.connect(self.progress_updated)
        self.worker.download_started.connect(self.download_started)
        self.worker.download_completed.connect(self._on_download_completed)
        self.worker.download_error.connect(self._on_download_error)
        self.worker.playlist_progress.connect(self.playlist_progress)
        
        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        
        # Start the thread
        self.thread.start()
    
    def cancel_download(self):
        """Cancel the current download operation."""
        if self.worker:
            self.worker.cancel()
        self.cleanup()
    
    def cleanup(self):
        """Clean up worker and thread."""
        if self.thread and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        
        self.worker = None
        self.thread = None
    
    def _on_download_completed(self, result: dict):
        """Handle download completion."""
        self.download_completed.emit(result)
        self.cleanup()
    
    def _on_download_error(self, error: str):
        """Handle download error."""
        self.download_error.emit(error)
        self.cleanup()
    
    def is_downloading(self) -> bool:
        """Check if a download is currently in progress."""
        return self.thread is not None and self.thread.isRunning()
