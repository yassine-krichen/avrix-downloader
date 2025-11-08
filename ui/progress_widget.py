"""
Progress widget for displaying download progress.
Shows current video progress and overall playlist progress.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt
from core.utils import format_bytes, format_speed, format_time


class ProgressWidget(QWidget):
    """Widget for displaying download progress with detailed information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.reset()
    
    def setup_ui(self):
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Current video section
        self.video_frame = QFrame()
        self.video_frame.setFrameShape(QFrame.StyledPanel)
        video_layout = QVBoxLayout(self.video_frame)
        
        # Video title label
        self.title_label = QLabel("Ready to download")
        self.title_label.setWordWrap(True)
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.title_label.setFont(font)
        video_layout.addWidget(self.title_label)
        
        # Video progress bar
        self.video_progress = QProgressBar()
        self.video_progress.setMinimum(0)
        self.video_progress.setMaximum(100)
        self.video_progress.setValue(0)
        self.video_progress.setTextVisible(True)
        self.video_progress.setFormat("%p%")
        video_layout.addWidget(self.video_progress)
        
        # Progress details (speed, size, ETA)
        details_layout = QHBoxLayout()
        
        self.speed_label = QLabel("Speed: --")
        self.speed_label.setMinimumWidth(120)
        details_layout.addWidget(self.speed_label)
        
        self.size_label = QLabel("Size: --")
        self.size_label.setMinimumWidth(150)
        details_layout.addWidget(self.size_label)
        
        self.eta_label = QLabel("ETA: --")
        self.eta_label.setMinimumWidth(100)
        details_layout.addWidget(self.eta_label)
        
        details_layout.addStretch()
        video_layout.addLayout(details_layout)
        
        layout.addWidget(self.video_frame)
        
        # Playlist progress section (hidden by default)
        self.playlist_frame = QFrame()
        self.playlist_frame.setFrameShape(QFrame.StyledPanel)
        self.playlist_frame.hide()
        playlist_layout = QVBoxLayout(self.playlist_frame)
        
        self.playlist_label = QLabel("Playlist Progress")
        font = self.playlist_label.font()
        font.setBold(True)
        self.playlist_label.setFont(font)
        playlist_layout.addWidget(self.playlist_label)
        
        self.playlist_progress = QProgressBar()
        self.playlist_progress.setMinimum(0)
        self.playlist_progress.setMaximum(100)
        self.playlist_progress.setValue(0)
        self.playlist_progress.setTextVisible(True)
        self.playlist_progress.setFormat("0 / 0")
        playlist_layout.addWidget(self.playlist_progress)
        
        layout.addWidget(self.playlist_frame)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
    
    def reset(self):
        """Reset all progress displays."""
        self.title_label.setText("Ready to download")
        self.video_progress.setValue(0)
        self.speed_label.setText("Speed: --")
        self.size_label.setText("Size: --")
        self.eta_label.setText("ETA: --")
        self.status_label.setText("")
        self.hide_playlist_progress()
    
    def update_progress(self, progress_info: dict):
        """
        Update progress display with new information.
        
        Args:
            progress_info: Dictionary containing progress data
        """
        status = progress_info.get('status', '')
        
        if status == 'downloading':
            percent = progress_info.get('percent', 0)
            self.video_progress.setValue(int(percent))
            
            # Update speed
            speed = progress_info.get('speed', 0)
            if speed > 0:
                self.speed_label.setText(f"Speed: {format_speed(speed)}")
            
            # Update size
            downloaded = progress_info.get('downloaded_bytes', 0)
            total = progress_info.get('total_bytes', 0)
            if total > 0:
                self.size_label.setText(
                    f"Size: {format_bytes(downloaded)} / {format_bytes(total)}"
                )
            elif downloaded > 0:
                self.size_label.setText(f"Downloaded: {format_bytes(downloaded)}")
            
            # Update ETA
            eta = progress_info.get('eta', 0)
            if eta > 0:
                self.eta_label.setText(f"ETA: {format_time(eta)}")
        
        elif status == 'finished':
            self.video_progress.setValue(100)
            self.speed_label.setText("Speed: --")
            self.eta_label.setText("ETA: Complete")
    
    def set_current_video(self, title: str):
        """
        Set the current video being downloaded.
        
        Args:
            title: Video title
        """
        self.title_label.setText(f"Downloading: {title}")
        self.video_progress.setValue(0)
        self.speed_label.setText("Speed: --")
        self.size_label.setText("Size: --")
        self.eta_label.setText("ETA: --")
    
    def show_playlist_progress(self):
        """Show the playlist progress bar."""
        self.playlist_frame.show()
    
    def hide_playlist_progress(self):
        """Hide the playlist progress bar."""
        self.playlist_frame.hide()
    
    def update_playlist_progress(self, current: int, total: int):
        """
        Update playlist progress.
        
        Args:
            current: Current video index (1-based)
            total: Total number of videos
        """
        self.show_playlist_progress()
        self.playlist_progress.setMaximum(total)
        self.playlist_progress.setValue(current)
        self.playlist_progress.setFormat(f"{current} / {total}")
        self.playlist_label.setText(f"Playlist Progress ({current}/{total})")
    
    def set_status(self, message: str, is_error: bool = False):
        """
        Set status message.
        
        Args:
            message: Status message to display
            is_error: Whether this is an error message
        """
        self.status_label.setText(message)
        if is_error:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
    
    def clear_status(self):
        """Clear the status message."""
        self.status_label.setText("")
        self.status_label.setStyleSheet("")
