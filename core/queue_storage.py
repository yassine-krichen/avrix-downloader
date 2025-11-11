"""
Queue storage interface and implementations.
Follows Repository pattern for queue persistence.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import json
from pathlib import Path

from core.queue_item import QueueItem, QueueItemStatus


class IQueueStorage(ABC):
    """
    Interface for queue storage (Dependency Inversion Principle).
    Allows different storage implementations without changing queue logic.
    """
    
    @abstractmethod
    def save(self, items: List[QueueItem]):
        """Save queue items to storage."""
        pass
    
    @abstractmethod
    def load(self) -> List[QueueItem]:
        """Load queue items from storage."""
        pass
    
    @abstractmethod
    def clear(self):
        """Clear all items from storage."""
        pass


class JsonQueueStorage(IQueueStorage):
    """
    JSON file-based queue storage implementation.
    Persists queue to disk for recovery after app restart.
    """
    
    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize JSON storage.
        
        Args:
            storage_path: Path to JSON file. If None, uses default.
        """
        if storage_path is None:
            config_dir = Path(__file__).parent.parent / 'config'
            config_dir.mkdir(exist_ok=True)
            storage_path = config_dir / 'download_queue.json'
        
        self.storage_path = Path(storage_path)
    
    def save(self, items: List[QueueItem]):
        """
        Save queue items to JSON file.
        
        Args:
            items: List of queue items to save
        """
        try:
            # Convert items to dictionaries
            data = {
                'version': '1.0',
                'items': [item.to_dict() for item in items]
            }
            
            # Save to file
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Error saving queue: {e}")
    
    def load(self) -> List[QueueItem]:
        """
        Load queue items from JSON file.
        
        Returns:
            List of queue items
        """
        if not self.storage_path.exists():
            return []
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert dictionaries back to QueueItems
            items = [QueueItem.from_dict(item_data) for item_data in data.get('items', [])]
            
            # Reset any items that were downloading when app closed
            for i, item in enumerate(items):
                if item.status == QueueItemStatus.DOWNLOADING:
                    items[i] = item.update_status(QueueItemStatus.PENDING)
            
            return items
            
        except Exception as e:
            print(f"Error loading queue: {e}")
            return []
    
    def clear(self):
        """Clear queue storage file."""
        try:
            if self.storage_path.exists():
                self.storage_path.unlink()
        except Exception as e:
            print(f"Error clearing queue: {e}")


class MemoryQueueStorage(IQueueStorage):
    """
    In-memory queue storage implementation.
    Useful for testing or when persistence is not needed.
    """
    
    def __init__(self):
        """Initialize memory storage."""
        self._items: List[QueueItem] = []
    
    def save(self, items: List[QueueItem]):
        """Save items to memory."""
        self._items = items.copy()
    
    def load(self) -> List[QueueItem]:
        """Load items from memory."""
        return self._items.copy()
    
    def clear(self):
        """Clear memory storage."""
        self._items.clear()
