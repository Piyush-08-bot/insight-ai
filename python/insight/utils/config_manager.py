"""
Global Configuration Manager for INsight.
Handles API key storage in the user's home directory (~/.insight/config.json).
"""

import os
import json
from pathlib import Path
from typing import Dict, Optional


class ConfigManager:
    """Manages the global configuration file for INsight."""

    def __init__(self):
        self.config_dir = Path.home() / ".insight"
        self.config_file = self.config_dir / "config.json"
        self._ensure_config_exists()

    def _ensure_config_exists(self):
        """Create the config directory and file if they don't exist."""
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True, exist_ok=True)
            # Ensure permissions are restricted for security
            try:
                os.chmod(self.config_dir, 0o700)
            except Exception: pass

        if not self.config_file.exists():
            with open(self.config_file, 'w') as f:
                json.dump({"api_keys": {}}, f)
            try:
                os.chmod(self.config_file, 0o600)
            except Exception: pass

    def load(self) -> Dict:
        """Load the full configuration."""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"api_keys": {}}

    def save(self, config: Dict):
        """Save the configuration to disk."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def set_key(self, provider: str, api_key: str):
        """Save an API key for a specific provider."""
        config = self.load()
        if "api_keys" not in config:
            config["api_keys"] = {}
        config["api_keys"][provider.lower()] = api_key
        self.save(config)

    def get_key(self, provider: str) -> Optional[str]:
        """Retrieve an API key for a specific provider."""
        config = self.load()
        return config.get("api_keys", {}).get(provider.lower())

    def list_keys(self) -> Dict[str, str]:
        """List all providers that have a saved API key (with masked values)."""
        config = self.load()
        keys = config.get("api_keys", {})
        masked = {}
        for provider, val in keys.items():
            val_str = str(val)
            if len(val_str) > 8:
                masked[provider] = f"{val_str[:4]}...{val_str[-4:]}"
            else:
                masked[provider] = "****"
        return masked

    def remove_key(self, provider: str):
        """Remove a specific API key."""
        config = self.load()
        if provider.lower() in config.get("api_keys", {}):
            del config["api_keys"][provider.lower()]
            self.save(config)

    def clear(self):
        """Wipe all keys."""
        self.save({"api_keys": {}})
