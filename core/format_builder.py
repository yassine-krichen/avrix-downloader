"""
Format builder for creating yt-dlp format strings.
Follows the Strategy pattern for different download strategies.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class FormatOptions:
    """Data class for format configuration options."""
    format_type: str  # 'mp3' or 'mp4'
    quality: str      # Quality setting
    download_path: str
    filename_template: str
    
    
class FormatStrategy(ABC):
    """Abstract base class for format strategies (Strategy Pattern)."""
    
    @abstractmethod
    def get_format_string(self) -> str:
        """Get the yt-dlp format string."""
        pass
    
    @abstractmethod
    def get_postprocessors(self) -> list:
        """Get the list of postprocessors."""
        pass
    
    @abstractmethod
    def get_additional_options(self) -> Dict[str, Any]:
        """Get additional yt-dlp options."""
        pass


class AudioFormatStrategy(FormatStrategy):
    """Strategy for audio (MP3) downloads."""
    
    def __init__(self, bitrate: str = "192"):
        self.bitrate = bitrate
    
    def get_format_string(self) -> str:
        """Get audio format string."""
        return 'bestaudio/best'
    
    def get_postprocessors(self) -> list:
        """Get audio extraction postprocessor."""
        return [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': self.bitrate,
        }]
    
    def get_additional_options(self) -> Dict[str, Any]:
        """No additional options for audio."""
        return {}


class VideoFormatStrategy(FormatStrategy):
    """Strategy for video (MP4) downloads with quality control."""
    
    def __init__(self, quality: str = "best"):
        self.quality = quality
    
    def get_format_string(self) -> str:
        """Get video format string with audio and quality fallbacks."""
        if self.quality == 'best':
            return (
                'bestvideo+bestaudio[ext=m4a]/'
                'bestvideo+bestaudio/'
                'best'
            )
        else:
            # Extract height from quality (e.g., "1080p" -> "1080")
            height = self.quality.replace('p', '')
            return (
                f'bestvideo[height<={height}]+bestaudio[ext=m4a]/'
                f'bestvideo[height<={height}]+bestaudio/'
                f'best[height<={height}][vcodec^=avc1]/'
                f'worstvideo[height<={height}]+bestaudio/'
                f'best[height<={height}]'
            )
    
    def get_postprocessors(self) -> list:
        """Get video conversion postprocessor."""
        return [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }]
    
    def get_additional_options(self) -> Dict[str, Any]:
        """Get video-specific options."""
        return {
            'merge_output_format': 'mp4',
            'prefer_ffmpeg': True,
        }


class FormatBuilder:
    """
    Builder for constructing yt-dlp options.
    Follows the Builder pattern for complex object creation.
    """
    
    def __init__(self, format_options: FormatOptions):
        self.format_options = format_options
        self.strategy = self._select_strategy()
    
    def _select_strategy(self) -> FormatStrategy:
        """Select appropriate format strategy based on format type."""
        if self.format_options.format_type == 'mp3':
            return AudioFormatStrategy()
        else:
            return VideoFormatStrategy(self.format_options.quality)
    
    def build(self) -> Dict[str, Any]:
        """
        Build complete yt-dlp options dictionary.
        
        Returns:
            Dictionary of yt-dlp options
        """
        import os
        
        # Base options
        options = {
            'outtmpl': os.path.join(
                self.format_options.download_path,
                self.format_options.filename_template
            ),
            'quiet': False,
            'no_warnings': False,
            'restrictfilenames': False,
            'windowsfilenames': True,
        }
        
        # Add format-specific options
        options['format'] = self.strategy.get_format_string()
        options['postprocessors'] = self.strategy.get_postprocessors()
        options.update(self.strategy.get_additional_options())
        
        return options
    
    def get_debug_info(self) -> Dict[str, str]:
        """
        Get debug information about the format configuration.
        
        Returns:
            Dictionary with debug information
        """
        return {
            'format_type': self.format_options.format_type,
            'quality': self.format_options.quality,
            'filename_template': self.format_options.filename_template,
            'format_string': self.strategy.get_format_string(),
            'strategy': self.strategy.__class__.__name__,
        }
