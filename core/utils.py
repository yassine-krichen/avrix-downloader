"""
Utility functions for YouTube downloader.
Includes URL validation, configuration management, and helper functions.
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import urlparse, parse_qs


class ConfigManager:
    """Manages application configuration and settings persistence."""
    
    DEFAULT_CONFIG = {
        'download_path': str(Path.home() / 'Downloads' / 'YoutubeDownloader'),
        'format_type': 'mp4',
        'quality': 'hd',
        'last_url': '',
        'download_subtitles': False,
        'subtitle_languages': 'en',
        'embed_thumbnail': False,
        'notifications_enabled': True
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        if config_path is None:
            config_dir = Path(__file__).parent.parent / 'config'
            config_dir.mkdir(exist_ok=True)
            config_path = config_dir / 'settings.json'
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file, or create default if doesn't exist."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print(f"Error loading config: {e}. Using defaults.")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set a configuration value and save."""
        self.config[key] = value
        self._save_config(self.config)
    
    def update(self, **kwargs):
        """Update multiple configuration values at once."""
        self.config.update(kwargs)
        self._save_config(self.config)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config.copy()


class URLValidator:
    """Validates and analyzes YouTube URLs."""
    
    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r'(https?://)?(www\.)?youtube\.com/watch\?v=[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/playlist\?list=[\w-]+',
        r'(https?://)?(www\.)?youtu\.be/[\w-]+',
        r'(https?://)?(www\.)?youtube\.com/shorts/[\w-]+',
    ]
    
    @staticmethod
    def is_valid_youtube_url(url: str) -> bool:
        """
        Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to validate
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        if not url or not url.strip():
            return False
        
        url = url.strip()
        
        for pattern in URLValidator.YOUTUBE_PATTERNS:
            if re.match(pattern, url):
                return True
        
        return False
    
    @staticmethod
    def is_playlist(url: str) -> bool:
        """
        Check if URL is a YouTube playlist.
        
        Args:
            url: URL to check
            
        Returns:
            True if playlist URL, False otherwise
        """
        if not url:
            return False
        
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Check for playlist parameter
        if 'list' in query_params:
            return True
        
        # Check for playlist in path
        if '/playlist' in parsed.path:
            return True
        
        return False
    
    @staticmethod
    def get_url_type(url: str) -> str:
        """
        Get the type of YouTube URL.
        
        Args:
            url: URL to analyze
            
        Returns:
            'playlist', 'video', or 'invalid'
        """
        if not URLValidator.is_valid_youtube_url(url):
            return 'invalid'
        
        if URLValidator.is_playlist(url):
            return 'playlist'
        
        return 'video'


def format_bytes(bytes_value: float) -> str:
    """
    Format bytes to human-readable string.
    
    Args:
        bytes_value: Number of bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    if bytes_value == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    unit_index = 0
    
    while bytes_value >= 1024 and unit_index < len(units) - 1:
        bytes_value /= 1024
        unit_index += 1
    
    return f"{bytes_value:.2f} {units[unit_index]}"


def format_speed(speed: float) -> str:
    """
    Format download speed to human-readable string.
    
    Args:
        speed: Speed in bytes per second
        
    Returns:
        Formatted string (e.g., "1.5 MB/s")
    """
    if speed == 0:
        return "0 B/s"
    
    return f"{format_bytes(speed)}/s"


def format_time(seconds: int) -> str:
    """
    Format time in seconds to human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string (e.g., "1h 23m 45s" or "23m 45s" or "45s")
    """
    if seconds < 0:
        return "Unknown"
    
    if seconds < 60:
        return f"{seconds}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{minutes}m {seconds}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    return f"{hours}h {minutes}m {seconds}s"


def ensure_directory_exists(path: str) -> bool:
    """
    Ensure a directory exists, create it if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}")
        return False


def get_default_download_path() -> str:
    """
    Get the default download path for the application.
    
    Returns:
        Default download directory path
    """
    default_path = Path.home() / 'Downloads' / 'YoutubeDownloader'
    ensure_directory_exists(str(default_path))
    return str(default_path)
