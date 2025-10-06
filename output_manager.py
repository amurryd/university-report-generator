"""
Output Manager Module
Handles saving reports to Markdown files with metadata

This module is responsible for:
- Creating output directories
- Generating unique filenames
- Saving reports with metadata
- Managing file organization
"""

from datetime import datetime
from pathlib import Path
import json


class OutputManager:
    """
    Manages output files for generated reports
    
    This class handles all file operations:
    - Creating directory structure
    - Saving reports as Markdown
    - Adding metadata
    - Organizing files by date/type
    """
    
    def __init__(self, output_dir="reports"):
        """
        Initialize the output manager
        
        Args:
            output_dir (str): Base directory for saving reports
        """
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()
        print("✓ Output Manager initialized")
    
    def _ensure_output_directory(self):
        """
        Create the output directory if it doesn't exist
        
        This ensures we have a place to save our reports
        """
        # Create main reports directory
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        (self.output_dir / "student_reports").mkdir(exist_ok=True)
        (self.output_dir / "finance_reports").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)
    
    def save_report(self, report_text, report_type="general", metadata=None):
        """
        Save a report to a Markdown file
        
        Args:
            report_text (str): The report content
            report_type (str): Type of report (for organization)
            metadata (dict): Optional metadata to save with report
            
        Returns:
            str: Path to the saved report file
        """
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.md"
        
        # Determine subdirectory based on report type
        if "student" in report_type.lower():
            subdir = "student_reports"
        elif "finance" in report_type.lower():
            subdir = "finance_reports"
        else:
            subdir = ""
        
        # Full path for the report
        if subdir:
            file_path = self.output_dir / subdir / filename
        else:
            file_path = self.output_dir / filename
        
        # Add metadata header to the report
        full_content = self._add_metadata_header(report_text, metadata)
        
        # Save the report
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        # Save metadata as separate JSON file
        if metadata:
            self._save_metadata(filename, metadata)
        
        return str(file_path)
    
    def _add_metadata_header(self, report_text, metadata):
        """
        Add metadata header to the report
        
        Args:
            report_text (str): Original report
            metadata (dict): Metadata to add
            
        Returns:
            str: Report with metadata header
        """
        header = "---\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        if metadata:
            if 'source_file' in metadata:
                header += f"Source: {metadata['source_file']}\n"
            if 'validation' in metadata:
                val = metadata['validation']
                header += f"Validated: {'✓ Pass' if val.get('is_valid') else '⚠ Issues detected'}\n"
        
        header += "Generator: University AI Report Generator\n"
        header += "---\n\n"
        
        return header + report_text
    
    def _save_metadata(self, report_filename, metadata):
        """
        Save metadata as a separate JSON file
        
        Args:
            report_filename (str): Name of the report file
            metadata (dict): Metadata to save
        """
        metadata_filename = report_filename.replace('.md', '_metadata.json')
        metadata_path = self.output_dir / "metadata" / metadata_filename
        
        # Add timestamp to metadata
        metadata['saved_at'] = datetime.now().isoformat()
        
        # Save as JSON
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def list_reports(self, report_type=None):
        """
        List all generated reports
        
        Args:
            report_type (str): Optional filter by report type
            
        Returns:
            list: List of report file paths
        """
        if report_type:
            if "student" in report_type.lower():
                search_dir = self.output_dir / "student_reports"
            elif "finance" in report_type.lower():
                search_dir = self.output_dir / "finance_reports"
            else:
                search_dir = self.output_dir
        else:
            search_dir = self.output_dir
        
        # Find all .md files
        reports = list(search_dir.glob("**/*.md"))
        return sorted(reports, reverse=True)  # Newest first


# For testing
if __name__ == "__main__":
    manager = OutputManager()
    print("Output Manager module loaded!")
    print(f"\nOutput directory: {manager.output_dir}")
    print("\nThis module provides:")
    print("- save_report(): Save reports as Markdown files")
    print("- list_reports(): List all generated reports")