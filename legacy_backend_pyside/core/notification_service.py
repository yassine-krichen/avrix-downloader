"""
Native notification service for desktop notifications.
Uses Windows native notifications via PySide6.
"""

from typing import Optional
from PySide6.QtWidgets import QSystemTrayIcon, QApplication
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import QObject, Qt
from pathlib import Path


class NotificationService(QObject):
    """
    Service for sending native desktop notifications.
    Uses Qt's system tray for cross-platform notifications.
    """
    
    def __init__(self, app_icon: Optional[QIcon] = None):
        """
        Initialize notification service.
        
        Args:
            app_icon: Optional application icon for notifications
        """
        super().__init__()
        self._enabled = True
        self._system_tray = None
        
        # Initialize system tray if supported
        if QSystemTrayIcon.isSystemTrayAvailable():
            self._system_tray = QSystemTrayIcon()
            
            # Use provided icon or create a simple default one
            if app_icon and not app_icon.isNull():
                self._system_tray.setIcon(app_icon)
            else:
                # Create a simple default icon
                default_icon = self._create_default_icon()
                self._system_tray.setIcon(default_icon)
            
            # Must show the tray icon for notifications to work
            self._system_tray.show()
    
    def _create_default_icon(self) -> QIcon:
        """
        Create a simple default icon for notifications.
        
        Returns:
            Default QIcon
        """
        # Create a 48x48 pixmap with a simple colored circle
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw a blue circle
        painter.setBrush(QColor(25, 118, 210))  # Blue color
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(4, 4, 40, 40)
        
        painter.end()
        
        return QIcon(pixmap)
    
    def is_available(self) -> bool:
        """
        Check if native notifications are available.
        
        Returns:
            True if notifications are supported
        """
        return self._system_tray is not None and QSystemTrayIcon.isSystemTrayAvailable()
    
    def set_enabled(self, enabled: bool):
        """
        Enable or disable notifications.
        
        Args:
            enabled: Whether to enable notifications
        """
        self._enabled = enabled
    
    def is_enabled(self) -> bool:
        """
        Check if notifications are enabled.
        
        Returns:
            True if enabled
        """
        return self._enabled
    
    def show_notification(
        self,
        title: str,
        message: str,
        notification_type: str = "info"
    ):
        """
        Show a native desktop notification.
        
        Args:
            title: Notification title
            message: Notification message
            notification_type: Type of notification ('info', 'warning', 'error')
        """
        if not self._enabled or not self.is_available():
            return
        
        # Map notification type to QSystemTrayIcon icon
        icon_map = {
            'info': QSystemTrayIcon.MessageIcon.Information,
            'warning': QSystemTrayIcon.MessageIcon.Warning,
            'error': QSystemTrayIcon.MessageIcon.Critical,
        }
        
        icon = icon_map.get(notification_type, QSystemTrayIcon.MessageIcon.Information)
        
        # Show the notification
        self._system_tray.showMessage(
            title,
            message,
            icon,
            5000  # Duration in milliseconds (5 seconds)
        )
    
    def show_success(self, title: str, message: str):
        """
        Show a success notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        self.show_notification(title, message, "info")
    
    def show_error(self, title: str, message: str):
        """
        Show an error notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        self.show_notification(title, message, "error")
    
    def show_warning(self, title: str, message: str):
        """
        Show a warning notification.
        
        Args:
            title: Notification title
            message: Notification message
        """
        self.show_notification(title, message, "warning")
    
    def cleanup(self):
        """Clean up system tray resources."""
        if self._system_tray:
            self._system_tray.hide()
