"""
Theme manager for light/dark mode support.
Follows system preferences and allows manual override.
"""

from enum import Enum
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, Signal, QObject
from PySide6.QtGui import QPalette, QColor


class ThemeMode(Enum):
    """Theme mode options."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeManager(QObject):
    """
    Manages application theme (light/dark mode).
    Single Responsibility: Theme switching and persistence.
    """
    
    theme_changed = Signal(str)  # Emits theme mode name
    
    def __init__(self):
        super().__init__()
        self.settings = QSettings("YouTubeDownloader", "Theme")
        self.current_mode = ThemeMode.SYSTEM
        
    def load_theme(self) -> ThemeMode:
        """Load saved theme preference."""
        saved_theme = self.settings.value("mode", "system")
        try:
            self.current_mode = ThemeMode(saved_theme)
        except ValueError:
            self.current_mode = ThemeMode.SYSTEM
        return self.current_mode
    
    def save_theme(self, mode: ThemeMode):
        """Save theme preference."""
        self.settings.setValue("mode", mode.value)
        self.current_mode = mode
    
    def get_current_theme(self) -> ThemeMode:
        """Get the current active theme (resolves SYSTEM to actual theme)."""
        if self.current_mode == ThemeMode.SYSTEM:
            return self._resolve_system_theme()
        return self.current_mode
    
    def apply_theme(self, mode: ThemeMode = None):
        """
        Apply theme to application.
        
        Args:
            mode: Theme mode to apply. If None, uses current mode.
        """
        if mode:
            self.current_mode = mode
            self.save_theme(mode)
        
        # Determine actual theme (resolve SYSTEM)
        actual_theme = self._resolve_system_theme() if self.current_mode == ThemeMode.SYSTEM else self.current_mode
        
        # Apply stylesheet
        app = QApplication.instance()
        if actual_theme == ThemeMode.DARK:
            app.setStyleSheet(self._get_dark_stylesheet())
        else:
            app.setStyleSheet(self._get_light_stylesheet())
        
        self.theme_changed.emit(actual_theme.value)
    
    def _resolve_system_theme(self) -> ThemeMode:
        """Detect system theme preference."""
        # Check system color scheme
        palette = QApplication.palette()
        bg_color = palette.color(QPalette.ColorRole.Window)
        
        # If background is dark, use dark theme
        if bg_color.lightness() < 128:
            return ThemeMode.DARK
        return ThemeMode.LIGHT
    
    def toggle_theme(self):
        """Toggle between light and dark mode."""
        if self.current_mode == ThemeMode.LIGHT:
            self.apply_theme(ThemeMode.DARK)
        else:
            self.apply_theme(ThemeMode.LIGHT)
    
    def _get_light_stylesheet(self) -> str:
        """Get minimal light theme stylesheet."""
        return """
            /* Minimal Professional Light Theme */
            QMainWindow {
                background-color: #f5f5f5;
                color: #212121;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            QMainWindow::centralWidget, QMainWindow > QWidget {
                background-color: #f5f5f5;
            }
            
            QWidget {
                background-color: transparent;
                color: #212121;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            /* Group Boxes */
            QGroupBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                color: #424242;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                background-color: #ffffff;
            }
            
            /* Headers */
            QLabel#titleLabel {
                color: #1976d2;
                font-size: 28px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }
            
            QLabel#subtitleLabel {
                color: #757575;
                font-size: 13px;
                font-weight: 400;
            }
            
            QLabel#sectionHeader {
                color: #424242;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Input Fields */
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 12px;
                color: #212121;
                font-size: 13px;
                selection-background-color: #1976d2;
                selection-color: white;
            }
            
            QLineEdit:focus {
                border: 2px solid #1976d2;
                padding: 9px 11px;
            }
            
            QLineEdit:read-only {
                background-color: #f5f5f5;
                color: #616161;
                border: 1px solid #e0e0e0;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #ffffff;
                color: #424242;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #bdbdbd;
            }
            
            QPushButton:pressed {
                background-color: #eeeeee;
            }
            
            QPushButton:disabled {
                background-color: #fafafa;
                color: #bdbdbd;
                border-color: #eeeeee;
            }
            
            QPushButton#primaryButton {
                background-color: #1976d2;
                color: white;
                border: none;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #1565c0;
            }
            
            QPushButton#primaryButton:pressed {
                background-color: #0d47a1;
            }
            
            QPushButton#primaryButton:disabled {
                background-color: #bbdefb;
                color: #e3f2fd;
            }
            
            QPushButton#secondaryButton {
                background-color: #ffffff;
                color: #1976d2;
                border: 1px solid #1976d2;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #e3f2fd;
            }
            
            QPushButton#cancelButton {
                background-color: #ffffff;
                color: #757575;
                border: 1px solid #e0e0e0;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #fafafa;
                color: #424242;
            }
            
            /* Queue Action Buttons */
            QTableWidget QPushButton {
                background-color: #ffffff;
                color: #1976d2;
                border: 1px solid #1976d2;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
                min-height: 24px;
            }
            
            QTableWidget QPushButton:hover {
                background-color: #1976d2;
                color: white;
            }
            
            QTableWidget QPushButton:pressed {
                background-color: #1565c0;
            }
            
            /* Info Buttons */
            QToolButton#infoButton {
                background-color: transparent;
                border: 1px solid #bdbdbd;
                border-radius: 10px;
                color: #757575;
                font-size: 11px;
                font-weight: bold;
                padding: 2px;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
            }
            
            QToolButton#infoButton:hover {
                background-color: #1976d2;
                border-color: #1976d2;
                color: white;
            }
            
            /* Combo Box */
            QComboBox {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px 12px;
                color: #212121;
                font-size: 13px;
            }
            
            QComboBox:focus {
                border: 2px solid #1976d2;
                padding: 9px 11px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                selection-background-color: #e3f2fd;
                selection-color: #1976d2;
                padding: 4px;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            /* Radio Buttons */
            QRadioButton {
                color: #424242;
                font-size: 13px;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #bdbdbd;
                border-radius: 9px;
                background-color: #ffffff;
            }
            
            QRadioButton::indicator:hover {
                border-color: #1976d2;
            }
            
            QRadioButton::indicator:checked {
                background-color: #1976d2;
                border: 2px solid #1976d2;
            }
            
            /* CheckBox */
            QCheckBox {
                color: #424242;
                font-size: 13px;
                spacing: 8px;
                padding: 4px 0;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #bdbdbd;
                border-radius: 3px;
                background-color: #ffffff;
            }
            
            QCheckBox::indicator:hover {
                border-color: #1976d2;
            }
            
            QCheckBox::indicator:checked {
                background-color: #1976d2;
                border: 2px solid #1976d2;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            }
            
            QCheckBox::indicator:checked:hover {
                background-color: #1565c0;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #f5f5f5;
                text-align: center;
                color: #424242;
                font-weight: 500;
                font-size: 12px;
                height: 8px;
            }
            
            QProgressBar::chunk {
                background-color: #1976d2;
                border-radius: 4px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background-color: #ffffff;
                top: -1px;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #757575;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QTabBar::tab:selected {
                color: #1976d2;
                border-bottom: 2px solid #1976d2;
            }
            
            QTabBar::tab:hover:!selected {
                color: #424242;
            }
            
            /* Table Widget */
            QTableWidget {
                background-color: #ffffff;
                border: none;
                border-radius: 8px;
                gridline-color: #f5f5f5;
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 8px 8px;
                color: #424242;
                border-bottom: 1px solid #f5f5f5;
            }
            
            QTableWidget::item:selected {
                background-color: #e3f2fd;
                color: #1976d2;
            }
            
            QHeaderView::section {
                background-color: #fafafa;
                color: #757575;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #e0e0e0;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background: #fafafa;
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: #bdbdbd;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #9e9e9e;
            }
            
            /* Tooltips */
            QToolTip {
                background-color: #424242;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
            }
        """
    
    def _get_dark_stylesheet(self) -> str:
        """Get minimal dark theme stylesheet - Avrix color scheme."""
        return """
            /* Avrix Dark Theme */
            QMainWindow {
                background-color: #11151e;
                color: #F0F0F0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            QMainWindow::centralWidget, QMainWindow > QWidget {
                background-color: #11151e;
            }
            
            QWidget {
                background-color: transparent;
                color: #F0F0F0;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }
            
            /* Group Boxes */
            QGroupBox {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 8px;
                margin-top: 12px;
                padding: 10px;
                font-size: 13px;
                font-weight: 600;
                color: #B0B0B0;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                background-color: #1a1f2e;
            }
            
            /* Headers */
            QLabel#titleLabel {
                color: #2F80ED;
                font-size: 28px;
                font-weight: 600;
                letter-spacing: -0.5px;
            }
            
            QLabel#subtitleLabel {
                color: #B0B0B0;
                font-size: 13px;
                font-weight: 400;
            }
            
            QLabel#sectionHeader {
                color: #B0B0B0;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                background-color: transparent;
            }
            
            QLabel#urlTypeLabel {
                color: #B0B0B0;
                font-size: 12px;
                padding: 8px 12px;
                border-radius: 6px;
                background-color: transparent;
            }
            
            /* Regular Labels - ensure they don't have contrasting backgrounds */
            QLabel {
                background-color: transparent;
            }
            
            /* Input Fields */
            QLineEdit {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 6px;
                padding: 10px 12px;
                color: #F0F0F0;
                font-size: 13px;
                selection-background-color: #2F80ED;
                selection-color: white;
            }
            
            QLineEdit:focus {
                border: 2px solid #2F80ED;
                padding: 9px 11px;
            }
            
            QLineEdit:read-only {
                background-color: #0d1117;
                color: #707070;
                border: 1px solid #2a3140;
            }
            
            /* Buttons */
            QPushButton {
                background-color: #1a1f2e;
                color: #F0F0F0;
                border: 1px solid #2a3140;
                border-radius: 6px;
                padding: 10px 24px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QPushButton:hover {
                background-color: #222733;
                border-color: #2F80ED;
                color: #FFFFFF;
            }
            
            QPushButton:pressed {
                background-color: #2a3140;
            }
            
            QPushButton:disabled {
                background-color: #0d1117;
                color: #606060;
                border-color: #1a1f2e;
            }
            
            QPushButton#primaryButton {
                background-color: #2F80ED;
                color: white;
                border: none;
            }
            
            QPushButton#primaryButton:hover {
                background-color: #4A90FF;
            }
            
            QPushButton#primaryButton:pressed {
                background-color: #1E6FDB;
            }
            
            QPushButton#primaryButton:disabled {
                background-color: #1E4C7F;
                color: #808080;
            }
            
            QPushButton#secondaryButton {
                background-color: #272A33;
                color: #2F80ED;
                border: 1px solid #2F80ED;
            }
            
            QPushButton#secondaryButton:hover {
                background-color: #2A3F5F;
            }
            
            QPushButton#cancelButton {
                background-color: #272A33;
                color: #F0F0F0;
                border: 1px solid #454A54;
            }
            
            QPushButton#cancelButton:hover {
                background-color: #2F3540;
                color: #FFFFFF;
            }
            
            /* Queue Action Buttons */
            QTableWidget QPushButton {
                background-color: #1a1f2e;
                color: #2F80ED;
                border: 1px solid #2F80ED;
                border-radius: 4px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
                min-height: 24px;
            }
            
            QTableWidget QPushButton:hover {
                background-color: #2F80ED;
                color: white;
            }
            
            QTableWidget QPushButton:pressed {
                background-color: #1E6FDB;
            }
            
            /* Info Buttons */
            QToolButton#infoButton {
                background-color: transparent;
                border: 1px solid #2a3140;
                border-radius: 10px;
                color: #B0B0B0;
                font-size: 11px;
                font-weight: bold;
                padding: 2px;
                min-width: 18px;
                max-width: 18px;
                min-height: 18px;
                max-height: 18px;
            }
            
            QToolButton#infoButton:hover {
                background-color: #2F80ED;
                border-color: #2F80ED;
                color: white;
            }
            
            /* Combo Box */
            QComboBox {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 6px;
                padding: 10px 12px;
                color: #F0F0F0;
                font-size: 13px;
            }
            
            QComboBox:focus {
                border: 2px solid #2F80ED;
                padding: 9px 11px;
            }
            
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 6px;
                selection-background-color: #2F80ED;
                selection-color: white;
                padding: 4px;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border-radius: 4px;
            }
            
            /* Radio Buttons */
            QRadioButton {
                color: #F0F0F0;
                font-size: 13px;
                spacing: 8px;
            }
            
            QRadioButton::indicator {
                width: 16px;
                height: 16px;
                border: 2px solid #2a3140;
                border-radius: 9px;
                background-color: #1a1f2e;
            }
            
            QRadioButton::indicator:hover {
                border-color: #2F80ED;
            }
            
            QRadioButton::indicator:checked {
                background-color: #2F80ED;
                border: 2px solid #2F80ED;
            }
            
            /* CheckBox */
            QCheckBox {
                color: #F0F0F0;
                font-size: 13px;
                spacing: 8px;
                padding: 4px 0;
            }
            
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 2px solid #2a3140;
                border-radius: 3px;
                background-color: #1a1f2e;
            }
            
            QCheckBox::indicator:hover {
                border-color: #2F80ED;
            }
            
            QCheckBox::indicator:checked {
                background-color: #2F80ED;
                border: 2px solid #2F80ED;
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w0LjUgOC41TDIgNiIgc3Ryb2tlPSJ3aGl0ZSIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=);
            }
            
            QCheckBox::indicator:checked:hover {
                background-color: #1E6FDB;
            }
            
            /* Progress Bar */
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #1a1f2e;
                text-align: center;
                color: #B0B0B0;
                font-weight: 500;
                font-size: 12px;
                height: 8px;
            }
            
            QProgressBar::chunk {
                background-color: #2F80ED;
                border-radius: 4px;
            }
            
            /* Tab Widget */
            QTabWidget::pane {
                border: 1px solid #2a3140;
                border-radius: 8px;
                background-color: #1a1f2e;
                top: -1px;
            }
            
            QTabBar::tab {
                background-color: transparent;
                color: #B0B0B0;
                border: none;
                border-bottom: 2px solid transparent;
                padding: 12px 24px;
                font-weight: 500;
                font-size: 13px;
            }
            
            QTabBar::tab:selected {
                color: #2F80ED;
                border-bottom: 2px solid #2F80ED;
            }
            
            QTabBar::tab:hover:!selected {
                color: #D0D0D0;
            }
            
            /* Table Widget */
            QTableWidget {
                background-color: #1a1f2e;
                border: none;
                border-radius: 8px;
                gridline-color: #2a3140;
                font-size: 13px;
            }
            
            QTableWidget::item {
                padding: 8px 8px;
                color: #F0F0F0;
                border-bottom: 1px solid #2a3140;
            }
            
            QTableWidget::item:selected {
                background-color: #2F80ED;
                color: white;
            }
            
            QHeaderView::section {
                background-color: #11151e;
                color: #B0B0B0;
                padding: 12px 8px;
                border: none;
                border-bottom: 1px solid #2a3140;
                font-weight: 600;
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            
            /* Scrollbar */
            QScrollBar:vertical {
                background: #11151e;
                width: 10px;
                border-radius: 5px;
            }
            
            QScrollBar::handle:vertical {
                background: #2a3140;
                border-radius: 5px;
                min-height: 20px;
            }
            
            QScrollBar::handle:vertical:hover {
                background: #3a414e;
            }
            
            /* Tooltips */
            QToolTip {
                background-color: #1a1f2e;
                color: #F0F0F0;
                border: 1px solid #2a3140;
                border-radius: 4px;
                padding: 8px 12px;
                font-size: 12px;
            }
            
            /* Message Box */
            QMessageBox {
                background-color: #1a1f2e;
            }
            
            QMessageBox QLabel {
                color: #F0F0F0;
            }
            
            /* SpinBox */
            QSpinBox {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 6px;
                padding: 10px 12px;
                color: #F0F0F0;
                font-size: 13px;
            }
            
            QSpinBox:focus {
                border: 2px solid #2F80ED;
                padding: 9px 11px;
            }
            
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #1a1f2e;
                border: 1px solid #2a3140;
                border-radius: 3px;
            }
            
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #222733;
            }
        """
