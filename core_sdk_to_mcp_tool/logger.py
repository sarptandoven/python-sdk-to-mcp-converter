"""logging utilities for the server."""
import sys
import time
import json


class Logger:
    """simple logger with structured output."""
    
    def __init__(self, level="INFO"):
        self.level = level
        self.levels = {"DEBUG": 0, "INFO": 1, "WARN": 2, "ERROR": 3}
        self.current_level = self.levels.get(level, 1)
    
    def _should_log(self, level):
        """check if message should be logged."""
        return self.levels.get(level, 1) >= self.current_level
    
    def _format_message(self, level, message, **kwargs):
        """format log message."""
        log_entry = {
            "timestamp": time.time(),
            "level": level,
            "message": message
        }
        
        if kwargs:
            log_entry["data"] = kwargs
        
        return json.dumps(log_entry)
    
    def debug(self, message, **kwargs):
        """log debug message."""
        if self._should_log("DEBUG"):
            print(self._format_message("DEBUG", message, **kwargs), file=sys.stderr)
    
    def info(self, message, **kwargs):
        """log info message."""
        if self._should_log("INFO"):
            print(self._format_message("INFO", message, **kwargs), file=sys.stderr)
    
    def warn(self, message, **kwargs):
        """log warning message."""
        if self._should_log("WARN"):
            print(self._format_message("WARN", message, **kwargs), file=sys.stderr)
    
    def error(self, message, **kwargs):
        """log error message."""
        if self._should_log("ERROR"):
            print(self._format_message("ERROR", message, **kwargs), file=sys.stderr)
    
    def request(self, method, params):
        """log incoming request."""
        self.debug(f"request: {method}", params=params)
    
    def response(self, method, duration_ms, success):
        """log response."""
        self.debug(f"response: {method}", duration_ms=duration_ms, success=success)


# global logger instance
_logger = None


def get_logger():
    """get global logger instance."""
    global _logger
    if _logger is None:
        import os
        level = os.getenv("LOG_LEVEL", "INFO")
        _logger = Logger(level)
    return _logger

