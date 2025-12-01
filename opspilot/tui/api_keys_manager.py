"""API Keys Management for OpsPilot TUI"""

import json
from pathlib import Path
from typing import Dict

from opspilot.tui.locations import config_directory


def api_keys_file() -> Path:
    """Return the path to the API keys file."""
    return config_directory() / "api_keys.json"


def load_api_keys() -> Dict[str, str]:
    """Load API keys from the config file.

    Returns a dictionary mapping provider names to API keys.
    """
    keys_file = api_keys_file()

    if not keys_file.exists():
        return {}

    try:
        with open(keys_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_api_keys(api_keys: Dict[str, str]) -> None:
    """Save API keys to the config file.

    Args:
        api_keys: Dictionary mapping provider names to API keys
    """
    keys_file = api_keys_file()

    # Ensure the directory exists
    keys_file.parent.mkdir(parents=True, exist_ok=True)

    # Filter out empty keys
    filtered_keys = {k: v for k, v in api_keys.items() if v and v.strip()}

    try:
        with open(keys_file, "w", encoding="utf-8") as f:
            json.dump(filtered_keys, f, indent=2)

        # Set restrictive permissions (readable/writable by owner only)
        keys_file.chmod(0o600)
    except IOError as e:
        raise RuntimeError(f"Failed to save API keys: {e}")


def update_api_key(provider: str, api_key: str) -> None:
    """Update a single API key for a provider.

    Args:
        provider: The provider name (e.g., 'OpenAI', 'Anthropic')
        api_key: The API key to store
    """
    keys = load_api_keys()

    if api_key and api_key.strip():
        keys[provider] = api_key
    elif provider in keys:
        # Remove empty keys
        del keys[provider]

    save_api_keys(keys)
