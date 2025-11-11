"""
Queue item data model for download queue.
Represents a single download task with all its properties.
"""

from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class QueueItemStatus(Enum):
    """Status of a queue item."""
    PENDING = "pending"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class QueueItem:
    """
    Represents a single download item in the queue.
    Immutable data structure following the Data Transfer Object pattern.
    """
    
    # Unique identifier
    id: str
    
    # Download parameters
    url: str
    download_path: str
    format_type: str  # 'mp3' or 'mp4'
    quality: str
    
    # Metadata
    title: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[int] = None
    url_type: Optional[str] = None  # 'video' or 'playlist'
    
    # Status tracking
    status: QueueItemStatus = QueueItemStatus.PENDING
    progress: float = 0.0
    error_message: Optional[str] = None
    
    # Timestamps
    added_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Statistics
    file_size: Optional[int] = None
    download_speed: Optional[float] = None
    
    def __post_init__(self):
        """Initialize computed fields."""
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.added_at is None:
            self.added_at = datetime.now().isoformat()
    
    @classmethod
    def create(
        cls,
        url: str,
        download_path: str,
        format_type: str,
        quality: str,
        title: Optional[str] = None,
        url_type: Optional[str] = None
    ) -> 'QueueItem':
        """
        Factory method to create a new queue item.
        
        Args:
            url: YouTube URL
            download_path: Destination path
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            title: Optional video title
            url_type: Optional URL type ('video' or 'playlist')
            
        Returns:
            New QueueItem instance
        """
        return cls(
            id=str(uuid.uuid4()),
            url=url,
            download_path=download_path,
            format_type=format_type,
            quality=quality,
            title=title,
            url_type=url_type,
            added_at=datetime.now().isoformat()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for serialization.
        
        Returns:
            Dictionary representation
        """
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'QueueItem':
        """
        Create instance from dictionary.
        
        Args:
            data: Dictionary with queue item data
            
        Returns:
            QueueItem instance
        """
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = QueueItemStatus(data['status'])
        return cls(**data)
    
    def update_status(self, status: QueueItemStatus) -> 'QueueItem':
        """
        Create a new instance with updated status.
        
        Args:
            status: New status
            
        Returns:
            New QueueItem with updated status
        """
        data = asdict(self)
        data['status'] = status
        
        # Update timestamps
        if status == QueueItemStatus.DOWNLOADING and not self.started_at:
            data['started_at'] = datetime.now().isoformat()
        elif status in [QueueItemStatus.COMPLETED, QueueItemStatus.FAILED, QueueItemStatus.CANCELLED]:
            data['completed_at'] = datetime.now().isoformat()
        
        return QueueItem(**data)
    
    def update_progress(self, progress: float, speed: Optional[float] = None) -> 'QueueItem':
        """
        Create a new instance with updated progress.
        
        Args:
            progress: Progress percentage (0-100)
            speed: Optional download speed
            
        Returns:
            New QueueItem with updated progress
        """
        data = asdict(self)
        data['progress'] = progress
        if speed is not None:
            data['download_speed'] = speed
        return QueueItem(**data)
    
    def with_error(self, error_message: str) -> 'QueueItem':
        """
        Create a new instance with error.
        
        Args:
            error_message: Error message
            
        Returns:
            New QueueItem with error
        """
        data = asdict(self)
        data['status'] = QueueItemStatus.FAILED
        data['error_message'] = error_message
        data['completed_at'] = datetime.now().isoformat()
        return QueueItem(**data)
    
    def is_active(self) -> bool:
        """Check if item is actively downloading."""
        return self.status == QueueItemStatus.DOWNLOADING
    
    def is_pending(self) -> bool:
        """Check if item is waiting to download."""
        return self.status == QueueItemStatus.PENDING
    
    def is_finished(self) -> bool:
        """Check if item is in a terminal state."""
        return self.status in [
            QueueItemStatus.COMPLETED,
            QueueItemStatus.FAILED,
            QueueItemStatus.CANCELLED
        ]
    
    def can_retry(self) -> bool:
        """Check if item can be retried."""
        return self.status in [QueueItemStatus.FAILED, QueueItemStatus.CANCELLED]
