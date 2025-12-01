"""
OpsPilot Configuration Management

Simple authentication with provider selection and API key management.
Supports multiple AI providers through litellm integration.
"""

import os
import yaml
from pathlib import Path
from typing import Optional, Dict, Any, Literal


class AuthConfig:
    """Simple authentication configuration."""

    def __init__(self, **kwargs: Any) -> None:
        # API Key - User provides their own API key
        self.api_key = kwargs.get("api_key")

        # Provider selection
        self.provider = kwargs.get(
            "provider", "openai"
        )  # openai, zhipu, anthropic, openrouter

        # Model selection
        self.model = kwargs.get("model")  # Will be set based on provider


class ModelConfig:
    """Model configuration for different providers."""

    def __init__(self, **kwargs: Any) -> None:
        # Available models for each provider
        # OpenRouter provides access to many models from different providers
        self.models = {
            "openai": {"plan": "gpt-4o", "build": "gpt-4o-mini"},
            "zhipu": {
                "plan": "openrouter/z-ai/glm-4.6",
                "build": "openrouter/z-ai/glm-4.6",
            },
            "anthropic": {
                "plan": "claude-sonnet-4-5",
                "build": "claude-opus-4-1",
            },
            "openrouter": {
                "plan": "openai/gpt-4o",  # GPT-4 Optimized via OpenRouter
                "build": "openai/gpt-4o-mini",  # Fast OpenAI model via OpenRouter
            },
        }


class AppConfig:
    """Complete application configuration."""

    def __init__(self, **kwargs: Any) -> None:
        self.auth = kwargs.get("auth", AuthConfig())
        self.models = kwargs.get("models", ModelConfig())

        # Application settings
        self.max_tokens = kwargs.get("max_tokens", 4000)
        self.temperature = kwargs.get("temperature", 0.7)
        self.timeout = kwargs.get("timeout", 30)

    def dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for serialization."""
        return {
            "auth": {
                "api_key": self.auth.api_key,
                "provider": self.auth.provider,
                "model": self.auth.model,
            },
            "models": {
                "models": self.models.models,
            },
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout": self.timeout,
        }


class ConfigManager:
    """Manages OpsPilot configuration loading and validation."""

    def __init__(self) -> None:
        self.config_dir = Path.home() / ".opspilot"
        self.config_file = self.config_dir / "config.yaml"
        self._config: Optional[AppConfig] = None

    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(exist_ok=True)

    def load_config(self) -> AppConfig:
        """Load configuration from file or create default."""
        if self._config:
            return self._config

        self.ensure_config_dir()

        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f)
                # Properly reconstruct nested objects
                auth_data = config_data.get("auth", {})
                auth = AuthConfig(**auth_data)
                models_data = config_data.get("models", {})
                models = ModelConfig(**models_data)
                self._config = AppConfig(
                    auth=auth,
                    models=models,
                    max_tokens=config_data.get("max_tokens", 4000),
                    temperature=config_data.get("temperature", 0.7),
                    timeout=config_data.get("timeout", 30),
                )
            except Exception as e:
                raise ValueError(f"Invalid configuration file: {e}")
        else:
            # Create default configuration
            self._config = self._create_default_config()
            self.save_config(self._config)

        return self._config

    def _create_default_config(self) -> AppConfig:
        """Create default configuration with environment variables."""
        auth_data = {}

        # Check for environment variables
        if os.getenv("OPSPILOT_API_KEY"):
            auth_data["api_key"] = os.getenv("OPSPILOT_API_KEY")
        if os.getenv("OPSPILOT_PROVIDER"):
            auth_data["provider"] = os.getenv("OPSPILOT_PROVIDER")

        if not auth_data:
            # No auth found - create empty config to trigger setup
            auth_data = {"api_key": None, "provider": "openai"}

        return AppConfig(auth=AuthConfig(**auth_data))

    def save_config(self, config: AppConfig) -> None:
        """Save configuration to file."""
        self.ensure_config_dir()

        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config.dict(), f, default_flow_style=False, indent=2)

        self._config = config

    def is_subscription_mode(self) -> bool:
        """Check if running in subscription mode."""
        # No longer used in simplified auth
        return False

    def get_litellm_config(self) -> Dict[str, Any]:
        """Get litellm configuration."""
        config = self.load_config()

        # Special handling for OpenRouter
        if config.auth.provider == "openrouter":
            return {
                "api_base": "https://openrouter.ai/api/v1",
                "timeout": config.timeout,
            }

        return {
            "timeout": config.timeout,
        }

    def get_model_for_mode(self, mode: Literal["plan", "build"]) -> str:
        """Get the appropriate model for the current mode."""
        config = self.load_config()
        provider = config.auth.provider

        return config.models.models[provider][mode]  # type: ignore[no-any-return]

    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for the configured provider."""
        config = self.load_config()

        if config.auth.provider == provider:
            return config.auth.api_key  # type: ignore[no-any-return]

        return None


# Global configuration manager instance
config_manager = ConfigManager()
