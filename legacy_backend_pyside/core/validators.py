"""
Input validation service.
Follows Single Responsibility Principle - only validates inputs.
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple
import os
from pathlib import Path


class ValidationResult:
    """Result of a validation operation."""
    
    def __init__(self, is_valid: bool, error_message: Optional[str] = None):
        self.is_valid = is_valid
        self.error_message = error_message
    
    def __bool__(self):
        """Allow using ValidationResult in boolean context."""
        return self.is_valid


class IValidator(ABC):
    """Interface for validators (Interface Segregation Principle)."""
    
    @abstractmethod
    def validate(self, value: any) -> ValidationResult:
        """Validate a value."""
        pass


class URLInputValidator(IValidator):
    """Validates URL inputs."""
    
    def __init__(self, url_validator):
        """
        Initialize with a URL validator.
        
        Args:
            url_validator: URLValidator instance for checking YouTube URLs
        """
        self.url_validator = url_validator
    
    def validate(self, url: str) -> ValidationResult:
        """
        Validate URL input.
        
        Args:
            url: URL to validate
            
        Returns:
            ValidationResult
        """
        if not url or not url.strip():
            return ValidationResult(False, "Please enter a YouTube URL.")
        
        if not self.url_validator.is_valid_youtube_url(url):
            return ValidationResult(
                False,
                "Please enter a valid YouTube video or playlist URL."
            )
        
        return ValidationResult(True)


class PathValidator(IValidator):
    """Validates file system paths."""
    
    def validate(self, path: str) -> ValidationResult:
        """
        Validate path input.
        
        Args:
            path: Path to validate
            
        Returns:
            ValidationResult
        """
        if not path or not path.strip():
            return ValidationResult(False, "Please select a destination folder.")
        
        # Try to create the path if it doesn't exist
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return ValidationResult(True)
        except Exception as e:
            return ValidationResult(
                False,
                f"Invalid destination path: {str(e)}"
            )


class DownloadOptionsValidator:
    """
    Validates complete download options.
    Composite validator that uses multiple validators.
    """
    
    def __init__(self, url_validator, path_validator: PathValidator):
        self.url_validator = url_validator
        self.path_validator = path_validator
    
    def validate_all(
        self,
        url: str,
        destination_path: str,
        format_type: str,
        quality: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate all download options.
        
        Args:
            url: YouTube URL
            destination_path: Download destination path
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate URL
        url_result = self.url_validator.validate(url)
        if not url_result:
            return False, url_result.error_message
        
        # Validate path
        path_result = self.path_validator.validate(destination_path)
        if not path_result:
            return False, path_result.error_message
        
        # Validate format and quality
        if format_type not in ['mp3', 'mp4']:
            return False, "Invalid format type selected."
        
        # All validations passed
        return True, None
