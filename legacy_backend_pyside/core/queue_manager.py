"""
Queue manager that orchestrates queue and download operations.
Coordinates between queue and download manager with concurrent download support.
"""

from typing import Optional, Dict
from PySide6.QtCore import QObject, Signal, Slot

from core.download_queue import DownloadQueue
from core.queue_item import QueueItem, QueueItemStatus
from core.downloader import DownloadManager, ConcurrentDownloadManager
from core.logger import get_logger


class QueueManager(QObject):
    """
    Manages download queue and coordinates with download manager.
    Single Responsibility: Orchestrate queue processing with concurrent download support.
    """
    
    # Signals
    queue_item_started = Signal(QueueItem)
    queue_item_completed = Signal(QueueItem)
    queue_item_failed = Signal(QueueItem, str)
    queue_item_progress = Signal(QueueItem)
    queue_processing_finished = Signal()
    
    def __init__(self, queue: DownloadQueue, download_manager: DownloadManager, max_concurrent: int = 3):
        """
        Initialize queue manager.
        
        Args:
            queue: Download queue instance
            download_manager: Download manager instance (for single direct downloads)
            max_concurrent: Maximum concurrent downloads for queue processing
        """
        super().__init__()
        self.queue = queue
        self.download_manager = download_manager
        self.logger = get_logger()
        
        # Concurrent download management
        self.concurrent_manager = ConcurrentDownloadManager(max_concurrent)
        self._active_items: Dict[str, QueueItem] = {}  # item_id -> QueueItem
        self._is_processing = False
        self._auto_process = True
        
        # Connect download manager signals (for direct downloads)
        self._connect_download_signals()
        
        # Connect concurrent manager signals (for queue downloads)
        self._connect_concurrent_signals()
    
    def _connect_download_signals(self):
        """Connect to download manager signals."""
        self.download_manager.download_started.connect(self._on_download_started)
        self.download_manager.download_completed.connect(self._on_download_completed)
        self.download_manager.download_error.connect(self._on_download_error)
        self.download_manager.progress_updated.connect(self._on_progress_updated)
        self.download_manager.playlist_progress.connect(self._on_playlist_progress)
    
    def _connect_concurrent_signals(self):
        """Connect to concurrent download manager signals."""
        self.concurrent_manager.download_started.connect(self._on_concurrent_started)
        self.concurrent_manager.download_completed.connect(self._on_concurrent_completed)
        self.concurrent_manager.download_error.connect(self._on_concurrent_error)
        self.concurrent_manager.progress_updated.connect(self._on_concurrent_progress)
        self.concurrent_manager.playlist_progress.connect(self._on_concurrent_playlist_progress)
    
    def set_max_concurrent(self, max_concurrent: int):
        """
        Set maximum concurrent downloads.
        
        Args:
            max_concurrent: Maximum number of simultaneous downloads (1-10)
        """
        self.concurrent_manager.set_max_concurrent(max_concurrent)
    
    def get_max_concurrent(self) -> int:
        """Get current max concurrent downloads setting."""
        return self.concurrent_manager.get_max_concurrent()
    
    def add_to_queue(
        self,
        url: str,
        download_path: str,
        format_type: str,
        quality: str,
        title: Optional[str] = None,
        url_type: Optional[str] = None,
        download_subtitles: bool = False,
        subtitle_languages: str = 'en',
        embed_thumbnail: bool = False
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
            download_subtitles: Whether to download subtitles
            subtitle_languages: Comma-separated language codes
            embed_thumbnail: Whether to embed thumbnail in audio files
            
        Returns:
            Created queue item or None if duplicate
        """
        item = QueueItem.create(
            url=url,
            download_path=download_path,
            format_type=format_type,
            quality=quality,
            title=title,
            url_type=url_type,
            download_subtitles=download_subtitles,
            subtitle_languages=subtitle_languages,
            embed_thumbnail=embed_thumbnail
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
        self._is_processing = True
        
        # Log queue status
        all_items = self.queue.get_all()
        pending_items = self.queue.get_pending()
        self.logger.info(f"Starting queue processing - Total items: {len(all_items)}, Pending: {len(pending_items)}")
        
        for item in all_items:
            self.logger.debug(f"  Item {item.id}: {item.title or item.url[:50]} - Status: {item.status.value}")
        
        self.process_queue()
    
    def stop_processing(self):
        """Stop processing queue (disable auto-processing and cancel active downloads)."""
        self._auto_process = False
        
        # If currently processing, cancel all active downloads
        if self._is_processing:
            self.logger.info("Stopping queue processing - cancelling active downloads")
            
            # Cancel all active downloads and reset items to pending
            item_ids = list(self._active_items.keys())
            for item_id in item_ids:
                self.concurrent_manager.cancel_download(item_id)
                
                item = self._active_items.pop(item_id)
                updated_item = item.update_status(QueueItemStatus.PENDING)
                updated_item = updated_item.update_progress(0.0)
                self.queue.update(updated_item)
            
            self._is_processing = False
            
            self.logger.info("Queue processing stopped")
    
    def process_queue(self):
        """Process next items in queue (supports concurrent downloads)."""
        if not self._is_processing:
            self.logger.warning("process_queue called but _is_processing is False")
            return
        
        active_count = self.concurrent_manager.get_active_count()
        max_concurrent = self.concurrent_manager.get_max_concurrent()
        self.logger.info(f"Processing queue - Active: {active_count}/{max_concurrent}")
        
        # Start as many downloads as we can up to the concurrent limit
        started_count = 0
        while self.concurrent_manager.can_start_download():
            # Get next pending item
            next_item = self.queue.get_next_pending()
            
            if next_item is None:
                # No more pending items
                if self.concurrent_manager.get_active_count() == 0:
                    # All done - no pending items and no active downloads
                    if started_count == 0:
                        self.logger.warning("No pending items in queue - nothing to download")
                    else:
                        self.logger.info("No pending items and no active downloads - queue complete")
                    self._is_processing = False
                    self.queue_processing_finished.emit()
                else:
                    # Still have active downloads, wait for them
                    self.logger.info(f"No more pending items, waiting for {self.concurrent_manager.get_active_count()} active downloads")
                break
            
            # Start download
            self._start_download(next_item)
            started_count += 1
        
        if started_count > 0:
            self.logger.info(f"Started {started_count} downloads")
    
    def _start_download(self, item: QueueItem):
        """
        Start downloading an item using concurrent manager.
        
        Args:
            item: Queue item to download
        """
        # Update item status
        updated_item = item.update_status(QueueItemStatus.DOWNLOADING)
        self.queue.update(updated_item)
        self._active_items[item.id] = updated_item
        
        self.logger.info(f"Starting download from queue: {item.title or item.url} (ID: {item.id})")
        self.queue_item_started.emit(updated_item)
        
        # Start download through concurrent manager
        success = self.concurrent_manager.start_download(
            item_id=item.id,
            url=item.url,
            download_path=item.download_path,
            format_type=item.format_type,
            quality=item.quality,
            download_subtitles=item.download_subtitles,
            subtitle_languages=item.subtitle_languages,
            embed_thumbnail=item.embed_thumbnail
        )
        
        if not success:
            self.logger.error(f"Failed to start download for {item.id}")
            updated_item = item.update_status(QueueItemStatus.FAILED)
            updated_item = updated_item.with_error("Could not start download")
            self.queue.update(updated_item)
            self._active_items.pop(item.id, None)
            self.queue_item_failed.emit(updated_item, "Could not start download")
    
    @Slot(str)
    def _on_download_started(self, title: str):
        """Handle download started event (for direct downloads, not used in queue processing)."""
        pass
    
    @Slot(dict)
    def _on_progress_updated(self, progress_info: dict):
        """Handle progress updates (for direct downloads, not used in queue processing)."""
        pass
    
    @Slot(int, int)
    def _on_playlist_progress(self, current: int, total: int):
        """Handle playlist progress updates (for direct downloads, not used in queue processing)."""
        pass
    
    @Slot(dict)
    def _on_download_completed(self, result: dict):
        """Handle download completion (for direct downloads, not used in queue processing)."""
        pass
    
    @Slot(str)
    def _on_download_error(self, error: str):
        """Handle download error (for direct downloads, not used in queue processing)."""
        pass
    
    # Concurrent download signal handlers
    @Slot(str, dict)
    def _on_concurrent_started(self, item_id: str, info: dict):
        """Handle concurrent download started event."""
        if item_id in self._active_items:
            item = self._active_items[item_id]
            # Update title if we didn't have it
            if not item.title and 'title' in info:
                updated_item = QueueItem.from_dict({
                    **item.to_dict(),
                    'title': info['title']
                })
                self.queue.update(updated_item)
                self._active_items[item_id] = updated_item
    
    @Slot(str, dict)
    def _on_concurrent_progress(self, item_id: str, progress_info: dict):
        """Handle concurrent download progress updates."""
        if item_id in self._active_items and progress_info.get('status') == 'downloading':
            item = self._active_items[item_id]
            percent = progress_info.get('percent', 0)
            speed = progress_info.get('speed', 0)
            
            updated_item = item.update_progress(percent, speed)
            self.queue.update(updated_item)
            self._active_items[item_id] = updated_item
            self.queue_item_progress.emit(updated_item)
    
    @Slot(str, int, int)
    def _on_concurrent_playlist_progress(self, item_id: str, current: int, total: int):
        """Handle concurrent download playlist progress updates."""
        if item_id in self._active_items:
            item = self._active_items[item_id]
            percent = (current / total) * 100.0 if total > 0 else 0
            
            updated_item = item.update_progress(percent, 0)
            self.queue.update(updated_item)
            self._active_items[item_id] = updated_item
            self.queue_item_progress.emit(updated_item)
            
            self.logger.debug(f"Playlist progress ({item_id}): {current}/{total} videos ({percent:.1f}%)")
    
    @Slot(str, dict)
    def _on_concurrent_completed(self, item_id: str, result: dict):
        """Handle concurrent download completion."""
        if item_id in self._active_items:
            item = self._active_items.pop(item_id)
            
            # Update item status
            updated_item = item.update_status(QueueItemStatus.COMPLETED)
            updated_item = updated_item.update_progress(100.0)
            self.queue.update(updated_item)
            
            self.logger.info(f"Queue item completed: {item.title or item.url} (ID: {item_id})")
            self.queue_item_completed.emit(updated_item)
            
            # Process next items immediately if auto-processing is enabled
            # No delay needed - the download is already marked as "finishing" so the slot is free
            if self._auto_process:
                self.process_queue()
    
    @Slot(str, str)
    def _on_concurrent_error(self, item_id: str, error: str):
        """Handle concurrent download error."""
        if item_id in self._active_items:
            item = self._active_items.pop(item_id)
            
            # Update item with error
            updated_item = item.with_error(error)
            self.queue.update(updated_item)
            
            self.logger.error(f"Queue item failed ({item_id}): {error}")
            self.queue_item_failed.emit(updated_item, error)
            
            # Process next items if auto-processing is enabled
            if self._auto_process:
                self.process_queue()
    
    def cancel_current(self):
        """Cancel all currently downloading items."""
        if self._active_items:
            item_ids = list(self._active_items.keys())
            for item_id in item_ids:
                self.concurrent_manager.cancel_download(item_id)
                
                item = self._active_items.pop(item_id)
                updated_item = item.update_status(QueueItemStatus.CANCELLED)
                self.queue.update(updated_item)
            
            self.logger.info(f"Cancelled {len(item_ids)} active downloads from queue")
    
    def retry_item(self, item_id: str):
        """
        Retry a failed or cancelled item, or redownload a completed item.
        Sets the item back to PENDING status without auto-starting.
        
        Args:
            item_id: ID of item to retry
        """
        item = self.queue.get(item_id)
        
        if item and item.can_retry():
            # Reset item status to PENDING
            updated_item = item.update_status(QueueItemStatus.PENDING)
            updated_item = QueueItem.from_dict({
                **updated_item.to_dict(),
                'progress': 0.0,
                'error_message': None,
                'started_at': None,
                'completed_at': None
            })
            self.queue.update(updated_item)
            
            status_text = "redownload" if item.status == QueueItemStatus.COMPLETED else "retry"
            self.logger.info(f"Item set to pending for {status_text}: {item.title or item.url}")
            
            # NOTE: Do NOT auto-start processing here
            # User must manually click "Start Queue" to process pending items
    
    def remove_item(self, item_id: str):
        """
        Remove item from queue.
        
        Args:
            item_id: ID of item to remove
        """
        # Don't remove if currently downloading
        if item_id in self._active_items:
            self.concurrent_manager.cancel_download(item_id)
            self._active_items.pop(item_id, None)
        
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
