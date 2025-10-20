# src/generator.py

"""
Report Generator Module — with Token Usage + Enhanced Validation

This module:
- Uses the google-genai (Google GenAI) Python SDK to call Gemini / generative models
- Builds prompt text from structured facts
- Has retry/backoff logic for API calls
- Extracts and reports token usage metadata
- Performs enhanced validation (claim checks, entity mismatch, length, placeholders)
- Falls back gracefully when API fails
"""

from google.genai import Client
from google.genai import types
import time
import re
from typing import Dict, Any, Optional, Tuple


class ReportGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        """
        Initialize the ReportGenerator with a GenAI client.
        """
        self.client = Client(api_key=api_key)
        self.model_name = model_name
        print(f"✓ ReportGenerator initialized with model: {self.model_name}")

    def generate_report(
        self,
        data_summary: Dict[str, Any],
        report_type: str = "general"
    ) -> Tuple[str, Dict[str, Optional[int]]]:
        """
        Generate a narrative report in Indonesian using GenAI,
        and return also the token usage metadata.

        Returns:
            - report_text: the narrative (or fallback)
            - usage_info: dict with keys 'prompt_tokens', 'output_tokens', 'total_tokens'
        """
        prompt = self._create_prompt(data_summary, report_type)
        try:
            response = self._call_model_with_retry(prompt)
            text = response.text  # Extract the generated narration
            usage_info = self._extract_usage_info(response)

            print(f"  ✓ Generated {len(text)} characters")
            print(f"  💡 Token usage: {usage_info}")

            # Append token usage to the narrative (Markdown section)
            report = text + "\n\n---\n" + self._format_usage_section(usage_info)
            return report, usage_info

        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
            fallback = self._create_fallback_report(data_summary)
            # In fallback, usage info is None or zeros
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}
            return fallback, usage_info

    def _create_prompt(self, data_summary: Dict[str, Any], report_type: str) -> str:
        """
        Construct the prompt text including instructions + facts.
        """
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)

        base = (
           "Anda adalah analis institusi universitas yang sangat berpengalaman. "
           "Tugas Anda adalah menyusun laporan analitis yang terstruktur, informatif, dan formal "
           "berdasarkan data yang diberikan di bawah ini. "
           "Gunakan hanya informasi yang tersedia dalam data — jangan membuat asumsi atau menambahkan data eksternal.\n\n"        
           )

        if report_type == "student_performance":
            spec = (
               "Tulis laporan performa mahasiswa dengan format berikut:\n"
               "1. RINGKASAN EKSEKUTIF — ringkas temuan utama (jumlah mahasiswa, tren nilai, status aktif, dsb.)\n"
               "2. ANALISIS PERFORMA — bahas analisis nilai (rata-rata, tren, variasi), IPK, dan kategori status\n"
               "3. KESIMPULAN & REKOMENDASI — simpulkan temuan dan berikan saran kebijakan atau tindakan\n\n"
               )
        elif report_type == "financial_analysis":
            spec = (
                "Tulis laporan keuangan institusi dengan format berikut:\n"
                "1. TINJAUAN KEUANGAN — gambaran umum kondisi keuangan\n"
                "2. ANALISIS DETAIL — bahas pendapatan, pengeluaran, rasio penting, serta tren utama\n"
                "3. KESIMPULAN & SARAN — simpulkan dan berikan rekomendasi strategis\n\n"
                )
        else:
            spec = (
                "Tulis laporan analitis umum dengan format berikut:\n"
                "1. Ringkasan Umum\n"
                "2. Analisis Data\n"
                "3. Kesimpulan & Rekomendasi\n\n"
            )
            
        style = (
            "Gaya penulisan:\n"
            "- Gunakan Bahasa Indonesia yang formal dan jelas.\n"
            "- Jangan hanya menyalin angka; jelaskan makna statistiknya (misalnya: tren IPK, jurusan dominan, variasi nilai).\n"
            "- Gunakan paragraf terstruktur, bukan bullet list.\n"
            "- Jika relevan, hubungkan temuan numerik dan kategorikal untuk memberikan insight.\n\n"    
        )

        prompt = (
            f"{base}{spec}{style}"
            f"DATA YANG HARUS DIANALISIS:\n{summary_block}\n\n"
            "Tulislah laporan naratif dalam Bahasa Indonesia sesuai struktur di atas:"
        )

        return prompt

    def _call_model_with_retry(self, prompt: str, max_retries: int = 3) -> types.GenerateContentResponse:
        """
        Call the GenAI model with retry logic.
        """
        for attempt in range(max_retries):
            try:
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

    def _extract_usage_info(self, response: types.GenerateContentResponse) -> Dict[str, Optional[int]]:
        """
        Extract token usage metadata from the response, if available.
        According to Gemini API, usage_metadata has prompt_token_count, candidates_token_count, total_token_count. :contentReference[oaicite:0]{index=0}
        """
        usage = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}
        try:
            meta = getattr(response, "usage_metadata", None)
            if meta is not None:
                usage["prompt_tokens"] = getattr(meta, "prompt_token_count", None)
                usage["output_tokens"] = getattr(meta, "candidates_token_count", None)
                usage["total_tokens"] = getattr(meta, "total_token_count", None)
        except Exception:
            pass
        return usage

    def _format_usage_section(self, usage: Dict[str, Optional[int]]) -> str:
        """
        Format a Markdown section showing token usage.
        """
        lines = ["### 📊 Token Usage"]
        if usage["prompt_tokens"] is None:
            lines.append("_Token usage data tidak tersedia._")
        else:
            lines.append(f"- Prompt tokens: **{usage['prompt_tokens']}**")
            lines.append(f"- Output tokens: **{usage['output_tokens']}**")
            lines.append(f"- Total tokens: **{usage['total_tokens']}**")
        return "\n".join(lines)

    def validate_report(
        self,
        report_text: str,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced validation to catch hallucinations and mismatches.
        Returns dict:
        - is_valid (bool)
        - issues (list)
        - num_extracted (int)
        """
        issues = []
        numbers = re.findall(r"\d+(?:\.\d+)?", report_text)

        # 1. Too short
        if len(report_text) < 200:
            issues.append("Teks laporan terlalu pendek (<200 karakter)")

        # 2. Placeholder phrases
        lower = report_text.lower()
        if "tidak dapat" in lower or "data terbatas" in lower:
            issues.append("Laporan menyiratkan ketidakpastian atau kekurangan data")

        # 3. Mismatch of departments/names (entity check)
        # Suppose data_summary has a list of valid departments under data_summary["departments"]
        depts = data_summary.get("departments", {})
        for dept in depts:
            # If a similar word appears in report, good; else, if report mentions a dept not in data, flag
            # Here we do a simple check: if any capitalized word “Departemen X” appears and not in depts
            pattern = rf"Departemen\s+([A-Za-z]+)"
            for match in re.findall(pattern, report_text):
                if match not in depts:
                    issues.append(f"Departemen '{match}' disebut dalam teks, tapi tidak ada di data")

        # 4. Claim extraction: if the narrative states “total mahasiswa = X”, compare X to data_summary
        # Suppose data_summary["total_students"] exists
        total = data_summary.get("total_students")
        if total is not None:
            # look for number near “mahasiswa” in the text
            match = re.search(r"mahasiswa\s*[=:]?\s*(\d+)", report_text)
            if match:
                val = int(match.group(1))
                if abs(val - total) > max(1, 0.05 * total):
                    issues.append(f"Isi narasi menyebut total mahasiswa = {val}, tetapi data menyebut {total}")

        return {
            "is_valid": (len(issues) == 0),
            "issues": issues,
            "num_extracted": len(numbers),
        }

    def _create_fallback_report(self, data_summary: Dict[str, Any]) -> str:
        """
        Return a fallback report when generation fails.
        """
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_block = processor.get_data_summary_for_ai(data_summary)

        fallback = (
            "# Laporan Universitas (Fallback)\n\n"
            "Laporan ini dihasilkan berdasarkan data berikut:\n\n"
            f"{summary_block}\n\n"
            "*Catatan: AI gagal menghasilkan teks, sehingga laporan fallback digunakan.*"
        )
        return fallback


if __name__ == "__main__":
    print("ReportGenerator module (with token usage & enhanced validation)")