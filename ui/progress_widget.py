"""
Progress widget for displaying download progress.
Shows current video progress and overall playlist progress.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QProgressBar, QFrame
)
from PySide6.QtCore import Qt, QUrl, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply
from core.utils import format_bytes, format_speed, format_time


class ProgressWidget(QWidget):
    """Widget for displaying download progress with detailed information."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.network_manager = QNetworkAccessManager(self)
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
        video_layout.setContentsMargins(10, 10, 10, 10)
        video_layout.setSpacing(8)
        
        # Main horizontal layout: Thumbnail on left, content on right
        main_layout = QHBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Thumbnail (left side) - increased size
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(160, 120)  # 4:3 aspect ratio, larger
        self.thumbnail_label.setScaledContents(True)
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        self.thumbnail_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.thumbnail_label.setText("No\nThumbnail")
        main_layout.addWidget(self.thumbnail_label, 0, Qt.AlignmentFlag.AlignTop)
        
        # Right side content - constrained to thumbnail height
        content_widget = QWidget()
        content_widget.setMaximumHeight(120)  # Match thumbnail height
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)
        
        # Status and Title
        self.title_label = QLabel("Ready to download")
        self.title_label.setWordWrap(True)
        self.title_label.setMaximumHeight(45)  # Limit title height to allow room for other elements
        font = self.title_label.font()
        font.setBold(True)
        font.setPointSize(10)
        self.title_label.setFont(font)
        content_layout.addWidget(self.title_label)
        
        # Add spacing
        content_layout.addSpacing(5)
        
        # Progress details (Speed, Size, ETA) - horizontal
        details_layout = QHBoxLayout()
        details_layout.setSpacing(15)
        
        self.speed_label = QLabel("Speed: --")
        self.speed_label.setMaximumHeight(20)
        details_layout.addWidget(self.speed_label)
        
        self.size_label = QLabel("Size: --")
        self.size_label.setMaximumHeight(20)
        details_layout.addWidget(self.size_label)
        
        self.eta_label = QLabel("ETA: --")
        self.eta_label.setMaximumHeight(20)
        details_layout.addWidget(self.eta_label)
        
        details_layout.addStretch()
        content_layout.addLayout(details_layout)
        
        # Add spacing
        content_layout.addSpacing(5)
        
        # Progress bar (spans full width of content area)
        self.video_progress = QProgressBar()
        self.video_progress.setMinimum(0)
        self.video_progress.setMaximum(100)
        self.video_progress.setValue(0)
        self.video_progress.setTextVisible(True)
        self.video_progress.setFormat("%p%")
        self.video_progress.setFixedHeight(24)
        content_layout.addWidget(self.video_progress)
        
        # Push everything to the top
        content_layout.addStretch()
        
        main_layout.addWidget(content_widget, 1)
        video_layout.addLayout(main_layout)
        
        layout.addWidget(self.video_frame)
        
        # Playlist progress section (hidden by default)
        self.playlist_frame = QFrame()
        self.playlist_frame.setFrameShape(QFrame.StyledPanel)
        self.playlist_frame.hide()
        playlist_layout = QVBoxLayout(self.playlist_frame)
        playlist_layout.setContentsMargins(10, 8, 10, 8)
        
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
    
    def reset(self):
        """Reset all progress displays."""
        self.title_label.setText("Ready to download")
        self.video_progress.setValue(0)
        self.speed_label.setText("Speed: --")
        self.size_label.setText("Size: --")
        self.eta_label.setText("ETA: --")
        self.hide_playlist_progress()
        self.clear_thumbnail()
    
    def clear_thumbnail(self):
        """Clear the thumbnail display."""
        self.thumbnail_label.clear()
        self.thumbnail_label.setStyleSheet("""
            QLabel {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
        """)
        self.thumbnail_label.setText("No\nThumbnail")
    
    def load_thumbnail(self, url: str):
        """
        Load thumbnail from URL.
        
        Args:
            url: Thumbnail URL
        """
        if not url:
            self.clear_thumbnail()
            return
        
        request = QNetworkRequest(QUrl(url))
        reply = self.network_manager.get(request)
        reply.finished.connect(lambda: self._on_thumbnail_loaded(reply))
    
    @Slot()
    def _on_thumbnail_loaded(self, reply: QNetworkReply):
        """Handle thumbnail loaded from network."""
        if reply.error() == QNetworkReply.NetworkError.NoError:
            data = reply.readAll()
            pixmap = QPixmap()
            if pixmap.loadFromData(data):
                # Scale to fit while maintaining aspect ratio
                scaled_pixmap = pixmap.scaled(
                    self.thumbnail_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.thumbnail_label.setPixmap(scaled_pixmap)
                self.thumbnail_label.setStyleSheet("""
                    QLabel {
                        border: 1px solid #e0e0e0;
                        border-radius: 4px;
                    }
                """)
        else:
            self.clear_thumbnail()
        
        reply.deleteLater()
    
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
    
    def set_current_video(self, title: str, thumbnail_url: str = None):
        """
        Set the current video being downloaded.
        
        Args:
            title: Video title
            thumbnail_url: Optional thumbnail URL
        """
        self.title_label.setText(f"Downloading: {title}")
        self.video_progress.setValue(0)
        self.speed_label.setText("Speed: --")
        self.size_label.setText("Size: --")
        self.eta_label.setText("ETA: --")
        
        # Load thumbnail if provided
        if thumbnail_url:
            self.load_thumbnail(thumbnail_url)
        else:
            self.clear_thumbnail()
    
    def set_completed(self, title: str):
        """
        Set the display to show a completed download.
        
        Args:
            title: Video title
        """
        self.title_label.setText(f"Completed: {title}")
        self.video_progress.setValue(100)
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
