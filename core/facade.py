"""
Application facade to simplify interaction with core services.
Follows the Facade pattern to provide a simple interface.
"""

from typing import Tuple, Optional
from pathlib import Path

from core.downloader import DownloadManager
from core.utils import ConfigManager, URLValidator
from core.settings_service import SettingsService, JsonSettingsRepository, AppSettings
from core.validators import URLInputValidator, PathValidator, DownloadOptionsValidator
from core.logger import get_logger, set_logger, ConsoleLogger


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
            last_url=''
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
        
        self.logger.info("Application initialized")
    
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
        quality: str
    ):
        """
        Start a download operation.
        
        Args:
            url: YouTube URL
            destination_path: Download destination
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
        """
        self.download_manager.start_download(
            url,
            destination_path,
            format_type,
            quality
        )
    
    def cancel_download(self):
        """Cancel the current download."""
        self.download_manager.cancel_download()
    
    def is_downloading(self) -> bool:
        """Check if a download is in progress."""
        return self.download_manager.is_downloading()
    
    def get_download_manager(self) -> DownloadManager:
        """
        Get the download manager for signal connections.
        
        Returns:
            DownloadManager instance
        """
        return self.download_manager
