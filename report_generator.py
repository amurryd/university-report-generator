# src/report_generator.py

"""
Report Generator Module — JSON Prompt Template Version

- Loads prompt templates from JSON file (under src/prompts/prompt_templates.json)
- Supports flexible prompt customization by report type
- Maintains retry, validation, and token usage extraction
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from google.genai import Client, types


class ReportGenerator:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        prompt_path: str = "prompts/general.json"
    ):
        """Initialize the ReportGenerator with a GenAI client and load prompt templates."""
        self.client = Client(api_key=api_key)
        self.model_name = model_name
        self.prompt_templates = self._load_prompt_templates(prompt_path)
        print(f"✓ ReportGenerator initialized with model: {self.model_name}")

    # -------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------

    def generate_report(
        self,
        data_summary: Dict[str, Any],
        report_type: str = "general"
    ) -> Tuple[str, Dict[str, Optional[int]]]:
        """
        Generate a narrative report in Indonesian using GenAI,
        and return also the token usage metadata.
        """
        prompt = self._create_prompt(data_summary, report_type)
        try:
            response = self._call_model_with_retry(prompt)
            text = response.text
            usage_info = self._extract_usage_info(response)

            print(f"  ✓ Generated {len(text)} characters")
            print(f"  💡 Token usage: {usage_info}")

            report = text + "\n\n---\n" + self._format_usage_section(usage_info)
            return report, usage_info

        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
            fallback = self._create_fallback_report(data_summary)
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}
            return fallback, usage_info

    def validate_report(self, report_text: str, data_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Enhanced validation to catch hallucinations and mismatches."""
        issues = []
        numbers = re.findall(r"\d+(?:\.\d+)?", report_text)

        if len(report_text) < 200:
            issues.append("Teks laporan terlalu pendek (<200 karakter)")

        lower = report_text.lower()
        if "tidak dapat" in lower or "data terbatas" in lower:
            issues.append("Laporan menyiratkan ketidakpastian atau kekurangan data")

        depts = data_summary.get("departments", {})
        for match in re.findall(r"Departemen\s+([A-Za-z]+)", report_text):
            if match not in depts:
                issues.append(f"Departemen '{match}' disebut dalam teks, tapi tidak ada di data")

        total = data_summary.get("total_students")
        if total is not None:
            match = re.search(r"mahasiswa\s*[=:]?\s*(\d+)", report_text)
            if match:
                val = int(match.group(1))
                if abs(val - total) > max(1, 0.05 * total):
                    issues.append(f"Isi narasi menyebut total mahasiswa = {val}, tetapi data menyebut {total}")

        return {"is_valid": len(issues) == 0, "issues": issues, "num_extracted": len(numbers)}

    # -------------------------------------------------------------------
    # Internal Helpers
    # -------------------------------------------------------------------

    def _load_prompt_templates(self, path: str) -> Dict[str, Any]:
        """Load prompt templates from JSON file."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Prompt template file not found: {path}")
        with open(path_obj, "r", encoding="utf-8") as f:
            return json.load(f)

    def _create_prompt(self, data_summary: Dict[str, Any], report_type: str) -> str:
        """Build a prompt using loaded JSON templates."""
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)

        base = self.prompt_templates.get("base", "")
        style = self.prompt_templates.get("style", "")
        templates = self.prompt_templates.get("templates", {})
        spec = templates.get(report_type, templates.get("general", ""))

        prompt = (
            f"{base}\n\n{spec}\n\n{style}\n\n"
            f"DATA YANG HARUS DIANALISIS:\n{summary_block}\n\n"
            "Tulislah laporan naratif dalam Bahasa Indonesia sesuai struktur di atas:"
        )
        return prompt

    def _call_model_with_retry(self, prompt: str, max_retries: int = 3) -> types.GenerateContentResponse:
        """Call the GenAI model with retry logic."""
        for attempt in range(max_retries):
            try:
                content = types.Content(parts=[types.Part(text=prompt)])
                resp = self.client.models.generate_content(model=self.model_name, contents=[content])
                return resp
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  ⚠ Attempt {attempt+1} failed, retrying in {wait}s…")
                    time.sleep(wait)
                else:
                    raise Exception(f"API call failed after {max_retries} attempts: {e}")

    def _extract_usage_info(self, response: types.GenerateContentResponse) -> Dict[str, Optional[int]]:
        """Extract token usage metadata."""
        usage = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}
        meta = getattr(response, "usage_metadata", None)
        if meta is not None:
            usage["prompt_tokens"] = getattr(meta, "prompt_token_count", None)
            usage["output_tokens"] = getattr(meta, "candidates_token_count", None)
            usage["total_tokens"] = getattr(meta, "total_token_count", None)
        return usage

    def _format_usage_section(self, usage: Dict[str, Optional[int]]) -> str:
        """Format a Markdown section showing token usage."""
        lines = ["### 📊 Token Usage"]
        if usage["prompt_tokens"] is None:
            lines.append("_Token usage data tidak tersedia._")
        else:
            lines.append(f"- Prompt tokens: **{usage['prompt_tokens']}**")
            lines.append(f"- Output tokens: **{usage['output_tokens']}**")
            lines.append(f"- Total tokens: **{usage['total_tokens']}**")
        return "\n".join(lines)

    def _create_fallback_report(self, data_summary: Dict[str, Any]) -> str:
        """Return a fallback report when generation fails."""
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)
        return (
            "# Laporan Universitas (Fallback)\n\n"
            "Laporan ini dihasilkan berdasarkan data berikut:\n\n"
            f"{summary_block}\n\n"
            "*Catatan: AI gagal menghasilkan teks, sehingga laporan fallback digunakan.*"
        )


if __name__ == "__main__":
    gen = ReportGenerator(api_key="DUMMY_KEY")
    print("ReportGenerator module with JSON prompt templates loaded successfully.")
