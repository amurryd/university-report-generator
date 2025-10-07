"""
Output Manager Module — with Token Usage Section
Handles saving reports to Markdown files with metadata including token usage
"""

from datetime import datetime
from pathlib import Path
import json


class OutputManager:
    """
    Manages output files for generated reports
    - Creating directory structure
    - Saving reports as Markdown
    - Adding metadata (source, validation, token usage)
    - Organizing files by date/type
    """

    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()
        print("✓ Output Manager initialized")

    def _ensure_output_directory(self):
        self.output_dir.mkdir(exist_ok=True)
        (self.output_dir / "student_reports").mkdir(exist_ok=True)
        (self.output_dir / "finance_reports").mkdir(exist_ok=True)
        (self.output_dir / "metadata").mkdir(exist_ok=True)

    def save_report(self, report_text, report_type="general", metadata=None):
        """
        Save a report to a Markdown file with metadata and token usage.

        Args:
            report_text (str): Generated report
            report_type (str): 'student_report', 'finance_report', etc.
            metadata (dict): Extra metadata including token_usage

        Returns:
            str: File path to saved report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.md"

        if "student" in report_type.lower():
            subdir = "student_reports"
        elif "finance" in report_type.lower():
            subdir = "finance_reports"
        else:
            subdir = ""

        file_path = self.output_dir / subdir / filename if subdir else self.output_dir / filename

        # Build final content with metadata header
        full_content = self._add_metadata_header(report_text, metadata)

        # Write markdown file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Save metadata JSON
        if metadata:
            self._save_metadata(filename, metadata)

        return str(file_path)

    def _add_metadata_header(self, report_text, metadata):
        """
        Add a structured YAML-like header to Markdown.
        Includes source, validation status, and token usage.
        """
        header = "---\n"
        header += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"

        if metadata:
            if "source_file" in metadata:
                header += f"Source: {metadata['source_file']}\n"
            if "validation" in metadata:
                val = metadata["validation"]
                header += f"Validation: {'✓ Pass' if val.get('is_valid') else '⚠ Issues detected'}\n"
            if "token_usage" in metadata:
                usage = metadata["token_usage"]
                prompt_t = usage.get("prompt_tokens", "?")
                output_t = usage.get("output_tokens", "?")
                total_t = usage.get("total_tokens", "?")
                header += f"Token Usage: prompt={prompt_t}, output={output_t}, total={total_t}\n"

        header += "Generator: University AI Report Generator\n"
        header += "---\n\n"

        return header + report_text

    def _save_metadata(self, report_filename, metadata):
        """
        Save metadata as a separate JSON file next to the report.
        """
        metadata_filename = report_filename.replace(".md", "_metadata.json")
        metadata_path = self.output_dir / "metadata" / metadata_filename

        metadata["saved_at"] = datetime.now().isoformat()

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def list_reports(self, report_type=None):
        """
        List generated reports, optionally filtered by type.
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

        reports = list(search_dir.glob("**/*.md"))
        return sorted(reports, reverse=True)


if __name__ == "__main__":
    manager = OutputManager()
    print("Output Manager module loaded!")
