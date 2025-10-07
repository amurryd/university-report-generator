"""
Output Manager Module — with Token Usage Section (improved)

Saves reports to Markdown files with metadata including token usage,
and writes a separate metadata JSON file.
"""

from datetime import datetime
from pathlib import Path
import json
import copy


class OutputManager:
    """
    Manages output files for generated reports:
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
        # create directories, parents=True to be robust
        (self.output_dir / "student_reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "finance_reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "metadata").mkdir(parents=True, exist_ok=True)

    def save_report(self, report_text, report_type="general", metadata=None):
        """
        Save a report to a Markdown file with metadata and token usage.

        Args:
            report_text (str): Generated report (may already contain appended usage)
            report_type (str): 'student_report', 'finance_report', etc.
            metadata (dict): Extra metadata including token_usage

        Returns:
            str: File path to saved report
        """
        # Safety defaults
        if metadata is None:
            metadata = {}

        # Debug: log metadata keys so we can see what arrived here
        try:
            print("DEBUG OutputManager.save_report: metadata keys =", list(metadata.keys()))
            print("DEBUG OutputManager.save_report: token_usage =", metadata.get("token_usage"))
        except Exception:
            print("DEBUG OutputManager.save_report: metadata (unprintable)")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.md"

        # choose subdir
        if "student" in report_type.lower():
            subdir = "student_reports"
        elif "finance" in report_type.lower():
            subdir = "finance_reports"
        else:
            subdir = ""

        file_path = (self.output_dir / subdir / filename) if subdir else (self.output_dir / filename)

        # Build final content with metadata header
        full_content = self._add_metadata_header(report_text, metadata)

        # Write markdown file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Save metadata JSON (use a copy so we don't mutate caller's object)
        if metadata:
            metadata_copy = copy.deepcopy(metadata)
            self._save_metadata(filename, metadata_copy)

        return str(file_path)

    def _add_metadata_header(self, report_text, metadata):
        """
        Add a structured YAML-like header to Markdown.
        Includes source, validation status, and token usage.
        """
        header_lines = ["---"]
        header_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if metadata:
            if "source_file" in metadata:
                header_lines.append(f"Source: {metadata['source_file']}")
            if "validation" in metadata:
                val = metadata["validation"]
                header_lines.append(f"Validation: {'✓ Pass' if val.get('is_valid') else '⚠ Issues detected'}")
            # token_usage: robust handling, print n/a if None
            if "token_usage" in metadata:
                usage = metadata.get("token_usage") or {}
                pt = usage.get("prompt_tokens")
                ot = usage.get("output_tokens")
                tt = usage.get("total_tokens")
                pt_s = str(pt) if pt is not None else "n/a"
                ot_s = str(ot) if ot is not None else "n/a"
                tt_s = str(tt) if tt is not None else "n/a"
                header_lines.append(f"Token Usage: prompt={pt_s}, output={ot_s}, total={tt_s}")

        header_lines.append("Generator: University AI Report Generator")
        header_lines.append("---\n")  # end of header

        header = "\n".join(header_lines)
        return header + report_text

    def _save_metadata(self, report_filename, metadata):
        """
        Save metadata as a separate JSON file next to the report.
        """
        metadata_filename = report_filename.replace(".md", "_metadata.json")
        metadata_path = self.output_dir / "metadata" / metadata_filename

        # Add timestamp and ensure token_usage exists as explicit key (to make missing usage obvious)
        metadata.setdefault("token_usage", metadata.get("token_usage", None))
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
