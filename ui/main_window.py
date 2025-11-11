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
    QButtonGroup, QTabWidget
)
from PySide6.QtCore import Qt, Slot

from core.facade import DownloaderFacade
from core.queue_item import QueueItem
from ui.progress_widget import ProgressWidget
from ui.queue_widget import QueueWidget
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
            'add_to_queue_button': self.add_to_queue_button,
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
        
        # Load queue
        self.load_queue()
        
        # Set initial state
        self.ui_state.set_state(UIState.READY, is_video=True)
    
    def setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("YouTube Downloader")
        self.setMinimumWidth(700)
        self.setMinimumHeight(700)  # Increased from 500 to 700
        
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
        
        # Tabs for progress and queue
        self._setup_tabs_section(main_layout)
        
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
    
    def _setup_tabs_section(self, layout: QVBoxLayout):
        """Set up tabs for progress and queue."""
        tab_widget = QTabWidget()
        
        # Progress tab
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        tab_widget.addTab(progress_tab, "Current Download")
        
        # Queue tab
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        self.queue_widget = QueueWidget()
        queue_layout.addWidget(self.queue_widget)
        
        # Queue control buttons
        queue_control_layout = QHBoxLayout()
        queue_control_layout.addStretch()
        
        self.start_queue_button = QPushButton("Start Queue")
        self.start_queue_button.setMinimumWidth(120)
        self.start_queue_button.clicked.connect(self.start_queue_processing)
        queue_control_layout.addWidget(self.start_queue_button)
        
        self.stop_queue_button = QPushButton("Stop Queue")
        self.stop_queue_button.setMinimumWidth(120)
        self.stop_queue_button.clicked.connect(self.stop_queue_processing)
        self.stop_queue_button.setEnabled(False)
        queue_control_layout.addWidget(self.stop_queue_button)
        
        queue_control_layout.addStretch()
        queue_layout.addLayout(queue_control_layout)
        
        tab_widget.addTab(queue_tab, "Download Queue")
        
        layout.addWidget(tab_widget)
    
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
        
        self.add_to_queue_button = QPushButton("Add to Queue")
        self.add_to_queue_button.setMinimumWidth(150)
        self.add_to_queue_button.setMinimumHeight(40)
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        button_layout.addWidget(self.add_to_queue_button)
        
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
        # Download manager signals
        manager = self.facade.get_download_manager()
        manager.progress_updated.connect(self.on_progress_updated)
        manager.download_started.connect(self.on_download_started)
        manager.download_completed.connect(self.on_download_completed)
        manager.download_error.connect(self.on_download_error)
        manager.playlist_progress.connect(self.on_playlist_progress)
        
        # Queue signals (from DownloadQueue)
        queue = self.facade.queue
        queue.item_added.connect(self.on_queue_updated)
        queue.item_removed.connect(self.on_queue_updated)
        queue.item_updated.connect(self.on_queue_item_updated)
        queue.queue_changed.connect(self.on_queue_updated)  # Added for clear operations
        queue.queue_cleared.connect(self.on_queue_updated)  # Added for clear all
        
        # Queue manager signals
        queue_manager = self.facade.get_queue_manager()
        queue_manager.queue_item_started.connect(self.on_queue_item_started)
        queue_manager.queue_item_completed.connect(self.on_queue_item_completed)
        queue_manager.queue_item_failed.connect(self.on_queue_item_failed)
        queue_manager.queue_processing_finished.connect(self.on_queue_processing_finished)
        
        # Queue widget signals
        self.queue_widget.retry_requested.connect(self.retry_queue_item)
        self.queue_widget.remove_requested.connect(self.remove_from_queue)
        self.queue_widget.move_up_requested.connect(self.move_queue_item_up)
        self.queue_widget.move_down_requested.connect(self.move_queue_item_down)
        self.queue_widget.clear_finished_requested.connect(self.clear_finished_queue)
        self.queue_widget.clear_all_requested.connect(self.clear_all_queue)
    
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
    
    # Queue-related methods
    def load_queue(self):
        """Load and display queue items."""
        items = self.facade.get_queue_items()
        self.queue_widget.update_queue(items)
    
    @Slot()
    def add_to_queue(self):
        """Add current download options to queue."""
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
        
        # Add to queue through facade
        item = self.facade.add_to_queue(url, dest_path, format_type, quality)
        
        if item is None:
            QMessageBox.information(
                self,
                "Duplicate Item",
                "This URL is already in the queue."
            )
            return
        
        # Save settings
        self.save_settings()
        
        # Show confirmation
        QMessageBox.information(
            self,
            "Added to Queue",
            f"Added to queue:\n{item.title or url}"
        )
        
        # Clear URL input for next item
        self.url_input.clear()
    
    @Slot()
    def start_queue_processing(self):
        """Start processing the download queue."""
        self.facade.start_queue_processing()
        self.start_queue_button.setEnabled(False)
        self.stop_queue_button.setEnabled(True)
    
    @Slot()
    def stop_queue_processing(self):
        """Stop processing the download queue."""
        self.facade.stop_queue_processing()
        self.start_queue_button.setEnabled(True)
        self.stop_queue_button.setEnabled(False)
    
    @Slot(str)
    def retry_queue_item(self, item_id: str):
        """Retry a failed queue item."""
        self.facade.retry_queue_item(item_id)
    
    @Slot(str)
    def remove_from_queue(self, item_id: str):
        """Remove an item from queue."""
        self.facade.remove_from_queue(item_id)
    
    @Slot(str)
    def move_queue_item_up(self, item_id: str):
        """Move queue item up in priority."""
        items = self.facade.get_queue_items()
        for i, item in enumerate(items):
            if item.id == item_id and i > 0:
                self.facade.move_queue_item(item_id, i - 1)
                break
    
    @Slot(str)
    def move_queue_item_down(self, item_id: str):
        """Move queue item down in priority."""
        items = self.facade.get_queue_items()
        for i, item in enumerate(items):
            if item.id == item_id and i < len(items) - 1:
                self.facade.move_queue_item(item_id, i + 1)
                break
    
    @Slot()
    def clear_finished_queue(self):
        """Clear finished items from queue."""
        reply = QMessageBox.question(
            self,
            "Clear Finished",
            "Remove all completed items from queue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.facade.clear_finished_from_queue()
    
    @Slot()
    def clear_all_queue(self):
        """Clear all items from queue."""
        reply = QMessageBox.question(
            self,
            "Clear Queue",
            "Remove all items from queue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.facade.clear_queue()
    
    @Slot()
    def on_queue_updated(self):
        """Handle queue updates."""
        items = self.facade.get_queue_items()
        self.queue_widget.update_queue(items)
    
    @Slot(QueueItem)
    def on_queue_item_updated(self, item: QueueItem):
        """Handle individual queue item update."""
        self.queue_widget.update_item(item)
    
    @Slot(QueueItem)
    def on_queue_item_started(self, item: QueueItem):
        """Handle queue item started."""
        self.queue_widget.update_item(item)
    
    @Slot(QueueItem)
    def on_queue_item_completed(self, item: QueueItem):
        """Handle queue item completion."""
        self.queue_widget.update_item(item)
    
    @Slot(QueueItem, str)
    def on_queue_item_failed(self, item: QueueItem, error: str):
        """Handle queue item failure."""
        self.queue_widget.update_item(item)
    
    @Slot()
    def on_queue_processing_finished(self):
        """Handle queue processing completion."""
        self.start_queue_button.setEnabled(True)
        self.stop_queue_button.setEnabled(False)
        
        stats = self.facade.get_queue_stats()
        if stats['failed'] > 0:
            QMessageBox.warning(
                self,
                "Queue Completed",
                f"Queue processing finished.\n\n"
                f"Completed: {stats['completed']}\n"
                f"Failed: {stats['failed']}"
            )
        else:
            QMessageBox.information(
                self,
                "Queue Completed",
                f"All {stats['completed']} items downloaded successfully!"
            )
    
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
