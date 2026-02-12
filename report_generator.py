# src/report_generator.py

"""
Report Generator Module — LED IAPT 4.1 Template Version

- Loads comprehensive LED prompt templates from JSON file
- Supports section-by-section generation for long reports
- Maintains retry, validation, and token usage extraction
- Specialized for BAN-PT accreditation reports
"""

import json
import time
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

from google.genai import Client, types


class ReportGenerator:
    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash",
        prompt_path: str = "prompts/prompt_templates.json"
    ):
        """Initialize the ReportGenerator with a GenAI client and load prompt templates."""
        self.client = Client(api_key=api_key)
        self.model_name = model_name
        self.template_config = self._load_template_config(prompt_path)
        print(f"✓ ReportGenerator initialized with model: {self.model_name}")
        print(f"✓ Template loaded: {self.template_config.get('primary_template', {}).get('name', 'Unknown')}")

    # -------------------------------------------------------------------
    # Public Methods
    # -------------------------------------------------------------------

    def generate_report(
        self,
        data_summary: Dict[str, Any],
        report_type: str = "led_iapt_4.1",
        custom_prompt: Optional[str] = None,
        section: Optional[str] = None
    ) -> Tuple[str, Dict[str, Optional[int]]]:
        """
        Generate a narrative report in Indonesian using GenAI.
        
        Args:
            data_summary: Processed data from API endpoints
            report_type: Type of report (currently supports "led_iapt_4.1")
            custom_prompt: Additional user instructions
            section: Specific section to generate (e.g., "section_3", "section_5")
                    If None, generates introduction or full report
        
        Returns:
            Tuple of (report_text, usage_info)
        """
        if section:
            prompt = self._create_section_prompt(data_summary, section, custom_prompt)
        else:
            prompt = self._create_full_prompt(data_summary, custom_prompt)
        
        try:
            response = self._call_model_with_retry(prompt)
            text = response.text
            usage_info = self._extract_usage_info(response)

            print(f"  ✓ Generated {len(text)} characters")
            print(f"  💡 Token usage: {usage_info}")

            # Add usage section at the end
            report = text + "\n\n---\n" + self._format_usage_section(usage_info)
            return report, usage_info

        except Exception as e:
            print(f"  ❌ Error generating report: {e}")
            fallback = self._create_fallback_report(data_summary, section)
            usage_info = {"prompt_tokens": None, "output_tokens": None, "total_tokens": None}
            return fallback, usage_info

    def generate_full_led_report(
        self,
        data_summary: Dict[str, Any],
        custom_prompt: Optional[str] = None
    ) -> Tuple[str, Dict[str, int]]:
        """
        Generate complete LED report by generating each section separately
        and combining them. This handles the 6000-8000 word requirement.
        
        Returns:
            Tuple of (complete_report, total_usage_info)
        """
        sections = [
            "section_1",  # Pendahuluan
            "section_2",  # Renstra SDM
            "section_3",  # Ketersediaan Dosen
            "section_4",  # Tenaga Kependidikan
            "section_5",  # Rasio Mahasiswa-Dosen
            "section_6",  # Analisis SWOT
            "section_7",  # Kesimpulan & Rekomendasi
        ]
        
        full_report = []
        total_usage = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0
        }
        
        print("\n" + "="*70)
        print("🎯 Generating Complete LED IAPT 4.1 Report")
        print("="*70)
        
        for i, section in enumerate(sections, 1):
            print(f"\n📝 Generating {section}... ({i}/{len(sections)})")
            
            section_text, usage = self.generate_report(
                data_summary=data_summary,
                section=section,
                custom_prompt=custom_prompt
            )
            
            # Remove usage footer from individual sections
            section_text = re.sub(r'\n---\n### 📊 Token Usage.*$', '', section_text, flags=re.DOTALL)
            full_report.append(section_text)
            
            # Accumulate token usage
            for key in total_usage:
                if usage.get(key) is not None:
                    total_usage[key] += usage[key]
            
            # Brief pause between sections to avoid rate limits
            if i < len(sections):
                time.sleep(1)
        
        # Combine all sections
        combined_report = "\n\n".join(full_report)
        
        # Add header and metadata
        header = self._create_report_header(data_summary)
        footer = self._create_report_footer(total_usage)
        
        complete_report = f"{header}\n\n{combined_report}\n\n{footer}"
        
        print("\n" + "="*70)
        print(f"✅ Complete report generated!")
        print(f"   Total length: {len(complete_report):,} characters")
        print(f"   Total tokens: {total_usage['total_tokens']:,}")
        print("="*70 + "\n")
        
        return complete_report, total_usage

    def validate_report(
        self, 
        report_text: str, 
        data_summary: Dict[str, Any],
        section: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enhanced validation for LED IAPT 4.1 reports."""
        issues = []
        warnings = []
        
        # Basic length check
        if len(report_text) < 200:
            issues.append("Teks laporan terlalu pendek (<200 karakter)")
        
        # Check for uncertainty language (potential hallucination)
        lower = report_text.lower()
        uncertainty_phrases = [
            "tidak dapat", "data terbatas", "tidak tersedia", 
            "kemungkinan", "mungkin", "diasumsikan"
        ]
        for phrase in uncertainty_phrases:
            if phrase in lower:
                warnings.append(f"Ditemukan frasa ketidakpastian: '{phrase}'")
        
        # Validate data references
        if section in ["section_3", "section_5"]:
            self._validate_staff_data(report_text, data_summary, issues)
        
        if section in ["section_5"]:
            self._validate_student_data(report_text, data_summary, issues)
            self._validate_ratio_calculations(report_text, data_summary, issues)
        
        # Check for required elements based on section
        if section:
            self._validate_section_requirements(report_text, section, issues, warnings)
        
        # Extract numbers for transparency
        numbers = re.findall(r"\d+(?:[.,]\d+)?", report_text)
        
        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "num_extracted": len(numbers),
            "extracted_numbers": numbers[:10]  # First 10 numbers for quick check
        }

    # -------------------------------------------------------------------
    # Internal Helpers — Template Loading
    # -------------------------------------------------------------------

    def _load_template_config(self, path: str) -> Dict[str, Any]:
        """Load comprehensive LED template configuration from JSON file."""
        path_obj = Path(path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Prompt template file not found: {path}")
        
        with open(path_obj, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # Validate required sections
        required_keys = ["system_role", "writing_style", "primary_template"]
        missing = [k for k in required_keys if k not in config]
        if missing:
            raise ValueError(f"Template missing required keys: {missing}")
        
        return config

    # -------------------------------------------------------------------
    # Internal Helpers — Prompt Creation
    # -------------------------------------------------------------------

    def _create_full_prompt(
        self, 
        data_summary: Dict[str, Any], 
        custom_prompt: Optional[str] = None
    ) -> str:
        """Create prompt for full report or introduction."""
        system_role = self._build_system_role()
        writing_guidelines = self._build_writing_guidelines()
        data_context = self._build_data_context(data_summary)
        
        template = self.template_config["primary_template"]
        
        prompt = f"""{system_role}

{writing_guidelines}

TUGAS ANDA:
Buatlah Laporan Evaluasi Diri (LED) untuk Kriteria 2.1.2 sesuai struktur berikut:

{self._format_document_structure()}

{data_context}

INSTRUKSI PENULISAN:
1. Gunakan paragraf naratif yang koheren (JANGAN gunakan bullet points)
2. Setiap klaim harus didukung data konkret
3. Sertakan analisis dan interpretasi, bukan hanya deskripsi
4. Ikuti panduan LED BAN-PT dengan ketat
5. Gunakan Bahasa Indonesia formal dan akademik

"""
        
        if custom_prompt:
            prompt += f"\nINSTRUKSI TAMBAHAN:\n{custom_prompt}\n"
        
        prompt += "\nMulai menulis laporan sekarang:"
        
        return prompt

    def _create_section_prompt(
        self,
        data_summary: Dict[str, Any],
        section: str,
        custom_prompt: Optional[str] = None
    ) -> str:
        """Create prompt for a specific section."""
        system_role = self._build_system_role()
        writing_guidelines = self._build_writing_guidelines()
        data_context = self._build_data_context(data_summary)
        
        section_config = self._get_section_config(section)
        if not section_config:
            raise ValueError(f"Section '{section}' not found in template")
        
        prompt = f"""{system_role}

{writing_guidelines}

TUGAS ANDA:
Buatlah {section_config['section']} dari Laporan Evaluasi Diri (LED) Kriteria 2.1.2.

TUJUAN BAGIAN INI:
{section_config['purpose']}

ELEMEN KUNCI YANG HARUS DIBAHAS:
{self._format_key_elements(section_config['key_elements'])}

PANJANG TARGET:
{section_config.get('word_count', '800-1000 kata')}

{data_context}

{self._build_section_specific_guidance(section, section_config)}

INSTRUKSI PENULISAN:
1. Gunakan paragraf naratif yang koheren (JANGAN gunakan bullet points)
2. Setiap klaim harus didukung data konkret dari data yang tersedia
3. Sertakan analisis dan interpretasi mendalam
4. Jangan membuat data fiktif - gunakan hanya data yang diberikan
5. Gunakan Bahasa Indonesia formal dan akademik

"""
        
        if custom_prompt:
            prompt += f"\nINSTRUKSI TAMBAHAN:\n{custom_prompt}\n"
        
        prompt += f"\nMulai menulis {section_config['section']} sekarang:"
        
        return prompt

    def _build_system_role(self) -> str:
        """Build system role description from template."""
        role = self.template_config["system_role"]
        
        expertise_list = "\n".join([f"- {e}" for e in role["expertise"]])
        principles_list = "\n".join([f"- {p}" for p in role["core_principles"]])
        
        return f"""PERAN ANDA:
{role['base']}

KEAHLIAN ANDA:
{expertise_list}

PRINSIP INTI:
{principles_list}
"""

    def _build_writing_guidelines(self) -> str:
        """Build writing style guidelines."""
        style = self.template_config["writing_style"]
        
        guidelines = "\n".join([f"- {g}" for g in style["guidelines"]])
        prohibited = "\n".join([f"- {p}" for p in style["prohibited_patterns"]])
        
        return f"""PANDUAN PENULISAN:
Bahasa: {style['language']}
Tone: {style['tone']}
Struktur: {style['structure']}

Pedoman:
{guidelines}

LARANGAN:
{prohibited}
"""

    def _build_data_context(self, data_summary: Dict[str, Any]) -> str:
        """Build data context section with available data."""
        context_parts = ["DATA YANG TERSEDIA UNTUK ANALISIS:\n"]
        
        # Staff/Guru Besar data
        if "staff_data" in data_summary:
            staff = data_summary["staff_data"]
            context_parts.append(f"""
DATA DOSEN (Guru Besar):
- Total Guru Besar: {staff.get('total_professors', 'N/A')}
- Distribusi per Fakultas: {json.dumps(staff.get('by_faculty', {}), ensure_ascii=False, indent=2)}
""")
        
        # Student data
        if "student_data" in data_summary:
            students = data_summary["student_data"]
            context_parts.append(f"""
DATA MAHASISWA AKTIF:
- Total Mahasiswa: {students.get('total_students', 'N/A')}
- Distribusi per Jenjang: {json.dumps(students.get('by_level', {}), ensure_ascii=False, indent=2)}
- Distribusi per Program Studi: {json.dumps(students.get('by_program', {}), ensure_ascii=False, indent=2)}
""")
        
        # Prodi unggul data
        if "prodi_data" in data_summary:
            prodi = data_summary["prodi_data"]
            context_parts.append(f"""
DATA PROGRAM STUDI UNGGULAN:
- Jumlah Prodi Unggulan: {prodi.get('total_programs', 'N/A')}
- Daftar Prodi: {json.dumps(prodi.get('programs', []), ensure_ascii=False, indent=2)}
""")
        
        # Calculated ratios
        if "calculated_ratios" in data_summary:
            ratios = data_summary["calculated_ratios"]
            context_parts.append(f"""
RASIO YANG TELAH DIHITUNG:
{json.dumps(ratios, ensure_ascii=False, indent=2)}
""")
        
        context_parts.append("""
CATATAN PENTING:
- Gunakan HANYA data yang tersedia di atas
- Jika data tidak tersedia, nyatakan dengan jelas "Data tidak tersedia"
- Jangan membuat asumsi atau data fiktif
- Setiap angka harus dapat ditelusuri ke data di atas
""")
        
        return "\n".join(context_parts)

    def _build_section_specific_guidance(
        self, 
        section: str, 
        config: Dict[str, Any]
    ) -> str:
        """Build specific guidance for different sections."""
        guidance_parts = []
        
        # Add metrics guidance
        if "metrics_to_calculate" in config:
            metrics_list = "\n".join([f"- {m}" for m in config["metrics_to_calculate"]])
            guidance_parts.append(f"""
METRIK YANG HARUS DIHITUNG:
{metrics_list}
""")
        
        # Add validation requirements
        if "validation" in config:
            if isinstance(config["validation"], list):
                validation_list = "\n".join([f"- {v}" for v in config["validation"]])
            else:
                validation_list = f"- {config['validation']}"
            
            guidance_parts.append(f"""
VALIDASI YANG HARUS DIPENUHI:
{validation_list}
""")
        
        # Add standards for ratio section
        if section == "section_5" and "standards" in config:
            standards = config["standards"]
            standards_text = "\n".join([f"- {k}: {v}" for k, v in standards.items()])
            guidance_parts.append(f"""
STANDAR RASIO MAHASISWA-DOSEN:
{standards_text}
""")
        
        # Add calculation formula
        if "calculation_formula" in config:
            guidance_parts.append(f"""
FORMULA PERHITUNGAN:
{config['calculation_formula']}
""")
        
        return "\n".join(guidance_parts)

    def _format_document_structure(self) -> str:
        """Format the complete document structure."""
        structure = self.template_config["primary_template"]["document_structure"]
        formatted = []
        
        for item in structure:
            formatted.append(f"{item['section']}")
            formatted.append(f"Tujuan: {item['purpose']}")
            formatted.append(f"Panjang: {item.get('word_count', 'sesuai kebutuhan')}")
            formatted.append("")
        
        return "\n".join(formatted)

    def _format_key_elements(self, elements: List[str]) -> str:
        """Format key elements list."""
        return "\n".join([f"- {elem}" for elem in elements])

    def _get_section_config(self, section: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific section."""
        section_map = {
            "section_1": 0,  # Pendahuluan
            "section_2": 1,  # Renstra SDM
            "section_3": 2,  # Ketersediaan Dosen
            "section_4": 3,  # Tenaga Kependidikan
            "section_5": 4,  # Rasio
            "section_6": 5,  # Analisis SWOT
            "section_7": 6,  # Kesimpulan
        }
        
        idx = section_map.get(section)
        if idx is None:
            return None
        
        structure = self.template_config["primary_template"]["document_structure"]
        return structure[idx] if idx < len(structure) else None

    # -------------------------------------------------------------------
    # Internal Helpers — Report Formatting
    # -------------------------------------------------------------------

    def _create_report_header(self, data_summary: Dict[str, Any]) -> str:
        """Create report header with metadata."""
        template = self.template_config["primary_template"]
        regulatory = template["regulatory_basis"]
        
        return f"""# LAPORAN EVALUASI DIRI (LED)
## {template['name']}

**Peraturan:** {regulatory['regulation']}  
**Instrumen:** {regulatory['instrument']}  
**Kriteria:** {regulatory['criteria']}

**Tanggal Pembuatan:** {time.strftime("%d %B %Y")}

---
"""

    def _create_report_footer(self, usage_info: Dict[str, int]) -> str:
        """Create report footer with metadata."""
        return f"""---

## 📊 Metadata Laporan

**Informasi Token:**
- Total Prompt Tokens: {usage_info['prompt_tokens']:,}
- Total Output Tokens: {usage_info['output_tokens']:,}
- Total Tokens: {usage_info['total_tokens']:,}

**Catatan:**
- Laporan ini dihasilkan menggunakan AI (Gemini 2.5 Flash)
- Semua data bersumber dari API SIMASTER UGM
- Validasi manual tetap diperlukan untuk akurasi
- Format sesuai IAPT 4.1 BAN-PT

---
*Dokumen ini dibuat secara otomatis. Harap verifikasi semua data dan analisis sebelum penggunaan resmi.*
"""

    # -------------------------------------------------------------------
    # Internal Helpers — Validation
    # -------------------------------------------------------------------

    def _validate_staff_data(
        self, 
        report_text: str, 
        data_summary: Dict[str, Any], 
        issues: List[str]
    ):
        """Validate staff-related data in report."""
        staff_data = data_summary.get("staff_data", {})
        total_prof = staff_data.get("total_professors")
        
        if total_prof is not None:
            # Check if report mentions professor count
            matches = re.findall(r"Guru\s+Besar\s*[:\s]+(\d+)", report_text, re.IGNORECASE)
            for match in matches:
                val = int(match)
                if abs(val - total_prof) > 2:  # Allow small rounding differences
                    issues.append(
                        f"Jumlah Guru Besar di narasi ({val}) tidak sesuai data ({total_prof})"
                    )

    def _validate_student_data(
        self,
        report_text: str,
        data_summary: Dict[str, Any],
        issues: List[str]
    ):
        """Validate student-related data in report."""
        student_data = data_summary.get("student_data", {})
        total_students = student_data.get("total_students")
        
        if total_students is not None:
            matches = re.findall(r"mahasiswa\s*(?:aktif)?\s*[:\s]+(\d+)", report_text, re.IGNORECASE)
            for match in matches:
                val = int(match.replace(".", "").replace(",", ""))
                tolerance = max(10, 0.02 * total_students)  # 2% tolerance
                if abs(val - total_students) > tolerance:
                    issues.append(
                        f"Jumlah mahasiswa di narasi ({val:,}) tidak sesuai data ({total_students:,})"
                    )

    def _validate_ratio_calculations(
        self,
        report_text: str,
        data_summary: Dict[str, Any],
        issues: List[str]
    ):
        """Validate ratio calculations in report."""
        ratios = data_summary.get("calculated_ratios", {})
        
        # Check if ratios are mentioned correctly
        ratio_matches = re.findall(r"rasio\s+(\d+):(\d+)", report_text, re.IGNORECASE)
        if ratio_matches and not ratios:
            issues.append("Rasio disebutkan di narasi tetapi tidak ada dalam data")

    def _validate_section_requirements(
        self,
        report_text: str,
        section: str,
        issues: List[str],
        warnings: List[str]
    ):
        """Validate section-specific requirements."""
        section_config = self._get_section_config(section)
        if not section_config:
            return
        
        # Check word count
        word_count_range = section_config.get("word_count", "")
        if "-" in word_count_range:
            min_words, max_words = map(int, word_count_range.split("-")[0].split())
            actual_words = len(report_text.split())
            
            if actual_words < min_words * 0.8:  # 80% of minimum
                warnings.append(
                    f"Jumlah kata ({actual_words}) di bawah target minimum ({min_words})"
                )
            elif actual_words > max_words * 1.2:  # 120% of maximum
                warnings.append(
                    f"Jumlah kata ({actual_words}) melebihi target maksimum ({max_words})"
                )
        
        # Check for key elements
        key_elements = section_config.get("key_elements", [])
        for element in key_elements[:3]:  # Check first 3 elements
            # Simple keyword check
            keywords = element.lower().split()[:3]  # First 3 words
            if not any(kw in report_text.lower() for kw in keywords):
                warnings.append(f"Elemen kunci mungkin belum dibahas: {element}")

    # -------------------------------------------------------------------
    # Internal Helpers — Model Interaction
    # -------------------------------------------------------------------

    def _call_model_with_retry(
        self, 
        prompt: str, 
        max_retries: int = 3
    ) -> types.GenerateContentResponse:
        """Call the GenAI model with retry logic."""
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

    def _extract_usage_info(
        self, 
        response: types.GenerateContentResponse
    ) -> Dict[str, Optional[int]]:
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
            lines.append(f"- Prompt tokens: **{usage['prompt_tokens']:,}**")
            lines.append(f"- Output tokens: **{usage['output_tokens']:,}**")
            lines.append(f"- Total tokens: **{usage['total_tokens']:,}**")
        return "\n".join(lines)

    def _create_fallback_report(
        self, 
        data_summary: Dict[str, Any],
        section: Optional[str] = None
    ) -> str:
        """Return a fallback report when generation fails."""
        section_name = f" - {section}" if section else ""
        data_json = json.dumps(data_summary, ensure_ascii=False, indent=2)
        
        return f"""# Laporan Evaluasi Diri (Fallback){section_name}

## ⚠️ Pemberitahuan

Laporan ini dihasilkan dalam mode fallback karena terjadi kesalahan saat 
menghasilkan narasi AI.

## Data yang Tersedia

```json
{data_json}
```

## Catatan

*AI gagal menghasilkan teks naratif. Silakan gunakan data di atas untuk 
membuat laporan secara manual atau coba lagi.*
"""


if __name__ == "__main__":
    print("="*70)
    print("LED IAPT 4.1 Report Generator Module")
    print("="*70)
    
    # Test with dummy data
    test_data = {
        "staff_data": {
            "total_professors": 150,
            "by_faculty": {"Teknik": 45, "MIPA": 38, "Kedokteran": 35}
        },
        "student_data": {
            "total_students": 5000,
            "by_level": {"S1": 3500, "S2": 1000, "S3": 500}
        }
    }
    
    try:
        gen = ReportGenerator(api_key="DUMMY_KEY")
        print("✓ ReportGenerator module loaded successfully.")
        print(f"✓ Template: {gen.template_config['primary_template']['name']}")
    except Exception as e:
        print(f"✗ Error: {e}")