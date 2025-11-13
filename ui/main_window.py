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
    QButtonGroup, QTabWidget, QMenu, QToolButton, QCheckBox, QSpinBox
)
from PySide6.QtCore import Qt, Slot, QUrl, QSize
from PySide6.QtGui import QIcon, QDragEnterEvent, QDropEvent, QAction, QFont

from core.facade import DownloaderFacade
from core.queue_item import QueueItem
from core.notification_service import NotificationService
from ui.progress_widget import ProgressWidget
from ui.queue_widget import QueueWidget
from ui.ui_state_manager import UIStateManager, UIState
from ui.theme_manager import ThemeManager, ThemeMode


class MainWindow(QMainWindow):
    """
    Refactored main application window.
    Uses facade pattern for simplified interaction with core services.
    """
    
    def __init__(self):
        super().__init__()
        
        # Initialize theme manager
        self.theme_manager = ThemeManager()
        
        # Initialize facade (single entry point to core services)
        self.facade = DownloaderFacade(enable_logging=True)
        
        # Set up UI
        self.setup_ui()
        
        # Apply theme
        saved_theme = self.theme_manager.load_theme()
        self.theme_manager.apply_theme(saved_theme)
        
        # Initialize notification service
        app_icon = self.windowIcon() if self.windowIcon() else None
        self.notification_service = NotificationService(app_icon)
        self.facade.set_notification_service(self.notification_service)
        
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
            'subtitle_checkbox': self.subtitle_checkbox,
            'thumbnail_checkbox': self.thumbnail_checkbox,
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
        self.setWindowTitle("YouTube Downloader Pro")
        self.setMinimumWidth(700)
        self.setMinimumHeight(850)
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Set window icon if available
        icon_path = "assets/icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path)) 
        
        # Create menu bar
        self._setup_menu_bar()
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Title
        self._setup_title(main_layout)
        
        # URL input section
        self._setup_url_section(main_layout)
        
        # Format selection section
        self._setup_format_section(main_layout)
        
        # Destination folder section
        self._setup_destination_section(main_layout)
        
        # Tabs for progress and queue (give it stretch priority)
        self._setup_tabs_section(main_layout)
        
        # Control buttons
        self._setup_control_buttons(main_layout)
    
    def _setup_menu_bar(self):
        """Set up the menu bar."""
        menubar = self.menuBar()
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        # Theme submenu
        theme_menu = QMenu("Theme", self)
        
        light_action = QAction("Light Mode", self)
        light_action.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeMode.LIGHT))
        theme_menu.addAction(light_action)
        
        dark_action = QAction("Dark Mode", self)
        dark_action.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeMode.DARK))
        theme_menu.addAction(dark_action)
        
        system_action = QAction("Follow System", self)
        system_action.triggered.connect(lambda: self.theme_manager.apply_theme(ThemeMode.SYSTEM))
        theme_menu.addAction(system_action)
        
        view_menu.addMenu(theme_menu)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
    
    def _setup_title(self, layout: QVBoxLayout):
        """Set up title label with branding."""
        title_widget = QWidget()
        title_layout = QVBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 10, 0, 5)
        title_layout.setSpacing(2)
        
        # Title
        title_label = QLabel("YouTube Downloader Pro")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        # Subtitle
        subtitle_label = QLabel("Professional video & audio download manager")
        subtitle_label.setObjectName("subtitleLabel")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)
        
        layout.addWidget(title_widget)
    
    def _setup_url_section(self, layout: QVBoxLayout):
        """Set up URL input section."""
        url_group = QGroupBox("Source")
        url_layout = QVBoxLayout(url_group)
        url_layout.setSpacing(5)
        url_layout.setContentsMargins(10, 8, 10, 10)
        
        # Header with info button
        header_layout = QHBoxLayout()
        header_label = QLabel("Enter YouTube URL")
        header_label.setObjectName("sectionHeader")
        header_layout.addWidget(header_label)
        
        # Info button
        info_button = QToolButton()
        info_button.setText("?")
        info_button.setToolTip(
            "Supported formats:\n"
            "• Single video URL\n"
            "• Playlist URL\n"
            "• Channel URL\n\n"
            "You can also drag and drop URLs from your browser"
        )
        info_button.setObjectName("infoButton")
        info_button.setCursor(Qt.CursorShape.WhatsThisCursor)
        header_layout.addWidget(info_button)
        header_layout.addStretch()
        
        url_layout.addLayout(header_layout)
        
        # URL input
        url_input_layout = QHBoxLayout()
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self.url_input.textChanged.connect(self.on_url_changed)
        url_input_layout.addWidget(self.url_input)
        
        # URL type indicator (minimal)
        self.url_type_label = QLabel("")
        self.url_type_label.setObjectName("urlTypeLabel")
        self.url_type_label.setMinimumWidth(100)
        url_input_layout.addWidget(self.url_type_label)
        
        url_layout.addLayout(url_input_layout)
        layout.addWidget(url_group)
    
    def _setup_format_section(self, layout: QVBoxLayout):
        """Set up format selection section."""
        format_group = QGroupBox("Download Configuration")
        format_layout = QVBoxLayout(format_group)
        format_layout.setSpacing(5)
        format_layout.setContentsMargins(10, 8, 10, 10)
        
        # Single row: Format type and Quality selection side by side
        config_row = QHBoxLayout()
        config_row.setSpacing(20)
        
        # Left side: Format type (MP3/MP4)
        format_container = QVBoxLayout()
        format_container.setSpacing(3)
        
        format_type_layout = QHBoxLayout()
        format_label = QLabel("Format")
        format_label.setObjectName("sectionHeader")
        format_type_layout.addWidget(format_label)
        
        # Info button for format
        format_info = QToolButton()
        format_info.setText("?")
        format_info.setToolTip(
            "MP4: Download full video with audio\n"
            "MP3: Extract audio only (ideal for music)"
        )
        format_info.setObjectName("infoButton")
        format_info.setCursor(Qt.CursorShape.WhatsThisCursor)
        format_type_layout.addWidget(format_info)
        format_type_layout.addStretch()
        format_container.addLayout(format_type_layout)
        
        # Radio buttons
        self.format_button_group = QButtonGroup()
        self.mp4_radio = QRadioButton("Video (MP4)")
        self.mp3_radio = QRadioButton("Audio (MP3)")
        self.mp4_radio.setChecked(True)
        
        self.format_button_group.addButton(self.mp4_radio)
        self.format_button_group.addButton(self.mp3_radio)
        
        format_container.addWidget(self.mp4_radio)
        format_container.addWidget(self.mp3_radio)
        
        config_row.addLayout(format_container)
        
        # Right side: Quality selection
        quality_container = QVBoxLayout()
        quality_container.setSpacing(3)
        
        quality_header = QHBoxLayout()
        quality_label = QLabel("Quality")
        quality_label.setObjectName("sectionHeader")
        quality_header.addWidget(quality_label)
        
        # Info button for quality
        quality_info = QToolButton()
        quality_info.setText("?")
        quality_info.setToolTip(
            "Available qualities:\n"
            "• Best: Highest quality available\n"
            "• 4K (2160p): Ultra HD\n"
            "• 2K (1440p): Quad HD\n"
            "• 1080p: Full HD\n"
            "• 720p: HD\n"
            "• 480p and below: SD\n\n"
            "Note: Quality depends on source video"
        )
        quality_info.setObjectName("infoButton")
        quality_info.setCursor(Qt.CursorShape.WhatsThisCursor)
        quality_header.addWidget(quality_info)
        quality_header.addStretch()
        quality_container.addLayout(quality_header)
        
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("Best Available", "best")
        self.quality_combo.addItem("2160p (4K)", "2160p")
        self.quality_combo.addItem("1440p (2K)", "1440p")
        self.quality_combo.addItem("1080p (Full HD)", "1080p")
        self.quality_combo.addItem("720p (HD)", "720p")
        self.quality_combo.addItem("480p (SD)", "480p")
        self.quality_combo.addItem("360p", "360p")
        self.quality_combo.addItem("240p", "240p")
        self.quality_combo.addItem("144p", "144p")
        self.quality_combo.setMinimumWidth(180)
        quality_container.addWidget(self.quality_combo)
        
        config_row.addLayout(quality_container)
        config_row.addStretch()
        
        format_layout.addLayout(config_row)
        
        # Download options (Subtitles and Thumbnails on same row)
        options_layout = QHBoxLayout()
        options_layout.setContentsMargins(0, 8, 0, 0)
        
        # Subtitle option
        self.subtitle_checkbox = QCheckBox("Download Subtitles")
        self.subtitle_checkbox.setToolTip(
            "Download available subtitles for the video.\n"
            "Video (MP4): Embedded in video file\n"
            "Audio (MP3): Saved as separate .srt file"
        )
        options_layout.addWidget(self.subtitle_checkbox)
        
        # Info button for subtitles
        subtitle_info = QToolButton()
        subtitle_info.setText("?")
        subtitle_info.setToolTip(
            "Downloads available subtitles/closed captions.\n"
            "Language: English (en) by default.\n"
            "Includes auto-generated subtitles if manual ones unavailable.\n\n"
            "For videos: Subtitles embedded in MP4 file.\n"
            "For audio: Subtitles saved as separate .srt file."
        )
        subtitle_info.setObjectName("infoButton")
        subtitle_info.setCursor(Qt.CursorShape.WhatsThisCursor)
        options_layout.addWidget(subtitle_info)
        
        # Add spacing between the two options
        options_layout.addSpacing(30)
        
        # Thumbnail embedding option
        self.thumbnail_checkbox = QCheckBox("Embed Thumbnail")
        self.thumbnail_checkbox.setToolTip(
            "Automatically embed video thumbnail in audio files.\n"
            "Note: Only works for audio (MP3) format."
        )
        options_layout.addWidget(self.thumbnail_checkbox)
        
        # Info button for thumbnails
        thumbnail_info = QToolButton()
        thumbnail_info.setText("?")
        thumbnail_info.setToolTip(
            "Embeds the video thumbnail as album artwork in audio files.\n"
            "This adds the thumbnail image as metadata (ID3 tags) in MP3 files.\n\n"
            "Note: This feature only applies to audio (MP3) downloads.\n"
            "For videos, thumbnails are not embedded."
        )
        thumbnail_info.setObjectName("infoButton")
        thumbnail_info.setCursor(Qt.CursorShape.WhatsThisCursor)
        options_layout.addWidget(thumbnail_info)
        
        options_layout.addStretch()
        
        format_layout.addLayout(options_layout)
        
        # Connect format change
        self.mp4_radio.toggled.connect(self.on_format_changed)
        self.mp3_radio.toggled.connect(self.on_format_changed)
        
        layout.addWidget(format_group)
    
    def _setup_destination_section(self, layout: QVBoxLayout):
        """Set up destination folder section."""
        dest_group = QGroupBox("Output Location")
        dest_layout = QVBoxLayout(dest_group)
        dest_layout.setSpacing(5)
        dest_layout.setContentsMargins(10, 8, 10, 10)
        
        # Single row: Label with info + Path input + Browse button
        path_layout = QHBoxLayout()
        
        # Label with info button
        label_container = QHBoxLayout()
        label_container.setSpacing(3)
        header_label = QLabel("Path")
        header_label.setObjectName("sectionHeader")
        label_container.addWidget(header_label)
        
        dest_info = QToolButton()
        dest_info.setText("?")
        dest_info.setToolTip(
            "Select where downloaded files will be saved.\n"
            "Folder will be created if it doesn't exist."
        )
        dest_info.setObjectName("infoButton")
        dest_info.setCursor(Qt.CursorShape.WhatsThisCursor)
        label_container.addWidget(dest_info)
        
        path_layout.addLayout(label_container)
        
        # Path input
        self.dest_input = QLineEdit()
        self.dest_input.setReadOnly(True)
        path_layout.addWidget(self.dest_input, 1)
        
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_destination)
        self.browse_button.setMinimumWidth(80)
        path_layout.addWidget(self.browse_button)
        
        dest_layout.addLayout(path_layout)
        
        layout.addWidget(dest_group)
    
    def _setup_tabs_section(self, layout: QVBoxLayout):
        """Set up tabs for progress and queue."""
        tab_widget = QTabWidget()
        tab_widget.setMinimumHeight(250)  # Ensure minimum visible height
        
        # Progress tab
        progress_tab = QWidget()
        progress_layout = QVBoxLayout(progress_tab)
        progress_layout.setContentsMargins(5, 5, 5, 5)
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        tab_widget.addTab(progress_tab, "Current Download")
        
        # Queue tab
        queue_tab = QWidget()
        queue_layout = QVBoxLayout(queue_tab)
        queue_layout.setContentsMargins(5, 5, 5, 5)
        
        # Concurrent downloads setting
        concurrent_layout = QHBoxLayout()
        concurrent_layout.setContentsMargins(0, 0, 0, 8)
        
        concurrent_label = QLabel("Concurrent Downloads:")
        concurrent_label.setToolTip("Maximum number of simultaneous downloads (1-10)")
        concurrent_layout.addWidget(concurrent_label)
        
        self.concurrent_spinbox = QSpinBox()
        self.concurrent_spinbox.setRange(1, 10)
        self.concurrent_spinbox.setValue(3)
        self.concurrent_spinbox.setToolTip("1 = Sequential (one at a time)\n3 = Default (recommended)\n5+ = High performance (more CPU/network)")
        self.concurrent_spinbox.valueChanged.connect(self.on_concurrent_changed)
        concurrent_layout.addWidget(self.concurrent_spinbox)
        
        concurrent_layout.addStretch()
        queue_layout.addLayout(concurrent_layout)
        
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
        
        # Give the tab widget stretch priority so it takes up remaining space
        layout.addWidget(tab_widget, 1)
    
    def _setup_progress_section(self, layout: QVBoxLayout):
        """Set up progress section."""
        progress_group = QGroupBox("Download Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.progress_widget = ProgressWidget()
        progress_layout.addWidget(self.progress_widget)
        
        layout.addWidget(progress_group)
    
    def _setup_control_buttons(self, layout: QVBoxLayout):
        """Set up control buttons with minimal styling."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        self.download_button = QPushButton("Start Download")
        self.download_button.setMinimumHeight(40)
        self.download_button.setObjectName("primaryButton")
        self.download_button.clicked.connect(self.start_download)
        self.download_button.setToolTip("Begin downloading immediately")
        button_layout.addWidget(self.download_button)
        
        self.add_to_queue_button = QPushButton("Add to Queue")
        self.add_to_queue_button.setMinimumHeight(45)
        self.add_to_queue_button.setObjectName("secondaryButton")
        self.add_to_queue_button.clicked.connect(self.add_to_queue)
        self.add_to_queue_button.setToolTip("Add to download queue for batch processing")
        button_layout.addWidget(self.add_to_queue_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setMinimumHeight(45)
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.cancel_download)
        self.cancel_button.setToolTip("Stop current download")
        button_layout.addWidget(self.cancel_button)
        
        self.open_folder_button = QPushButton("Open Folder")
        self.open_folder_button.setMinimumHeight(45)
        self.open_folder_button.setObjectName("secondaryButton")
        self.open_folder_button.clicked.connect(self.open_download_folder)
        self.open_folder_button.setToolTip("Open download location in file explorer")
        button_layout.addWidget(self.open_folder_button)
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
        
        # Load subtitle settings
        download_subtitles = self.facade.get_setting('download_subtitles', False)
        self.subtitle_checkbox.setChecked(download_subtitles)
        
        # Load thumbnail settings
        embed_thumbnail = self.facade.get_setting('embed_thumbnail', False)
        self.thumbnail_checkbox.setChecked(embed_thumbnail)
        
        # Load concurrent downloads setting
        max_concurrent = self.facade.get_setting('max_concurrent_downloads', 3)
        self.concurrent_spinbox.setValue(max_concurrent)
        self.facade.set_max_concurrent_downloads(max_concurrent)
    
    def save_settings(self):
        """Save current settings to configuration."""
        self.facade.update_settings(
            download_path=self.dest_input.text(),
            format_type='mp3' if self.mp3_radio.isChecked() else 'mp4',
            quality=self.quality_combo.currentData(),
            last_url=self.url_input.text(),
            download_subtitles=self.subtitle_checkbox.isChecked(),
            embed_thumbnail=self.thumbnail_checkbox.isChecked(),
            max_concurrent_downloads=self.concurrent_spinbox.value()
        )
    
    @Slot()
    def on_concurrent_changed(self, value: int):
        """Handle concurrent downloads setting change."""
        self.facade.set_max_concurrent_downloads(value)
        self.save_settings()
    
    @Slot()
    def on_url_changed(self):
        """Handle URL input changes with minimal visual feedback."""
        url = self.url_input.text().strip()
        
        if not url:
            self.url_type_label.setText("")
            self.url_type_label.setStyleSheet("")
            return
        
        url_type = self.facade.get_url_type(url)
        
        if url_type == 'video':
            self.url_type_label.setText("Single Video")
            self.url_type_label.setStyleSheet("color: #1976d2; font-weight: 500;")
        elif url_type == 'playlist':
            self.url_type_label.setText("Playlist")
            self.url_type_label.setStyleSheet("color: #1976d2; font-weight: 500;")
        else:
            self.url_type_label.setText("Invalid URL")
            self.url_type_label.setStyleSheet("color: #757575; font-weight: 500;")
    
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
        self.facade.start_download(
            url, dest_path, format_type, quality,
            download_subtitles=self.subtitle_checkbox.isChecked(),
            subtitle_languages='en',
            embed_thumbnail=self.thumbnail_checkbox.isChecked()
        )
    
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
    
    @Slot(dict)
    def on_download_started(self, video_info: dict):
        """Handle download started event."""
        title = video_info.get('title', 'Unknown')
        thumbnail = video_info.get('thumbnail', '')
        self.progress_widget.set_current_video(title, thumbnail)
    
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
        
        # Show native notification instead of QMessageBox
        if self.notification_service and self.notification_service.is_enabled():
            self.notification_service.show_success(
                "Download Complete",
                message
            )
    
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
        item = self.facade.add_to_queue(
            url, dest_path, format_type, quality,
            download_subtitles=self.subtitle_checkbox.isChecked(),
            subtitle_languages='en',
            embed_thumbnail=self.thumbnail_checkbox.isChecked()
        )
        
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
        
        # Show native notification for each completed queue item
        if self.notification_service and self.notification_service.is_enabled():
            title = item.title or "Video"
            self.notification_service.show_success(
                "Download Complete",
                f"{title} downloaded successfully!"
            )
    
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
        
        # Show native notification instead of QMessageBox
        if self.notification_service and self.notification_service.is_enabled():
            if stats['failed'] > 0:
                self.notification_service.show_warning(
                    "Queue Completed",
                    f"Completed: {stats['completed']} | Failed: {stats['failed']}"
                )
            else:
                self.notification_service.show_success(
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
        
        # Clean up notification service
        if self.notification_service:
            self.notification_service.cleanup()
        
        event.accept()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event for drag and drop."""
        if event.mimeData().hasUrls() or event.mimeData().hasText():
            event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop event for drag and drop."""
        mime_data = event.mimeData()
        
        # Try to get URL from dropped data
        url = None
        if mime_data.hasUrls():
            urls = mime_data.urls()
            if urls:
                url = urls[0].toString()
        elif mime_data.hasText():
            url = mime_data.text().strip()
        
        if url:
            # Check if it's a YouTube URL
            url_type = self.facade.get_url_type(url)
            if url_type in ['video', 'playlist']:
                self.url_input.setText(url)
                event.acceptProposedAction()
                
                # Show feedback
                QMessageBox.information(
                    self,
                    "URL Added",
                    f"YouTube {url_type} URL detected and added!"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Invalid URL",
                    "Please drop a valid YouTube video or playlist URL."
                )
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h2>YouTube Downloader Pro</h2>
        <p><b>Version:</b> 2.0.0</p>
        <p><b>A powerful YouTube video and audio downloader</b></p>
        <br>
        <p><b>Features:</b></p>
        <ul>
            <li>Download videos in multiple qualities (144p to 4K)</li>
            <li>Extract audio as MP3</li>
            <li>Queue management system</li>
            <li>Playlist support</li>
            <li>Dark and light themes</li>
            <li>Drag and drop support</li>
        </ul>
        <br>
        <p><b>Built with:</b> Python, PySide6, yt-dlp</p>
        <p><b>Architecture:</b> SOLID principles, modular design</p>
        """
        
        QMessageBox.about(self, "About YouTube Downloader Pro", about_text)

