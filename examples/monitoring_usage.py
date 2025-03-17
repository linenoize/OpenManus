#!/usr/bin/env python3
"""
Example script demonstrating the use of the monitoring tool in OpenManus.
This script shows how to track system metrics, tool usage, and LLM provider usage.
"""

import sys
import os
import json
import time
import uuid
import random
from datetime import datetime

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.monitoring import MonitoringTool
except ImportError as e:
    print(f"Error importing MonitoringTool: {e}")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def simulate_tool_usage(monitoring, name, operations, count=5):
    """Simulate tool usage with random operations and durations."""
    print(f"Simulating {count} uses of the {name} tool...")
    
    for _ in range(count):
        # Pick a random operation
        operation = random.choice(operations)
        
        # Generate random duration between 0.1 and 2.0 seconds
        duration = random.uniform(0.1, 2.0)
        
        # Simulate a small chance of error
        status = "error" if random.random() < 0.1 else "success"
        error = f"Simulated error for {name}.{operation}" if status == "error" else None
        
        # Simulate the operation by sleeping
        start_time = time.time()
        time.sleep(min(0.05, duration / 10))  # Just sleep a fraction of the time for the demo
        actual_duration = time.time() - start_time
        
        # Track the tool usage
        monitoring.track_tool_usage(
            tool_name=name,
            operation=operation,
            duration=duration,  # Use the simulated duration
            status=status,
            error=error
        )
        
        # Print what happened
        result = "✓" if status == "success" else "✗"
        print(f"  {result} {name}.{operation} ({duration:.3f}s)")

def simulate_llm_usage(monitoring, providers, count=3):
    """Simulate LLM provider usage with random token counts and durations."""
    print(f"Simulating {count} LLM API calls...")
    
    for _ in range(count):
        # Pick a random provider
        provider = random.choice(providers)
        
        # Generate random token counts
        tokens_input = random.randint(100, 1000)
        tokens_output = random.randint(50, 500)
        
        # Generate random duration between 0.5 and 3.0 seconds
        duration = random.uniform(0.5, 3.0)
        
        # Simulate a small chance of error
        status = "error" if random.random() < 0.1 else "success"
        error = f"Simulated API error for {provider}" if status == "error" else None
        
        # Simulate the API call by sleeping
        start_time = time.time()
        time.sleep(min(0.1, duration / 10))  # Just sleep a fraction of the time for the demo
        actual_duration = time.time() - start_time
        
        # Track the LLM usage
        monitoring.track_llm_usage(
            provider=provider,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            duration=duration,  # Use the simulated duration
            status=status,
            error=error
        )
        
        # Print what happened
        result = "✓" if status == "success" else "✗"
        print(f"  {result} {provider} ({tokens_input} in, {tokens_output} out, {duration:.3f}s)")

def simulate_api_request(monitoring, tools, providers):
    """Simulate a complete API request with multiple tool and LLM calls."""
    # Generate a unique request ID
    request_id = f"req_{uuid.uuid4().hex[:8]}"
    
    # Start tracking the request
    context = {
        "type": "simulated_request",
        "timestamp": datetime.now().isoformat()
    }
    monitoring.start_request(request_id, context)
    print(f"Started request: {request_id}")
    
    # Simulate tool usage within this request
    tool_name = random.choice(list(tools.keys()))
    operations = tools[tool_name]
    simulate_tool_usage(monitoring, tool_name, operations, count=random.randint(1, 3))
    
    # Simulate LLM usage within this request
    simulate_llm_usage(monitoring, providers, count=random.randint(1, 2))
    
    # Simulate a small chance of request error
    status = "error" if random.random() < 0.1 else "success"
    error = f"Simulated request error: {random.choice(['timeout', 'internal_error', 'validation_failed'])}" if status == "error" else None
    
    # End the request tracking
    result = monitoring.end_request(request_id, status=status, error=error)
    print(f"Ended request: {request_id} (duration: {result['duration']:.3f}s, status: {status})")
    
    return request_id, result

def pretty_print_json(data):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=2))

def main():
    print("OpenManus Monitoring Tool Demo")
    print("=" * 60)
    
    # Initialize monitoring tool
    monitoring = MonitoringTool(
        log_path="data/demo_logs",
        metrics_path="data/demo_metrics",
        enabled=True,
        log_level="INFO"
    )
    print("Monitoring system initialized")
    
    # Define tool operations for simulation
    tools = {
        "memory": ["store", "get", "search", "update", "delete"],
        "vector_db": ["create_collection", "add_text", "search", "update_metadata"],
        "file_manager": ["read_text", "write_text", "list_files", "file_exists"],
        "code_executor": ["execute_code"]
    }
    
    # Define LLM providers for simulation
    providers = ["openai", "claude", "local"]
    
    # 1. Simulate individual tool usage
    print_section("1. Simulating individual tool usage")
    for tool_name, operations in tools.items():
        simulate_tool_usage(monitoring, tool_name, operations, count=3)
    
    # 2. Simulate individual LLM usage
    print_section("2. Simulating LLM API calls")
    simulate_llm_usage(monitoring, providers, count=5)
    
    # 3. Simulate full API requests
    print_section("3. Simulating complete API requests")
    request_results = []
    for i in range(10):
        print(f"\nRequest {i+1}/10:")
        request_id, result = simulate_api_request(monitoring, tools, providers)
        request_results.append(result)
        time.sleep(0.1)  # Brief pause between requests
    
    # 4. Show current metrics
    print_section("4. Current system metrics")
    metrics = monitoring.get_metrics()
    
    # Print system metrics
    print("\nSystem Metrics:")
    print(f"  API Calls: {metrics['system']['api_calls']}")
    print(f"  Completed Tasks: {metrics['system']['completed_tasks']}")
    print(f"  Active Tasks: {metrics['system']['active_tasks']}")
    print(f"  Errors: {metrics['system']['errors']}")
    print(f"  Uptime: {metrics['system']['uptime_formatted']}")
    
    # 5. Show tool usage metrics
    print_section("5. Tool usage metrics")
    tool_metrics = monitoring.get_tool_metrics()
    
    # Group metrics by tool
    tool_groups = {}
    for key, value in tool_metrics.items():
        parts = key.split(".")
        tool = parts[0]
        operation = parts[1] if len(parts) > 1 else "general"
        
        if tool not in tool_groups:
            tool_groups[tool] = {}
        
        tool_groups[tool][operation] = value
    
    # Print tool metrics grouped by tool
    for tool, operations in tool_groups.items():
        print(f"\n{tool.capitalize()} Tool:")
        
        total_calls = sum(op.get("calls", 0) for op in operations.values())
        total_errors = sum(op.get("errors", 0) for op in operations.values())
        total_duration = sum(op.get("total_duration", 0) for op in operations.values())
        
        print(f"  Total Calls: {total_calls}")
        print(f"  Total Errors: {total_errors}")
        print(f"  Total Duration: {total_duration:.2f}s")
        
        if operations:
            print(f"  Operations:")
            for op_name, op_metrics in operations.items():
                print(f"    - {op_name}: {op_metrics['calls']} calls, {op_metrics['errors']} errors, " +
                      f"avg: {op_metrics['avg_duration']:.3f}s, min: {op_metrics['min_duration']:.3f}s, " +
                      f"max: {op_metrics['max_duration']:.3f}s")
    
    # 6. Show LLM usage metrics
    print_section("6. LLM provider metrics")
    llm_metrics = monitoring.get_llm_metrics()
    
    for provider, metrics in llm_metrics.items():
        print(f"\n{provider.capitalize()}:")
        print(f"  Calls: {metrics['calls']}")
        print(f"  Errors: {metrics['errors']}")
        print(f"  Input Tokens: {metrics['tokens_input']}")
        print(f"  Output Tokens: {metrics['tokens_output']}")
        print(f"  Total Duration: {metrics['total_duration']:.2f}s")
        if metrics['calls'] > 0:
            print(f"  Avg Duration: {metrics['total_duration'] / metrics['calls']:.2f}s")
    
    # 7. Save metrics to disk
    print_section("7. Saving metrics to disk")
    metrics_file = monitoring.save_metrics()
    print(f"Metrics saved to: {metrics_file}")
    
    # 8. Reset metrics
    if input("\nReset metrics? (y/n): ").lower() == 'y':
        monitoring.reset_metrics()
        print("Metrics reset.")
        
        # Show empty metrics
        current = monitoring.get_metrics()
        print("\nCurrent metrics after reset:")
        print(f"  API Calls: {current['system']['api_calls']}")
        print(f"  Completed Tasks: {current['system']['completed_tasks']}")
    
    print("\nMonitoring demo complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()