"""
Configuration Module
Handles API keys, data ingestion configuration, and application settings
"""

import os
from pathlib import Path


class Config:
    """
    Configuration manager for the University Report Generator.

    Responsibilities:
    - Load API keys securely
    - Manage ingestion sources (local vs API)
    - Provide settings for report generation
    """

    def __init__(self):
        # Load Gemini API key from environment or .env
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self._load_from_env_file()

        # === Base Application Settings ===
        self.settings = {
            "max_retries": 3,
            "timeout": 30,
            "language": "id",
            "temperature": 0.7,
            "model_name": "gemini-2.5-flash",
        }

        # === Data Ingestion Configuration ===
        self.API_BASE_URL = os.getenv("FAKE_API_BASE_URL", "http://127.0.0.1:8000")

        # Local dataset folders
        self.LOCAL_DATA_PATHS = {
            "students": "data/students",
            "finance": "data/finance",
            "akreditasi": "data/akreditasi",
        }

        # API endpoints for dataset listing
        # These return JSON describing available CSVs
        self.API_ENDPOINTS = {
            "students": f"{self.API_BASE_URL}/data/students?format=json",
            "finance": f"{self.API_BASE_URL}/data/finance?format=json",
            "akreditasi": f"{self.API_BASE_URL}/data/akreditasi?format=json",
        }

        # Aggregation mode: local | api
        self.AGGREGATION_MODE = os.getenv("AGGREGATION_MODE", "local").lower()

        # Cache directory for downloaded CSVs
        self.CACHE_DIR = Path("data")

        print(f"🔧 Aggregation mode set to: {self.AGGREGATION_MODE}")

    # ----------------------------------------------------------------------
    # Internal methods
    # ----------------------------------------------------------------------

    def _load_from_env_file(self):
        """Load API key from .env file (fallback)"""
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "=" in line:
                            key, value = line.split("=", 1)
                            if key.strip() == "GEMINI_API_KEY":
                                self.api_key = value.strip()
                                break

    # ----------------------------------------------------------------------
    # Public methods
    # ----------------------------------------------------------------------

    def get_api_key(self):
        """Return Gemini API key"""
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found! Please set GEMINI_API_KEY in your environment or .env file."
            )
        return self.api_key

    def get_ingestion_sources(self):
        """
        Determine where to load CSV data from (local vs API).

        In API mode:
            - Fetch /data/{dataset}?format=json first
            - Extract actual download URLs (e.g. /download/students/file.csv)
            - Prepend base URL

        In Local mode:
            - Return paths to CSVs in local data folders
        """
        if self.AGGREGATION_MODE == "api":
            print("🌐 Using API-based data ingestion")

            import requests
            sources = []
            for dataset, endpoint in self.API_ENDPOINTS.items():
                try:
                    resp = requests.get(endpoint, timeout=10)
                    resp.raise_for_status()
                    json_data = resp.json()

                    for item in json_data:
                        url = f"{self.API_BASE_URL}{item['url']}"
                        sources.append(url)
                except Exception as e:
                    print(f"⚠ Failed to fetch dataset '{dataset}' from API: {e}")

            return sources

        else:
            print("📁 Using local CSV-based data ingestion")

            sources = []
            for folder in self.LOCAL_DATA_PATHS.values():
                folder_path = Path(folder)
                if folder_path.exists() and folder_path.is_dir():
                    csv_files = sorted(folder_path.glob("*.csv"))
                    sources.extend([str(p) for p in csv_files])
                else:
                    print(f"⚠ Folder not found: {folder_path}")

            return sources

    def get_setting(self, key, default=None):
        """Retrieve a config setting"""
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        """Update an app setting"""
        self.settings[key] = value


# ----------------------------------------------------------------------
# Debug usage
# ----------------------------------------------------------------------
if __name__ == "__main__":
    config = Config()
    print("\n🔍 Config Test Output:")
    print(f"API Key Loaded: {'Yes' if config.api_key else 'No'}")
    print(f"Mode: {config.AGGREGATION_MODE}")
    print(f"Ingestion Sources:")
    for src in config.get_ingestion_sources():
        print(f" - {src}")
