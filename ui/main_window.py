"""
Main window for YouTube downloader application.
Provides the user interface for downloading videos and playlists.
"""

import os
import subprocess
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QButtonGroup
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon

from core.downloader import DownloadManager
from core.utils import ConfigManager, URLValidator
from ui.progress_widget import ProgressWidget


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.download_manager = DownloadManager()
        self.is_downloading = False
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        
        # Title
        title_label = QLabel("YouTube Downloader")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # URL input section
        url_group = QGroupBox("Video/Playlist URL")
        url_layout = QVBoxLayout(url_group)
        
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste YouTube video or playlist URL here...")
        self.url_input.textChanged.connect(self.on_url_changed)
        url_input_layout.addWidget(self.url_input)
        
        self.url_type_label = QLabel("")
        self.url_type_label.setMinimumWidth(80)
        url_input_layout.addWidget(self.url_type_label)
        
        url_layout.addLayout(url_input_layout)
        main_layout.addWidget(url_group)
        
        # Format selection section
        format_group = QGroupBox("Download Options")
        format_layout = QVBoxLayout(format_group)
        
        # Format type (MP3/MP4)
        format_type_layout = QHBoxLayout()
        format_type_layout.addWidget(QLabel("Format:"))
        
        self.format_button_group = QButtonGroup()
        self.mp4_radio = QRadioButton("MP4 (Video)")
        self.mp3_radio = QRadioButton("MP3 (Audio)")
        self.mp4_radio.setChecked(True)
        
        self.format_button_group.addButton(self.mp4_radio)
        self.format_button_group.addButton(self.mp3_radio)
        
        format_type_layout.addWidget(self.mp4_radio)
        format_type_layout.addWidget(self.mp3_radio)
        format_type_layout.addStretch()
        
        format_layout.addLayout(format_type_layout)
        
        # Quality selection (for video only)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("High Definition (HD - 1080p)", "hd")
        self.quality_combo.addItem("Standard Definition (SD - 480p)", "sd")
        self.quality_combo.setMinimumWidth(250)
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        
        format_layout.addLayout(quality_layout)
        
        # Connect format change to enable/disable quality
        self.mp4_radio.toggled.connect(self.on_format_changed)
        self.mp3_radio.toggled.connect(self.on_format_changed)
        
        main_layout.addWidget(format_group)
        
        # Destination folder section
        dest_group = QGroupBox("Destination Folder")
        dest_layout = QHBoxLayout(dest_group)
        
        self.dest_input = QLineEdit()
        self.dest_input.setReadOnly(True)
        dest_layout.addWidget(self.dest_input)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_destination)
        self.browse_button.setMinimumWidth(100)
        dest_layout.addWidget(self.browse_button)
        
        main_layout.addWidget(dest_group)
        
        # Progress section
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        
        main_layout.addWidget(progress_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.download_button = QPushButton("Start Download")
        self.download_button.setMinimumWidth(150)
        self.download_button.setMinimumHeight(40)
        self.download_button.clicked.connect(self.start_download)
        button_layout.addWidget(self.download_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumWidth(100)
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setMinimumWidth(120)
        self.open_folder_button.setMinimumHeight(40)
        self.open_folder_button.clicked.connect(self.open_download_folder)
        self.open_folder_button.setEnabled(False)
        button_layout.addWidget(self.open_folder_button)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # Apply initial format state
        self.on_format_changed()
    
    def connect_signals(self):
        """Connect download manager signals to slots."""
        self.download_manager.progress_updated.connect(self.on_progress_updated)
        self.download_manager.download_started.connect(self.on_download_started)
        self.download_manager.download_completed.connect(self.on_download_completed)
        self.download_manager.download_error.connect(self.on_download_error)
        self.download_manager.playlist_progress.connect(self.on_playlist_progress)
    
    def load_settings(self):
        """Load saved settings from configuration."""
        # Load download path
        download_path = self.config.get('download_path')
        self.dest_input.setText(download_path)
        
        # Load format type
        format_type = self.config.get('format_type', 'mp4')
        if format_type == 'mp3':
            self.mp3_radio.setChecked(True)
        else:
            self.mp4_radio.setChecked(True)
        
        # Load quality
        quality = self.config.get('quality', 'hd')
        index = self.quality_combo.findData(quality)
        if index >= 0:
            self.quality_combo.setCurrentIndex(index)
        
        # Load last URL
        last_url = self.config.get('last_url', '')
        if last_url:
            self.url_input.setText(last_url)
    
    def save_settings(self):
        """Save current settings to configuration."""
        self.config.update(
            download_path=self.dest_input.text(),
            format_type='mp3' if self.mp3_radio.isChecked() else 'mp4',
            quality=self.quality_combo.currentData(),
            last_url=self.url_input.text()
        )
    
    @Slot()
    def on_url_changed(self):
        """Handle URL input changes."""
        url = self.url_input.text().strip()
        
        if not url:
            self.url_type_label.setText("")
            return
        
        url_type = URLValidator.get_url_type(url)
        
        if url_type == 'video':
            self.url_type_label.setText("📹 Video")
            self.url_type_label.setStyleSheet("color: blue; font-weight: bold;")
        elif url_type == 'playlist':
            self.url_type_label.setText("📋 Playlist")
            self.url_type_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.url_type_label.setText("❌ Invalid")
            self.url_type_label.setStyleSheet("color: red; font-weight: bold;")
    
    @Slot()
    def on_format_changed(self):
        """Handle format type changes."""
        is_video = self.mp4_radio.isChecked()
        self.quality_combo.setEnabled(is_video)
    
    @Slot()
    def browse_destination(self):
        """Open folder browser dialog."""
        current_path = self.dest_input.text()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Destination Folder",
            current_path
        )
        
        if folder:
            self.dest_input.setText(folder)
    
    @Slot()
    def start_download(self):
        """Start the download process."""
        # Validate URL
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a YouTube URL.")
            return
        
        if not URLValidator.is_valid_youtube_url(url):
            QMessageBox.warning(
                self,
                "Invalid URL",
                "Please enter a valid YouTube video or playlist URL."
            )
            return
        
        # Validate destination
        dest_path = self.dest_input.text()
        if not dest_path:
            QMessageBox.warning(self, "Input Error", "Please select a destination folder.")
            return
        
        # Get download options
        format_type = 'mp3' if self.mp3_radio.isChecked() else 'mp4'
        quality = self.quality_combo.currentData() if self.mp4_radio.isChecked() else 'best'
        
        # Save settings
        self.save_settings()
        
        # Update UI state
        self.is_downloading = True
        self.download_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.url_input.setEnabled(False)
        self.mp4_radio.setEnabled(False)
        self.mp3_radio.setEnabled(False)
        self.quality_combo.setEnabled(False)
        self.browse_button.setEnabled(False)
        self.open_folder_button.setEnabled(False)
        
        # Reset progress
        self.progress_widget.reset()
        self.progress_widget.clear_status()
        
        # Start download
        self.download_manager.start_download(url, dest_path, format_type, quality)
    
    @Slot()
    def cancel_download(self):
        """Cancel the current download."""
        reply = QMessageBox.question(
            self,
            "Cancel Download",
            "Are you sure you want to cancel the download?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.download_manager.cancel_download()
            self.reset_ui_state()
            self.progress_widget.set_status("Download cancelled", is_error=True)
    
    @Slot()
    def open_download_folder(self):
        """Open the download folder in file explorer."""
        dest_path = self.dest_input.text()
        if os.path.exists(dest_path):
            # Open folder in file explorer (cross-platform)
            if os.name == 'nt':  # Windows
                os.startfile(dest_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.run(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', dest_path])
    
    @Slot(dict)
    def on_progress_updated(self, progress_info: dict):
        """Handle progress updates."""
        self.progress_widget.update_progress(progress_info)
    
    @Slot(str)
    def on_download_started(self, title: str):
        """Handle download started event."""
        self.progress_widget.set_current_video(title)
    
    @Slot(dict)
    def on_download_completed(self, result: dict):
        """Handle download completion."""
        self.reset_ui_state()
        
        download_type = result.get('type', 'video')
        count = result.get('count', 1)
        
        if download_type == 'playlist':
            message = f"Successfully downloaded {count} videos from playlist!"
        else:
            message = "Download completed successfully!"
        
        self.progress_widget.set_status(message, is_error=False)
        self.open_folder_button.setEnabled(True)
        
        QMessageBox.information(
            self,
            "Download Complete",
            message
        )
    
    @Slot(str)
    def on_download_error(self, error: str):
        """Handle download errors."""
        self.reset_ui_state()
        self.progress_widget.set_status(f"Error: {error}", is_error=True)
        
        QMessageBox.critical(
            self,
            "Download Error",
            f"An error occurred during download:\n\n{error}"
        )
    
    @Slot(int, int)
    def on_playlist_progress(self, current: int, total: int):
        """Handle playlist progress updates."""
        self.progress_widget.update_playlist_progress(current, total)
    
    def reset_ui_state(self):
        """Reset UI to ready state."""
        self.is_downloading = False
        self.download_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.url_input.setEnabled(True)
        self.mp4_radio.setEnabled(True)
        self.mp3_radio.setEnabled(True)
        self.quality_combo.setEnabled(self.mp4_radio.isChecked())
        self.browse_button.setEnabled(True)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_downloading:
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "A download is currently in progress. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.download_manager.cancel_download()
        
        event.accept()
