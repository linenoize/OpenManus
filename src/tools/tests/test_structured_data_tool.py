import unittest
import os
import tempfile
import shutil
import json
import pandas as pd
import sqlite3
from pathlib import Path

from src.tools.structured_data import StructuredDataTool

class TestStructuredDataTool(unittest.TestCase):
    """Tests for Structured Data Tool."""
    
    def setUp(self):
        # Create a temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize the structured data tool with the test directory
        self.data_tool = StructuredDataTool(
            base_path=os.path.join(self.test_dir, "data"),
            db_path=os.path.join(self.test_dir, "data/db"),
            viz_path=os.path.join(self.test_dir, "data/viz")
        )
        
        # Create test CSV data
        self.csv_data = [
            {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
            {"id": 2, "name": "Bob", "age": 25, "city": "San Francisco"},
            {"id": 3, "name": "Charlie", "age": 35, "city": "Chicago"},
            {"id": 4, "name": "Diana", "age": 28, "city": "Boston"},
            {"id": 5, "name": "Eve", "age": 40, "city": "Seattle"}
        ]
        
        # Create test JSON data
        self.json_data = {
            "users": [
                {"id": 1, "profile": {"name": "Alice", "email": "alice@example.com"}},
                {"id": 2, "profile": {"name": "Bob", "email": "bob@example.com"}},
                {"id": 3, "profile": {"name": "Charlie", "email": "charlie@example.com"}}
            ],
            "metadata": {
                "version": "1.0",
                "count": 3
            }
        }
        
        # Save test data to files
        os.makedirs(os.path.join(self.test_dir, "data"), exist_ok=True)
        
        # CSV file
        df = pd.DataFrame(self.csv_data)
        self.csv_path = os.path.join(self.test_dir, "data/test.csv")
        df.to_csv(self.csv_path, index=False)
        
        # JSON file
        self.json_path = os.path.join(self.test_dir, "data/test.json")
        with open(self.json_path, "w") as f:
            json.dump(self.json_data, f)
        
    def tearDown(self):
        # Clean up test directory
        shutil.rmtree(self.test_dir)
    
    # ------ CSV Tests ------
    
    def test_read_csv(self):
        """Test reading a CSV file."""
        # Read the entire CSV
        data = self.data_tool.read_csv(self.csv_path)
        self.assertEqual(len(data), 5)
        self.assertEqual(data[0]["name"], "Alice")
        
        # Read with limit
        limited_data = self.data_tool.read_csv(self.csv_path, limit=2)
        self.assertEqual(len(limited_data), 2)
        
    def test_write_csv(self):
        """Test writing data to a CSV file."""
        output_path = "output.csv"
        result = self.data_tool.write_csv(output_path, self.csv_data)
        self.assertTrue(result)
        
        # Verify the file was written correctly
        full_path = os.path.join(self.test_dir, "data", output_path)
        self.assertTrue(os.path.exists(full_path))
        
        # Read it back to check contents
        df = pd.read_csv(full_path)
        self.assertEqual(len(df), 5)
        
    def test_csv_summary(self):
        """Test generating summary statistics for a CSV file."""
        summary = self.data_tool.csv_summary(self.csv_path)
        
        # Check basic summary info
        self.assertEqual(summary["row_count"], 5)
        self.assertEqual(summary["column_count"], 4)
        
        # Check numeric column stats
        self.assertIn("age", summary["numeric_columns"])
        self.assertEqual(summary["numeric_columns"]["age"]["min"], 25)
        self.assertEqual(summary["numeric_columns"]["age"]["max"], 40)
        
    def test_filter_csv(self):
        """Test filtering CSV data."""
        # Filter for people in New York
        filtered = self.data_tool.filter_csv(self.csv_path, {"city": "New York"})
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "Alice")
        
        # Filter for multiple conditions
        # (This will return no results since no one is both 30 and in Boston)
        multi_filter = self.data_tool.filter_csv(self.csv_path, {"age": 30, "city": "Boston"})
        self.assertEqual(len(multi_filter), 0)
        
    # ------ JSON Tests ------
    
    def test_read_json(self):
        """Test reading a JSON file."""
        data = self.data_tool.read_json(self.json_path)
        self.assertIsNotNone(data)
        self.assertEqual(len(data["users"]), 3)
        self.assertEqual(data["metadata"]["version"], "1.0")
        
    def test_write_json(self):
        """Test writing data to a JSON file."""
        output_path = "output.json"
        result = self.data_tool.write_json(output_path, self.json_data)
        self.assertTrue(result)
        
        # Verify the file was written correctly
        full_path = os.path.join(self.test_dir, "data", output_path)
        self.assertTrue(os.path.exists(full_path))
        
        # Read it back to check contents
        with open(full_path, 'r') as f:
            data = json.load(f)
        self.assertEqual(len(data["users"]), 3)
        
    def test_query_json(self):
        """Test querying JSON data."""
        # Simple query
        results = self.data_tool.query_json(self.json_data["users"], {"id": 2})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["profile"]["name"], "Bob")
        
        # Nested query using dot notation
        results = self.data_tool.query_json(
            self.json_data["users"], 
            {"profile.name": "Charlie"}
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["id"], 3)
        
    def test_transform_json(self):
        """Test transforming JSON data structure."""
        # Define mapping from new keys to original paths
        mapping = {
            "userId": "id",
            "userName": "profile.name",
            "userEmail": "profile.email"
        }
        
        # Transform the data
        transformed = self.data_tool.transform_json(self.json_data["users"], mapping)
        
        # Check the transformed structure
        self.assertEqual(len(transformed), 3)
        self.assertEqual(transformed[0]["userId"], 1)
        self.assertEqual(transformed[0]["userName"], "Alice")
        self.assertEqual(transformed[0]["userEmail"], "alice@example.com")
        
    # ------ SQL Database Tests ------
    
    def test_connect_db(self):
        """Test connecting to an SQLite database."""
        result = self.data_tool.connect_db("test_db")
        self.assertTrue(result)
        self.assertIn("test_db.db", self.data_tool.db_connections)
        
    def test_csv_to_sql_and_query(self):
        """Test importing CSV to SQL and querying it."""
        # Import CSV to database
        self.data_tool.connect_db("test_db")
        result = self.data_tool.csv_to_sql(self.csv_path, "test_db", "people")
        self.assertTrue(result)
        
        # Check if table was created
        tables = self.data_tool.list_tables("test_db")
        self.assertIn("people", tables)
        
        # Get table schema
        schema = self.data_tool.get_table_schema("test_db", "people")
        self.assertEqual(len(schema), 4)  # id, name, age, city
        
        # Execute a query
        query_result = self.data_tool.execute_query(
            "test_db", 
            "SELECT * FROM people WHERE age > ?", 
            (30,)
        )
        self.assertEqual(len(query_result), 2)  # Charlie and Eve
        
    def test_sql_to_csv(self):
        """Test exporting SQL query results to CSV."""
        # First import CSV to database
        self.data_tool.connect_db("test_db")
        self.data_tool.csv_to_sql(self.csv_path, "test_db", "people")
        
        # Export query results to CSV
        output_path = "query_results.csv"
        result = self.data_tool.sql_to_csv(
            "test_db",
            "SELECT name, age FROM people WHERE age > 30",
            output_path
        )
        self.assertTrue(result)
        
        # Verify the file was written correctly
        full_path = os.path.join(self.test_dir, "data", output_path)
        self.assertTrue(os.path.exists(full_path))
        
        # Read it back to check contents
        df = pd.read_csv(full_path)
        self.assertEqual(len(df), 2)  # Charlie and Eve
        
    # ------ Visualization Tests ------
    
    def test_generate_chart(self):
        """Test generating a chart from data."""
        # Generate a bar chart
        chart_result = self.data_tool.generate_chart(
            self.csv_data,
            chart_type="bar",
            x_column="name",
            y_column="age",
            title="Age by Person",
            output_path="chart.png"
        )
        
        # Verify the chart was saved
        self.assertIsNotNone(chart_result)
        chart_path = os.path.join(self.test_dir, "data/viz", "chart.png")
        self.assertTrue(os.path.exists(chart_path))
        
        # Test base64 output
        base64_result = self.data_tool.generate_chart(
            self.csv_data,
            chart_type="line",
            x_column="name",
            y_column="age",
            title="Age by Person"
        )
        self.assertIsNotNone(base64_result)
        self.assertTrue(isinstance(base64_result, str))
        
    def test_generate_summary_stats(self):
        """Test generating summary statistics."""
        stats = self.data_tool.generate_summary_stats(self.csv_data)
        
        # Check basic stats
        self.assertEqual(stats["row_count"], 5)
        self.assertEqual(stats["column_count"], 4)
        
        # Check column stats
        self.assertIn("age", stats["columns"])
        self.assertEqual(stats["columns"]["age"]["min"], 25)
        self.assertEqual(stats["columns"]["age"]["max"], 40)
        
        # Check correlation
        self.assertIn("correlation", stats)
        

if __name__ == '__main__':
    unittest.main()