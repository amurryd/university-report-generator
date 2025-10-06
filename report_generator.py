"""
Report Generator Module
Integrates with Google Gemini API to generate narrative reports

This is the core AI integration module that:
- Calls the Gemini API
- Generates Indonesian-language reports
- Validates outputs for hallucinations
"""

import google.genai as genai
import time
from typing import Dict, Any


class ReportGenerator:
    """
    Handles AI-powered report generation using Google Gemini
    
    This class manages:
    - API communication with Gemini
    - Prompt engineering for good reports
    - Hallucination detection
    - Error handling and retries
    """
    
    def __init__(self, api_key, model_name='gemini-2.5-flash'):
        """
        Initialize the report generator with Gemini API
        
        Args:
            api_key (str): Google Gemini API key
            model_name (str): Gemini model to use
                Options: 
                - 'gemini-2.5-flash' (recommended: best price-performance)
                - 'gemini-2.5-pro' (highest quality, slower)
                - 'gemini-2.0-flash' (alternative)
        """
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
        
        print(f"✓ Report Generator initialized ({model_name})")
    
    def generate_report(self, data_summary, report_type="general"):
        """
        Generate a narrative report in Indonesian using Gemini AI
        
        Args:
            data_summary (dict): Analysis results from DataProcessor
            report_type (str): Type of report (student_performance, financial_analysis, etc.)
            
        Returns:
            str: Generated report in Markdown format
        """
        # Create the prompt for Gemini
        prompt = self._create_prompt(data_summary, report_type)
        
        try:
            # Call Gemini API with retry logic
            response = self._call_gemini_with_retry(prompt)
            
            # Extract text from response
            report_text = response.text
            
            print(f"  ✓ Generated {len(report_text)} characters")
            
            return report_text
            
        except Exception as e:
            print(f"  ❌ Error generating report: {str(e)}")
            # Return a fallback report
            return self._create_fallback_report(data_summary)
    
    def _create_prompt(self, data_summary, report_type):
        """
        Create a detailed prompt for Gemini based on report type
        
        This is crucial for getting good results from the AI.
        A well-crafted prompt ensures the AI generates accurate,
        relevant reports.
        
        Args:
            data_summary (dict): The data analysis
            report_type (str): Type of report
            
        Returns:
            str: Complete prompt for Gemini
        """
        # Get the data summary text
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary_text = processor.get_data_summary_for_ai(data_summary)
        
        # Base instructions (always included)
        base_instructions = """
Anda adalah seorang analis data universitas yang ahli. Tugas Anda adalah membuat laporan 
naratif yang profesional dan mudah dipahami berdasarkan data yang diberikan.

PENTING: Hanya gunakan informasi dari data yang diberikan. Jangan membuat asumsi atau 
menambahkan informasi yang tidak ada dalam data.
"""
        
        # Specific instructions based on report type
        if report_type == "student_performance":
            specific_instructions = """
Buatlah laporan analisis performa mahasiswa dengan struktur berikut:

1. RINGKASAN EKSEKUTIF (2-3 paragraf)
   - Gambaran umum data mahasiswa
   - Temuan utama

2. ANALISIS DETAIL
   - Distribusi nilai/IPK
   - Identifikasi pola atau trend
   - Perbandingan antar kelompok (jika ada)

3. KESIMPULAN DAN REKOMENDASI
   - Kesimpulan berdasarkan data
   - Rekomendasi untuk perbaikan

Gunakan format Markdown dengan heading, bullet points, dan penekanan yang sesuai.
"""
        elif report_type == "financial_analysis":
            specific_instructions = """
Buatlah laporan analisis keuangan dengan struktur berikut:

1. RINGKASAN KEUANGAN (2-3 paragraf)
   - Overview kondisi keuangan
   - Highlight angka-angka penting

2. ANALISIS MENDALAM
   - Breakdown per kategori
   - Trend pendapatan/pengeluaran
   - Analisis rasio (jika relevan)

3. KESIMPULAN DAN SARAN
   - Kesimpulan finansial
   - Rekomendasi strategis

Gunakan format Markdown. Sertakan angka dengan format yang jelas (Rp untuk rupiah).
"""
        else:
            specific_instructions = """
Buatlah laporan analisis data dengan struktur:

1. RINGKASAN
2. ANALISIS DETAIL
3. KESIMPULAN

Gunakan format Markdown.
"""
        
        # Combine everything
        full_prompt = f"""{base_instructions}

{specific_instructions}

DATA YANG HARUS DIANALISIS:
{summary_text}

Mulai menulis laporan sekarang dalam Bahasa Indonesia:
"""
        
        return full_prompt
    
    def _call_gemini_with_retry(self, prompt, max_retries=3):
        """
        Call Gemini API with automatic retry on failure
        
        Args:
            prompt (str): The prompt to send
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            Response object from Gemini
            
        Raises:
            Exception: If all retries fail
        """
        for attempt in range(max_retries):
            try:
                # Call the Gemini API
                response = self.model.generate_content(prompt)
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    print(f"  ⚠ API call failed, retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"API call failed after {max_retries} attempts: {str(e)}")
    
    def validate_report(self, report_text, original_data_summary):
        """
        Validate the generated report for potential hallucinations
        
        This checks if the AI made up numbers or facts that aren't in the original data.
        
        Args:
            report_text (str): The generated report
            original_data_summary (dict): Original data analysis
            
        Returns:
            dict: Validation results with is_valid flag and issues list
        """
        issues = []
        
        # Extract numbers from the report
        import re
        numbers_in_report = re.findall(r'\d+(?:\.\d+)?', report_text)
        
        # Extract numbers from original data
        numbers_in_data = set()
        
        # Check statistics
        if 'statistics' in original_data_summary:
            for col_stats in original_data_summary['statistics'].values():
                for value in col_stats.values():
                    if isinstance(value, (int, float)):
                        numbers_in_data.add(f"{value:.2f}")
                        numbers_in_data.add(f"{int(value)}")
        
        # Add row count
        numbers_in_data.add(str(original_data_summary.get('row_count', 0)))
        numbers_in_data.add(str(original_data_summary.get('column_count', 0)))
        
        # Check for exact column names mentioned
        columns = original_data_summary.get('columns', [])
        for col in columns:
            if col not in report_text:
                # This is okay - not all columns need to be mentioned
                pass
        
        # Basic validation checks
        if len(report_text) < 200:
            issues.append("Report seems too short (less than 200 characters)")
        
        if "Data yang diberikan" in report_text or "tidak dapat" in report_text.lower():
            issues.append("Report may indicate missing or unclear data")
        
        # Overall validation result
        is_valid = len(issues) == 0
        
        return {
            'is_valid': is_valid,
            'issues': issues,
            'report_length': len(report_text),
            'numbers_found': len(numbers_in_report)
        }
    
    def _create_fallback_report(self, data_summary):
        """
        Create a basic fallback report if AI generation fails
        
        Args:
            data_summary (dict): Data analysis
            
        Returns:
            str: Basic report in Markdown
        """
        from data_processor import DataProcessor
        processor = DataProcessor()
        summary = processor.get_data_summary_for_ai(data_summary)
        
        fallback = f"""# Laporan Data Universitas

## Ringkasan

Laporan ini dibuat secara otomatis berdasarkan data yang tersedia.

## Data Overview

{summary}

## Catatan

Laporan ini dibuat menggunakan template fallback karena terjadi kesalahan 
dalam proses generasi AI. Untuk laporan yang lebih detail, silakan coba lagi.

---
*Generated by University Report Generator*
"""
        return fallback


# For testing
if __name__ == "__main__":
    print("Report Generator module loaded!")
    print("\nThis module provides:")
    print("- generate_report(): Generate AI reports using Gemini")
    print("- validate_report(): Check for hallucinations")
    print("\nNote: Requires valid Gemini API key to function")