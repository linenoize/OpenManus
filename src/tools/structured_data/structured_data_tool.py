"""
Structured Data Tool for OpenManus.

This tool provides functionalities to work with structured data formats:
- CSV: parsing, transformation, and analysis
- JSON: querying, transformation, and manipulation
- SQL: database connections and queries
- Data visualization capabilities
"""

import os
import json
import csv
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional, Union, Tuple
from pathlib import Path
import logging
import matplotlib.pyplot as plt
import io
import base64

# Configure logging
logger = logging.getLogger(__name__)

class StructuredDataTool:
    """
    Tool for working with structured data formats like CSV, JSON, and databases.
    Provides capabilities for data parsing, transformation, querying, and visualization.
    """
    
    def __init__(self, 
                base_path: str = "data/structured_data",
                db_path: str = "data/structured_data/databases",
                viz_path: str = "data/structured_data/visualizations"):
        """
        Initialize structured data tool with paths for storing data.
        
        Args:
            base_path: Base path for storing structured data files
            db_path: Path for SQLite database files
            viz_path: Path for saving visualizations
        """
        self.base_path = Path(base_path)
        self.db_path = Path(db_path)
        self.viz_path = Path(viz_path)
        
        # Ensure directories exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.viz_path.mkdir(parents=True, exist_ok=True)
        
        # Keep track of DB connections
        self.db_connections = {}
        
    def __del__(self):
        """Clean up database connections."""
        for conn in self.db_connections.values():
            try:
                conn.close()
            except:
                pass
                
    # ------ CSV Functions ------
    
    def read_csv(self, 
                file_path: str, 
                delimiter: str = ',',
                has_header: bool = True,
                limit: Optional[int] = None,
                sample: bool = False) -> List[Dict[str, Any]]:
        """
        Read a CSV file and return its contents as a list of dictionaries.
        
        Args:
            file_path: Path to the CSV file (if not absolute, relative to base_path)
            delimiter: CSV delimiter character
            has_header: Whether the CSV has a header row
            limit: Maximum number of rows to return (None for all)
            sample: If True and limit is provided, return random sample instead of first rows
            
        Returns:
            List of dictionaries representing CSV rows
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        # Read CSV into pandas DataFrame
        try:
            if has_header:
                df = pd.read_csv(file_path, delimiter=delimiter)
            else:
                df = pd.read_csv(file_path, delimiter=delimiter, header=None)
                df.columns = [f"column_{i}" for i in range(len(df.columns))]
                
            # Apply limit if specified
            if limit:
                if sample:
                    df = df.sample(min(limit, len(df)))
                else:
                    df = df.head(limit)
                    
            # Convert to list of dictionaries
            return df.to_dict(orient='records')
            
        except Exception as e:
            logger.error(f"Error reading CSV file {file_path}: {e}")
            return []
            
    def write_csv(self,
                 file_path: str,
                 data: List[Dict[str, Any]],
                 delimiter: str = ',',
                 include_header: bool = True) -> bool:
        """
        Write a list of dictionaries to a CSV file.
        
        Args:
            file_path: Path to save the CSV file (if not absolute, relative to base_path)
            data: List of dictionaries to write as CSV rows
            delimiter: CSV delimiter character
            include_header: Whether to include a header row
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            # Convert to pandas DataFrame and write to CSV
            df = pd.DataFrame(data)
            df.to_csv(file_path, sep=delimiter, index=False, header=include_header)
            return True
        except Exception as e:
            logger.error(f"Error writing CSV file {file_path}: {e}")
            return False
            
    def csv_summary(self, file_path: str, delimiter: str = ',') -> Dict[str, Any]:
        """
        Generate a summary of a CSV file including column statistics.
        
        Args:
            file_path: Path to the CSV file (if not absolute, relative to base_path)
            delimiter: CSV delimiter character
            
        Returns:
            Dictionary with summary statistics
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        try:
            # Read CSV into pandas DataFrame
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            # Generate summary
            summary = {
                "filename": os.path.basename(file_path),
                "row_count": len(df),
                "column_count": len(df.columns),
                "columns": df.columns.tolist(),
                "dtypes": {col: str(df[col].dtype) for col in df.columns},
                "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
                "numeric_columns": {}
            }
            
            # Add statistics for numeric columns
            for col in df.columns:
                if pd.api.types.is_numeric_dtype(df[col]):
                    summary["numeric_columns"][col] = {
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "median": float(df[col].median()),
                        "std": float(df[col].std())
                    }
                    
            return summary
            
        except Exception as e:
            logger.error(f"Error generating CSV summary for {file_path}: {e}")
            return {"error": str(e)}
            
    def filter_csv(self,
                  file_path: str,
                  filters: Dict[str, Any],
                  output_path: Optional[str] = None,
                  delimiter: str = ',') -> List[Dict[str, Any]]:
        """
        Filter CSV data based on column conditions.
        
        Args:
            file_path: Path to the CSV file (if not absolute, relative to base_path)
            filters: Dictionary mapping column names to filter values
            output_path: Optional path to save filtered results
            delimiter: CSV delimiter character
            
        Returns:
            Filtered data as a list of dictionaries
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        try:
            # Read CSV into pandas DataFrame
            df = pd.read_csv(file_path, delimiter=delimiter)
            
            # Apply filters
            for col, value in filters.items():
                if col in df.columns:
                    df = df[df[col] == value]
                    
            # Convert to list of dictionaries
            result = df.to_dict(orient='records')
            
            # Save to output file if specified
            if output_path:
                if not os.path.isabs(output_path):
                    output_path = self.base_path / output_path
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                df.to_csv(output_path, sep=delimiter, index=False)
                
            return result
            
        except Exception as e:
            logger.error(f"Error filtering CSV data from {file_path}: {e}")
            return []
            
    # ------ JSON Functions ------
    
    def read_json(self, file_path: str) -> Any:
        """
        Read a JSON file and return its contents.
        
        Args:
            file_path: Path to the JSON file (if not absolute, relative to base_path)
            
        Returns:
            Parsed JSON data (dict, list, etc.)
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading JSON file {file_path}: {e}")
            return None
            
    def write_json(self,
                  file_path: str,
                  data: Any,
                  pretty: bool = True) -> bool:
        """
        Write data to a JSON file.
        
        Args:
            file_path: Path to save the JSON file (if not absolute, relative to base_path)
            data: Data to write as JSON
            pretty: Whether to format the JSON with indentation
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve file path
        if not os.path.isabs(file_path):
            file_path = self.base_path / file_path
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        try:
            with open(file_path, 'w') as f:
                if pretty:
                    json.dump(data, f, indent=2)
                else:
                    json.dump(data, f)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON file {file_path}: {e}")
            return False
            
    def query_json(self, 
                  data: Union[Dict[str, Any], List[Dict[str, Any]]],
                  query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query JSON data using simple key-value matches.
        
        Args:
            data: JSON data to query (dict or list of dicts)
            query: Dictionary of key-value pairs to match
            
        Returns:
            List of matching items
        """
        results = []
        
        # Convert single dict to list
        if isinstance(data, dict):
            data = [data]
            
        # Handle case where data is not a list of dicts
        if not isinstance(data, list):
            return []
            
        # Process each item
        for item in data:
            if not isinstance(item, dict):
                continue
                
            # Check if all query conditions match
            match = True
            for key, value in query.items():
                # Support nested keys with dot notation
                if '.' in key:
                    parts = key.split('.')
                    curr = item
                    for part in parts[:-1]:
                        if isinstance(curr, dict) and part in curr:
                            curr = curr[part]
                        else:
                            curr = None
                            break
                    
                    if curr is None or parts[-1] not in curr or curr[parts[-1]] != value:
                        match = False
                        break
                # Simple key
                elif key not in item or item[key] != value:
                    match = False
                    break
                    
            if match:
                results.append(item)
                
        return results
            
    def transform_json(self,
                      data: Union[Dict[str, Any], List[Dict[str, Any]]],
                      mapping: Dict[str, str]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Transform JSON data structure using a key mapping.
        
        Args:
            data: Original JSON data
            mapping: Dict mapping new keys to original keys or path expressions
            
        Returns:
            Transformed data with the new structure
        """
        # Helper function to get nested values
        def get_nested_value(obj, path):
            parts = path.split('.')
            curr = obj
            for part in parts:
                if isinstance(curr, dict) and part in curr:
                    curr = curr[part]
                else:
                    return None
            return curr
        
        # Process single dict
        if isinstance(data, dict):
            result = {}
            for new_key, path in mapping.items():
                result[new_key] = get_nested_value(data, path)
            return result
            
        # Process list of dicts
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, dict):
                    transformed = {}
                    for new_key, path in mapping.items():
                        transformed[new_key] = get_nested_value(item, path)
                    result.append(transformed)
            return result
            
        # Unsupported data type
        return data
            
    # ------ SQL Database Functions ------
    
    def connect_db(self, db_name: str) -> bool:
        """
        Connect to an SQLite database.
        
        Args:
            db_name: Name of the database (if not a full path, stored in db_path)
            
        Returns:
            True if connection successful, False otherwise
        """
        # Check if already connected
        if db_name in self.db_connections and self.db_connections[db_name]:
            return True
            
        # Resolve database path
        if not db_name.endswith('.db'):
            db_name += '.db'
            
        if os.path.sep not in db_name:
            db_path = self.db_path / db_name
        else:
            db_path = db_name  # Assume it's a full path
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.db_connections[db_name] = conn
            return True
        except Exception as e:
            logger.error(f"Error connecting to database {db_name}: {e}")
            return False
            
    def execute_query(self,
                     db_name: str,
                     query: str,
                     params: Optional[Union[Tuple, Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """
        Execute an SQL query on a database.
        
        Args:
            db_name: Name of the database to query
            query: SQL query to execute
            params: Optional parameters for the query (for parameterized queries)
            
        Returns:
            List of dictionaries containing query results
        """
        # Connect to database if not already connected
        if db_name not in self.db_connections or not self.db_connections[db_name]:
            if not self.connect_db(db_name):
                return []
                
        conn = self.db_connections[db_name]
        
        try:
            cursor = conn.cursor()
            
            # Execute query with or without parameters
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            # Get results for SELECT queries
            if query.strip().upper().startswith('SELECT'):
                results = []
                for row in cursor.fetchall():
                    results.append(dict(row))
                return results
            else:
                # For non-SELECT queries, commit and return empty list
                conn.commit()
                return []
                
        except Exception as e:
            logger.error(f"Error executing query on {db_name}: {e}")
            return []
            
    def get_table_schema(self, db_name: str, table_name: str) -> List[Dict[str, Any]]:
        """
        Get the schema of a table in a database.
        
        Args:
            db_name: Name of the database
            table_name: Name of the table
            
        Returns:
            List of column information dictionaries
        """
        # Connect to database if not already connected
        if db_name not in self.db_connections or not self.db_connections[db_name]:
            if not self.connect_db(db_name):
                return []
                
        conn = self.db_connections[db_name]
        
        try:
            # Get table schema
            query = f"PRAGMA table_info({table_name});"
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Parse results
            columns = []
            for row in cursor.fetchall():
                columns.append({
                    "cid": row["cid"],
                    "name": row["name"],
                    "type": row["type"],
                    "notnull": row["notnull"] == 1,
                    "default_value": row["dflt_value"],
                    "pk": row["pk"] == 1
                })
                
            return columns
            
        except Exception as e:
            logger.error(f"Error getting schema for {table_name} in {db_name}: {e}")
            return []
            
    def list_tables(self, db_name: str) -> List[str]:
        """
        List all tables in a database.
        
        Args:
            db_name: Name of the database
            
        Returns:
            List of table names
        """
        # Connect to database if not already connected
        if db_name not in self.db_connections or not self.db_connections[db_name]:
            if not self.connect_db(db_name):
                return []
                
        conn = self.db_connections[db_name]
        
        try:
            # Query for all tables
            query = "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
            cursor = conn.cursor()
            cursor.execute(query)
            
            # Extract table names
            tables = [row["name"] for row in cursor.fetchall()]
            return tables
            
        except Exception as e:
            logger.error(f"Error listing tables in {db_name}: {e}")
            return []
            
    def csv_to_sql(self,
                  csv_file: str,
                  db_name: str,
                  table_name: str,
                  delimiter: str = ',',
                  if_exists: str = 'replace') -> bool:
        """
        Import a CSV file into an SQLite database table.
        
        Args:
            csv_file: Path to the CSV file
            db_name: Database name
            table_name: Table name to create
            delimiter: CSV delimiter
            if_exists: What to do if table exists ('replace', 'append', 'fail')
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve CSV file path
        if not os.path.isabs(csv_file):
            csv_file = self.base_path / csv_file
            
        # Connect to database
        if not self.connect_db(db_name):
            return False
            
        try:
            # Read CSV with pandas
            df = pd.read_csv(csv_file, delimiter=delimiter)
            
            # Get database connection
            conn = self.db_connections[db_name]
            
            # Write to database
            df.to_sql(table_name, conn, if_exists=if_exists, index=False)
            return True
            
        except Exception as e:
            logger.error(f"Error importing CSV to database: {e}")
            return False
            
    def sql_to_csv(self,
                  db_name: str,
                  query: str,
                  output_file: str,
                  delimiter: str = ',',
                  params: Optional[Union[Tuple, Dict[str, Any]]] = None) -> bool:
        """
        Export SQL query results to a CSV file.
        
        Args:
            db_name: Database name
            query: SQL query to execute
            output_file: Path to save the CSV output
            delimiter: CSV delimiter
            params: Optional parameters for the query
            
        Returns:
            True if successful, False otherwise
        """
        # Resolve output file path
        if not os.path.isabs(output_file):
            output_file = self.base_path / output_file
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Execute query
        results = self.execute_query(db_name, query, params)
        if not results:
            return False
            
        try:
            # Convert to DataFrame and save to CSV
            df = pd.DataFrame(results)
            df.to_csv(output_file, sep=delimiter, index=False)
            return True
            
        except Exception as e:
            logger.error(f"Error exporting query results to CSV: {e}")
            return False
            
    # ------ Data Visualization Functions ------
    
    def generate_chart(self,
                      data: Union[List[Dict[str, Any]], pd.DataFrame],
                      chart_type: str,
                      x_column: str,
                      y_column: Optional[str] = None,
                      title: str = "",
                      output_path: Optional[str] = None,
                      **kwargs) -> Optional[str]:
        """
        Generate a visualization chart from data.
        
        Args:
            data: Data to visualize (list of dicts or DataFrame)
            chart_type: Type of chart ('bar', 'line', 'scatter', 'pie', 'histogram')
            x_column: Column name for x-axis
            y_column: Column name for y-axis (not needed for all chart types)
            title: Chart title
            output_path: Path to save the chart image (if not provided, returns base64)
            **kwargs: Additional plotting parameters
            
        Returns:
            Base64-encoded image string if output_path is None, otherwise None
        """
        # Convert to DataFrame if needed
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data
            
        # Create figure
        plt.figure(figsize=kwargs.get('figsize', (10, 6)))
        
        # Generate the requested chart type
        if chart_type == 'bar':
            df.plot(kind='bar', x=x_column, y=y_column, ax=plt.gca())
            
        elif chart_type == 'line':
            df.plot(kind='line', x=x_column, y=y_column, ax=plt.gca())
            
        elif chart_type == 'scatter':
            df.plot(kind='scatter', x=x_column, y=y_column, ax=plt.gca())
            
        elif chart_type == 'pie':
            df.plot(kind='pie', y=y_column, ax=plt.gca(), labels=df[x_column])
            
        elif chart_type == 'histogram':
            df[x_column].plot(kind='hist', bins=kwargs.get('bins', 10), ax=plt.gca())
            
        else:
            logger.error(f"Unsupported chart type: {chart_type}")
            return None
            
        # Add title and labels
        plt.title(title)
        plt.xlabel(kwargs.get('xlabel', x_column))
        plt.ylabel(kwargs.get('ylabel', y_column if y_column else 'Count'))
        
        # Add grid if requested
        if kwargs.get('grid', True):
            plt.grid(alpha=0.3)
            
        # Handle output
        if output_path:
            # Save to file
            if not os.path.isabs(output_path):
                output_path = self.viz_path / output_path
                
            # Ensure parent directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            plt.savefig(output_path, bbox_inches='tight', dpi=kwargs.get('dpi', 100))
            plt.close()
            return output_path
        else:
            # Return as base64
            buf = io.BytesIO()
            plt.savefig(buf, format='png', bbox_inches='tight', dpi=kwargs.get('dpi', 100))
            plt.close()
            buf.seek(0)
            img_str = base64.b64encode(buf.read()).decode('utf-8')
            return img_str
            
    def generate_summary_stats(self,
                              data: Union[List[Dict[str, Any]], pd.DataFrame],
                              columns: Optional[List[str]] = None,
                              include_corr: bool = True) -> Dict[str, Any]:
        """
        Generate summary statistics for data.
        
        Args:
            data: Data to analyze (list of dicts or DataFrame)
            columns: List of column names to include (None for all numeric columns)
            include_corr: Whether to include correlation matrix
            
        Returns:
            Dictionary of summary statistics
        """
        # Convert to DataFrame if needed
        if not isinstance(data, pd.DataFrame):
            df = pd.DataFrame(data)
        else:
            df = data
            
        # Select columns if specified
        if columns:
            df = df[columns]
            
        # Get descriptive statistics
        stats = {}
        
        # Overall information
        stats["row_count"] = len(df)
        stats["column_count"] = len(df.columns)
        
        # Per-column statistics
        stats["columns"] = {}
        for col in df.columns:
            col_stats = {}
            
            # Type information
            col_stats["dtype"] = str(df[col].dtype)
            col_stats["missing"] = int(df[col].isna().sum())
            
            # Numeric column statistics
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats["min"] = float(df[col].min())
                col_stats["max"] = float(df[col].max())
                col_stats["mean"] = float(df[col].mean())
                col_stats["median"] = float(df[col].median())
                col_stats["std"] = float(df[col].std())
                
            # Categorical column statistics
            elif pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
                value_counts = df[col].value_counts().to_dict()
                col_stats["unique_values"] = len(value_counts)
                col_stats["top_values"] = {str(k): int(v) for k, v in sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:5]}
                
            stats["columns"][col] = col_stats
            
        # Correlation matrix for numeric columns
        if include_corr:
            numeric_df = df.select_dtypes(include='number')
            if not numeric_df.empty:
                corr_matrix = numeric_df.corr().to_dict()
                stats["correlation"] = corr_matrix
                
        return stats