"""
Configuration Manager - Application configuration management
"""

import json
from pathlib import Path
from typing import Any, Dict


class ConfigManager:
    """Application configuration management"""
    
    def __init__(self, config_file_path):
        self.config_file_path = Path(config_file_path)
        self.config_data = {}
        self.default_config = {
            "window": {
                "width": 1024,
                "height": 768,
                "maximized": False
            },
            "vault": {
                "last_opened": "",
                "path": "./vault"
            },
            "preferences": {
                "theme": "default",
                "auto_save": True
            }
        }
        self.load_config()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if self.config_file_path.exists():
                with open(self.config_file_path, 'r', encoding='utf-8') as f:
                    self.config_data = json.load(f)
            else:
                # Create default config file
                self.config_data = self.default_config.copy()
                self.save_config()
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading config: {e}")
            self.config_data = self.default_config.copy()
            
    def save_config(self):
        """Save configuration to file"""
        try:
            # Ensure directory exists
            self.config_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=4)
        except IOError as e:
            print(f"Error saving config: {e}")
            
    def get_setting(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set_setting(self, key, value):
        """Update configuration value"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        # Set the value
        config[keys[-1]] = value
        
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config_data = self.default_config.copy()
        self.save_config()