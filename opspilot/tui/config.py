import os
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, SecretStr


class OpsPilotChatModel(BaseModel):
    name: str
    """The name of the model e.g. `gpt-3.5-turbo`.
    This must match the name of the model specified by the provider.
    """
    id: str | None = None
    """If you have multiple versions of the same model (e.g. a personal
    OpenAI gpt-3.5 and a work OpenAI gpt-3.5 with different API keys/org keys),
    you need to be able to refer to them. For example, when setting the `default_model`
    key in the config, if you write `gpt-3.5`, there's no way to know whether you
    mean your work or your personal `gpt-3.5`. That's where `id` comes in."""
    display_name: str | None = None
    """The display name of the model in the UI."""
    provider: str | None = None
    """The provider of the model, e.g. openai, anthropic, etc"""
    api_key: SecretStr | None = None
    """If set, this will be used in place of the environment variable that
    would otherwise be used for this model (instead of OPENAI_API_KEY,
    ANTHROPIC_API_KEY, etc.)."""
    api_base: AnyHttpUrl | None = None
    """If set, this will be used as the base URL for making API calls.
    This can be useful if you're hosting models on a LocalAI server, for
    example."""
    organization: str | None = None
    """Some providers, such as OpenAI, allow you to specify an organization.
    In the case of """
    description: str | None = Field(default=None)
    """A description of the model which may appear inside the OpsPilot UI."""
    product: str | None = Field(default=None)
    """For example `ChatGPT`, `Claude`, `Gemini`, etc."""
    temperature: float = Field(default=1.0)
    """The temperature to use. Low temperature means the same prompt is likely
    to produce similar results. High temperature means a flatter distribution
    when predicting the next token, and so the next token will be more random.
    Setting a very high temperature will likely produce junk output."""
    max_retries: int = Field(default=0)
    """The number of times to retry a request after it fails before giving up."""

    @property
    def lookup_key(self) -> str:
        return self.id or self.name


def get_builtin_openai_models() -> list[OpsPilotChatModel]:
    return [
        OpsPilotChatModel(
            id="opspilot-gpt-4o",
            name="gpt-4o",
            display_name="GPT-4o",
            provider="OpenAI",
            product="ChatGPT",
            description="Most advanced multimodal flagship model.",
            temperature=0.7,
        ),
        OpsPilotChatModel(
            id="opspilot-gpt-4o-mini",
            name="gpt-4o-mini",
            display_name="GPT-4o Mini",
            provider="OpenAI",
            product="ChatGPT",
            description="Fast and affordable small model.",
            temperature=0.7,
        ),
        OpsPilotChatModel(
            id="opspilot-o1-preview",
            name="o1-preview",
            display_name="o1 Preview",
            provider="OpenAI",
            product="ChatGPT",
            description="Advanced reasoning model.",
            temperature=1.0,
        ),
        OpsPilotChatModel(
            id="opspilot-o1-mini",
            name="o1-mini",
            display_name="o1 Mini",
            provider="OpenAI",
            product="ChatGPT",
            description="Fast reasoning for coding.",
            temperature=1.0,
        ),
    ]


def get_builtin_anthropic_models() -> list[OpsPilotChatModel]:
    return [
        OpsPilotChatModel(
            id="opspilot-claude-sonnet-4-5",
            name="claude-sonnet-4-5",
            display_name="Claude Sonnet 4.5",
            provider="Anthropic",
            product="Claude 4",
            description="Latest Sonnet with advanced reasoning and coding.",
        ),
        OpsPilotChatModel(
            id="opspilot-claude-opus-4-5",
            name="claude-opus-4-5",
            display_name="Claude Opus 4.5",
            provider="Anthropic",
            product="Claude 4",
            description="Most powerful Claude model for complex tasks.",
        ),
        OpsPilotChatModel(
            id="opspilot-claude-opus-4-1",
            name="claude-opus-4-1",
            display_name="Claude Opus 4.1",
            provider="Anthropic",
            product="Claude 4",
            description="High-performance model for demanding workloads.",
        ),
    ]


def get_builtin_google_models() -> list[OpsPilotChatModel]:
    return [
        OpsPilotChatModel(
            id="opspilot-gemini-2.5-pro",
            name="gemini/gemini-2.5-pro",
            display_name="Gemini 2.5 Pro",
            provider="Google",
            product="Gemini",
            description="Most reliable reasoning engine.",
        ),
        OpsPilotChatModel(
            id="opspilot-gemini-2.5-flash",
            name="gemini/gemini-2.5-flash",
            display_name="Gemini 2.5 Flash",
            provider="Google",
            product="Gemini",
            description="Fast with improved tool use.",
        ),
        OpsPilotChatModel(
            id="opspilot-gemini-1.5-pro",
            name="gemini/gemini-1.5-pro",
            display_name="Gemini 1.5 Pro",
            provider="Google",
            product="Gemini",
            description="Long context up to 2M tokens.",
        ),
    ]


def get_builtin_deepseek_models() -> list[OpsPilotChatModel]:
    return [
        OpsPilotChatModel(
            id="opspilot-deepseek-v3",
            name="deepseek/deepseek-chat",
            display_name="DeepSeek V3",
            provider="DeepSeek",
            product="DeepSeek",
            description="671B MoE model with strong coding (Dec 2024).",
            temperature=0.7,
        ),
        OpsPilotChatModel(
            id="opspilot-deepseek-reasoner",
            name="deepseek/deepseek-reasoner",
            display_name="DeepSeek Reasoner",
            provider="DeepSeek",
            product="DeepSeek",
            description="Enhanced reasoning model for complex problems.",
            temperature=0.7,
        ),
    ]


def get_builtin_zhipu_models() -> list[OpsPilotChatModel]:
    return [
        OpsPilotChatModel(
            id="opspilot-glm-4.6",
            name="openrouter/z-ai/glm-4.6",
            display_name="GLM-4.6",
            provider="Zhipu AI",
            product="GLM",
            description="Latest GLM model via OpenRouter.",
            temperature=0.7,
        ),
    ]


def get_builtin_models() -> list[OpsPilotChatModel]:
    return (
        get_builtin_openai_models()
        + get_builtin_anthropic_models()
        + get_builtin_google_models()
        + get_builtin_deepseek_models()
        + get_builtin_zhipu_models()
    )


class LaunchConfig(BaseModel):
    """The config of the application at launch.

    Values may be sourced via command line options, env vars, config files.
    """

    model_config = ConfigDict(frozen=True)

    default_model: str = Field(default="opspilot-gpt-4o")
    """The ID or name of the default model."""
    system_prompt: str = Field(
        default=os.getenv(
            "OPSPILOT_SYSTEM_PROMPT",
            "You are OpsPilot, an expert DevOps/SRE engineer assistant. You specialize in infrastructure automation, cloud platforms, container orchestration, CI/CD pipelines, monitoring, security, and incident response. You provide practical, production-ready solutions with clear explanations and best practices.",
        )
    )
    message_code_theme: str = Field(default="monokai")
    """The default Pygments syntax highlighting theme to be used in chatboxes."""
    models: list[OpsPilotChatModel] = Field(default_factory=list)
    builtin_models: list[OpsPilotChatModel] = Field(
        default_factory=get_builtin_models, init=False
    )
    theme: str = Field(default="nebula")
    api_keys: dict[str, str] = Field(default_factory=dict)
    """API keys per provider. Keys: provider name (e.g., 'OpenAI', 'Anthropic'), Values: API key"""

    def __init__(self, **data):
        """Initialize LaunchConfig and load API keys from file if not provided."""
        # If api_keys not provided, load from file
        if "api_keys" not in data or not data["api_keys"]:
            from opspilot.tui.api_keys_manager import load_api_keys

            data["api_keys"] = load_api_keys()
        super().__init__(**data)

    @property
    def all_models(self) -> list[OpsPilotChatModel]:
        return self.models + self.builtin_models

    @property
    def default_model_object(self) -> OpsPilotChatModel:
        from opspilot.tui.models import get_model

        return get_model(self.default_model, self)

    def get_api_key_for_provider(self, provider: str) -> str | None:
        """Get API key for a provider, checking config first then environment variables."""
        # Check config first
        if provider in self.api_keys:
            return self.api_keys[provider]

        # Fall back to environment variables
        env_var_map = {
            "OpenAI": "OPENAI_API_KEY",
            "Anthropic": "ANTHROPIC_API_KEY",
            "Google": "GOOGLE_API_KEY",
            "DeepSeek": "DEEPSEEK_API_KEY",
            "Zhipu AI": "ZHIPUAI_API_KEY",
            "OpenRouter": "OPENROUTER_API_KEY",
        }

        env_var = env_var_map.get(provider)
        if env_var:
            return os.getenv(env_var)

        return None

    @classmethod
    def get_current(cls) -> "LaunchConfig":
        """Get the current launch config with API keys loaded from file."""
        from opspilot.tui.api_keys_manager import load_api_keys

        return cls(api_keys=load_api_keys())
