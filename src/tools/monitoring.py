import os
import json
import time
import logging
import datetime
from typing import Dict, List, Any, Optional, Union
from collections import defaultdict
import threading

class MonitoringTool:
    """
    Tool for monitoring system performance, tool usage, and capturing metrics.
    Provides both real-time monitoring and historical data collection.
    """
    
    def __init__(self, 
                log_path: str = "data/logs",
                metrics_path: str = "data/metrics",
                enabled: bool = True,
                log_level: str = "INFO"):
        """
        Initialize the monitoring tool.
        
        Args:
            log_path: Path to store log files
            metrics_path: Path to store metrics data
            enabled: Whether monitoring is enabled
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.enabled = enabled
        self.log_path = log_path
        self.metrics_path = metrics_path
        
        # Create directories if they don't exist
        if self.enabled:
            os.makedirs(self.log_path, exist_ok=True)
            os.makedirs(self.metrics_path, exist_ok=True)
        
        # Set up logging
        self.setup_logging(log_level)
        
        # Metrics storage
        self.metrics = {
            "system": {
                "start_time": time.time(),
                "api_calls": 0,
                "errors": 0,
                "active_tasks": 0,
                "completed_tasks": 0
            },
            "tools": defaultdict(lambda: {
                "calls": 0,
                "errors": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0
            }),
            "llm_providers": defaultdict(lambda: {
                "tokens_input": 0,
                "tokens_output": 0,
                "calls": 0,
                "errors": 0,
                "total_duration": 0
            })
        }
        
        # Active requests tracking
        self.active_requests = {}
        
        # Locks for thread safety
        self.metrics_lock = threading.Lock()
        self.requests_lock = threading.Lock()
        
        # Start periodic metrics saving
        self.last_save_time = time.time()
        self.save_interval = 300  # 5 minutes
        
        self.logger.info("Monitoring system initialized")
    
    def setup_logging(self, log_level: str):
        """Set up the logging system."""
        log_file = os.path.join(self.log_path, f"openmanus_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        
        # Convert string level to logging level
        level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configure logging
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Also log to console
            ]
        )
        
        # Create logger for this class
        self.logger = logging.getLogger("MonitoringTool")
    
    def start_request(self, request_id: str, context: Dict[str, Any]) -> None:
        """
        Start tracking a new API request.
        
        Args:
            request_id: Unique identifier for the request
            context: Request context information
        """
        if not self.enabled:
            return
            
        with self.requests_lock:
            self.active_requests[request_id] = {
                "start_time": time.time(),
                "context": context
            }
        
        with self.metrics_lock:
            self.metrics["system"]["api_calls"] += 1
            self.metrics["system"]["active_tasks"] += 1
        
        self.logger.info(f"Request started: {request_id}")
        self.check_save_metrics()
    
    def end_request(self, request_id: str, status: str = "success", error: Optional[str] = None) -> Dict[str, Any]:
        """
        End tracking for an API request.
        
        Args:
            request_id: Unique identifier for the request
            status: Request status (success, error)
            error: Error message if status is error
            
        Returns:
            Request timing information
        """
        if not self.enabled:
            return {"enabled": False}
            
        end_time = time.time()
        request_info = None
        
        with self.requests_lock:
            if request_id in self.active_requests:
                request_info = self.active_requests.pop(request_id)
            else:
                self.logger.warning(f"Attempt to end unknown request: {request_id}")
                return {"error": "Unknown request ID"}
        
        if request_info:
            duration = end_time - request_info["start_time"]
            
            with self.metrics_lock:
                self.metrics["system"]["active_tasks"] -= 1
                self.metrics["system"]["completed_tasks"] += 1
                
                if status == "error" and error:
                    self.metrics["system"]["errors"] += 1
                    self.logger.error(f"Request {request_id} failed: {error}")
                else:
                    self.logger.info(f"Request {request_id} completed in {duration:.2f}s")
            
            self.check_save_metrics()
            
            return {
                "request_id": request_id,
                "duration": duration,
                "start_time": request_info["start_time"],
                "end_time": end_time,
                "status": status
            }
        
        return {"error": "Request information not found"}
    
    def track_tool_usage(self, 
                       tool_name: str, 
                       operation: Optional[str] = None,
                       duration: float = 0.0,
                       status: str = "success",
                       error: Optional[str] = None) -> None:
        """
        Track tool usage metrics.
        
        Args:
            tool_name: Name of the tool
            operation: Optional operation name for complex tools
            duration: Execution duration in seconds
            status: Execution status (success, error)
            error: Error message if status is error
        """
        if not self.enabled:
            return
            
        # Format the tool identifier (include operation if provided)
        tool_id = f"{tool_name}.{operation}" if operation else tool_name
        
        with self.metrics_lock:
            tool_metrics = self.metrics["tools"][tool_id]
            
            # Update call count
            tool_metrics["calls"] += 1
            
            # Update duration metrics
            tool_metrics["total_duration"] += duration
            tool_metrics["avg_duration"] = tool_metrics["total_duration"] / tool_metrics["calls"]
            
            if duration < tool_metrics["min_duration"]:
                tool_metrics["min_duration"] = duration
                
            if duration > tool_metrics["max_duration"]:
                tool_metrics["max_duration"] = duration
            
            # Update error count
            if status == "error":
                tool_metrics["errors"] += 1
                if error:
                    self.logger.error(f"Tool {tool_id} error: {error}")
            else:
                self.logger.debug(f"Tool {tool_id} completed in {duration:.4f}s")
        
        self.check_save_metrics()
    
    def track_llm_usage(self,
                      provider: str,
                      tokens_input: int = 0,
                      tokens_output: int = 0,
                      duration: float = 0.0,
                      status: str = "success",
                      error: Optional[str] = None) -> None:
        """
        Track LLM usage metrics.
        
        Args:
            provider: Name of the LLM provider
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens
            duration: Execution duration in seconds
            status: Execution status (success, error)
            error: Error message if status is error
        """
        if not self.enabled:
            return
            
        with self.metrics_lock:
            provider_metrics = self.metrics["llm_providers"][provider]
            
            # Update call count
            provider_metrics["calls"] += 1
            
            # Update token counts
            provider_metrics["tokens_input"] += tokens_input
            provider_metrics["tokens_output"] += tokens_output
            
            # Update duration
            provider_metrics["total_duration"] += duration
            
            # Update error count
            if status == "error":
                provider_metrics["errors"] += 1
                if error:
                    self.logger.error(f"LLM provider {provider} error: {error}")
            else:
                self.logger.debug(f"LLM {provider} call: {tokens_input} in, {tokens_output} out, {duration:.2f}s")
        
        self.check_save_metrics()
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics snapshot.
        
        Returns:
            Dictionary of all metrics
        """
        with self.metrics_lock:
            # Calculate system uptime
            uptime = time.time() - self.metrics["system"]["start_time"]
            
            # Create a copy of metrics with calculated values
            metrics_copy = {
                "system": {
                    **self.metrics["system"],
                    "uptime": uptime,
                    "uptime_formatted": self._format_duration(uptime),
                    "active_requests": len(self.active_requests)
                },
                "tools": dict(self.metrics["tools"]),
                "llm_providers": dict(self.metrics["llm_providers"])
            }
            
            return metrics_copy
    
    def get_tool_metrics(self, tool_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific tool or all tools.
        
        Args:
            tool_name: Name of the tool or None for all tools
            
        Returns:
            Tool metrics dictionary
        """
        with self.metrics_lock:
            if tool_name:
                # Return metrics for specific tool
                result = {}
                for key, value in self.metrics["tools"].items():
                    if key == tool_name or key.startswith(f"{tool_name}."):
                        result[key] = value
                return result
            else:
                # Return all tool metrics
                return dict(self.metrics["tools"])
    
    def get_llm_metrics(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific LLM provider or all providers.
        
        Args:
            provider: Name of the provider or None for all providers
            
        Returns:
            LLM provider metrics dictionary
        """
        with self.metrics_lock:
            if provider:
                # Return metrics for specific provider
                if provider in self.metrics["llm_providers"]:
                    return {provider: self.metrics["llm_providers"][provider]}
                return {}
            else:
                # Return all provider metrics
                return dict(self.metrics["llm_providers"])
    
    def reset_metrics(self) -> None:
        """Reset all metrics to initial values."""
        with self.metrics_lock:
            # Reset system metrics
            self.metrics["system"] = {
                "start_time": time.time(),
                "api_calls": 0,
                "errors": 0,
                "active_tasks": 0,
                "completed_tasks": 0
            }
            
            # Reset tool metrics
            self.metrics["tools"] = defaultdict(lambda: {
                "calls": 0,
                "errors": 0,
                "total_duration": 0,
                "avg_duration": 0,
                "min_duration": float('inf'),
                "max_duration": 0
            })
            
            # Reset LLM provider metrics
            self.metrics["llm_providers"] = defaultdict(lambda: {
                "tokens_input": 0,
                "tokens_output": 0,
                "calls": 0,
                "errors": 0,
                "total_duration": 0
            })
        
        self.logger.info("Metrics reset")
    
    def save_metrics(self) -> str:
        """
        Save current metrics to disk.
        
        Returns:
            Path to the saved metrics file
        """
        if not self.enabled:
            return ""
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        metrics_file = os.path.join(self.metrics_path, f"metrics_{timestamp}.json")
        
        with self.metrics_lock:
            # Create a copy of the metrics to save
            metrics_to_save = self.get_metrics()
            
            # Add timestamp
            metrics_to_save["timestamp"] = timestamp
            
            # Save to file
            with open(metrics_file, 'w') as f:
                json.dump(metrics_to_save, f, indent=2)
            
            self.last_save_time = time.time()
            
        self.logger.info(f"Metrics saved to {metrics_file}")
        return metrics_file
    
    def check_save_metrics(self) -> None:
        """Check if it's time to save metrics and save if needed."""
        if time.time() - self.last_save_time > self.save_interval:
            self.save_metrics()
    
    def _format_duration(self, seconds: float) -> str:
        """Format a duration in seconds to a human-readable string."""
        m, s = divmod(int(seconds), 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        
        components = []
        if d > 0:
            components.append(f"{d}d")
        if h > 0:
            components.append(f"{h}h")
        if m > 0:
            components.append(f"{m}m")
        components.append(f"{s}s")
        
        return " ".join(components)