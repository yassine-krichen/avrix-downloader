"""
UI state manager for controlling widget states.
Follows Single Responsibility Principle - only manages UI state.
"""

from typing import Dict, Any
from PySide6.QtWidgets import QWidget


class UIState:
    """Enumeration of UI states."""
    READY = "ready"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    ERROR = "error"


class UIStateManager:
    """
    Manages UI widget states based on application state.
    Single Responsibility: UI state management.
    """
    
    def __init__(self, widgets: Dict[str, QWidget]):
        """
        Initialize with UI widgets to manage.
        
        Args:
            widgets: Dictionary of widget names to widget objects
        """
        self.widgets = widgets
        self.current_state = UIState.READY
    
    def set_state(self, state: str, **kwargs):
        """
        Set the UI state and update widget states accordingly.
        
        Args:
            state: Target state (from UIState)
            **kwargs: Additional state-specific parameters
        """
        self.current_state = state
        
        if state == UIState.READY:
            self._apply_ready_state(**kwargs)
        elif state == UIState.DOWNLOADING:
            self._apply_downloading_state()
        elif state == UIState.COMPLETED:
            self._apply_completed_state()
        elif state == UIState.ERROR:
            self._apply_error_state()
    
    def _apply_ready_state(self, **kwargs):
        """Apply ready state to widgets."""
        is_video = kwargs.get('is_video', True)
        
        self._set_enabled('download_button', True)
        self._set_enabled('cancel_button', False)
        self._set_enabled('url_input', True)
        self._set_enabled('mp4_radio', True)
        self._set_enabled('mp3_radio', True)
        self._set_enabled('quality_combo', is_video)
        self._set_enabled('browse_button', True)
        # open_folder_button is always enabled
    
    def _apply_downloading_state(self):
        """Apply downloading state to widgets."""
        self._set_enabled('download_button', False)
        self._set_enabled('cancel_button', True)
        self._set_enabled('url_input', False)
        self._set_enabled('mp4_radio', False)
        self._set_enabled('mp3_radio', False)
        self._set_enabled('quality_combo', False)
        self._set_enabled('browse_button', False)
        # open_folder_button is always enabled
    
    def _apply_completed_state(self):
        """Apply completed state to widgets."""
        self._apply_ready_state()
        # open_folder_button is always enabled
    
    def _apply_error_state(self):
        """Apply error state to widgets."""
        self._apply_ready_state()
        # open_folder_button is always enabled
    
    def _set_enabled(self, widget_name: str, enabled: bool):
        """
        Set enabled state of a widget.
        
        Args:
            widget_name: Name of widget in widgets dictionary
            enabled: Whether widget should be enabled
        """
        widget = self.widgets.get(widget_name)
        if widget:
            widget.setEnabled(enabled)
    
    def get_state(self) -> str:
        """
        Get current UI state.
        
        Returns:
            Current state
        """
        return self.current_state
