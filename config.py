"""
Configuration Module
Handles API keys and application settings

This module manages sensitive information like API keys
and application-wide settings
"""

import os
from pathlib import Path


class Config:
    """
    Configuration manager for the application
    
    Responsibilities:
    - Load API keys securely
    - Manage application settings
    - Provide easy access to configuration values
    """
    
    def __init__(self):
        """Initialize configuration by loading environment variables"""
        # Load API key from environment variable (secure method)
        self.api_key = os.getenv('GEMINI_API_KEY')
        
        # If not in environment, try to load from .env file
        if not self.api_key:
            self._load_from_env_file()
        
        # Application settings
        self.settings = {
            'max_retries': 3,  # How many times to retry API calls
            'timeout': 30,  # API timeout in seconds
            'language': 'id',  # Indonesian language code
            'temperature': 0.7,  # AI creativity (0.0 = focused, 1.0 = creative)
            'model_name': 'gemini-2.5-flash',  # Latest Gemini model (Oct 2024)
            # Options: 'gemini-2.5-flash' (best), 'gemini-2.5-pro' (highest quality)
        }
    
    def _load_from_env_file(self):
        """
        Load API key from .env file
        This is a fallback if environment variable is not set
        """
        env_file = Path('.env')
        
        if env_file.exists():
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            if key.strip() == 'GEMINI_API_KEY':
                                self.api_key = value.strip()
                                break
    
    def get_api_key(self):
        """
        Get the Gemini API key
        
        Returns:
            str: API key
            
        Raises:
            ValueError: If API key is not configured
        """
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found!\n"
                "Please set it in one of these ways:\n"
                "1. Create a .env file with: GEMINI_API_KEY=your_key_here\n"
                "2. Set environment variable: set GEMINI_API_KEY=your_key_here"
            )
        return self.api_key
    
    def get_setting(self, key, default=None):
        """
        Get a configuration setting
        
        Args:
            key (str): Setting name
            default: Default value if setting doesn't exist
            
        Returns:
            Setting value or default
        """
        return self.settings.get(key, default)
    
    def update_setting(self, key, value):
        """
        Update a configuration setting
        
        Args:
            key (str): Setting name
            value: New value
        """
        self.settings[key] = value


# For easy testing
if __name__ == "__main__":
    config = Config()
    print("Configuration loaded successfully!")
    print(f"API Key configured: {'Yes' if config.api_key else 'No'}")
    print(f"Language: {config.get_setting('language')}")
    print(f"Temperature: {config.get_setting('temperature')}")