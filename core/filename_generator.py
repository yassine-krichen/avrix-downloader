"""
Filename generator for creating download filenames with quality suffixes.
Follows the Single Responsibility Principle.
"""

from typing import Optional


class FilenameGenerator:
    """
    Generates filenames with quality/format suffixes.
    Single responsibility: filename generation logic.
    """
    
    @staticmethod
    def generate_template(format_type: str, quality: Optional[str] = None) -> str:
        """
        Generate filename template for yt-dlp.
        
        Args:
            format_type: 'mp3' or 'mp4'
            quality: Quality setting (for video) or None (for audio)
            
        Returns:
            Filename template string for yt-dlp
        """
        if format_type == 'mp3':
            return '%(title)s [MP3-192k].%(ext)s'
        else:
            # For video, add quality suffix
            quality_suffix = FilenameGenerator._format_quality_suffix(quality)
            return f'%(title)s [{quality_suffix}].%(ext)s'
    
    @staticmethod
    def _format_quality_suffix(quality: Optional[str]) -> str:
        """
        Format quality into a readable suffix.
        
        Args:
            quality: Quality setting (e.g., '1080p', 'best')
            
        Returns:
            Formatted quality suffix
        """
        if not quality or quality == 'best':
            return 'Best'
        return quality
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to be Windows-compatible.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace Windows-invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename
