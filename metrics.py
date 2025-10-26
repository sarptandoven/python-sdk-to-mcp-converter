"""metrics collection and reporting."""
import time
from collections import defaultdict


class Metrics:
    """simple metrics collector."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}
        self.start_time = time.time()
    
    def increment(self, name, value=1):
        """increment a counter."""
        self.counters[name] += value
    
    def record_time(self, name, duration_ms):
        """record a timing value."""
        self.timers[name].append(duration_ms)
    
    def set_gauge(self, name, value):
        """set a gauge value."""
        self.gauges[name] = value
    
    def get_counter(self, name):
        """get counter value."""
        return self.counters.get(name, 0)
    
    def get_timer_stats(self, name):
        """get timer statistics."""
        values = self.timers.get(name, [])
        
        if not values:
            return None
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }
    
    def get_all_stats(self):
        """get all metrics."""
        timer_stats = {}
        for name, values in self.timers.items():
            timer_stats[name] = self.get_timer_stats(name)
        
        return {
            "uptime_seconds": time.time() - self.start_time,
            "counters": dict(self.counters),
            "timers": timer_stats,
            "gauges": dict(self.gauges)
        }
    
    def reset(self):
        """reset all metrics."""
        self.counters = defaultdict(int)
        self.timers = defaultdict(list)
        self.gauges = {}


# global metrics instance
_metrics = None


def get_metrics():
    """get global metrics instance."""
    global _metrics
    if _metrics is None:
        _metrics = Metrics()
    return _metrics

