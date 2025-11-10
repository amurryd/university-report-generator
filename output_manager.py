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
        Convert a Markdown report into a professionally styled HTML file
        suitable for printing or PDF export (A4 layout with header/footer).
        """
        if metadata is None:
            metadata = {}

        html_output_path = self.output_dir / "html" / (markdown_path.stem + ".html")

        with open(markdown_path, "r", encoding="utf-8") as f:
            md_text = f.read()

        html_body = markdown.markdown(md_text, extensions=["fenced_code", "tables"])

        # Clean metadata info
        report_title = metadata.get("title", "Laporan Universitas")
        generated_time = datetime.now().strftime("%d %B %Y, %H:%M:%S")

        # Professional print-ready HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <title>{report_title}</title>
    <style>
        /* ====== PRINT STYLES (A4 Layout) ====== */
        @page {{
            size: A4;
            margin: 25mm 20mm 25mm 20mm;
        }}
        @media print {{
            body {{
                margin: 0;
                padding: 0;
                background: white;
            }}
            header, footer {{
                position: fixed;
                left: 0;
                right: 0;
                color: #555;
                font-size: 0.8em;
            }}
            header {{
                top: 0;
                border-bottom: 1px solid #ccc;
                padding: 8px 0;
                text-align: center;
            }}
            footer {{
                bottom: 0;
                border-top: 1px solid #ccc;
                padding: 6px 0;
                text-align: center;
            }}
            .page-break {{
                page-break-before: always;
            }}
        }}

        /* ====== GENERAL PAGE STYLES ====== */
        body {{
            font-family: 'Segoe UI', Tahoma, sans-serif;
            line-height: 1.6;
            color: #222;
            margin: 40px auto;
            max-width: 900px;
        }}
        h1, h2, h3, h4 {{
            color: #1f3b73;
            font-weight: 600;
            margin-top: 1.6em;
        }}
        h1 {{
            text-align: center;
            border-bottom: 3px solid #1f3b73;
            padding-bottom: 0.3em;
        }}
        h2 {{
            margin-top: 1.4em;
            border-left: 5px solid #2c6e91;
            padding-left: 8px;
        }}
        p {{
            text-align: justify;
            margin: 0.5em 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 0.95em;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 10px;
        }}
        th {{
            background-color: #f4f6f9;
            color: #333;
            text-align: center;
        }}
        tr:nth-child(even) {{
            background-color: #fafafa;
        }}
        code, pre {{
            background-color: #f8f8f8;
            padding: 3px 6px;
            border-radius: 4px;
            font-family: Consolas, monospace;
            font-size: 0.9em;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #ccc;
            margin: 30px 0;
        }}
        footer {{
            margin-top: 60px;
            text-align: center;
            color: #666;
            font-size: 0.85em;
        }}
        .page-break {{
            page-break-before: always;
        }}
    </style>
</head>
<body>

<header>
    <strong>{report_title}</strong>
</header>

<footer>
    Dihasilkan oleh <strong>University AI Report Generator</strong> — {generated_time}
</footer>

<main>
{html_body}
</main>

</body>
</html>"""

        with open(html_output_path, "w", encoding="utf-8") as f:
            f.write(html_template)

        print(f"🖨️  Professional HTML version saved: {html_output_path}")
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
