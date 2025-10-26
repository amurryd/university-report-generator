# file: data_processor.py
"""
Data Processor Module
Handles reading CSV files and analyzing data

This module is responsible for:
- Reading CSV files with pandas
- Cleaning and validating data
- Calculating statistics
- Preparing data summaries for AI
"""

import pandas as pd
import numpy as np
from pathlib import Path


class DataProcessor:
    """
    Processes university data from CSV files
    
    This class handles all data-related operations:
    - Reading CSV files
    - Data validation
    - Statistical analysis
    - Summary generation
    """
    
    def __init__(self):
        """Initialize the data processor"""
        print("✓ Data Processor initialized")
    
    def read_multiple_csvs(self, file_paths):
        frames = []
        for fp in file_paths:
            try:
                df = pd.read_csv(fp, encoding='utf-8-sig')
                df["source_file"] = Path(fp).name
                frames.append(df)
                print(f" ✓ Loaded {fp} ({len(df)} rows)")
            except Exception as e:
                print(f" ❌ Failed to read {fp}: {e}")
        
        if frames:
            combined_df = pd.concat(frames, ignore_index=True, sort=False)
            print(f"✅ Combined {len(frames)} CSVs ({len(combined_df)} total rows)")
            return combined_df
        else:
            print("⚠ No valid CSV files provided.")
            return pd.DataFrame()

    def read_csv(self, file_path):
        """
        Read data from a CSV file
        
        Args:
            file_path (str): Path to the CSV file
            
        Returns:
            pandas.DataFrame: The data from the CSV file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if not file_path.endswith('.csv'):
            raise ValueError("File must be a CSV file (.csv)")
        
        try:
            df = pd.read_csv(file_path, encoding='utf-8-sig')
            print(f"  ✓ Loaded {len(df)} rows, {len(df.columns)} columns")
            return df
        except Exception as e:
            raise ValueError(f"Error reading CSV file: {str(e)}")
        
    def clean_data(self, df):
        """Clean and standardize the dataset."""
        df = df.copy()

        before_rows = len(df)
        df = df.drop_duplicates()
        after_rows = len(df)
        duplicates_removed = before_rows - after_rows

        empty_cols = df.columns[df.isna().all()].tolist()
        df = df.dropna(axis=1, how='all')

        for col in df.columns:
            if df[col].dtype == 'object':
                new_col = df[col].astype(str).str.replace(',', '.', regex=True)
                try:
                    df[col] = pd.to_numeric(new_col)
                except Exception:
                    df[col] = new_col

        num_cols = list(df.select_dtypes(include=[np.number]).columns)
        for col in num_cols:
            mean_val = df[col].mean()
            df.loc[:, col] = df[col].fillna(mean_val)
        
        cat_cols = list(df.select_dtypes(include=['object']).columns)
        for col in cat_cols:
            if df[col].isna().any():
                mode_series = df[col].mode()
                mode_val = mode_series[0] if not mode_series.empty else ""
                df.loc[:, col] = df[col].fillna(mode_val)
        
        print(f"  ✓ Cleaned data: removed {duplicates_removed} duplicates, dropped {len(empty_cols)} empty columns")
        return df

    def analyze_data(self, df):
        """Analyze the data and generate statistics"""
        analysis = {
            'row_count': len(df),
            'column_count': len(df.columns),
            'columns': list(df.columns),
            'statistics': {},
            'summary': {}
        }
        
        detected_type = self._detect_data_type(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns

        if detected_type == "student":
            exclude_keywords = ['nim', 'id', 'kode']
            numeric_cols = [col for col in numeric_cols if not any(k in col.lower() for k in exclude_keywords)]

        for col in numeric_cols:
            analysis['statistics'][col] = {
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'std': float(df[col].std()),
                'missing': int(df[col].isna().sum())
            }
        
        categorical_cols = df.select_dtypes(include=['object']).columns
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            analysis['summary'][col] = {
                'unique_values': int(df[col].nunique()),
                'most_common': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                'most_common_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                'missing': int(df[col].isna().sum())
            }
        
        analysis['detected_type'] = detected_type
        return analysis
    
    def _detect_data_type(self, df):
        columns_lower = [col.lower() for col in df.columns]
        joined = ' '.join(columns_lower)
        
        student_keywords = ['student', 'mahasiswa', 'nama', 'grade', 'nilai', 'ipk', 'gpa']
        finance_keywords = ['finance', 'keuangan', 'biaya', 'pembayaran', 'tagihan', 'revenue', 'expense']
        akreditasi_keywords = ['akreditasi', 'program', 'dosen', 'kurikulum', 'sk', 'unggul', 'prodi']
        
        is_student = any(k in joined for k in student_keywords)
        is_finance = any(k in joined for k in finance_keywords)
        is_akreditasi = any(k in joined for k in akreditasi_keywords)
        
        if sum([is_student, is_finance, is_akreditasi]) > 1:
            return "mixed"
        elif is_student:
            return "student"
        elif is_finance:
            return "finance"
        elif is_akreditasi:
            return "akreditasi"
        else:
            return "unknown"
    
    def get_data_summary_for_ai(self, analysis):
        """Convert analysis dict into AI-readable text summary"""
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
        
        if analysis['statistics']:
            summary_lines.append("\nNumerical Statistics:")
            for col, stats in analysis['statistics'].items():
                summary_lines.append(f"\n{col}:")
                summary_lines.append(f"  - Mean: {stats['mean']:.2f}")
                summary_lines.append(f"  - Median: {stats['median']:.2f}")
                summary_lines.append(f"  - Range: {stats['min']:.2f} - {stats['max']:.2f}")
                summary_lines.append(f"  - Std Dev: {stats['std']:.2f}")
        
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
    print("- read_csv(): Read CSV files")
    print("- analyze_data(): Analyze data and calculate statistics")
    print("- get_data_summary_for_ai(): Create AI-ready summaries")
