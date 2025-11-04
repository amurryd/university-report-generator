"""
University AI Report Generator
Main orchestrator — handles full unified report generation
"""

import os
from datetime import datetime
from pathlib import Path

# Import your project modules
from config import Config
from data_aggregator import DataAggregator
from data_processor import DataProcessor
from report_generator import ReportGenerator
from output_manager import OutputManager


class UniversityReportApp:
    """
    Main application class that coordinates:
    - Data ingestion (local or API)
    - Data cleaning / processing
    - AI report generation
    - Output saving (Markdown + HTML)
    """

    def __init__(self, mode: str = "local"):
        print("=" * 60)
        print("🎓 UNIVERSITY AI REPORT GENERATOR")
        print("=" * 60)

        # Force mode (local/api) into environment before Config loads
        os.environ["AGGREGATION_MODE"] = mode
        self.mode = mode

        # Initialize configuration and modules
        self.config = Config()
        self.aggregator = DataAggregator(cache_dir=str(self.config.CACHE_DIR), verbose=True)
        self.data_processor = DataProcessor()

        api_key = self.config.get_api_key()
        model_name = self.config.get_setting("model_name", "gemini-2.5-flash")
        self.report_generator = ReportGenerator(api_key, model_name=model_name)
        self.output_manager = OutputManager()

        print(f"✓ Application initialized successfully in [{self.mode.upper()}] mode\n")

    # --------------------------------------------------------
    # Main workflow
    # --------------------------------------------------------
    def generate_unified_report(self) -> str:
        print(f"🧩 Step 0: Preparing to ingest sources (mode={self.mode})...")
        sources = self.config.get_ingestion_sources()
        print(f"→ Sources to ingest ({len(sources)}):")
        for src in sources:
            print(f"   - {src}")

        # 1️⃣ Aggregate data
        print("\n📊 Step 1: Aggregating data...")
        combined_df = self.aggregator.ingest(sources, cache=True)

        # 2️⃣ Clean data
        print("\n🧹 Step 2: Cleaning combined data...")
        cleaned_df = self.data_processor.clean_data(combined_df)

        # 3️⃣ Analyze data
        print("\n📈 Step 3: Analyzing combined dataset...")
        analysis = self.data_processor.analyze_data(cleaned_df)

        # 4️⃣ Generate AI report
        print("\n🤖 Step 4: Generating unified report (AI call)...")
        report_text, usage_info = self.report_generator.generate_report(
            data_summary=analysis,
            report_type="combined"
        )

        usage_info = usage_info or {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}

        # 5️⃣ Validate
        print("\n🧠 Step 5: Validating report content...")
        validation_result = self.report_generator.validate_report(report_text, analysis)
        if validation_result["is_valid"]:
            print("✓ Report validation passed")
        else:
            print(f"⚠ Warning: Issues detected: {validation_result['issues']}")

        # 6️⃣ Save output
        print("\n💾 Step 6: Saving report output...")
        metadata = {
            "mode": self.mode,
            "source_files": sources,
            "analysis": analysis,
            "validation": validation_result,
            "token_usage": usage_info,
            "timestamp": datetime.now().isoformat(),
        }

        output_path = self.output_manager.save_report(
            report_text,
            report_type="unified_report",
            metadata=metadata
        )

        print("\n✅ Unified report generated successfully!")
        print(f"📄 Saved to: {output_path}\n")
        return output_path


# --------------------------------------------------------
# CLI Entrypoint
# --------------------------------------------------------
def main():
    print("=" * 60)
    print("🎓 UNIVERSITY AI REPORT GENERATOR")
    print("=" * 60)
    print("\nSelect data ingestion mode:")
    print("1️⃣  Local CSV mode")
    print("2️⃣  API mode (fetch from FastAPI server)")

    choice = input("\nEnter choice [1-2]: ").strip()
    mode = "local" if choice == "1" else "api" if choice == "2" else "local"

    print(f"\n🚀 Launching in {mode.upper()} mode...\n")

    try:
        app = UniversityReportApp(mode=mode)
        app.generate_unified_report()
    except KeyboardInterrupt:
        print("\n⏹ Operation cancelled by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Please check your configuration or dataset paths and try again.")


if __name__ == "__main__":
    main()
