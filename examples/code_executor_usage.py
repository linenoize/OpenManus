#!/usr/bin/env python3
"""
Example script demonstrating the use of the code executor tool in OpenManus.
This script shows how to execute code snippets in various programming languages.
"""

import sys
import os
import time

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.code_executor import CodeExecutorTool
except ImportError as e:
    print(f"Error importing CodeExecutorTool: {e}")
    sys.exit(1)

def print_section(title):
    """Helper to print formatted section titles"""
    print(f"\n{title}")
    print("=" * len(title))

def main():
    print("OpenManus Code Executor Tool Demo")
    print("=" * 60)
    
    # Initialize code executor tool
    executor = CodeExecutorTool()
    print("Code Executor initialized")
    
    # Example 1: Python code
    print_section("1. Executing Python code")
    
    python_code = """
def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

# Calculate first 10 Fibonacci numbers
for i in range(10):
    print(f"Fibonacci({i}) = {fibonacci(i)}")
    """
    
    print("Python code to execute:")
    print(python_code)
    
    result = executor.execute_code(python_code, "python")
    print("\nExecution result:")
    print(result)
    
    # Example 2: JavaScript code
    print_section("2. Executing JavaScript code")
    
    js_code = """
// Calculate factorial
function factorial(n) {
    if (n === 0 || n === 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// Print factorials 1-5
for (let i = 1; i <= 5; i++) {
    console.log(`Factorial of ${i} is ${factorial(i)}`);
}
    """
    
    print("JavaScript code to execute:")
    print(js_code)
    
    result = executor.execute_code(js_code, "javascript")
    print("\nExecution result:")
    print(result)
    
    # Example 3: SQL query
    print_section("3. Executing SQL query")
    
    sql_code = """
-- Create a sample table
CREATE TABLE employees (
    id INTEGER PRIMARY KEY,
    name TEXT,
    position TEXT,
    salary REAL
);

-- Insert some data
INSERT INTO employees VALUES (1, 'John Doe', 'Developer', 75000);
INSERT INTO employees VALUES (2, 'Jane Smith', 'Engineer', 82000);
INSERT INTO employees VALUES (3, 'Bob Johnson', 'Manager', 95000);

-- Query the data
SELECT name, position, salary
FROM employees
WHERE salary > 80000;
    """
    
    print("SQL code to execute:")
    print(sql_code)
    
    result = executor.execute_code(sql_code, "sql")
    print("\nExecution result:")
    print(result)
    
    # Example 4: Shell script
    print_section("4. Executing Shell script")
    
    shell_code = """
#!/bin/bash
# Simple system information script

echo "System Information:"
echo "==================="
echo "Hostname: $(hostname)"
echo "Current user: $(whoami)"
echo "Current directory: $(pwd)"
echo "Current date: $(date)"
echo "-------------------"
echo "Listing directory contents:"
ls -la
    """
    
    print("Shell script to execute:")
    print(shell_code)
    
    result = executor.execute_code(shell_code, "bash")
    print("\nExecution result:")
    print(result)
    
    # Example 5: Markdown rendering
    print_section("5. Rendering Markdown")
    
    markdown_code = """
# Sample Document

This is a demonstration of Markdown rendering capabilities in the CodeExecutorTool.

## Features

- **Bold text** and *italic text*
- Ordered and unordered lists
- Code blocks with syntax highlighting
- Tables and other formatting

## Example Code

```python
def hello_world():
    print("Hello, world!")
```

## Table Example

| Name | Role | Department |
|------|------|------------|
| Alice | Manager | Engineering |
| Bob | Developer | Engineering |
| Carol | Designer | Product |
    """
    
    print("Markdown code to render:")
    print(markdown_code)
    
    result = executor.execute_code(markdown_code, "markdown")
    print("\nRendering result:")
    print(result)
    
    print("\nCode Executor demo complete!")
    print("=" * 60)
    print("Note: This demo uses placeholder implementations. In a real environment,")
    print("the CodeExecutorTool would execute code in safe, isolated environments.")

if __name__ == "__main__":
    main()