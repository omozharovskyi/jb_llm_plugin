"""
Memory leak detection utilities for tests.
This module provides utilities to detect memory leaks in tests.
It uses tracemalloc to track memory allocations and identify potential leaks.
"""
import tracemalloc
import gc
import linecache
from functools import wraps


def display_top(snapshot, key_type='lineno', limit=10):
    """
    Display the top memory-consuming objects.
    Args:
        snapshot: A tracemalloc snapshot
        key_type: The type of grouping ('lineno' or 'traceback')
        limit: The number of top entries to display
    """
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, "<frozen importlib._bootstrap>"),
        tracemalloc.Filter(False, "<unknown>"),
    ))
    top_stats = snapshot.statistics(key_type)
    print(f"\nTop {limit} memory allocations:")
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        print(f"#{index}: {frame.filename}:{frame.lineno}: {stat.size / 1024:.1f} KiB")
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            print(f"    {line}")
    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        print(f"{len(other)} other: {size / 1024:.1f} KiB")
    total = sum(stat.size for stat in top_stats)
    print(f"Total allocated size: {total / 1024:.1f} KiB")


class MemoryLeakDetector:
    """
    A context manager for detecting memory leaks.
    Usage:
        with MemoryLeakDetector() as detector:
            # Code that might leak memory
        # Check for leaks
        detector.check_leaks()
    """
    def __init__(self, threshold_kb=100):
        """
        Initialize the memory leak detector.
        Args:
            threshold_kb: The threshold in KB above which to report a leak
        """
        self.threshold_kb = threshold_kb
        self.start_snapshot = None
        self.end_snapshot = None
    
    def __enter__(self):
        """Start tracking memory allocations."""
        gc.collect()
        tracemalloc.start()
        self.start_snapshot = tracemalloc.take_snapshot()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop tracking memory allocations."""
        if tracemalloc.is_tracing():
            self.end_snapshot = tracemalloc.take_snapshot()
            tracemalloc.stop()
    
    def check_leaks(self, display_limit=10):
        """
        Check for memory leaks.
        Args:
            display_limit: The number of top memory consumers to display
        Returns:
            True if a leak was detected, False otherwise
        """
        if self.start_snapshot is None or self.end_snapshot is None:
            print("Error: Memory leak detection was not properly initialized")
            return False
        # Compare snapshots
        stats = self.end_snapshot.compare_to(self.start_snapshot, 'lineno')
        # Check if there's a significant increase in memory usage
        total_diff = sum(stat.size for stat in stats if stat.size > 0)
        if total_diff > self.threshold_kb * 1024:
            print(f"\nPotential memory leak detected: {total_diff / 1024:.1f} KiB")
            # Display top memory consumers
            top_stats = [stat for stat in stats if stat.size > 0]
            top_stats.sort(key=lambda x: x.size, reverse=True)
            for index, stat in enumerate(top_stats[:display_limit], 1):
                frame = stat.traceback[0]
                print(f"#{index}: {frame.filename}:{frame.lineno}: {stat.size / 1024:.1f} KiB")
                line = linecache.getline(frame.filename, frame.lineno).strip()
                if line:
                    print(f"    {line}")
            return True
        return False


def detect_leaks(func):
    """
    Decorator to detect memory leaks in a function.
    Usage:
        @detect_leaks
        def test_function():
            # Test code that might leak memory
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with MemoryLeakDetector() as detector:
            result = func(*args, **kwargs)
            # Check for leaks
            detector.check_leaks()
            return result
    return wrapper


def memory_usage_decorator(func):
    """
    Decorator to track memory usage of a function.
    Usage:
        @memory_usage_decorator
        def test_function():
            # Test code
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Force garbage collection before starting
        gc.collect()
        # Start tracking memory
        tracemalloc.start()
        # Call the function
        result = func(*args, **kwargs)
        # Take snapshot and stop tracking
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        # Display memory usage
        display_top(snapshot)
        # Force garbage collection after finishing
        gc.collect()
        return result
    return wrapper