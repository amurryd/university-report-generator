"""
University AI Report Generator
Main application file - orchestrates the entire report generation process

Author: [Your Name]
Thesis Project: AI-Powered Report Generation System
University: [Your University]
"""

import os
from datetime import datetime
from pathlib import Path

# Import our custom modules
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager
from config import Config


class UniversityReportApp:
    """
    Main application class that coordinates all components
    
    This class brings together:
    - Data reading (Excel files)
    - AI report generation (Gemini API)
    - Output management (Markdown files)
    """
    
    def __init__(self):
        """Initialize the application with all necessary components"""
        print("=" * 60)
        print("UNIVERSITY AI REPORT GENERATOR")
        print("=" * 60)
        
        # Load configuration (API keys, settings)
        self.config = Config()
        
        # Initialize components
        self.data_processor = DataProcessor()
        
        # Get model name from config (default: gemini-2.5-flash - Latest Oct 2024)
        model_name = self.config.get_setting('model_name', 'gemini-2.5-flash')
        self.report_generator = ReportGenerator(
            self.config.get_api_key(),
            model_name=model_name
        )
        
        self.output_manager = OutputManager()
        
        print("✓ Application initialized successfully\n")
    
    def generate_student_report(self, excel_file_path):
        """
        Generate a comprehensive report about student data
        
        Args:
            excel_file_path (str): Path to the Excel file containing student data
            
        Returns:
            str: Path to the generated report file
        """
        print(f"Processing: {excel_file_path}")
        print("-" * 60)
        
        # Step 1: Read and process Excel data
        print("Step 1: Reading Excel data...")
        student_data = self.data_processor.read_excel(excel_file_path)
        
        # Step 2: Analyze the data
        print("Step 2: Analyzing data...")
        analysis = self.data_processor.analyze_data(student_data)
        
        # Step 3: Generate AI report using Gemini
        print("Step 3: Generating AI report (calling Gemini API)...")
        report_text = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="student_performance"
        )
        
        # Step 4: Validate for hallucinations
        print("Step 4: Validating report accuracy...")
        validation_result = self.report_generator.validate_report(
            report_text, 
            analysis
        )
        
        if not validation_result['is_valid']:
            print(f"⚠ Warning: Potential issues detected: {validation_result['issues']}")
        else:
            print("✓ Report validated successfully")
        
        # Step 5: Save to Markdown file
        print("Step 5: Saving report...")
        output_path = self.output_manager.save_report(
            report_text,
            report_type="student_report",
            metadata={
                'source_file': excel_file_path,
                'analysis': analysis,
                'validation': validation_result
            }
        )
        
        print("-" * 60)
        print(f"✓ Report generated successfully!")
        print(f"📄 Saved to: {output_path}\n")
        
        return output_path
    
    def generate_finance_report(self, excel_file_path):
        """
        Generate a financial analysis report
        
        Args:
            excel_file_path (str): Path to the Excel file with finance data
            
        Returns:
            str: Path to the generated report
        """
        print(f"Processing: {excel_file_path}")
        print("-" * 60)
        
        # Similar process but for financial data
        print("Step 1: Reading financial data...")
        finance_data = self.data_processor.read_excel(excel_file_path)
        
        print("Step 2: Analyzing financial metrics...")
        analysis = self.data_processor.analyze_data(finance_data)
        
        print("Step 3: Generating financial report...")
        report_text = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="financial_analysis"
        )
        
        print("Step 4: Validating report...")
        validation_result = self.report_generator.validate_report(
            report_text, 
            analysis
        )
        
        print("Step 5: Saving report...")
        output_path = self.output_manager.save_report(
            report_text,
            report_type="finance_report",
            metadata={
                'source_file': excel_file_path,
                'analysis': analysis,
                'validation': validation_result
            }
        )
        
        print("-" * 60)
        print(f"✓ Financial report generated!")
        print(f"📄 Saved to: {output_path}\n")
        
        return output_path
    
    def run_demo(self):
        """
        Run a demonstration of the system
        This is useful for showing to your advisor
        """
        print("\n🎓 DEMO MODE - University Report Generator\n")
        
        # Check if sample data exists
        sample_files = {
            'students': 'data/sample_students.xlsx',
            'finance': 'data/sample_finance.xlsx'
        }
        
        results = []
        
        for data_type, file_path in sample_files.items():
            if os.path.exists(file_path):
                print(f"\n📊 Processing {data_type} data...")
                if data_type == 'students':
                    report_path = self.generate_student_report(file_path)
                else:
                    report_path = self.generate_finance_report(file_path)
                results.append(report_path)
            else:
                print(f"⚠ Sample file not found: {file_path}")
                print(f"  Please create sample data in the 'data' folder")
        
        print("\n" + "=" * 60)
        print("DEMO COMPLETE!")
        print("=" * 60)
        print(f"Generated {len(results)} reports:")
        for report in results:
            print(f"  - {report}")
        print()


def main():
    """
    Main entry point for the application
    This is what runs when you execute: python main.py
    """
    try:
        # Create application instance
        app = UniversityReportApp()
        
        # Show menu
        print("Select an option:")
        print("1. Generate Student Performance Report")
        print("2. Generate Financial Analysis Report")
        print("3. Run Demo (process all sample files)")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            file_path = input("Enter path to student Excel file: ").strip()
            app.generate_student_report(file_path)
            
        elif choice == "2":
            file_path = input("Enter path to finance Excel file: ").strip()
            app.generate_finance_report(file_path)
            
        elif choice == "3":
            app.run_demo()
            
        elif choice == "4":
            print("Goodbye!")
            
        else:
            print("Invalid choice. Please run again.")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("Please check your configuration and try again.")


if __name__ == "__main__":
    main()