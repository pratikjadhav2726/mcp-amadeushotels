"""
Performance monitoring and metrics for multithreaded operations.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from threading import Lock
from collections import defaultdict, deque
import statistics

logger = logging.getLogger(__name__)


@dataclass
class OperationMetrics:
    """Metrics for a single operation."""
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    thread_id: Optional[str] = None
    concurrent_operations: int = 0
    
    @property
    def duration(self) -> Optional[float]:
        """Get operation duration in seconds."""
        if self.end_time is None:
            return None
        return self.end_time - self.start_time


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    avg_duration: float = 0.0
    median_duration: float = 0.0
    p95_duration: float = 0.0
    p99_duration: float = 0.0
    concurrent_operations_avg: float = 0.0
    concurrent_operations_max: int = 0
    error_rate: float = 0.0
    throughput_per_second: float = 0.0


class PerformanceMonitor:
    """Monitor and track performance metrics for multithreaded operations."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self._metrics: deque = deque(maxlen=max_history)
        self._active_operations: Dict[str, OperationMetrics] = {}
        self._lock = Lock()
        self._operation_counts: Dict[str, int] = defaultdict(int)
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._start_time = time.time()
    
    def start_operation(self, operation_name: str, thread_id: Optional[str] = None) -> str:
        """Start tracking an operation."""
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"
        
        with self._lock:
            active_count = len(self._active_operations)
            metric = OperationMetrics(
                operation_name=operation_name,
                start_time=time.time(),
                thread_id=thread_id,
                concurrent_operations=active_count
            )
            self._active_operations[operation_id] = metric
            self._operation_counts[operation_name] += 1
        
        logger.debug(f"Started operation {operation_id} ({operation_name})")
        return operation_id
    
    def end_operation(self, operation_id: str, success: bool = True, error_message: Optional[str] = None):
        """End tracking an operation."""
        with self._lock:
            if operation_id not in self._active_operations:
                logger.warning(f"Operation {operation_id} not found in active operations")
                return
            
            metric = self._active_operations[operation_id]
            metric.end_time = time.time()
            metric.success = success
            metric.error_message = error_message
            
            # Move to completed metrics
            self._metrics.append(metric)
            
            # Remove from active operations
            del self._active_operations[operation_id]
            
            # Update error counts
            if not success:
                self._error_counts[metric.operation_name] += 1
        
        duration = metric.duration
        status = "success" if success else "failed"
        logger.debug(f"Completed operation {operation_id} ({metric.operation_name}) in {duration:.3f}s - {status}")
    
    def get_active_operations(self) -> Dict[str, OperationMetrics]:
        """Get currently active operations."""
        with self._lock:
            return self._active_operations.copy()
    
    def get_stats(self, operation_name: Optional[str] = None) -> PerformanceStats:
        """Get performance statistics."""
        with self._lock:
            # Filter metrics by operation name if specified
            if operation_name:
                relevant_metrics = [m for m in self._metrics if m.operation_name == operation_name]
            else:
                relevant_metrics = list(self._metrics)
            
            if not relevant_metrics:
                return PerformanceStats()
            
            # Calculate basic stats
            total_ops = len(relevant_metrics)
            successful_ops = sum(1 for m in relevant_metrics if m.success)
            failed_ops = total_ops - successful_ops
            
            durations = [m.duration for m in relevant_metrics if m.duration is not None]
            if not durations:
                return PerformanceStats(total_operations=total_ops, successful_operations=successful_ops, failed_operations=failed_ops)
            
            total_duration = sum(durations)
            min_duration = min(durations)
            max_duration = max(durations)
            avg_duration = total_duration / len(durations)
            median_duration = statistics.median(durations)
            
            # Calculate percentiles
            sorted_durations = sorted(durations)
            p95_index = int(len(sorted_durations) * 0.95)
            p99_index = int(len(sorted_durations) * 0.99)
            p95_duration = sorted_durations[min(p95_index, len(sorted_durations) - 1)]
            p99_duration = sorted_durations[min(p99_index, len(sorted_durations) - 1)]
            
            # Calculate concurrent operations stats
            concurrent_ops = [m.concurrent_operations for m in relevant_metrics]
            concurrent_avg = statistics.mean(concurrent_ops) if concurrent_ops else 0
            concurrent_max = max(concurrent_ops) if concurrent_ops else 0
            
            # Calculate error rate and throughput
            error_rate = failed_ops / total_ops if total_ops > 0 else 0
            uptime = time.time() - self._start_time
            throughput = total_ops / uptime if uptime > 0 else 0
            
            return PerformanceStats(
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                total_duration=total_duration,
                min_duration=min_duration,
                max_duration=max_duration,
                avg_duration=avg_duration,
                median_duration=median_duration,
                p95_duration=p95_duration,
                p99_duration=p99_duration,
                concurrent_operations_avg=concurrent_avg,
                concurrent_operations_max=concurrent_max,
                error_rate=error_rate,
                throughput_per_second=throughput
            )
    
    def get_operation_summary(self) -> Dict[str, Any]:
        """Get summary of all operations."""
        with self._lock:
            summary = {
                "total_operations": sum(self._operation_counts.values()),
                "operation_types": dict(self._operation_counts),
                "error_counts": dict(self._error_counts),
                "active_operations": len(self._active_operations),
                "uptime_seconds": time.time() - self._start_time,
                "metrics_history_size": len(self._metrics)
            }
            
            # Add per-operation stats
            operation_names = set(self._operation_counts.keys())
            operation_stats = {}
            for op_name in operation_names:
                stats = self.get_stats(op_name)
                operation_stats[op_name] = {
                    "total_operations": stats.total_operations,
                    "success_rate": (stats.successful_operations / stats.total_operations * 100) if stats.total_operations > 0 else 0,
                    "avg_duration_ms": stats.avg_duration * 1000,
                    "max_duration_ms": stats.max_duration * 1000,
                    "error_rate": stats.error_rate * 100,
                    "throughput_per_second": stats.throughput_per_second
                }
            
            summary["operation_stats"] = operation_stats
            return summary
    
    def clear_history(self):
        """Clear metrics history."""
        with self._lock:
            self._metrics.clear()
            self._operation_counts.clear()
            self._error_counts.clear()
            self._start_time = time.time()
    
    def get_recent_operations(self, limit: int = 10) -> List[OperationMetrics]:
        """Get recent operations."""
        with self._lock:
            return list(self._metrics)[-limit:]


class AsyncPerformanceMonitor:
    """Async wrapper for performance monitoring."""
    
    def __init__(self, max_history: int = 1000):
        self.monitor = PerformanceMonitor(max_history)
    
    async def track_operation(self, operation_name: str, coro):
        """Track an async operation."""
        operation_id = self.monitor.start_operation(operation_name)
        try:
            result = await coro
            self.monitor.end_operation(operation_id, success=True)
            return result
        except Exception as e:
            self.monitor.end_operation(operation_id, success=False, error_message=str(e))
            raise
    
    def get_stats(self, operation_name: Optional[str] = None) -> PerformanceStats:
        """Get performance statistics."""
        return self.monitor.get_stats(operation_name)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return self.monitor.get_operation_summary()
    
    def get_active_operations(self) -> Dict[str, OperationMetrics]:
        """Get active operations."""
        return self.monitor.get_active_operations()
    
    def clear_history(self):
        """Clear metrics history."""
        self.monitor.clear_history()


# Global performance monitor instance
_performance_monitor: Optional[AsyncPerformanceMonitor] = None


def get_performance_monitor() -> AsyncPerformanceMonitor:
    """Get the global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = AsyncPerformanceMonitor()
    return _performance_monitor


def track_operation(operation_name: str):
    """Decorator to track async operations."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            return await monitor.track_operation(operation_name, func(*args, **kwargs))
        return wrapper
    return decorator






