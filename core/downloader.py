"""
YouTube downloader core module using yt-dlp.
Follows SOLID principles and modular design.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import yt_dlp
from PySide6.QtCore import QObject, Signal, QThread

from core.format_builder import FormatBuilder, FormatOptions
from core.filename_generator import FilenameGenerator
from core.logger import get_logger


class DownloadWorker(QObject):
    """
    Worker class to handle downloads in a separate thread.
    Single Responsibility: Execute download operations.
    """
    
    # Signals for progress updates
    progress_updated = Signal(dict)
    download_started = Signal(str)
    download_completed = Signal(dict)
    download_error = Signal(str)
    playlist_progress = Signal(int, int)
    
    def __init__(self, url: str, download_path: str, format_type: str, quality: str = "best"):
        super().__init__()
        self.url = url
        self.download_path = download_path
        self.format_type = format_type
        self.quality = quality
        self.is_cancelled = False
        self.current_video_index = 0
        self.total_videos = 1
        self.logger = get_logger()
        
    def progress_hook(self, d: Dict[str, Any]):
        """Hook called by yt-dlp to report download progress."""
        if self.is_cancelled:
            raise Exception("Download cancelled by user")
            
        if d['status'] == 'downloading':
            progress_info = self._create_progress_info(d)
            self.progress_updated.emit(progress_info)
            
        elif d['status'] == 'finished':
            self.progress_updated.emit({
                'status': 'finished',
                'filename': d.get('filename', ''),
                'percent': 100.0
            })
    
    def _create_progress_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create progress information dictionary from yt-dlp data.
        
        Args:
            data: Raw data from yt-dlp
            
        Returns:
            Formatted progress information
        """
        progress_info = {
            'status': 'downloading',
            'downloaded_bytes': data.get('downloaded_bytes', 0),
            'total_bytes': data.get('total_bytes') or data.get('total_bytes_estimate', 0),
            'speed': data.get('speed', 0),
            'eta': data.get('eta', 0),
            'filename': data.get('filename', ''),
            'percent': 0.0
        }
        
        # Calculate percentage
        if progress_info['total_bytes'] > 0:
            progress_info['percent'] = (
                progress_info['downloaded_bytes'] / progress_info['total_bytes']
            ) * 100
        
        return progress_info
    
    def cancel(self):
        """Cancel the current download."""
        self.is_cancelled = True
        self.logger.info("Download cancelled by user")
    
    def run(self):
        """Main download execution method."""
        try:
            self._log_download_start()
            self._ensure_directory_exists()
            
            # Build yt-dlp options
            ydl_opts = self._build_ydl_options()
            
            # Execute download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = self._extract_video_info(ydl)
                
                if self._is_playlist(info):
                    self._download_playlist(ydl, info)
                else:
                    self._download_single_video(ydl, info)
            
            # Emit completion signal
            if not self.is_cancelled:
                self._emit_completion()
        
        except Exception as e:
            if not self.is_cancelled:
                self._emit_error(e)
    
    def _log_download_start(self):
        """Log download start information."""
        self.logger.info(
            "Starting download",
            URL=self.url,
            Path=self.download_path,
            Format=self.format_type,
            Quality=self.quality
        )
    
    def _ensure_directory_exists(self):
        """Create download directory if it doesn't exist."""
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
    
    def _build_ydl_options(self) -> Dict[str, Any]:
        """
        Build yt-dlp options using FormatBuilder.
        
        Returns:
            Dictionary of yt-dlp options
        """
        # Generate filename template
        filename_template = FilenameGenerator.generate_template(
            self.format_type,
            self.quality
        )
        
        # Create format options
        format_options = FormatOptions(
            format_type=self.format_type,
            quality=self.quality,
            download_path=self.download_path,
            filename_template=filename_template
        )
        
        # Build options using builder
        builder = FormatBuilder(format_options)
        options = builder.build()
        
        # Add progress hook
        options['progress_hooks'] = [self.progress_hook]
        
        # Log configuration
        debug_info = builder.get_debug_info()
        self.logger.debug("Download configuration", **debug_info)
        
        return options
    
    def _extract_video_info(self, ydl: yt_dlp.YoutubeDL) -> Dict[str, Any]:
        """
        Extract video information without downloading.
        
        Args:
            ydl: YoutubeDL instance
            
        Returns:
            Video information dictionary
        """
        self.logger.debug("Extracting video information")
        return ydl.extract_info(self.url, download=False)
    
    def _is_playlist(self, info: Dict[str, Any]) -> bool:
        """
        Check if the URL is a playlist.
        
        Args:
            info: Video information
            
        Returns:
            True if playlist, False otherwise
        """
        return 'entries' in info
    
    def _download_playlist(self, ydl: yt_dlp.YoutubeDL, info: Dict[str, Any]):
        """
        Download all videos in a playlist.
        
        Args:
            ydl: YoutubeDL instance
            info: Playlist information
        """
        self.total_videos = len(info['entries'])
        self.playlist_progress.emit(0, self.total_videos)
        self.logger.info(f"Detected playlist with {self.total_videos} videos")
        
        for idx, entry in enumerate(info['entries'], 1):
            if self.is_cancelled:
                break
                
            if entry:
                self._download_playlist_entry(ydl, entry, idx)
    
    def _download_playlist_entry(self, ydl: yt_dlp.YoutubeDL, entry: Dict[str, Any], index: int):
        """
        Download a single entry from a playlist.
        
        Args:
            ydl: YoutubeDL instance
            entry: Playlist entry information
            index: Current video index
        """
        self.current_video_index = index
        video_title = entry.get('title', f'Video {index}')
        
        self.logger.debug(f"Downloading video {index}/{self.total_videos}: {video_title}")
        self.download_started.emit(video_title)
        self.playlist_progress.emit(index, self.total_videos)
        
        ydl.download([entry['webpage_url']])
    
    def _download_single_video(self, ydl: yt_dlp.YoutubeDL, info: Dict[str, Any]):
        """
        Download a single video.
        
        Args:
            ydl: YoutubeDL instance
            info: Video information
        """
        video_title = info.get('title', 'Video')
        video_height = info.get('height', 'unknown')
        video_width = info.get('width', 'unknown')
        
        self.logger.debug(
            "Single video detected",
            Title=video_title,
            Resolution=f"{video_width}x{video_height}"
        )
        
        self.download_started.emit(video_title)
        ydl.download([self.url])
    
    def _emit_completion(self):
        """Emit download completion signal."""
        result = {
            'success': True,
            'path': self.download_path,
            'type': 'playlist' if self.total_videos > 1 else 'video',
            'count': self.total_videos
        }
        
        self.logger.info(
            "Download completed successfully",
            Type=result['type'],
            Count=result['count'],
            Path=result['path']
        )
        
        self.download_completed.emit(result)
    
    def _emit_error(self, error: Exception):
        """
        Emit download error signal.
        
        Args:
            error: Exception that occurred
        """
        error_message = str(error)
        self.logger.error("Download error", Error=error_message)
        self.download_error.emit(error_message)


class DownloadManager(QObject):
    """
    Download manager that coordinates download operations.
    Single Responsibility: Manage worker threads and provide UI interface.
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
        self.logger = get_logger()
    
    def start_download(self, url: str, download_path: str, format_type: str, quality: str = "best"):
        """
        Start a new download operation.
        
        Args:
            url: YouTube video or playlist URL
            download_path: Directory to save downloaded files
            format_type: 'mp3' for audio, 'mp4' for video
            quality: Quality setting for video
        """
        # Clean up any existing download
        self.cleanup()
        
        # Create worker and thread
        self.worker = DownloadWorker(url, download_path, format_type, quality)
        self.thread = QThread()
        
        # Move worker to thread
        self.worker.moveToThread(self.thread)
        
        # Connect signals
        self._connect_worker_signals()
        
        # Connect thread signals
        self.thread.started.connect(self.worker.run)
        
        # Start the thread
        self.thread.start()
        self.logger.info("Download thread started")
    
    def _connect_worker_signals(self):
        """Connect worker signals to manager signals."""
        self.worker.progress_updated.connect(self.progress_updated)
        self.worker.download_started.connect(self.download_started)
        self.worker.download_completed.connect(self._on_download_completed)
        self.worker.download_error.connect(self._on_download_error)
        self.worker.playlist_progress.connect(self.playlist_progress)
    
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
