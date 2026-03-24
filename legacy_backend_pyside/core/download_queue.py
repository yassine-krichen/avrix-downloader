"""
Download queue management.
Handles queue operations following SOLID principles.
"""

from typing import List, Optional, Callable
from PySide6.QtCore import QObject, Signal

from core.queue_item import QueueItem, QueueItemStatus
from core.queue_storage import IQueueStorage
from core.logger import get_logger


class DownloadQueue(QObject):
    """
    Manages the download queue.
    Single Responsibility: Queue data structure and operations.
    """
    
    # Signals for queue changes
    item_added = Signal(QueueItem)
    item_removed = Signal(str)  # item_id
    item_updated = Signal(QueueItem)
    queue_cleared = Signal()
    queue_changed = Signal()  # General change notification
    
    def __init__(self, storage: IQueueStorage):
        """
        Initialize queue with storage.
        
        Args:
            storage: Storage implementation for persistence
        """
        super().__init__()
        self.storage = storage
        self._items: List[QueueItem] = []
        self.logger = get_logger()
        
        # Load existing queue
        self._load()
    
    def _load(self):
        """Load queue from storage."""
        self._items = self.storage.load()
        self.logger.info(f"Loaded {len(self._items)} items from queue storage")
    
    def _save(self):
        """Save queue to storage."""
        self.storage.save(self._items)
    
    def add(self, item: QueueItem) -> bool:
        """
        Add item to queue.
        
        Args:
            item: Queue item to add
            
        Returns:
            True if added successfully
        """
        # Check for duplicates (same URL and quality)
        if self._has_duplicate(item):
            self.logger.warning(f"Duplicate item not added: {item.url}")
            return False
        
        self._items.append(item)
        self._save()
        
        self.logger.info(f"Added item to queue: {item.title or item.url}")
        self.item_added.emit(item)
        self.queue_changed.emit()
        
        return True
    
    def _has_duplicate(self, item: QueueItem) -> bool:
        """Check if item is duplicate."""
        return any(
            existing.url == item.url and 
            existing.quality == item.quality and
            existing.format_type == item.format_type and
            not existing.is_finished()
            for existing in self._items
        )
    
    def remove(self, item_id: str) -> bool:
        """
        Remove item from queue by ID.
        
        Args:
            item_id: ID of item to remove
            
        Returns:
            True if removed successfully
        """
        original_count = len(self._items)
        self._items = [item for item in self._items if item.id != item_id]
        
        if len(self._items) < original_count:
            self._save()
            self.logger.info(f"Removed item from queue: {item_id}")
            self.item_removed.emit(item_id)
            self.queue_changed.emit()
            return True
        
        return False
    
    def update(self, item: QueueItem):
        """
        Update an existing item in the queue.
        
        Args:
            item: Updated queue item
        """
        for i, existing in enumerate(self._items):
            if existing.id == item.id:
                self._items[i] = item
                self._save()
                self.item_updated.emit(item)
                self.queue_changed.emit()
                return
        
        self.logger.warning(f"Item not found for update: {item.id}")
    
    def get(self, item_id: str) -> Optional[QueueItem]:
        """
        Get item by ID.
        
        Args:
            item_id: ID of item to get
            
        Returns:
            Queue item or None if not found
        """
        for item in self._items:
            if item.id == item_id:
                return item
        return None
    
    def get_all(self) -> List[QueueItem]:
        """
        Get all items in queue.
        
        Returns:
            List of all queue items
        """
        return self._items.copy()
    
    def get_pending(self) -> List[QueueItem]:
        """
        Get all pending items.
        
        Returns:
            List of pending items
        """
        return [item for item in self._items if item.is_pending()]
    
    def get_next_pending(self) -> Optional[QueueItem]:
        """
        Get the next pending item to download.
        
        Returns:
            Next pending item or None
        """
        pending = self.get_pending()
        return pending[0] if pending else None
    
    def get_active(self) -> Optional[QueueItem]:
        """
        Get currently downloading item.
        
        Returns:
            Active item or None
        """
        for item in self._items:
            if item.is_active():
                return item
        return None
    
    def clear_finished(self):
        """Remove all finished items from queue."""
        original_count = len(self._items)
        self._items = [item for item in self._items if not item.is_finished()]
        
        if len(self._items) < original_count:
            self._save()
            self.logger.info(f"Cleared {original_count - len(self._items)} finished items")
            self.queue_changed.emit()
    
    def clear_all(self):
        """Remove all items from queue."""
        self._items.clear()
        self._save()
        self.logger.info("Cleared all items from queue")
        self.queue_cleared.emit()
        self.queue_changed.emit()
    
    def move(self, item_id: str, new_position: int) -> bool:
        """
        Move item to new position in queue.
        
        Args:
            item_id: ID of item to move
            new_position: New position (0-based index)
            
        Returns:
            True if moved successfully
        """
        # Find item
        item_index = None
        for i, item in enumerate(self._items):
            if item.id == item_id:
                item_index = i
                break
        
        if item_index is None:
            return False
        
        # Check if item can be moved (not downloading)
        if self._items[item_index].is_active():
            return False
        
        # Validate new position
        new_position = max(0, min(new_position, len(self._items) - 1))
        
        # Move item
        item = self._items.pop(item_index)
        self._items.insert(new_position, item)
        
        self._save()
        self.logger.info(f"Moved item {item_id} to position {new_position}")
        self.queue_changed.emit()
        
        return True
    
    def size(self) -> int:
        """Get queue size."""
        return len(self._items)
    
    def is_empty(self) -> bool:
        """Check if queue is empty."""
        return len(self._items) == 0
    
    def has_pending(self) -> bool:
        """Check if there are pending items."""
        return any(item.is_pending() for item in self._items)
