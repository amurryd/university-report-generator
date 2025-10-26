# main.py
"""
University AI Report Generator
Main application file — orchestrates the entire report generation process

This version now fetches multiple CSVs (via API or local), aggregates them,
cleans/analyzes, generates one unified report, then exports to Markdown + HTML.
"""

import os
from datetime import datetime
from pathlib import Path

# Import your custom modules
from config import Config
from data_aggregator import DataAggregator
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager


class UniversityReportApp:
    """
    Main application class that coordinates all components:
    - Data ingestion / aggregation (multiple CSVs) 
    - Data cleaning / processing
    - AI report generation
    - Validation
    - Export to Markdown + HTML
    """

    def __init__(self):
        print("=" * 60)
        print("UNIVERSITY AI REPORT GENERATOR – Unified Report Mode")
        print("=" * 60)

        # Load config (API keys, settings)
        self.config = Config()

        # Initialize modules
        self.aggregator = DataAggregator(cache_dir=str(self.config.CACHE_DIR), verbose=True)
        self.data_processor = DataProcessor()

        model_name = self.config.get_setting("model_name", "gemini-2.5-flash")
        api_key = self.config.get_api_key()
        self.report_generator = ReportGenerator(api_key, model_name=model_name)

        self.output_manager = OutputManager()

        print("✓ Application initialized successfully\n")

    def generate_unified_report(self) -> str:
        """
        Generate a unified institutional report by:
         1. Ingesting multiple data sources
         2. Aggregating into one DataFrame
         3. Cleaning and analyzing data
         4. Generating AI narrative report
         5. Saving report (Markdown + HTML)
        """
        print("Step 0: Preparing to ingest multiple data sources...")
        sources = self.config.get_ingestion_sources()
        print(f"Sources to ingest: {sources}")

        # 1. Ingest & aggregate
        print("Step 1: Aggregating data from all sources...")
        combined_df = self.aggregator.ingest(sources, cache=True)

        # 2. Clean data
        print("Step 2: Cleaning combined data...")
        cleaned_df = self.data_processor.clean_data(combined_df)

        # 3. Analyze data
        print("Step 3: Analyzing combined dataset...")
        analysis = self.data_processor.analyze_data(cleaned_df)

        # 4. Generate AI report
        print("Step 4: Generating unified report (calling Gemini API)...")
        report_text, usage_info = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="combined"  # ensure this matches JSON template in prompts/
        )
        print("DEBUG: generator returned usage_info =", usage_info)
        if usage_info is None:
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}

        # 5. Validate
        print("Step 5: Validating report accuracy...")
        validation_result = self.report_generator.validate_report(report_text, analysis)
        if not validation_result["is_valid"]:
            print(f"⚠ Warning: Potential issues detected: {validation_result['issues']}")
        else:
            print("✓ Report validated successfully")

        # 6. Save report
        metadata = {
            "source_files": sources,
            "analysis": analysis,
            "validation": validation_result,
            "token_usage": usage_info,
            "timestamp": datetime.now().isoformat()
        }
        print("DEBUG: about to save report. metadata keys:", list(metadata.keys()))
        print("DEBUG: token_usage in metadata:", metadata.get("token_usage"))

        print("Step 7: Saving report...")
        output_path = self.output_manager.save_report(
            report_text,
            report_type="unified_report",
            metadata=metadata
        )

        print("-" * 60)
        print("✓ Unified report generated successfully!")
        print(f"📄 Saved to: {output_path}\n")
        return output_path

    def run_demo(self):
        """
        Run demonstration mode: ingest sample CSVs + generate unified report.
        """
        print("\n🎓 DEMO MODE – Unified Institutional Report\n")
        output_path = None
        try:
            output_path = self.generate_unified_report()
        except Exception as e:
            print(f"❌ Error during demo: {e}")
        print("\n" + "=" * 60)
        print("DEMO COMPLETE!")
        print("=" * 60)
        if output_path:
            print(f"Generated report: {output_path}")
        print()

def main():
    """
    Main entry point when running `python main.py`.
    """
    try:
        app = UniversityReportApp()

        print("Select an option:")
        print("1. Generate Unified Institutional Report")
        print("2. Exit")

        choice = input("\nEnter your choice (1-2): ").strip()
        if choice == "1":
            app.generate_unified_report()
        elif choice == "2":
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
