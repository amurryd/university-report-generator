"""
Data Processor Module
Handles reading Excel files and analyzing data

This module is responsible for:
- Reading Excel files with pandas
- Cleaning and validating data
- Calculating statistics
- Preparing data summaries for AI
"""

import pandas as pd
import numpy as np
from pathlib import Path


class DataProcessor:
    """
    Processes university data from Excel files
    
    This class handles all data-related operations:
    - Reading Excel files
    - Data validation
    - Statistical analysis
    - Summary generation
    """
    
    def __init__(self):
        """Initialize the data processor"""
        print("✓ Data Processor initialized")
    
    def read_excel(self, file_path):
        """
        Read data from an Excel file
        
        Args:
            file_path (str): Path to the Excel file
            
        Returns:
            pandas.DataFrame: The data from the Excel file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check file extension
        if not file_path.endswith(('.xlsx', '.xls')):
            raise ValueError("File must be an Excel file (.xlsx or .xls)")
        
        try:
            # Read Excel file using pandas
            # pandas automatically handles different Excel formats
            df = pd.read_excel(file_path)
            
            print(f"  ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
            
            return df
            
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {str(e)}")
    
    def analyze_data(self, df):
        """
        Analyze the data and generate statistics
        
        This function calculates various metrics depending on
        what columns are present in the data
        
        Args:
            df (pandas.DataFrame): The data to analyze
            
        Returns:
            dict: Dictionary containing analysis results
        """
        analysis = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'statistics': {},
            'summary': {}
        }
        
        detected_type = self._detect_data_type(df)
        
        # Analyze numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if detected_type == "student":
            exclude_keywords = ['nim', 'id', 'kode']
            numeric_cols = [col for col in numeric_cols if not any(k in col.lower() for k in exclude_keywords)]

        for col in numeric_cols:
            # Calculate statistics for each numeric column
            analysis['statistics'][col] = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'std': float(df[col].std()),
                'missing': int(df[col].isna().sum())
            }
        
        # Analyze categorical columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        for col in categorical_cols:
            # Get value counts for categorical data
            value_counts = df[col].value_counts()
            analysis['summary'][col] = {
                'unique_values': int(df[col].nunique()),
                'most_common': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                'most_common_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                'missing': int(df[col].isna().sum())
            }
        
        # Detect data type (student, finance, etc.)
        analysis['detected_type'] = detected_type
        
        return analysis
    
    def _detect_data_type(self, df):
        """
        Try to detect what type of data this is based on column names
        
        Args:
            df (pandas.DataFrame): The data to analyze
            
        Returns:
            str: Detected data type (student, finance, or unknown)
        """
        columns_lower = [col.lower() for col in df.columns]
        
        # Keywords for student data
        student_keywords = ['student', 'mahasiswa', 'nama', 'grade', 'nilai', 'ipk', 'gpa']
        if any(keyword in ' '.join(columns_lower) for keyword in student_keywords):
            return 'student'
        
        # Keywords for financial data
        finance_keywords = ['finance', 'keuangan', 'biaya', 'pembayaran', 'tagihan', 'revenue', 'expense']
        if any(keyword in ' '.join(columns_lower) for keyword in finance_keywords):
            return 'finance'
        
        return 'unknown'
    
    def get_data_summary_for_ai(self, analysis):
        """
        Create a text summary of the data for the AI to process
        
        This converts our analysis dictionary into a clear text description
        that the AI can understand and use to generate reports
        
        Args:
            analysis (dict): Analysis results from analyze_data()
            
        Returns:
            str: Text summary suitable for AI processing
        """
        summary_lines = [
            f"Data Overview:",
            f"- Total records: {analysis['row_count']}",
            f"- Total columns: {analysis['column_count']}",
            f"- Detected type: {analysis['detected_type']}",
            "",
            "Columns:",
        ]
        
        for col in analysis['columns']:
            summary_lines.append(f"- {col}")
        
        # Add numeric statistics
        if analysis['statistics']:
            summary_lines.append("\nNumerical Statistics:")
            for col, stats in analysis['statistics'].items():
                summary_lines.append(f"\n{col}:")
                summary_lines.append(f"  - Mean: {stats['mean']:.2f}")
                summary_lines.append(f"  - Median: {stats['median']:.2f}")
                summary_lines.append(f"  - Range: {stats['min']:.2f} - {stats['max']:.2f}")
                summary_lines.append(f"  - Std Dev: {stats['std']:.2f}")
        
        # Add categorical summaries
        if analysis['summary']:
            summary_lines.append("\nCategorical Data:")
            for col, info in analysis['summary'].items():
                summary_lines.append(f"\n{col}:")
                summary_lines.append(f"  - Unique values: {info['unique_values']}")
                if info['most_common']:
                    summary_lines.append(f"  - Most common: {info['most_common']} ({info['most_common_count']} times)")
        
        return "\n".join(summary_lines)


# For testing this module independently
if __name__ == "__main__":
    processor = DataProcessor()
    print("Data Processor module loaded successfully!")
    print("\nThis module provides:")
    print("- read_excel(): Read Excel files")
    print("- analyze_data(): Analyze data and calculate statistics")
    print("- get_data_summary_for_ai(): Create AI-ready summaries")