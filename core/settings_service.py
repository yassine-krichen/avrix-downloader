"""
Settings service for managing application settings.
Follows Single Responsibility and Dependency Inversion principles.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class AppSettings:
    """Data class for application settings."""
    download_path: str
    format_type: str
    quality: str
    last_url: str = ""


class ISettingsRepository(ABC):
    """Interface for settings storage (Dependency Inversion Principle)."""
    
    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load settings from storage."""
        pass
    
    @abstractmethod
    def save(self, settings: Dict[str, Any]):
        """Save settings to storage."""
        pass


class SettingsService:
    """
    Service for managing application settings.
    Single Responsibility: Settings business logic.
    """
    
    def __init__(self, repository: ISettingsRepository, defaults: AppSettings):
        """
        Initialize with a settings repository.
        
        Args:
            repository: Settings storage repository
            defaults: Default settings
        """
        self.repository = repository
        self.defaults = defaults
        self._current_settings = self._load_settings()
    
    def _load_settings(self) -> AppSettings:
        """Load settings from repository with defaults fallback."""
        stored = self.repository.load()
        
        # Merge with defaults
        settings_dict = asdict(self.defaults)
        settings_dict.update(stored)
        
        return AppSettings(**settings_dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value
        """
        return getattr(self._current_settings, key, default)
    
    def get_all(self) -> AppSettings:
        """
        Get all settings.
        
        Returns:
            AppSettings instance
        """
        return self._current_settings
    
    def update(self, **kwargs):
        """
        Update multiple settings at once.
        
        Args:
            **kwargs: Settings to update
        """
        # Update current settings
        for key, value in kwargs.items():
            if hasattr(self._current_settings, key):
                setattr(self._current_settings, key, value)
        
        # Save to repository
        self.repository.save(asdict(self._current_settings))
    
    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self._current_settings = AppSettings(**asdict(self.defaults))
        self.repository.save(asdict(self._current_settings))


class JsonSettingsRepository(ISettingsRepository):
    """JSON file-based settings repository."""
    
    def __init__(self, config_manager):
        """
        Initialize with ConfigManager.
        
        Args:
            config_manager: ConfigManager instance for file operations
        """
        self.config_manager = config_manager
    
    def load(self) -> Dict[str, Any]:
        """Load settings from JSON file."""
        return self.config_manager.get_all()
    
    def save(self, settings: Dict[str, Any]):
        """Save settings to JSON file."""
        self.config_manager.config = settings
        self.config_manager._save_config(settings)
