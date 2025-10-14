# main.py
"""
University AI Report Generator
Main application file — orchestrates the entire report generation process

This version includes debug prints to verify metadata (especially token_usage)
is passed into OutputManager.save_report.
"""

import os
from datetime import datetime
from pathlib import Path

# Import your custom modules
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager
from config import Config


class UniversityReportApp:
    """
    Main application class that coordinates all components:
    - Data reading / processing
    - AI report generation (Gemini / GenAI)
    - Validation
    - Export to Markdown
    """

    def __init__(self):
        print("=" * 60)
        print("UNIVERSITY AI REPORT GENERATOR")
        print("=" * 60)

        # Load config (API keys, settings)
        self.config = Config()

        # Initialize modules
        self.data_processor = DataProcessor()

        model_name = self.config.get_setting("model_name", "gemini-2.5-flash")
        api_key = self.config.get_api_key()
        self.report_generator = ReportGenerator(api_key, model_name=model_name)

        self.output_manager = OutputManager()

        print("✓ Application initialized successfully\n")

    def generate_student_report(self, excel_file_path: str) -> str:
        """
        Generate a report for student performance data.
        Returns the path to the generated Markdown file.
        """
        print(f"Processing: {excel_file_path}")
        print("-" * 60)

        # 1. Read Excel data
        print("Step 1: Reading Excel data...")
        student_data = self.data_processor.read_excel(excel_file_path)

        # 1,5. Cleaning the data
        print("Step 1.5: Cleaning data...")
        student_data = self.data_processor.clean_data(student_data)

        # 2. Analyze data
        print("Step 2: Analyzing data...")
        analysis = self.data_processor.analyze_data(student_data)

        # 3. Generate AI report + token usage
        print("Step 3: Generating AI report (calling Gemini API)...")
        report_text, usage_info = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="student_performance"
        )

        # Debug: show usage_info returned by generator
        print("DEBUG: generator returned usage_info =", usage_info)

        # normalize usage_info so metadata always contains the key
        if usage_info is None:
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}

        # 4. Validate the generated report (only pass the text)
        print("Step 4: Validating report accuracy...")
        validation_result = self.report_generator.validate_report(report_text, analysis)
        if not validation_result["is_valid"]:
            print(f"⚠ Warning: Potential issues detected: {validation_result['issues']}")
        else:
            print("✓ Report validated successfully")

        # 5. Prepare metadata and save the report (with debug)
        metadata = {
            "source_file": excel_file_path,
            "analysis": analysis,
            "validation": validation_result,
            "token_usage": usage_info,
            "timestamp": datetime.now().isoformat()
        }

        # Debug: show metadata just before saving
        print("DEBUG: about to save report. metadata keys:", list(metadata.keys()))
        print("DEBUG: token_usage in metadata:", metadata.get("token_usage"))

        print("Step 5: Saving report...")
        output_path = self.output_manager.save_report(
            report_text,
            report_type="student_report",
            metadata=metadata
        )

        print("-" * 60)
        print("✓ Report generated successfully!")
        print(f"📄 Saved to: {output_path}\n")
        return output_path

    def generate_finance_report(self, excel_file_path: str) -> str:
        """
        Generate a financial analysis report.
        Returns the path to the generated file.
        """
        print(f"Processing: {excel_file_path}")
        print("-" * 60)

        # 1. Read finance data
        print("Step 1: Reading financial data...")
        finance_data = self.data_processor.read_excel(excel_file_path)

        # 1,5. Cleaning the data
        print("Step 1.5: Cleaning data...")
        finance_data = self.data_processor.clean_data(finance_data)

        # 2. Analyze finance data
        print("Step 2: Analyzing financial metrics...")
        analysis = self.data_processor.analyze_data(finance_data)

        # 3. Generate AI report + usage
        print("Step 3: Generating financial report...")
        report_text, usage_info = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="financial_analysis"
        )

        # Debug: show usage_info returned by generator
        print("DEBUG: generator returned usage_info =", usage_info)
        if usage_info is None:
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}

        # 4. Validate
        print("Step 4: Validating report...")
        validation_result = self.report_generator.validate_report(report_text, analysis)
        if not validation_result["is_valid"]:
            print(f"⚠ Warning: Potential issues detected: {validation_result['issues']}")
        else:
            print("✓ Report validated successfully")

        # 5. Prepare metadata and save (with debug)
        metadata = {
            "source_file": excel_file_path,
            "analysis": analysis,
            "validation": validation_result,
            "token_usage": usage_info,
            "timestamp": datetime.now().isoformat()
        }

        # Debug: show metadata just before saving
        print("DEBUG: about to save report. metadata keys:", list(metadata.keys()))
        print("DEBUG: token_usage in metadata:", metadata.get("token_usage"))

        print("Step 5: Saving report...")
        output_path = self.output_manager.save_report(
            report_text,
            report_type="finance_report",
            metadata=metadata
        )

        print("-" * 60)
        print("✓ Financial report generated!")
        print(f"📄 Saved to: {output_path}\n")
        return output_path

    def run_demo(self):
        """
        Run demonstration mode: process sample student + finance files.
        """
        print("\n🎓 DEMO MODE - University Report Generator\n")
        sample_files = {
            "students": "data/sample_students.xlsx",
            "finance": "data/sample_finance.xlsx"
        }

        results = []
        for dtype, path in sample_files.items():
            if os.path.exists(path):
                print(f"\n📊 Processing {dtype} data...")
                if dtype == "students":
                    report = self.generate_student_report(path)
                else:
                    report = self.generate_finance_report(path)
                results.append(report)
            else:
                print(f"⚠ Sample file not found: {path}. Please place a sample file in folder 'data'.")

        print("\n" + "=" * 60)
        print("DEMO COMPLETE!")
        print("=" * 60)
        print(f"Generated {len(results)} reports:")
        for r in results:
            print("  -", r)
        print()

def main():
    """
    Main entry point when running `python main.py`.
    """
    try:
        app = UniversityReportApp()

        print("Select an option:")
        print("1. Generate Student Performance Report")
        print("2. Generate Financial Analysis Report")
        print("3. Run Demo (process all sample files)")
        print("4. Exit")

        choice = input("\nEnter your choice (1-4): ").strip()
        if choice == "1":
            fp = input("Enter path to student Excel file: ").strip()
            app.generate_student_report(fp)
        elif choice == "2":
            fp = input("Enter path to finance Excel file: ").strip()
            app.generate_finance_report(fp)
        elif choice == "3":
            app.run_demo()
        elif choice == "4":
            print("Goodbye!")
        else:
            print("Invalid choice. Please run again.")

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration and try again.")

if __name__ == "__main__":
    main()
