#!/usr/bin/env python3
"""
Example script demonstrating the use of the Structured Data Tool in OpenManus.

This script shows how to work with:
- CSV data: reading, filtering, and analyzing
- JSON data: querying and transforming
- SQLite databases: importing, querying, and exporting
- Data visualization: generating charts and summary statistics
"""

import os
import sys
import json
import base64
from pathlib import Path
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, display
from io import BytesIO

# Add the parent directory to sys.path to import OpenManus modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.tools.structured_data import StructuredDataTool
except ImportError as e:
    print(f"Error importing StructuredDataTool: {e}")
    print("Please install the required dependencies:")
    print("  pip install pandas matplotlib numpy")
    sys.exit(1)

# Create sample data directory
EXAMPLES_DIR = Path("data/examples/structured_data")
EXAMPLES_DIR.mkdir(parents=True, exist_ok=True)

def create_sample_data():
    """Create sample files for the examples."""
    # Sample CSV data - Employee records
    employees = [
        {"id": 1, "name": "John Smith", "department": "Engineering", "salary": 85000, "years_experience": 5},
        {"id": 2, "name": "Jane Doe", "department": "Marketing", "salary": 75000, "years_experience": 3},
        {"id": 3, "name": "Michael Brown", "department": "Engineering", "salary": 92000, "years_experience": 7},
        {"id": 4, "name": "Emma Wilson", "department": "Sales", "salary": 79000, "years_experience": 4},
        {"id": 5, "name": "Robert Johnson", "department": "Engineering", "salary": 115000, "years_experience": 10},
        {"id": 6, "name": "Lisa Davis", "department": "Marketing", "salary": 68000, "years_experience": 2},
        {"id": 7, "name": "David Miller", "department": "Sales", "salary": 81000, "years_experience": 5},
        {"id": 8, "name": "Sarah Wilson", "department": "Engineering", "salary": 95000, "years_experience": 8},
        {"id": 9, "name": "James Anderson", "department": "Sales", "salary": 110000, "years_experience": 9},
        {"id": 10, "name": "Emily Thomas", "department": "Marketing", "salary": 82000, "years_experience": 6}
    ]
    
    # Save as CSV
    df = pd.DataFrame(employees)
    df.to_csv(EXAMPLES_DIR / "employees.csv", index=False)
    
    # Sample JSON data - Product catalog
    products = {
        "product_catalog": {
            "version": "2.0",
            "last_updated": datetime.now().isoformat(),
            "products": [
                {
                    "id": "p1001",
                    "name": "Smartphone X",
                    "category": "Electronics",
                    "details": {
                        "price": 799.99,
                        "rating": 4.5,
                        "in_stock": True,
                        "specs": {
                            "display": "6.5 inch OLED",
                            "processor": "Snapdragon 8 Gen 2",
                            "camera": "108MP"
                        }
                    }
                },
                {
                    "id": "p1002",
                    "name": "Laptop Pro",
                    "category": "Electronics",
                    "details": {
                        "price": 1299.99,
                        "rating": 4.8,
                        "in_stock": True,
                        "specs": {
                            "display": "15.6 inch 4K",
                            "processor": "Intel i9-12900H",
                            "memory": "32GB DDR5"
                        }
                    }
                },
                {
                    "id": "p1003",
                    "name": "Wireless Headphones",
                    "category": "Electronics",
                    "details": {
                        "price": 249.99,
                        "rating": 4.3,
                        "in_stock": False,
                        "specs": {
                            "type": "Over-ear",
                            "battery": "30 hours",
                            "features": "Noise cancellation"
                        }
                    }
                },
                {
                    "id": "p2001",
                    "name": "Running Shoes",
                    "category": "Sports",
                    "details": {
                        "price": 129.99,
                        "rating": 4.2,
                        "in_stock": True,
                        "specs": {
                            "material": "Synthetic mesh",
                            "sizes": [7, 8, 9, 10, 11, 12],
                            "colors": ["Black", "White", "Red"]
                        }
                    }
                },
                {
                    "id": "p3001",
                    "name": "Coffee Maker",
                    "category": "Home",
                    "details": {
                        "price": 89.99,
                        "rating": 4.0,
                        "in_stock": True,
                        "specs": {
                            "capacity": "12 cups",
                            "features": "Programmable timer",
                            "warranty": "2 years"
                        }
                    }
                }
            ]
        }
    }
    
    # Save as JSON
    with open(EXAMPLES_DIR / "products.json", "w") as f:
        json.dump(products, f, indent=2)

    print(f"Created sample data files in {EXAMPLES_DIR}")

def csv_examples(data_tool):
    """Examples for working with CSV data."""
    print("\n===== CSV Examples =====")
    
    # Read CSV file
    print("\n1. Reading CSV data:")
    employees = data_tool.read_csv(EXAMPLES_DIR / "employees.csv")
    print(f"Loaded {len(employees)} employee records")
    print(f"First employee: {employees[0]['name']}, {employees[0]['department']}, ${employees[0]['salary']}")
    
    # Filter CSV data
    print("\n2. Filtering CSV data:")
    engineering = data_tool.filter_csv(
        EXAMPLES_DIR / "employees.csv",
        {"department": "Engineering"}
    )
    print(f"Found {len(engineering)} employees in Engineering")
    
    # Get a CSV summary
    print("\n3. CSV Summary Statistics:")
    summary = data_tool.csv_summary(EXAMPLES_DIR / "employees.csv")
    print(f"Number of rows: {summary['row_count']}")
    print(f"Number of columns: {summary['column_count']}")
    print(f"Salary range: ${summary['numeric_columns']['salary']['min']} - ${summary['numeric_columns']['salary']['max']}")
    print(f"Average salary: ${summary['numeric_columns']['salary']['mean']:.2f}")
    
    # Write filtered data to a new CSV
    high_earners = data_tool.filter_csv(
        EXAMPLES_DIR / "employees.csv",
        {"salary": lambda x: x > 90000}  # Using a lambda for comparison
    )
    data_tool.write_csv("high_earners.csv", high_earners)
    print(f"\nWrote {len(high_earners)} high earners to a new CSV file")
    
    return employees

def json_examples(data_tool):
    """Examples for working with JSON data."""
    print("\n===== JSON Examples =====")
    
    # Read JSON file
    print("\n1. Reading JSON data:")
    product_data = data_tool.read_json(EXAMPLES_DIR / "products.json")
    products = product_data["product_catalog"]["products"]
    print(f"Loaded {len(products)} products")
    print(f"Product catalog version: {product_data['product_catalog']['version']}")
    
    # Query JSON data
    print("\n2. Querying JSON data:")
    # Find electronics products
    electronics = data_tool.query_json(products, {"category": "Electronics"})
    print(f"Found {len(electronics)} electronics products")
    
    # Find products with high ratings
    high_rated = [p for p in products if p["details"]["rating"] >= 4.5]
    print(f"Found {len(high_rated)} highly rated products (4.5+ stars)")
    
    # Find out-of-stock products using dot notation
    out_of_stock = data_tool.query_json(products, {"details.in_stock": False})
    print(f"Found {len(out_of_stock)} out-of-stock products: {out_of_stock[0]['name']}")
    
    # Transform JSON structure
    print("\n3. Transforming JSON data:")
    # Simplify the product structure
    mapping = {
        "productId": "id",
        "productName": "name",
        "price": "details.price",
        "rating": "details.rating",
        "available": "details.in_stock"
    }
    
    simplified = data_tool.transform_json(products, mapping)
    print("Simplified product structure:")
    print(json.dumps(simplified[0], indent=2))
    
    # Save transformed data
    data_tool.write_json("simplified_products.json", simplified)
    print("Saved simplified product data to JSON file")
    
    return products

def sql_examples(data_tool, employees):
    """Examples for working with SQL databases."""
    print("\n===== SQL Database Examples =====")
    
    # Connect to a database
    print("\n1. Creating and connecting to a database:")
    if data_tool.connect_db("example_db"):
        print("Connected to example_db successfully")
    
    # Import CSV to a table
    print("\n2. Importing CSV data to a table:")
    result = data_tool.csv_to_sql(
        EXAMPLES_DIR / "employees.csv",
        "example_db",
        "employees"
    )
    if result:
        print("Successfully imported employee data to database")
    
    # List tables
    tables = data_tool.list_tables("example_db")
    print(f"Database tables: {', '.join(tables)}")
    
    # Get table schema
    print("\n3. Table schema:")
    schema = data_tool.get_table_schema("example_db", "employees")
    for column in schema:
        print(f"  {column['name']}: {column['type']}" + (" (Primary Key)" if column['pk'] else ""))
    
    # Execute queries
    print("\n4. Executing SQL queries:")
    
    # Get average salary by department
    avg_salary_query = """
    SELECT department, AVG(salary) as avg_salary 
    FROM employees 
    GROUP BY department 
    ORDER BY avg_salary DESC
    """
    
    avg_salaries = data_tool.execute_query("example_db", avg_salary_query)
    print("Average salary by department:")
    for dept in avg_salaries:
        print(f"  {dept['department']}: ${dept['avg_salary']:.2f}")
    
    # Find employees with the highest salary in each department
    top_earners_query = """
    SELECT e1.name, e1.department, e1.salary
    FROM employees e1
    JOIN (
        SELECT department, MAX(salary) as max_salary
        FROM employees
        GROUP BY department
    ) e2 ON e1.department = e2.department AND e1.salary = e2.max_salary
    ORDER BY e1.salary DESC
    """
    
    top_earners = data_tool.execute_query("example_db", top_earners_query)
    print("\nTop earners by department:")
    for emp in top_earners:
        print(f"  {emp['name']} ({emp['department']}): ${emp['salary']}")
    
    # Export query results to CSV
    export_result = data_tool.sql_to_csv(
        "example_db",
        top_earners_query,
        "top_earners_by_dept.csv"
    )
    if export_result:
        print("\nExported top earners query results to CSV file")
    
    return top_earners

def visualization_examples(data_tool, employees, products):
    """Examples for data visualization."""
    print("\n===== Data Visualization Examples =====")
    
    # Bar chart of salaries by employee
    print("\n1. Generating bar chart:")
    salary_chart = data_tool.generate_chart(
        employees,
        chart_type="bar",
        x_column="name",
        y_column="salary",
        title="Employee Salaries",
        output_path="salary_chart.png",
        figsize=(12, 6)
    )
    print(f"Saved salary bar chart to {salary_chart}")
    
    # Scatter plot of salary vs. experience
    print("\n2. Generating scatter plot:")
    scatter_chart = data_tool.generate_chart(
        employees,
        chart_type="scatter",
        x_column="years_experience",
        y_column="salary",
        title="Salary vs. Experience",
        output_path="scatter_chart.png",
        xlabel="Years of Experience",
        ylabel="Salary ($)"
    )
    print(f"Saved scatter plot to {scatter_chart}")
    
    # Prepare data for price comparison chart
    product_prices = [
        {"name": p["name"], "price": p["details"]["price"]}
        for p in products
    ]
    
    # Bar chart of product prices
    print("\n3. Generating product price comparison:")
    price_chart = data_tool.generate_chart(
        product_prices,
        chart_type="bar",
        x_column="name",
        y_column="price",
        title="Product Price Comparison",
        output_path="price_chart.png",
        figsize=(10, 5),
        ylabel="Price ($)"
    )
    print(f"Saved price comparison chart to {price_chart}")
    
    # Generate summary statistics
    print("\n4. Generating summary statistics:")
    stats = data_tool.generate_summary_stats(employees)
    
    print("Salary statistics:")
    salary_stats = stats["columns"]["salary"]
    print(f"  Min: ${salary_stats['min']}")
    print(f"  Max: ${salary_stats['max']}")
    print(f"  Mean: ${salary_stats['mean']:.2f}")
    print(f"  Median: ${salary_stats['median']:.2f}")
    print(f"  Standard Deviation: ${salary_stats['std']:.2f}")
    
    print("\nCorrelation between salary and years of experience:")
    print(f"  {stats['correlation']['salary']['years_experience']:.4f}")
    
    return stats

def main():
    print("OpenManus Structured Data Tool Demo")
    print("=" * 60)
    
    # Create sample data for examples
    create_sample_data()
    
    # Initialize the structured data tool
    data_tool = StructuredDataTool()
    
    # Run examples
    employees = csv_examples(data_tool)
    products = json_examples(data_tool)
    top_earners = sql_examples(data_tool, employees)
    stats = visualization_examples(data_tool, employees, products)
    
    print("\nStructured data processing demo complete!")
    print("=" * 60)
    print(f"All output files are saved in {data_tool.base_path}")

if __name__ == "__main__":
    main()