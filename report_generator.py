# src/generator.py

"""
Report Generator Module — updated for Google GenAI SDK

This module:
- Uses the google-genai (Google GenAI) Python SDK to call Gemini / generative models
- Builds prompt text from structured facts
- Has retry/backoff logic for API calls
- Parses responses and falls back gracefully
- (Optional) Basic validation logic of output text
"""

from google.genai import Client
from google.genai import types
import time
from typing import Dict, Any, Optional

class ReportGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the ReportGenerator with a GenAI client.
        """
        # Create a client instance
        self.client = Client(api_key=api_key)
        self.model_name = model_name
        print(f"✓ ReportGenerator initialized with model: {self.model_name}")

    def generate_report(
        self,
        data_summary: Dict[str, Any],
        report_type: str = "general"
    ) -> str:
        """
        Generate a narrative report in Indonesian using GenAI.

        Args:
            data_summary: dictionary of facts/calculated metrics
            report_type: controls type of structure (e.g. "student_performance", "financial_analysis", or general)

        Returns:
            Generated text from model, or fallback text if failure.
        """
        prompt = self._create_prompt(data_summary, report_type)
        try:
            response = self._call_model_with_retry(prompt)
            text = response.text  # GenAI SDK response has `.text`
            print(f"  ✓ Successfully generated {len(text)} characters")
            return text
        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
            return self._create_fallback_report(data_summary)

    def _create_prompt(self, data_summary: Dict[str, Any], report_type: str) -> str:
        """
        Construct the prompt text to feed into the model, combining instructions + data summary.
        """
        # You may have a helper to convert data_summary to readable text
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)

        base = (
            "Anda adalah analis data universitas yang ahli. "
            "Anda hanya boleh menggunakan data yang diberikan — jangan menambahkan informasi eksternal.\n\n"
        )

        if report_type == "student_performance":
            spec = (
                "Struktur laporan:\n"
                "1. RINGKASAN EKSEKUTIF\n"
                "2. ANALISIS PERFORMA MAHASISWA (nilai, tren)\n"
                "3. KESIMPULAN & REKOMENDASI\n\n"
            )
        elif report_type == "financial_analysis":
            spec = (
                "Struktur laporan:\n"
                "1. TINJAUAN KEUANGAN\n"
                "2. ANALISIS DETAIL (pendapatan, pengeluaran, rasio)\n"
                "3. KESIMPULAN & SARAN\n\n"
            )
        else:
            spec = (
                "Struktur laporan umum:\n"
                "1. Ringkasan\n"
                "2. Analisis\n"
                "3. Kesimpulan\n\n"
            )

        prompt = (
            f"{base}{spec}"
            f"DATA YANG HARUS DIANALISIS:\n{summary_block}\n\n"
            "Tulislah laporan naratif dalam Bahasa Indonesia sesuai struktur di atas:"
        )

        return prompt

    def _call_model_with_retry(self, prompt: str, max_retries: int = 3) -> types.GenerateContentResponse:
        """
        Call the GenAI model with retry / exponential backoff.

        Args:
            prompt: prompt string
            max_retries: number of attempts

        Returns:
            The GenAI response object.

        Raises:
            Exception if all retries fail.
        """
        for attempt in range(max_retries):
            try:
                # Build content object
                content = types.Content(parts=[types.Part(text=prompt)])
                resp = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[content]
                )
                return resp
            except Exception as e:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    print(f"  ⚠ Attempt {attempt+1} failed, retrying in {wait}s…")
                    time.sleep(wait)
                else:
                    raise Exception(f"API call failed after {max_retries} attempts: {e}")

    def validate_report(
        self,
        report_text: str,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        (Optional) Basic validation to catch glaring issues.

        Returns a dict with keys:
        - is_valid (bool)
        - issues (list of strings)
        - num_extracted (int) — number of numeric matches in text
        """
        import re
        issues = []
        numbers = re.findall(r"\d+(?:\.\d+)?", report_text)

        # Example check: too short
        if len(report_text) < 200:
            issues.append("Teks laporan terlalu pendek (<200 karakter)")

        # Example check: presence of placeholder phrases
        lower = report_text.lower()
        if "tidak dapat" in lower or "data terbatas" in lower:
            issues.append("Laporan menyiratkan ketidakpastian atau kekurangan data")

        return {
            "is_valid": (len(issues) == 0),
            "issues": issues,
            "num_extracted": len(numbers),
        }

    def _create_fallback_report(self, data_summary: Dict[str, Any]) -> str:
        """
        Return a simple fallback markdown report if AI fails.
        """
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)

        fallback = (
            "# Laporan Universitas (Fallback)\n\n"
            "Laporan ini dihasilkan berdasarkan data berikut:\n\n"
            f"{summary_block}\n\n"
            "*Catatan: AI gagal menghasilkan teks, laporan fallback digunakan.*"
        )

        return fallback


if __name__ == "__main__":
    print("This is the ReportGenerator module (GenAI version).")
    print("Instantiate ReportGenerator(api_key, model_name) and call generate_report(...).")
