#!/usr/bin/env python
"""
Configuration module for Auto-PRDGen
Handles user preferences, settings, and configuration management
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, Any, Optional
from colorama import Fore, Style

class Config:
    """Configuration manager for Auto-PRDGen"""
    
    def __init__(self):
        self.config_dir = Path.home() / ".auto-prdgen"
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history.json"
        self.default_config = {
            "ui": {
                "colors_enabled": True,
                "theme": "default",
                "quiet_mode": False,
                "progress_bars": True,
                "animation_speed": 0.3
            },
            "llm": {
                "provider": "google",
                "model": "gemini-2.5-flash-preview-05-20",
                "temperature": 0.7,
                "max_tokens": 4096
            },
            "output": {
                "format": "markdown",
                "include_metadata": True,
                "auto_backup": True
            },
            "history": {
                "max_entries": 50,
                "save_responses": True
            }
        }
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file or create default"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                # Merge with defaults to ensure all keys exist
                self._config = self._merge_configs(self.default_config, self._config)
            else:
                self._config = self.default_config.copy()
                self._save_config()
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not load config file. Using defaults. Error: {e}{Style.RESET_ALL}")
            self._config = self.default_config.copy()
    
    def _merge_configs(self, default: Dict, user: Dict) -> Dict:
        """Recursively merge user config with defaults"""
        result = default.copy()
        for key, value in user.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self):
        """Save current configuration to file"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.RED}Error saving config: {e}{Style.RESET_ALL}")
    
    def get(self, key_path: str, default=None):
        """Get configuration value using dot notation (e.g., 'ui.colors_enabled')"""
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, key_path: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key_path.split('.')
        config = self._config
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        config[keys[-1]] = value
        self._save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self._config = self.default_config.copy()
        self._save_config()
    
    def add_to_history(self, entry_type: str, data: Dict[str, Any]):
        """Add entry to command history"""
        if not self.get('history.save_responses'):
            return
        
        try:
            history = self.get_history()
            entry = {
                "timestamp": int(time.time()),
                "type": entry_type,
                "data": data
            }
            history.append(entry)
            
            # Limit history size
            max_entries = self.get('history.max_entries', 50)
            if len(history) > max_entries:
                history = history[-max_entries:]
            
            self.config_dir.mkdir(parents=True, exist_ok=True)
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"{Fore.YELLOW}Warning: Could not save to history: {e}{Style.RESET_ALL}")
    
    def get_history(self, entry_type: Optional[str] = None) -> list:
        """Get command history, optionally filtered by type"""
        try:
            if not self.history_file.exists():
                return []
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
            
            if entry_type:
                history = [entry for entry in history if entry.get('type') == entry_type]
            
            return history
        except Exception:
            return []
    
    def clear_history(self):
        """Clear command history"""
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except Exception as e:
            print(f"{Fore.RED}Error clearing history: {e}{Style.RESET_ALL}")

# Global config instance
config = Config()