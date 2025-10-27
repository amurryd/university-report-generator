"""
Output Manager Module — with Token Usage + HTML Export (Enhanced)

Saves reports to Markdown files with metadata including token usage,
writes a separate metadata JSON file, and can generate a printable HTML version.
"""

from datetime import datetime
from pathlib import Path
import json
import copy
import markdown  # pip install markdown


class OutputManager:
    """
    Manages output files for generated reports:
    - Creating directory structure
    - Saving reports as Markdown
    - Adding metadata (source, validation, token usage)
    - Organizing files by date/type
    - Converting Markdown to HTML for printable/exportable versions
    """

    def __init__(self, output_dir="reports"):
        self.output_dir = Path(output_dir)
        self._ensure_output_directory()
        print("✓ Output Manager initialized")

    def _ensure_output_directory(self):
        (self.output_dir / "student_reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "finance_reports").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "metadata").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "html").mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------
    # Markdown SAVE
    # ----------------------------------------------------------
    def save_report(self, report_text, report_type="general", metadata=None):
        """
        Save a report to a Markdown file with metadata and token usage.

        Args:
            report_text (str): Generated report (may already contain appended usage)
            report_type (str): 'student_report', 'finance_report', etc.
            metadata (dict): Extra metadata including token_usage

        Returns:
            dict: {"markdown_path": str, "html_path": str}
        """
        if metadata is None:
            metadata = {}

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{report_type}_{timestamp}.md"

        # choose subdir
        if "student" in report_type.lower():
            subdir = "student_reports"
        elif "finance" in report_type.lower():
            subdir = "finance_reports"
        else:
            subdir = ""

        md_path = (self.output_dir / subdir / filename) if subdir else (self.output_dir / filename)

        # Build final content with metadata header
        full_content = self._add_metadata_header(report_text, metadata)

        # Write markdown file
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full_content)

        # Save metadata JSON
        if metadata:
            metadata_copy = copy.deepcopy(metadata)
            self._save_metadata(filename, metadata_copy)

        # Convert to HTML
        html_path = self.convert_to_html(md_path, metadata)

        return {"markdown_path": str(md_path), "html_path": str(html_path)}

    # ----------------------------------------------------------
    # Metadata
    # ----------------------------------------------------------
    def _add_metadata_header(self, report_text, metadata):
        header_lines = ["---"]
        header_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if metadata:
            if "source_file" in metadata:
                header_lines.append(f"Source: {metadata['source_file']}")
            if "validation" in metadata:
                val = metadata["validation"]
                header_lines.append(f"Validation: {'✓ Pass' if val.get('is_valid') else '⚠ Issues detected'}")

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
        header_lines.append("---\n")

        header = "\n".join(header_lines)
        return header + report_text

    def _save_metadata(self, report_filename, metadata):
        metadata_filename = report_filename.replace(".md", "_metadata.json")
        metadata_path = self.output_dir / "metadata" / metadata_filename
        metadata.setdefault("token_usage", metadata.get("token_usage", None))
        metadata["saved_at"] = datetime.now().isoformat()
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    # ----------------------------------------------------------
    # Markdown → HTML Conversion
    # ----------------------------------------------------------
    def convert_to_html(self, markdown_path: Path, metadata: dict = None):
        """
        Convert a Markdown report into a styled HTML file for printing/exporting.

        Args:
            markdown_path (Path): path to .md file
            metadata (dict): optional metadata (for header/footer info)
        Returns:
            Path: path to saved .html file
        """
        if metadata is None:
            metadata = {}

        html_output_path = self.output_dir / "html" / (markdown_path.stem + ".html")

        with open(markdown_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        html_body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])

        # Basic HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>{metadata.get("title", "Laporan Universitas")}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            margin: 40px auto;
            max-width: 900px;
            line-height: 1.6;
            color: #222;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        th {{
            background-color: #f4f4f4;
        }}
        code, pre {{
            background-color: #f8f8f8;
            padding: 2px 5px;
            border-radius: 4px;
        }}
        hr {{
            margin: 30px 0;
        }}
        footer {{
            margin-top: 50px;
            font-size: 0.85em;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
{html_body}
<hr>
<footer>
    <p>Dihasilkan oleh <strong>University AI Report Generator</strong></p>
    <p>{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
</footer>
</body>
</html>"""

        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"🖨️  HTML version saved: {html_output_path}")
        return html_output_path

    # ----------------------------------------------------------
    # Listing Reports
    # ----------------------------------------------------------
    def list_reports(self, report_type=None):
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
