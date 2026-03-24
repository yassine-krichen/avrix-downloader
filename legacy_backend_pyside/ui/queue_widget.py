"""
Queue widget for displaying and managing download queue.
"""
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from core.queue_item import QueueItem, QueueItemStatus


class QueueWidget(QWidget):
    """Widget for displaying and managing download queue."""
    
    # Signals
    retry_requested = Signal(str)  # item_id
    remove_requested = Signal(str)  # item_id
    move_up_requested = Signal(str)  # item_id
    move_down_requested = Signal(str)  # item_id
    clear_finished_requested = Signal()
    clear_all_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._items = {}  # item_id -> QueueItem
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        
        # Header with stats
        header_layout = QHBoxLayout()
        self.stats_label = QLabel("Queue: 0 items")
        self.stats_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self.stats_label)
        header_layout.addStretch()
        
        # Clear buttons
        self.clear_finished_btn = QPushButton("Clear Finished")
        self.clear_finished_btn.clicked.connect(self.clear_finished_requested.emit)
        header_layout.addWidget(self.clear_finished_btn)
        
        self.clear_all_btn = QPushButton("Clear All")
        self.clear_all_btn.clicked.connect(self.clear_all_requested.emit)
        header_layout.addWidget(self.clear_all_btn)
        
        layout.addLayout(header_layout)
        
        # Queue table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Title", "Status", "Format", "Quality", "Progress", "Actions"
        ])
        
        # Table settings
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        
        # Set default row height for better button visibility
        self.table.verticalHeader().setDefaultSectionSize(60)
        
        # Column sizing
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Title
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # Status
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Format
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Quality
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Progress
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Actions
        
        self.table.setColumnWidth(1, 100)  # Status
        self.table.setColumnWidth(2, 70)   # Format
        self.table.setColumnWidth(3, 80)   # Quality
        self.table.setColumnWidth(4, 80)   # Progress
        self.table.setColumnWidth(5, 220)  # Actions - increased for button text
        
        layout.addWidget(self.table)
        
    def update_queue(self, items: list[QueueItem]):
        """
        Update the queue display with new items.
        
        Args:
            items: List of queue items to display
        """
        # Store items
        self._items = {item.id: item for item in items}
        
        # Update stats
        self._update_stats(items)
        
        # Update table
        self.table.setRowCount(len(items))
        
        for row, item in enumerate(items):
            self._populate_row(row, item)
            
    def update_item(self, item: QueueItem):
        """
        Update a specific item in the queue.
        
        Args:
            item: Updated queue item
        """
        # Update stored item
        self._items[item.id] = item
        
        # Find row
        row = self._find_item_row(item.id)
        if row is not None:
            self._populate_row(row, item)
            
        # Update stats
        self._update_stats(list(self._items.values()))
    
    def _populate_row(self, row: int, item: QueueItem):
        """
        Populate a table row with item data.
        
        Args:
            row: Row index
            item: Queue item to display
        """
        # Title - handle both string and dict (for backward compatibility)
        title = item.title
        if isinstance(title, dict):
            # If title is a dict (old format), extract the 'title' key
            title = title.get('title', item.url) if title else item.url
        title_text = title or item.url
        
        title_item = QTableWidgetItem(str(title_text))
        title_item.setToolTip(item.url)
        self.table.setItem(row, 0, title_item)
        
        # Status
        status_item = QTableWidgetItem(item.status.value)
        status_item.setForeground(self._get_status_color(item.status))
        self.table.setItem(row, 1, status_item)
        
        # Format
        format_item = QTableWidgetItem(item.format_type.upper())
        self.table.setItem(row, 2, format_item)
        
        # Quality
        quality_item = QTableWidgetItem(item.quality)
        self.table.setItem(row, 3, quality_item)
        
        # Progress
        progress_text = f"{int(item.progress)}%" if item.progress > 0 else "-"
        if item.error_message:
            progress_text = "Error"
        progress_item = QTableWidgetItem(progress_text)
        progress_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 4, progress_item)
        
        # Actions
        actions_widget = self._create_actions_widget(item)
        self.table.setCellWidget(row, 5, actions_widget)
        
    def _create_actions_widget(self, item: QueueItem) -> QWidget:
        """
        Create action buttons widget for an item.
        
        Args:
            item: Queue item
            
        Returns:
            Widget containing action buttons
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)
        
        # Retry/Redownload button (for failed/cancelled/completed)
        if item.status in [QueueItemStatus.FAILED, QueueItemStatus.CANCELLED, QueueItemStatus.COMPLETED]:
            retry_text = "Redownload" if item.status == QueueItemStatus.COMPLETED else "Retry"
            retry_btn = QPushButton(retry_text)
            retry_btn.clicked.connect(lambda: self.retry_requested.emit(item.id))
            layout.addWidget(retry_btn)
        
        # Move buttons (for pending items)
        if item.status == QueueItemStatus.PENDING:
            up_btn = QPushButton("↑")
            up_btn.setMaximumWidth(30)
            up_btn.clicked.connect(lambda: self.move_up_requested.emit(item.id))
            layout.addWidget(up_btn)
            
            down_btn = QPushButton("↓")
            down_btn.setMaximumWidth(30)
            down_btn.clicked.connect(lambda: self.move_down_requested.emit(item.id))
            layout.addWidget(down_btn)
        
        # Remove button (not for downloading)
        if item.status != QueueItemStatus.DOWNLOADING:
            remove_btn = QPushButton("Remove")
            remove_btn.clicked.connect(lambda: self.remove_requested.emit(item.id))
            layout.addWidget(remove_btn)
        
        layout.addStretch()
        return widget
        
    def _find_item_row(self, item_id: str) -> Optional[int]:
        """
        Find the row index of an item.
        
        Args:
            item_id: Item ID to find
            
        Returns:
            Row index or None if not found
        """
        for row in range(self.table.rowCount()):
            title_item = self.table.item(row, 0)
            if title_item and item_id in self._items:
                # Check if this row matches the item
                stored_item = self._items[item_id]
                if (title_item.text() == stored_item.title or 
                    title_item.text() == stored_item.url):
                    return row
        return None
        
    def _update_stats(self, items: list[QueueItem]):
        """
        Update the statistics label.
        
        Args:
            items: List of queue items
        """
        total = len(items)
        pending = sum(1 for item in items if item.status == QueueItemStatus.PENDING)
        downloading = sum(1 for item in items if item.status == QueueItemStatus.DOWNLOADING)
        completed = sum(1 for item in items if item.status == QueueItemStatus.COMPLETED)
        failed = sum(1 for item in items if item.status == QueueItemStatus.FAILED)
        
        stats_text = f"Queue: {total} items"
        if pending > 0:
            stats_text += f" | {pending} pending"
        if downloading > 0:
            stats_text += f" | {downloading} downloading"
        if completed > 0:
            stats_text += f" | {completed} completed"
        if failed > 0:
            stats_text += f" | {failed} failed"
            
        self.stats_label.setText(stats_text)
        
    def _get_status_color(self, status: QueueItemStatus) -> QColor:
        """
        Get color for status display.
        
        Args:
            status: Queue item status
            
        Returns:
            Color for status
        """
        color_map = {
            QueueItemStatus.PENDING: QColor(100, 100, 100),      # Gray
            QueueItemStatus.DOWNLOADING: QColor(0, 100, 200),    # Blue
            QueueItemStatus.COMPLETED: QColor(0, 150, 0),        # Green
            QueueItemStatus.FAILED: QColor(200, 0, 0),           # Red
            QueueItemStatus.CANCELLED: QColor(150, 150, 0),      # Orange
        }
        return color_map.get(status, QColor(0, 0, 0))
