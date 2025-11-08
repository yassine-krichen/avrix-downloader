"""
Main window for YouTube downloader application.
Uses facade pattern for clean architecture and SOLID principles.
"""

import os
import subprocess
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QFileDialog, QMessageBox, QGroupBox, QRadioButton,
    QButtonGroup
)
from PySide6.QtCore import Qt, Slot

from core.facade import DownloaderFacade
from ui.progress_widget import ProgressWidget
from ui.ui_state_manager import UIStateManager, UIState


class MainWindow(QMainWindow):
    """
    Refactored main application window.
    Uses facade pattern for simplified interaction with core services.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize facade (single entry point to core services)
        self.facade = DownloaderFacade(enable_logging=True)
        
        # Set up UI
        self.setup_ui()
        
        # Initialize UI state manager
        self.ui_state = UIStateManager({
            'download_button': self.download_button,
            'cancel_button': self.cancel_button,
            'url_input': self.url_input,
            'mp4_radio': self.mp4_radio,
            'mp3_radio': self.mp3_radio,
            'quality_combo': self.quality_combo,
            'browse_button': self.browse_button,
            'open_folder_button': self.open_folder_button,
        })
        
        # Connect signals and load settings
        self.connect_signals()
        self.load_settings()
        
        # Set initial state
        self.ui_state.set_state(UIState.READY, is_video=True)
    
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
        self._setup_title(main_layout)
        
        # URL input section
        self._setup_url_section(main_layout)
        
        # Format selection section
        self._setup_format_section(main_layout)
        
        # Destination folder section
        self._setup_destination_section(main_layout)
        
        # Progress section
        self._setup_progress_section(main_layout)
        
        # Control buttons
        self._setup_control_buttons(main_layout)
    
    def _setup_title(self, layout: QVBoxLayout):
        """Set up title label."""
        title_label = QLabel("YouTube Downloader")
        font = title_label.font()
        font.setPointSize(16)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
    
    def _setup_url_section(self, layout: QVBoxLayout):
        """Set up URL input section."""
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
        layout.addWidget(url_group)
    
    def _setup_format_section(self, layout: QVBoxLayout):
        """Set up format selection section."""
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
        
        # Quality selection
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality:"))
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Best Available (Highest Quality)", "best")
        self.quality_combo.addItem("4K - 2160p", "2160p")
        self.quality_combo.addItem("2K - 1440p", "1440p")
        self.quality_combo.addItem("Full HD - 1080p", "1080p")
        self.quality_combo.addItem("HD - 720p", "720p")
        self.quality_combo.addItem("SD - 480p", "480p")
        self.quality_combo.addItem("360p", "360p")
        self.quality_combo.addItem("240p", "240p")
        self.quality_combo.addItem("144p", "144p")
        self.quality_combo.setMinimumWidth(250)
        quality_layout.addWidget(self.quality_combo)
        quality_layout.addStretch()
        
        format_layout.addLayout(quality_layout)
        
        # Connect format change
        self.mp4_radio.toggled.connect(self.on_format_changed)
        self.mp3_radio.toggled.connect(self.on_format_changed)
        
        layout.addWidget(format_group)
    
    def _setup_destination_section(self, layout: QVBoxLayout):
        """Set up destination folder section."""
        dest_group = QGroupBox("Destination Folder")
        dest_layout = QHBoxLayout(dest_group)
        
        self.dest_input = QLineEdit()
        self.dest_input.setReadOnly(True)
        dest_layout.addWidget(self.dest_input)
        
        self.browse_button = QPushButton("Browse...")
        self.browse_button.clicked.connect(self.browse_destination)
        self.browse_button.setMinimumWidth(100)
        dest_layout.addWidget(self.browse_button)
        
        layout.addWidget(dest_group)
    
    def _setup_progress_section(self, layout: QVBoxLayout):
        """Set up progress section."""
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        
        layout.addWidget(progress_group)
    
    def _setup_control_buttons(self, layout: QVBoxLayout):
        """Set up control buttons."""
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
        button_layout.addWidget(self.cancel_button)
        
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setMinimumWidth(120)
        self.open_folder_button.setMinimumHeight(40)
        self.open_folder_button.clicked.connect(self.open_download_folder)
        button_layout.addWidget(self.open_folder_button)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def connect_signals(self):
        """Connect download manager signals to slots."""
        manager = self.facade.get_download_manager()
        manager.progress_updated.connect(self.on_progress_updated)
        manager.download_started.connect(self.on_download_started)
        manager.download_completed.connect(self.on_download_completed)
        manager.download_error.connect(self.on_download_error)
        manager.playlist_progress.connect(self.on_playlist_progress)
    
    def load_settings(self):
        """Load saved settings from configuration."""
        settings = self.facade.get_all_settings()
        
        # Load download path
        self.dest_input.setText(settings.download_path)
        
        # Load format type
        if settings.format_type == 'mp3':
            self.mp3_radio.setChecked(True)
        else:
            self.mp4_radio.setChecked(True)
        
        # Load quality
        index = self.quality_combo.findData(settings.quality)
        if index >= 0:
            self.quality_combo.setCurrentIndex(index)
        
        # Load last URL
        if settings.last_url:
            self.url_input.setText(settings.last_url)
    
    def save_settings(self):
        """Save current settings to configuration."""
        self.facade.update_settings(
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
        
        url_type = self.facade.get_url_type(url)
        
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
        # Get download options
        url = self.url_input.text().strip()
        dest_path = self.dest_input.text()
        format_type = 'mp3' if self.mp3_radio.isChecked() else 'mp4'
        quality = self.quality_combo.currentData() if self.mp4_radio.isChecked() else 'best'
        
        # Validate using facade
        is_valid, error_message = self.facade.validate_download_options(
            url, dest_path, format_type, quality
        )
        
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_message)
            return
        
        # Save settings
        self.save_settings()
        
        # Update UI state
        self.ui_state.set_state(UIState.DOWNLOADING)
        
        # Reset progress
        self.progress_widget.reset()
        self.progress_widget.clear_status()
        
        # Start download through facade
        self.facade.start_download(url, dest_path, format_type, quality)
    
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
            self.facade.cancel_download()
            self.ui_state.set_state(UIState.READY, is_video=self.mp4_radio.isChecked())
            self.progress_widget.set_status("Download cancelled", is_error=True)
    
    @Slot()
    def open_download_folder(self):
        """Open the download folder in file explorer."""
        dest_path = self.dest_input.text()
        if os.path.exists(dest_path):
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
        self.ui_state.set_state(UIState.COMPLETED)
        
        download_type = result.get('type', 'video')
        count = result.get('count', 1)
        
        message = (
            f"Successfully downloaded {count} videos from playlist!"
            if download_type == 'playlist'
            else "Download completed successfully!"
        )
        
        self.progress_widget.set_status(message, is_error=False)
        
        QMessageBox.information(self, "Download Complete", message)
    
    @Slot(str)
    def on_download_error(self, error: str):
        """Handle download errors."""
        self.ui_state.set_state(UIState.ERROR)
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
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.facade.is_downloading():
            reply = QMessageBox.question(
                self,
                "Download in Progress",
                "A download is currently in progress. Are you sure you want to quit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
            
            self.facade.cancel_download()
        
        event.accept()
