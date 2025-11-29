"""
Basic tests for OpsPilot configuration.
"""

import pytest
from opspilot.config import AuthConfig, ModelConfig, AppConfig, ConfigManager


def test_auth_config():
    """Test AuthConfig initialization."""
    auth = AuthConfig(api_key="test-key", provider="zhipu")
    assert auth.api_key == "test-key"
    assert auth.provider == "zhipu"


def test_model_config():
    """Test ModelConfig initialization."""
    models = ModelConfig()
    assert "openai" in models.models
    assert "zhipu" in models.models
    assert "anthropic" in models.models
    assert models.models["zhipu"]["plan"] == "glm-4-plus"
    assert models.models["zhipu"]["build"] == "glm-4-flash"


def test_app_config():
    """Test AppConfig initialization."""
    auth = AuthConfig(api_key="test-key", provider="zhipu")
    models = ModelConfig()
    config = AppConfig(auth=auth, models=models)
    assert config.auth.api_key == "test-key"
    assert config.auth.provider == "zhipu"


def test_config_manager():
    """Test ConfigManager basic functionality."""
    manager = ConfigManager()
    config = manager.load_config()
    assert hasattr(config, "auth")
    assert hasattr(config, "models")


def test_get_model_for_mode():
    """Test model selection for different modes."""
    manager = ConfigManager()
    # Test with zhipu provider
    manager._config = AppConfig(
        auth=AuthConfig(api_key="test", provider="zhipu"), models=ModelConfig()
    )
    plan_model = manager.get_model_for_mode("plan")
    build_model = manager.get_model_for_mode("build")
    assert plan_model == "glm-4-plus"
    assert build_model == "glm-4-flash"


def test_openrouter_support():
    """Test OpenRouter provider support."""
    manager = ConfigManager()
    # Test with openrouter provider
    manager._config = AppConfig(
        auth=AuthConfig(api_key="test", provider="openrouter"), models=ModelConfig()
    )
    plan_model = manager.get_model_for_mode("plan")
    build_model = manager.get_model_for_mode("build")
    assert plan_model == "openai/gpt-4o"
    assert build_model == "anthropic/claude-3-haiku"

    # Test litellm config for OpenRouter
    litellm_config = manager.get_litellm_config()
    assert litellm_config["api_base"] == "https://openrouter.ai/api/v1"


if __name__ == "__main__":
    pytest.main([__file__])
