"""
Configuration Module
Handles API keys, API endpoints, and application settings
"""

import os
from pathlib import Path


class Config:
    """
    Configuration manager for the application

    Responsibilities:
    - Load API keys securely
    - Manage application and data ingestion settings
    - Provide easy access to configuration values
    """

    def __init__(self):
        """Initialize configuration by loading environment variables"""
        # Load API key from environment variable or .env file
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self._load_from_env_file()

        # Base application settings
        self.settings = {
            "max_retries": 3,
            "timeout": 30,
            "language": "id",
            "temperature": 0.7,
            "model_name": "gemini-2.5-flash",
        }

        # ==============================
        # DATA INGESTION CONFIGURATION
        # ==============================

        # Base URL for local fake API (FastAPI)
        self.API_BASE_URL = os.getenv("FAKE_API_BASE_URL", "http://127.0.0.1:8000")

        # Local fallback dataset folders
        self.LOCAL_DATA_PATHS = {
            "student": "data/students",
            "finance": "data/finance",
            "akreditasi": "data/akreditasi/sample_akreditasi.csv",
        }

        # API endpoints for fetching CSVs
        self.API_ENDPOINTS = {
            "student": f"{self.API_BASE_URL}/data/student",
            "finance": f"{self.API_BASE_URL}/data/finance",
            "akreditasi": f"{self.API_BASE_URL}/data/akreditasi",
        }

        # Aggregation & report settings
        # Default to local if not explicitly overridden
        self.AGGREGATION_MODE = os.getenv("AGGREGATION_MODE", "local").lower()

        # Cache directory
        self.CACHE_DIR = Path("data")

        print(f"🔧 Aggregation mode set to: {self.AGGREGATION_MODE}")

    # ------------------------------------------------------
    # Internal helper methods
    # ------------------------------------------------------

    def _load_from_env_file(self):
        """Load API key from .env file"""
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

    # ------------------------------------------------------
    # Public methods
    # ------------------------------------------------------

    def get_api_key(self):
        """Return Gemini API key or raise error if not set"""
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found! Please configure it in .env or as environment variable."
            )
        return self.api_key

    def get_ingestion_sources(self):
        """
        Get a list of CSV sources (URLs or local paths) based on aggregation mode.

        Returns:
            list[str]: List of CSV URLs or file paths
        """
        if self.AGGREGATION_MODE == "api":
            print("🌐 Using API-based data ingestion")
            return list(self.API_ENDPOINTS.values())
        else:
            print("📁 Using local CSV-based data ingestion")
            sources = []
            for path in self.LOCAL_DATA_PATHS.values():
                path_obj = Path(path)
                if path_obj.is_dir():
                    # Load all CSVs from folder
                    csv_files = sorted(path_obj.glob("*.csv"))
                    sources.extend([str(p) for p in csv_files])
                elif path_obj.exists():
                    sources.append(str(path_obj))
                else:
                    print(f"⚠ Warning: Path not found: {path_obj}")
            return sources

    def get_setting(self, key, default=None):
        """Get an app setting"""
        return self.settings.get(key, default)

    def update_setting(self, key, value):
        """Update an app setting"""
        self.settings[key] = value


# Example usage for testing
if __name__ == "__main__":
    config = Config()
    print("\nConfiguration loaded successfully!")
    print(f"API Key configured: {'Yes' if config.api_key else 'No'}")
    print(f"Aggregation mode: {config.AGGREGATION_MODE}")
    print(f"Using sources: {config.get_ingestion_sources()}")
