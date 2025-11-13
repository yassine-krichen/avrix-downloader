"""
Application facade to simplify interaction with core services.
Follows the Facade pattern to provide a simple interface.
"""

from typing import Tuple, Optional, List
from pathlib import Path

from core.downloader import DownloadManager
from core.utils import ConfigManager, URLValidator
from core.settings_service import SettingsService, JsonSettingsRepository, AppSettings
from core.validators import URLInputValidator, PathValidator, DownloadOptionsValidator
from core.logger import get_logger, set_logger, ConsoleLogger
from core.download_queue import DownloadQueue
from core.queue_storage import JsonQueueStorage
from core.queue_manager import QueueManager
from core.queue_item import QueueItem
from core.notification_service import NotificationService


class DownloaderFacade:
    """
    Facade for the YouTube downloader application.
    Provides a simplified interface for the UI layer.
    """
    
    def __init__(self, enable_logging: bool = True):
        """
        Initialize the facade with all required services.
        
        Args:
            enable_logging: Whether to enable console logging
        """
        # Set up logging
        set_logger(ConsoleLogger(enabled=enable_logging))
        self.logger = get_logger()
        
        # Initialize core components
        self.config_manager = ConfigManager()
        self.url_validator = URLValidator()
        
        # Initialize settings service
        default_settings = AppSettings(
            download_path=str(Path.home() / 'Downloads' / 'YoutubeDownloader'),
            format_type='mp4',
            quality='1080p',
            last_url='',
            download_subtitles=False,
            subtitle_languages='en',
            embed_thumbnail=False,
            notifications_enabled=True,
            max_concurrent_downloads=3
        )
        settings_repo = JsonSettingsRepository(self.config_manager)
        self.settings_service = SettingsService(settings_repo, default_settings)
        
        # Initialize validators
        url_input_validator = URLInputValidator(self.url_validator)
        path_validator = PathValidator()
        self.options_validator = DownloadOptionsValidator(
            url_input_validator,
            path_validator
        )
        
        # Initialize download manager
        self.download_manager = DownloadManager()
        
        # Initialize queue system
        queue_storage = JsonQueueStorage()
        self.queue = DownloadQueue(queue_storage)
        self.queue_manager = QueueManager(self.queue, self.download_manager)
        
        # Initialize notification service (will be configured by UI)
        self.notification_service = None
        
        self.logger.info("Application initialized with queue management")
    
    # Notification operations
    def set_notification_service(self, notification_service: NotificationService):
        """
        Set the notification service.
        
        Args:
            notification_service: Notification service instance
        """
        self.notification_service = notification_service
    
    def get_notification_service(self) -> Optional[NotificationService]:
        """Get the notification service."""
        return self.notification_service
    
    # Settings operations
    def get_setting(self, key: str, default=None):
        """Get a setting value."""
        return self.settings_service.get(key, default)
    
    def get_all_settings(self) -> AppSettings:
        """Get all settings."""
        return self.settings_service.get_all()
    
    def update_settings(self, **kwargs):
        """Update settings."""
        self.settings_service.update(**kwargs)
    
    # URL validation operations
    def validate_url(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        validator = URLInputValidator(self.url_validator)
        result = validator.validate(url)
        return result.is_valid, result.error_message
    
    def get_url_type(self, url: str) -> str:
        """
        Get the type of YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            'video', 'playlist', or 'invalid'
        """
        return self.url_validator.get_url_type(url)
    
    # Download operations
    def validate_download_options(
        self,
        url: str,
        destination_path: str,
        format_type: str,
        quality: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all download options before starting download.
        
        Args:
            url: YouTube URL
            destination_path: Download destination
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return self.options_validator.validate_all(
            url,
            destination_path,
            format_type,
            quality
        )
    
    def start_download(
        self,
        url: str,
        destination_path: str,
        format_type: str,
        quality: str,
        download_subtitles: bool = False,
        subtitle_languages: str = 'en',
        embed_thumbnail: bool = False
    ):
        """
        Start a download operation (direct download, not queued).
        
        Args:
            url: YouTube URL
            destination_path: Download destination
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            download_subtitles: Whether to download subtitles
            subtitle_languages: Comma-separated language codes
            embed_thumbnail: Whether to embed thumbnail in audio files
        """
        self.download_manager.start_download(
            url,
            destination_path,
            format_type,
            quality,
            download_subtitles,
            subtitle_languages,
            embed_thumbnail
        )
    
    def cancel_download(self):
        """Cancel the current download."""
        self.download_manager.cancel_download()
    
    def is_downloading(self) -> bool:
        """Check if a download is in progress."""
        return self.download_manager.is_downloading()
    
    # Queue operations
    def add_to_queue(
        self,
        url: str,
        destination_path: str,
        format_type: str,
        quality: str,
        title: Optional[str] = None,
        download_subtitles: bool = False,
        subtitle_languages: str = 'en',
        embed_thumbnail: bool = False
    ) -> Optional[QueueItem]:
        """
        Add download to queue.
        
        Args:
            url: YouTube URL
            destination_path: Download destination
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            title: Optional video title
            download_subtitles: Whether to download subtitles
            subtitle_languages: Comma-separated language codes
            embed_thumbnail: Whether to embed thumbnail in audio files
            
        Returns:
            Created queue item or None if duplicate
        """
        url_type = self.get_url_type(url)
        return self.queue_manager.add_to_queue(
            url=url,
            download_path=destination_path,
            format_type=format_type,
            quality=quality,
            title=title,
            url_type=url_type,
            download_subtitles=download_subtitles,
            subtitle_languages=subtitle_languages,
            embed_thumbnail=embed_thumbnail
        )
    
    def remove_from_queue(self, item_id: str):
        """Remove item from queue."""
        self.queue_manager.remove_item(item_id)
    
    def retry_queue_item(self, item_id: str):
        """Retry a failed or cancelled queue item."""
        self.queue_manager.retry_item(item_id)
    
    def start_queue_processing(self):
        """Start processing the queue."""
        self.queue_manager.start_processing()
    
    def stop_queue_processing(self):
        """Stop processing the queue."""
        self.queue_manager.stop_processing()
    
    def set_max_concurrent_downloads(self, max_concurrent: int):
        """
        Set maximum concurrent downloads for queue processing.
        
        Args:
            max_concurrent: Maximum number (1-10)
        """
        self.queue_manager.set_max_concurrent(max_concurrent)
    
    def get_max_concurrent_downloads(self) -> int:
        """Get current max concurrent downloads setting."""
        return self.queue_manager.get_max_concurrent()
    
    def get_queue_items(self) -> List[QueueItem]:
        """Get all items in queue."""
        return self.queue.get_all()
    
    def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        return self.queue_manager.get_queue_stats()
    
    def clear_finished_from_queue(self):
        """Remove all finished items from queue."""
        self.queue.clear_finished()
    
    def clear_queue(self):
        """Remove all items from queue."""
        self.queue.clear_all()
    
    def move_queue_item(self, item_id: str, new_position: int) -> bool:
        """
        Move queue item to new position.
        
        Args:
            item_id: ID of item to move
            new_position: New position in queue
            
        Returns:
            True if moved successfully
        """
        return self.queue.move(item_id, new_position)
    
    def get_queue_manager(self) -> QueueManager:
        """
        Get queue manager for signal connections.
        
        Returns:
            QueueManager instance
        """
        return self.queue_manager
    
    def get_download_manager(self) -> DownloadManager:
        """
        Get the download manager for signal connections.
        
        Returns:
            DownloadManager instance
        """
        return self.download_manager
