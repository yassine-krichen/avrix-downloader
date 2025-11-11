"""
Queue manager that orchestrates queue and download operations.
Coordinates between queue and download manager.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal, Slot

from core.download_queue import DownloadQueue
from core.queue_item import QueueItem, QueueItemStatus
from core.downloader import DownloadManager
from core.logger import get_logger


class QueueManager(QObject):
    """
    Manages download queue and coordinates with download manager.
    Single Responsibility: Orchestrate queue processing.
    """
    
    # Signals
    queue_item_started = Signal(QueueItem)
    queue_item_completed = Signal(QueueItem)
    queue_item_failed = Signal(QueueItem, str)
    queue_item_progress = Signal(QueueItem)
    queue_processing_finished = Signal()
    
    def __init__(self, queue: DownloadQueue, download_manager: DownloadManager):
        """
        Initialize queue manager.
        
        Args:
            queue: Download queue instance
            download_manager: Download manager instance
        """
        super().__init__()
        self.queue = queue
        self.download_manager = download_manager
        self.logger = get_logger()
        
        self._current_item: Optional[QueueItem] = None
        self._is_processing = False
        self._auto_process = True
        
        # Connect download manager signals
        self._connect_download_signals()
    
    def _connect_download_signals(self):
        """Connect to download manager signals."""
        self.download_manager.download_started.connect(self._on_download_started)
        self.download_manager.download_completed.connect(self._on_download_completed)
        self.download_manager.download_error.connect(self._on_download_error)
        self.download_manager.progress_updated.connect(self._on_progress_updated)
    
    def add_to_queue(
        self,
        url: str,
        download_path: str,
        format_type: str,
        quality: str,
        title: Optional[str] = None,
        url_type: Optional[str] = None
    ) -> Optional[QueueItem]:
        """
        Add new item to queue.
        
        Args:
            url: YouTube URL
            download_path: Download destination
            format_type: Format type ('mp3' or 'mp4')
            quality: Quality setting
            title: Optional video title
            url_type: Optional URL type
            
        Returns:
            Created queue item or None if duplicate
        """
        item = QueueItem.create(
            url=url,
            download_path=download_path,
            format_type=format_type,
            quality=quality,
            title=title,
            url_type=url_type
        )
        
        if self.queue.add(item):
            self.logger.info(f"Added to queue: {title or url}")
            
            # Don't auto-start when adding to queue
            # User must explicitly start queue processing
            
            return item
        
        return None
    
    def start_processing(self):
        """Start processing queue (enable auto-processing)."""
        self._auto_process = True
        if not self._is_processing:
            self.process_queue()
    
    def stop_processing(self):
        """Stop processing queue (disable auto-processing)."""
        self._auto_process = False
    
    def process_queue(self):
        """Process next item in queue."""
        if self._is_processing:
            self.logger.debug("Already processing a download")
            return
        
        is_busy = self.download_manager.is_downloading()
        self.logger.debug(f"Download manager busy status: {is_busy}")
        
        if is_busy:
            self.logger.debug("Download manager is busy")
            return
        
        # Get next pending item
        next_item = self.queue.get_next_pending()
        
        if next_item is None:
            self.logger.info("No pending items in queue")
            self._is_processing = False
            self.queue_processing_finished.emit()
            return
        
        # Start download
        self._start_download(next_item)
    
    def _start_download(self, item: QueueItem):
        """
        Start downloading an item.
        
        Args:
            item: Queue item to download
        """
        self._current_item = item
        self._is_processing = True
        
        # Update item status
        updated_item = item.update_status(QueueItemStatus.DOWNLOADING)
        self.queue.update(updated_item)
        self._current_item = updated_item
        
        self.logger.info(f"Starting download from queue: {item.title or item.url}")
        self.queue_item_started.emit(updated_item)
        
        # Start download through download manager
        self.download_manager.start_download(
            url=item.url,
            download_path=item.download_path,
            format_type=item.format_type,
            quality=item.quality
        )
    
    @Slot(str)
    def _on_download_started(self, title: str):
        """Handle download started event."""
        if self._current_item:
            # Update title if we didn't have it
            if not self._current_item.title:
                updated_item = QueueItem.from_dict({
                    **self._current_item.to_dict(),
                    'title': title
                })
                self.queue.update(updated_item)
                self._current_item = updated_item
    
    @Slot(dict)
    def _on_progress_updated(self, progress_info: dict):
        """Handle progress updates."""
        if self._current_item and progress_info.get('status') == 'downloading':
            percent = progress_info.get('percent', 0)
            speed = progress_info.get('speed', 0)
            
            updated_item = self._current_item.update_progress(percent, speed)
            self.queue.update(updated_item)
            self._current_item = updated_item
            self.queue_item_progress.emit(updated_item)
    
    @Slot(dict)
    def _on_download_completed(self, result: dict):
        """Handle download completion."""
        if self._current_item:
            # Update item status
            updated_item = self._current_item.update_status(QueueItemStatus.COMPLETED)
            updated_item = updated_item.update_progress(100.0)
            self.queue.update(updated_item)
            
            self.logger.info(f"Queue item completed: {self._current_item.title or self._current_item.url}")
            self.queue_item_completed.emit(updated_item)
            
            self._current_item = None
            self._is_processing = False
            
            # Process next item if auto-processing is enabled
            # Use QTimer to delay to ensure download_manager cleanup is fully done
            if self._auto_process:
                from PySide6.QtCore import QTimer
                QTimer.singleShot(200, self.process_queue)  # Small delay for cleanup
    
    @Slot(str)
    def _on_download_error(self, error: str):
        """Handle download error."""
        if self._current_item:
            # Update item with error
            updated_item = self._current_item.with_error(error)
            self.queue.update(updated_item)
            
            self.logger.error(f"Queue item failed: {error}")
            self.queue_item_failed.emit(updated_item, error)
            
            self._current_item = None
            self._is_processing = False
            
            # Process next item if auto-processing is enabled
            if self._auto_process:
                self.process_queue()
    
    def cancel_current(self):
        """Cancel currently downloading item."""
        if self._current_item and self._is_processing:
            self.download_manager.cancel_download()
            
            # Update item status
            updated_item = self._current_item.update_status(QueueItemStatus.CANCELLED)
            self.queue.update(updated_item)
            
            self._current_item = None
            self._is_processing = False
            
            self.logger.info("Cancelled current download from queue")
    
    def retry_item(self, item_id: str):
        """
        Retry a failed or cancelled item.
        
        Args:
            item_id: ID of item to retry
        """
        item = self.queue.get(item_id)
        
        if item and item.can_retry():
            # Reset item status
            updated_item = item.update_status(QueueItemStatus.PENDING)
            updated_item = QueueItem.from_dict({
                **updated_item.to_dict(),
                'progress': 0.0,
                'error_message': None,
                'started_at': None,
                'completed_at': None
            })
            self.queue.update(updated_item)
            
            self.logger.info(f"Retrying item: {item.title or item.url}")
            
            # Start processing if not already
            if self._auto_process and not self._is_processing:
                self.process_queue()
    
    def remove_item(self, item_id: str):
        """
        Remove item from queue.
        
        Args:
            item_id: ID of item to remove
        """
        # Don't remove if currently downloading
        if self._current_item and self._current_item.id == item_id:
            self.cancel_current()
        
        self.queue.remove(item_id)
    
    def get_queue_stats(self) -> dict:
        """
        Get queue statistics.
        
        Returns:
            Dictionary with queue stats
        """
        items = self.queue.get_all()
        
        return {
            'total': len(items),
            'pending': sum(1 for item in items if item.is_pending()),
            'downloading': sum(1 for item in items if item.is_active()),
            'completed': sum(1 for item in items if item.status == QueueItemStatus.COMPLETED),
            'failed': sum(1 for item in items if item.status == QueueItemStatus.FAILED),
            'cancelled': sum(1 for item in items if item.status == QueueItemStatus.CANCELLED),
        }
    
    def is_processing(self) -> bool:
        """Check if queue is being processed."""
        return self._is_processing
    
    def get_current_item(self) -> Optional[QueueItem]:
        """Get currently downloading item."""
        return self._current_item
