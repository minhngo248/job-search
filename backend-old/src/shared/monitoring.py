"""
Monitoring and observability utilities for the Regulatory Jobs application.

This module provides utilities for structured logging, metrics collection,
and error tracking across all Lambda functions.
"""

import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from functools import wraps

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class StructuredLogger:
    """Enhanced logger with structured logging capabilities."""
    
    def __init__(self, name: str, level: int = logging.INFO):
        """
        Initialize structured logger.
        
        Args:
            name: Logger name
            level: Logging level
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Configure formatter for structured logging
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Ensure we have a handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def log_with_context(self, level: int, message: str, **context):
        """
        Log message with additional context.
        
        Args:
            level: Logging level
            message: Log message
            **context: Additional context fields
        """
        if context:
            # Add context as JSON for structured logging
            context_str = json.dumps(context, default=str, separators=(',', ':'))
            full_message = f"{message} | Context: {context_str}"
        else:
            full_message = message
        
        self.logger.log(level, full_message)
    
    def info(self, message: str, **context):
        """Log info message with context."""
        self.log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message with context."""
        self.log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """Log error message with context."""
        self.log_with_context(logging.ERROR, message, **context)
    
    def debug(self, message: str, **context):
        """Log debug message with context."""
        self.log_with_context(logging.DEBUG, message, **context)


class CloudWatchMetrics:
    """CloudWatch custom metrics client."""
    
    def __init__(self, namespace: str = "RegulatoryJobs"):
        """
        Initialize CloudWatch metrics client.
        
        Args:
            namespace: CloudWatch namespace for metrics
        """
        self.namespace = namespace
        self.cloudwatch = None
        
        if BOTO3_AVAILABLE:
            try:
                self.cloudwatch = boto3.client('cloudwatch')
            except Exception as e:
                logging.warning(f"Failed to initialize CloudWatch client: {e}")
    
    def put_metric(
        self, 
        metric_name: str, 
        value: float, 
        unit: str = 'Count',
        dimensions: Optional[Dict[str, str]] = None,
        timestamp: Optional[datetime] = None
    ):
        """
        Send custom metric to CloudWatch.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Metric unit (Count, Seconds, etc.)
            dimensions: Optional metric dimensions
            timestamp: Optional timestamp (defaults to now)
        """
        if not self.cloudwatch:
            return
        
        try:
            metric_data = {
                'MetricName': metric_name,
                'Value': value,
                'Unit': unit,
                'Timestamp': timestamp or datetime.utcnow()
            }
            
            if dimensions:
                metric_data['Dimensions'] = [
                    {'Name': k, 'Value': v} for k, v in dimensions.items()
                ]
            
            self.cloudwatch.put_metric_data(
                Namespace=self.namespace,
                MetricData=[metric_data]
            )
        except Exception as e:
            logging.warning(f"Failed to send metric {metric_name}: {e}")
    
    def put_multiple_metrics(self, metrics: List[Dict[str, Any]]):
        """
        Send multiple metrics to CloudWatch in batch.
        
        Args:
            metrics: List of metric dictionaries
        """
        if not self.cloudwatch or not metrics:
            return
        
        try:
            # CloudWatch allows max 20 metrics per request
            for i in range(0, len(metrics), 20):
                batch = metrics[i:i+20]
                
                metric_data = []
                for metric in batch:
                    metric_entry = {
                        'MetricName': metric['name'],
                        'Value': metric['value'],
                        'Unit': metric.get('unit', 'Count'),
                        'Timestamp': metric.get('timestamp', datetime.utcnow())
                    }
                    
                    if metric.get('dimensions'):
                        metric_entry['Dimensions'] = [
                            {'Name': k, 'Value': v} 
                            for k, v in metric['dimensions'].items()
                        ]
                    
                    metric_data.append(metric_entry)
                
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data
                )
        except Exception as e:
            logging.warning(f"Failed to send batch metrics: {e}")


class PerformanceTracker:
    """Performance tracking and timing utilities."""
    
    def __init__(self, metrics_client: Optional[CloudWatchMetrics] = None):
        """
        Initialize performance tracker.
        
        Args:
            metrics_client: Optional CloudWatch metrics client
        """
        self.metrics = metrics_client or CloudWatchMetrics()
        self.timers = {}
    
    @contextmanager
    def timer(self, operation_name: str, send_metric: bool = True):
        """
        Context manager for timing operations.
        
        Args:
            operation_name: Name of the operation being timed
            send_metric: Whether to send timing metric to CloudWatch
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            
            if send_metric:
                self.metrics.put_metric(
                    f"{operation_name}Duration",
                    duration,
                    'Seconds'
                )
    
    def time_function(self, metric_name: Optional[str] = None):
        """
        Decorator for timing function execution.
        
        Args:
            metric_name: Optional custom metric name
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                name = metric_name or f"{func.__name__}Duration"
                with self.timer(name):
                    return func(*args, **kwargs)
            return wrapper
        return decorator


class ErrorTracker:
    """Error tracking and alerting utilities."""
    
    def __init__(
        self, 
        logger: Optional[StructuredLogger] = None,
        metrics_client: Optional[CloudWatchMetrics] = None
    ):
        """
        Initialize error tracker.
        
        Args:
            logger: Optional structured logger
            metrics_client: Optional CloudWatch metrics client
        """
        self.logger = logger or StructuredLogger(__name__)
        self.metrics = metrics_client or CloudWatchMetrics()
    
    def track_error(
        self, 
        error: Exception, 
        context: Optional[Dict[str, Any]] = None,
        error_type: Optional[str] = None,
        send_metric: bool = True
    ):
        """
        Track and log error with context.
        
        Args:
            error: Exception that occurred
            context: Additional context information
            error_type: Optional error type classification
            send_metric: Whether to send error metric to CloudWatch
        """
        error_context = {
            'error_type': error_type or type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc()
        }
        
        if context:
            error_context.update(context)
        
        self.logger.error(f"Error occurred: {str(error)}", **error_context)
        
        if send_metric:
            self.metrics.put_metric(
                'Errors',
                1,
                'Count',
                {'ErrorType': error_context['error_type']}
            )
    
    def track_warning(
        self, 
        message: str, 
        context: Optional[Dict[str, Any]] = None,
        warning_type: Optional[str] = None
    ):
        """
        Track and log warning with context.
        
        Args:
            message: Warning message
            context: Additional context information
            warning_type: Optional warning type classification
        """
        warning_context = {
            'warning_type': warning_type or 'General'
        }
        
        if context:
            warning_context.update(context)
        
        self.logger.warning(message, **warning_context)
        
        self.metrics.put_metric(
            'Warnings',
            1,
            'Count',
            {'WarningType': warning_context['warning_type']}
        )


class MonitoringContext:
    """Centralized monitoring context for Lambda functions."""
    
    def __init__(
        self, 
        function_name: str,
        request_id: Optional[str] = None,
        namespace: str = "RegulatoryJobs"
    ):
        """
        Initialize monitoring context.
        
        Args:
            function_name: Name of the Lambda function
            request_id: Optional request ID for correlation
            namespace: CloudWatch namespace
        """
        self.function_name = function_name
        self.request_id = request_id or 'unknown'
        self.namespace = namespace
        
        # Initialize components
        self.logger = StructuredLogger(function_name)
        self.metrics = CloudWatchMetrics(namespace)
        self.performance = PerformanceTracker(self.metrics)
        self.errors = ErrorTracker(self.logger, self.metrics)
        
        # Execution context
        self.start_time = datetime.utcnow()
        self.context_data = {
            'function_name': function_name,
            'request_id': self.request_id,
            'start_time': self.start_time.isoformat()
        }
    
    def log_execution_start(self, **additional_context):
        """Log function execution start."""
        context = {**self.context_data, **additional_context}
        self.logger.info("Function execution started", **context)
        
        self.metrics.put_metric(
            'FunctionInvocations',
            1,
            'Count',
            {'FunctionName': self.function_name}
        )
    
    def log_execution_end(self, success: bool = True, **additional_context):
        """Log function execution end."""
        end_time = datetime.utcnow()
        duration = (end_time - self.start_time).total_seconds()
        
        context = {
            **self.context_data,
            'end_time': end_time.isoformat(),
            'duration_seconds': duration,
            'success': success,
            **additional_context
        }
        
        if success:
            self.logger.info("Function execution completed successfully", **context)
            status = 'Success'
        else:
            self.logger.error("Function execution failed", **context)
            status = 'Error'
        
        # Send metrics
        self.metrics.put_multiple_metrics([
            {
                'name': 'FunctionDuration',
                'value': duration,
                'unit': 'Seconds',
                'dimensions': {'FunctionName': self.function_name}
            },
            {
                'name': 'FunctionExecutions',
                'value': 1,
                'unit': 'Count',
                'dimensions': {
                    'FunctionName': self.function_name,
                    'Status': status
                }
            }
        ])
    
    def add_context(self, **context):
        """Add additional context data."""
        self.context_data.update(context)


# Global monitoring instances for easy access
def get_monitoring_context(function_name: str, request_id: Optional[str] = None) -> MonitoringContext:
    """
    Get a monitoring context for a Lambda function.
    
    Args:
        function_name: Name of the Lambda function
        request_id: Optional request ID
        
    Returns:
        MonitoringContext instance
    """
    return MonitoringContext(function_name, request_id)