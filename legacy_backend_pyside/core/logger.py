"""
Logger service for consistent logging across the application.
Follows the Dependency Inversion Principle - depends on abstraction.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class ILogger(ABC):
    """Interface for logger (Dependency Inversion Principle)."""
    
    @abstractmethod
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        pass
    
    @abstractmethod
    def info(self, message: str, **kwargs):
        """Log info message."""
        pass
    
    @abstractmethod
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        pass
    
    @abstractmethod
    def error(self, message: str, **kwargs):
        """Log error message."""
        pass


class ConsoleLogger(ILogger):
    """Console logger implementation."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
    
    def debug(self, message: str, **kwargs):
        """Log debug message to console."""
        if self.enabled:
            self._print_formatted("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message to console."""
        if self.enabled:
            self._print_formatted("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message to console."""
        if self.enabled:
            self._print_formatted("WARNING", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message to console."""
        if self.enabled:
            self._print_formatted("ERROR", message, **kwargs)
    
    def _print_formatted(self, level: str, message: str, **kwargs):
        """Print formatted message with optional key-value pairs."""
        separator = '=' * 60 if level in ["DEBUG", "INFO"] else '!' * 60
        
        print(f"\n{separator}")
        print(f"{level}: {message}")
        
        for key, value in kwargs.items():
            print(f"  {key}: {value}")
        
        print(f"{separator}\n")


class NullLogger(ILogger):
    """Null logger (does nothing) - Null Object Pattern."""
    
    def debug(self, message: str, **kwargs):
        pass
    
    def info(self, message: str, **kwargs):
        pass
    
    def warning(self, message: str, **kwargs):
        pass
    
    def error(self, message: str, **kwargs):
        pass


# Singleton logger instance
_logger_instance: Optional[ILogger] = None


def get_logger() -> ILogger:
    """
    Get the global logger instance (Singleton Pattern).
    
    Returns:
        Logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = ConsoleLogger(enabled=True)
    return _logger_instance


def set_logger(logger: ILogger):
    """
    Set the global logger instance.
    
    Args:
        logger: Logger instance to use
    """
    global _logger_instance
    _logger_instance = logger
