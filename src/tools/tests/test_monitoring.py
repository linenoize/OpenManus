import unittest
import os
import tempfile
import shutil
import json
import time
from unittest.mock import patch, MagicMock
from src.tools.monitoring import MonitoringTool

class TestMonitoringTool(unittest.TestCase):
    def setUp(self):
        # Create temporary directories for logs and metrics
        self.temp_dir = tempfile.mkdtemp()
        self.log_path = os.path.join(self.temp_dir, "logs")
        self.metrics_path = os.path.join(self.temp_dir, "metrics")
        
        # Create monitoring tool
        self.monitoring = MonitoringTool(
            log_path=self.log_path,
            metrics_path=self.metrics_path,
            enabled=True,
            log_level="INFO"
        )
    
    def tearDown(self):
        # Clean up temp directories
        shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test monitoring tool initialization"""
        # Verify directories were created
        self.assertTrue(os.path.exists(self.log_path))
        self.assertTrue(os.path.exists(self.metrics_path))
        
        # Verify metrics were initialized
        metrics = self.monitoring.get_metrics()
        self.assertIn("system", metrics)
        self.assertIn("tools", metrics)
        self.assertIn("llm_providers", metrics)
        
        # Verify system metrics
        self.assertEqual(metrics["system"]["api_calls"], 0)
        self.assertEqual(metrics["system"]["errors"], 0)
        self.assertEqual(metrics["system"]["active_tasks"], 0)
        self.assertEqual(metrics["system"]["completed_tasks"], 0)
    
    def test_request_tracking(self):
        """Test request tracking functionality"""
        # Start a request
        request_id = "test_request_1"
        context = {"type": "test", "user_id": "user123"}
        self.monitoring.start_request(request_id, context)
        
        # Verify active tasks increased
        metrics = self.monitoring.get_metrics()
        self.assertEqual(metrics["system"]["api_calls"], 1)
        self.assertEqual(metrics["system"]["active_tasks"], 1)
        
        # End the request
        result = self.monitoring.end_request(request_id, status="success")
        
        # Verify request was tracked correctly
        self.assertEqual(result["request_id"], request_id)
        self.assertIn("duration", result)
        self.assertIn("start_time", result)
        self.assertIn("end_time", result)
        self.assertEqual(result["status"], "success")
        
        # Verify metrics were updated
        metrics = self.monitoring.get_metrics()
        self.assertEqual(metrics["system"]["active_tasks"], 0)
        self.assertEqual(metrics["system"]["completed_tasks"], 1)
    
    def test_error_tracking(self):
        """Test error tracking in requests"""
        # Start a request
        request_id = "error_request"
        self.monitoring.start_request(request_id, {"type": "error_test"})
        
        # End with error
        error_msg = "Test error message"
        result = self.monitoring.end_request(request_id, status="error", error=error_msg)
        
        # Verify error count increased
        metrics = self.monitoring.get_metrics()
        self.assertEqual(metrics["system"]["errors"], 1)
        self.assertEqual(metrics["system"]["completed_tasks"], 1)
    
    def test_tool_usage_tracking(self):
        """Test tool usage metrics tracking"""
        # Track tool usage
        self.monitoring.track_tool_usage(
            tool_name="memory",
            operation="store",
            duration=0.25,
            status="success"
        )
        
        # Verify tool metrics were recorded
        tool_metrics = self.monitoring.get_tool_metrics("memory")
        self.assertIn("memory.store", tool_metrics)
        self.assertEqual(tool_metrics["memory.store"]["calls"], 1)
        self.assertEqual(tool_metrics["memory.store"]["errors"], 0)
        self.assertEqual(tool_metrics["memory.store"]["total_duration"], 0.25)
        
        # Track another operation
        self.monitoring.track_tool_usage(
            tool_name="memory",
            operation="search",
            duration=0.5,
            status="success"
        )
        
        # Track an error
        self.monitoring.track_tool_usage(
            tool_name="memory",
            operation="store",
            duration=0.1,
            status="error",
            error="Test error"
        )
        
        # Verify updated metrics
        tool_metrics = self.monitoring.get_tool_metrics("memory")
        self.assertEqual(tool_metrics["memory.store"]["calls"], 2)
        self.assertEqual(tool_metrics["memory.store"]["errors"], 1)
        self.assertEqual(tool_metrics["memory.search"]["calls"], 1)
        self.assertEqual(tool_metrics["memory.search"]["errors"], 0)
        
        # Verify duration calculations
        self.assertAlmostEqual(tool_metrics["memory.store"]["avg_duration"], 0.175)
        self.assertEqual(tool_metrics["memory.store"]["min_duration"], 0.1)
        self.assertEqual(tool_metrics["memory.store"]["max_duration"], 0.25)
        
        # Verify getting metrics for just one tool
        memory_metrics = self.monitoring.get_tool_metrics("memory")
        self.assertEqual(len(memory_metrics), 2)  # memory.store and memory.search
        
        # Verify getting all tool metrics
        all_metrics = self.monitoring.get_tool_metrics()
        self.assertEqual(len(all_metrics), 2)  # memory.store and memory.search
    
    def test_llm_usage_tracking(self):
        """Test LLM provider usage tracking"""
        # Track LLM usage
        self.monitoring.track_llm_usage(
            provider="openai",
            tokens_input=100,
            tokens_output=50,
            duration=1.5,
            status="success"
        )
        
        # Verify LLM metrics were recorded
        llm_metrics = self.monitoring.get_llm_metrics("openai")
        self.assertIn("openai", llm_metrics)
        self.assertEqual(llm_metrics["openai"]["calls"], 1)
        self.assertEqual(llm_metrics["openai"]["tokens_input"], 100)
        self.assertEqual(llm_metrics["openai"]["tokens_output"], 50)
        self.assertEqual(llm_metrics["openai"]["total_duration"], 1.5)
        
        # Track another provider
        self.monitoring.track_llm_usage(
            provider="claude",
            tokens_input=200,
            tokens_output=75,
            duration=2.0,
            status="success"
        )
        
        # Track an error
        self.monitoring.track_llm_usage(
            provider="openai",
            tokens_input=50,
            tokens_output=0,
            duration=0.5,
            status="error",
            error="API error"
        )
        
        # Verify updated metrics
        llm_metrics = self.monitoring.get_llm_metrics()
        self.assertEqual(llm_metrics["openai"]["calls"], 2)
        self.assertEqual(llm_metrics["openai"]["errors"], 1)
        self.assertEqual(llm_metrics["openai"]["tokens_input"], 150)
        self.assertEqual(llm_metrics["openai"]["tokens_output"], 50)
        self.assertEqual(llm_metrics["claude"]["calls"], 1)
        self.assertEqual(llm_metrics["claude"]["errors"], 0)
    
    def test_metrics_saving(self):
        """Test saving metrics to disk"""
        # Add some metrics data
        self.monitoring.track_tool_usage("test_tool", duration=1.0)
        self.monitoring.track_llm_usage("test_provider", tokens_input=100, tokens_output=50)
        
        # Save metrics
        metrics_file = self.monitoring.save_metrics()
        
        # Verify file was created
        self.assertTrue(os.path.exists(metrics_file))
        
        # Load and verify saved data
        with open(metrics_file, 'r') as f:
            saved_metrics = json.load(f)
        
        self.assertIn("system", saved_metrics)
        self.assertIn("tools", saved_metrics)
        self.assertIn("llm_providers", saved_metrics)
        self.assertIn("timestamp", saved_metrics)
        self.assertIn("test_tool", saved_metrics["tools"])
        self.assertIn("test_provider", saved_metrics["llm_providers"])
    
    def test_disabled_monitoring(self):
        """Test behavior when monitoring is disabled"""
        # Create disabled monitoring instance
        disabled_monitoring = MonitoringTool(
            log_path=self.log_path,
            metrics_path=self.metrics_path,
            enabled=False
        )
        
        # Try various operations
        disabled_monitoring.start_request("test", {})
        result = disabled_monitoring.end_request("test")
        disabled_monitoring.track_tool_usage("tool", duration=1.0)
        metrics_file = disabled_monitoring.save_metrics()
        
        # Verify operations had no effect
        self.assertEqual(result, {"enabled": False})
        self.assertEqual(metrics_file, "")
        
        # Metrics should still be accessible
        metrics = disabled_monitoring.get_metrics()
        self.assertEqual(metrics["system"]["api_calls"], 0)
    
    def test_reset_metrics(self):
        """Test resetting metrics"""
        # Add some data
        self.monitoring.start_request("test", {})
        self.monitoring.end_request("test")
        self.monitoring.track_tool_usage("tool", duration=1.0)
        
        # Reset metrics
        self.monitoring.reset_metrics()
        
        # Verify metrics were reset
        metrics = self.monitoring.get_metrics()
        self.assertEqual(metrics["system"]["api_calls"], 0)
        self.assertEqual(metrics["system"]["completed_tasks"], 0)
        self.assertEqual(len(metrics["tools"]), 0)
    
    def test_duration_formatting(self):
        """Test duration formatting helper"""
        # Test different durations
        self.assertEqual(self.monitoring._format_duration(5), "5s")
        self.assertEqual(self.monitoring._format_duration(65), "1m 5s")
        self.assertEqual(self.monitoring._format_duration(3665), "1h 1m 5s")
        self.assertEqual(self.monitoring._format_duration(90000), "1d 1h 0m 0s")
    
    @patch('time.time')
    def test_auto_metrics_saving(self, mock_time):
        """Test automatic metrics saving based on interval"""
        # Mock time to control the interval
        current_time = 1000000.0
        mock_time.return_value = current_time
        
        # Initialize with mocked time
        self.monitoring.last_save_time = current_time
        self.monitoring.save_interval = 300  # 5 minutes
        
        # This call shouldn't trigger a save (not enough time elapsed)
        mock_time.return_value = current_time + 10
        with patch.object(self.monitoring, 'save_metrics') as mock_save:
            self.monitoring.check_save_metrics()
            mock_save.assert_not_called()
        
        # This call should trigger a save (interval exceeded)
        mock_time.return_value = current_time + 301
        with patch.object(self.monitoring, 'save_metrics') as mock_save:
            self.monitoring.check_save_metrics()
            mock_save.assert_called_once()

if __name__ == '__main__':
    unittest.main()