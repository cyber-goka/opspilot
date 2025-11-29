"""
OpsPilot TUI Screens

Modal screens for settings, model picker, and other dialogs.
Provides configuration and session management interfaces.
"""

from typing import Optional, Dict, Any, List, Generator
from dataclasses import dataclass

# Check if Textual is available
TEXTUAL_AVAILABLE = False
try:
    from textual.screen import ModalScreen
    from textual.containers import Container, Horizontal, Vertical
    from textual.widgets import (
        Button,
        Label,
        Input,
        Select,
        TextArea,
        Static,
        Checkbox,
        ListView,
        ListItem,
    )
    from textual.binding import Binding
    from textual import events

    TEXTUAL_AVAILABLE = True
except ImportError:
    pass

# Import our modules
try:
    from ..config import config_manager, AppConfig, AuthConfig, ModelConfig
    from ..agent.memory import memory_manager
except ImportError:
    # Fallback for development
    class config_manager:  # type: ignore[no-redef]
        @staticmethod
        def load_config() -> Any:
            class MockConfig:
                auth = type(
                    "Auth",
                    (),
                    {
                        "openai_api_key": None,
                        "zhipu_api_key": None,
                        "anthropic_api_key": None,
                        "license_key": None,
                        "proxy_url": "https://api.opspilot.com/v1",
                    },
                )()
                models = type(
                    "Models",
                    (),
                    {
                        "default_provider": "zhipu",
                        "plan_model_openai": "gpt-4",
                        "plan_model_zhipu": "glm-4-plus",
                        "plan_model_anthropic": "claude-3-sonnet-20240229",
                        "build_model_openai": "gpt-3.5-turbo",
                        "build_model_zhipu": "glm-4-flash",
                        "build_model_anthropic": "claude-3-haiku-20240307",
                    },
                )()

            return MockConfig()

        @staticmethod
        def save_config(config: Any) -> None:
            pass

        @staticmethod
        def is_subscription_mode() -> bool:
            return False

    class memory_manager:  # type: ignore[no-redef]
        @staticmethod
        def list_sessions() -> List[Dict[str, Any]]:
            return [
                {
                    "id": "1",
                    "title": "Session 1",
                    "created_at": 1234567890,
                    "updated_at": 1234567890,
                    "message_count": 10,
                },
                {
                    "id": "2",
                    "title": "Session 2",
                    "created_at": 1234567890,
                    "updated_at": 1234567890,
                    "message_count": 5,
                },
            ]

        @staticmethod
        def delete_session(session_id: str) -> None:
            pass

        @staticmethod
        def load_session(session_id: str) -> bool:
            return True


if TEXTUAL_AVAILABLE:

    class SettingsScreen(ModalScreen):
        """Settings configuration screen."""

        DEFAULT_CSS = """
        SettingsScreen {
            align: center middle;
        }
        
        .settings-container {
            width: 80;
            height: 25;
            border: thick $primary;
            background: $surface;
        }
        
        .settings-title {
            text-align: center;
            text-style: bold;
            color: $primary;
            padding: 1;
        }
        
        .settings-tabs {
            height: 3;
            dock: top;
        }
        
        .settings-content {
            padding: 1;
            height: 15;
        }
        
        .settings-row {
            height: 3;
            align: left middle;
        }
        
        .settings-label {
            width: 20;
            text-align: right;
            padding-right: 1;
        }
        
        .settings-input {
            width: 40;
        }
        
        .settings-buttons {
            height: 3;
            align: bottom middle;
        }
        
        .settings-buttons Button {
            width: 12;
            margin: 0 1;
        }
        """

        BINDINGS = [
            Binding("escape", "dismiss", "Cancel"),
            Binding("ctrl+s", "save", "Save"),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.config = config_manager.load_config()
            self.current_tab = "auth"

        def compose(self) -> Any:
            with Container(classes="settings-container"):
                yield Label("⚙️  OpsPilot Settings", classes="settings-title")

                with Horizontal(classes="settings-tabs"):
                    yield Button("Authentication", id="auth-tab", variant="primary")
                    yield Button("Models", id="models-tab")
                    yield Button("Advanced", id="advanced-tab")

                with Container(classes="settings-content", id="settings-content"):
                    self._compose_auth_tab()

                with Horizontal(classes="settings-buttons"):
                    yield Button("Save", variant="success", id="save-button")
                    yield Button("Cancel", variant="error", id="cancel-button")

        def _compose_auth_tab(self) -> Generator[Any, None, None]:
            """Compose authentication settings tab."""
            content = self.query_one("#settings-content", Container)
            content.remove_children()

            with content:
                # Provider Selection
                yield Label("AI Provider", classes="settings-label")
                yield Select(
                    options=[
                        ("OpenAI", "openai"),
                        ("Zhipu AI", "zhipu"),
                        ("Anthropic", "anthropic"),
                        ("OpenRouter", "openrouter"),
                    ],
                    value=self.config.auth.provider,
                    id="provider",
                    classes="settings-input",
                )

                # API Key
                yield Label("API Key", classes="settings-label")
                yield Input(
                    value=self.config.auth.api_key or "",
                    placeholder="Your API Key",
                    id="api-key",
                    classes="settings-input",
                    password=True,
                )

                # API Key
                yield Label("API Key", classes="settings-label")
                yield Input(
                    value=self.config.auth.api_key or "",
                    placeholder="Your API Key",
                    id="api-key",
                    classes="settings-input",
                    password=True,
                )

                yield Label("", classes="settings-label")
                yield Input(
                    value=self.config.auth.zhipu_api_key or "",
                    placeholder="Zhipu AI API Key",
                    id="zhipu-key",
                    classes="settings-input",
                    password=True,
                )

                yield Label("", classes="settings-label")
                yield Input(
                    value=self.config.auth.anthropic_api_key or "",
                    placeholder="Anthropic API Key",
                    id="anthropic-key",
                    classes="settings-input",
                    password=True,
                )

                # Subscription Mode
                yield Label("Subscription Mode", classes="settings-label")
                yield Input(
                    value=self.config.auth.license_key or "",
                    placeholder="License Key",
                    id="license-key",
                    classes="settings-input",
                    password=True,
                )

                yield Label("", classes="settings-label")
                yield Input(
                    value=self.config.auth.proxy_url,
                    placeholder="Proxy URL",
                    id="proxy-url",
                    classes="settings-input",
                )

        def _compose_models_tab(self) -> Generator[Any, None, None]:
            """Compose models settings tab."""
            content = self.query_one("#settings-content", Container)
            content.remove_children()

            with content:
                yield Label("Default Provider", classes="settings-label")
                yield Select(
                    options=[
                        ("OpenAI", "openai"),
                        ("Zhipu AI", "zhipu"),
                        ("Anthropic", "anthropic"),
                    ],
                    value=self.config.models.default_provider,
                    id="default-provider",
                    classes="settings-input",
                )

                yield Label("Plan Mode Models", classes="settings-label")
                yield Input(
                    value=self.config.models.plan_model_openai,
                    placeholder="OpenAI Plan Model",
                    id="plan-openai",
                    classes="settings-input",
                )

                yield Label("", classes="settings-label")
                yield Input(
                    value=self.config.models.plan_model_zhipu,
                    placeholder="Zhipu Plan Model",
                    id="plan-zhipu",
                    classes="settings-input",
                )

                yield Label("", classes="settings-label")
                yield Input(
                    value=self.config.models.plan_model_anthropic,
                    placeholder="Anthropic Plan Model",
                    id="plan-anthropic",
                    classes="settings-input",
                )

        def _compose_advanced_tab(self) -> Generator[Any, None, None]:
            """Compose advanced settings tab."""
            content = self.query_one("#settings-content", Container)
            content.remove_children()

            with content:
                yield Label("Max Tokens", classes="settings-label")
                yield Input(
                    value=str(self.config.max_tokens),
                    placeholder="Max Tokens",
                    id="max-tokens",
                    classes="settings-input",
                )

                yield Label("Temperature", classes="settings-label")
                yield Input(
                    value=str(self.config.temperature),
                    placeholder="Temperature",
                    id="temperature",
                    classes="settings-input",
                )

                yield Label("Timeout (seconds)", classes="settings-label")
                yield Input(
                    value=str(self.config.timeout),
                    placeholder="Timeout",
                    id="timeout",
                    classes="settings-input",
                )

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press events."""
            if event.button.id == "save-button":
                self.action_save()
            elif event.button.id == "cancel-button":
                self.dismiss()
            elif event.button.id and event.button.id.endswith("-tab"):
                self._switch_tab(event.button.id.replace("-tab", ""))

        def _switch_tab(self, tab_name: str) -> None:
            """Switch settings tab."""
            self.current_tab = tab_name

            # Update button styles
            for button in self.query("Button"):
                if button.id and button.id.endswith("-tab"):
                    if button.id == f"{tab_name}-tab":
                        button.variant = "primary"  # type: ignore[attr-defined]
                    else:
                        button.variant = "default"  # type: ignore[attr-defined]

            # Update content
            if tab_name == "auth":
                self._compose_auth_tab()
            elif tab_name == "models":
                self._compose_models_tab()
            elif tab_name == "advanced":
                self._compose_advanced_tab()

        def action_save(self) -> None:
            """Save settings."""
            try:
                # Update config with form values
                self.config.auth.provider = self.query_one("#provider", Select).value
                self.config.auth.api_key = self.query_one("#api-key", Input).value

                self.config.max_tokens = int(
                    self.query_one("#max-tokens", Input).value or "4000"
                )
                self.config.temperature = float(
                    self.query_one("#temperature", Input).value or "0.7"
                )
                self.config.timeout = int(
                    self.query_one("#timeout", Input).value or "30"
                )

                # Save config
                config_manager.save_config(self.config)

                self.dismiss()

            except Exception as e:
                # Show error message
                error_label = Label(f"Error saving settings: {str(e)}", classes="error")
                self.mount(error_label)

    class SessionManagerScreen(ModalScreen):
        """Session management screen."""

        DEFAULT_CSS = """
        SessionManagerScreen {
            align: center middle;
        }
        
        .session-container {
            width: 80;
            height: 20;
            border: thick $primary;
            background: $surface;
        }
        
        .session-title {
            text-align: center;
            text-style: bold;
            color: $primary;
            padding: 1;
        }
        
        .session-list {
            height: 12;
            border: solid $primary;
            margin: 1;
        }
        
        .session-buttons {
            height: 3;
            align: bottom middle;
        }
        
        .session-buttons Button {
            width: 12;
            margin: 0 1;
        }
        """

        BINDINGS = [
            Binding("escape", "dismiss", "Close"),
            Binding("delete", "delete_session", "Delete Session"),
        ]

        def compose(self) -> Any:
            with Container(classes="session-container"):
                yield Label("📚 Session Manager", classes="session-title")

                with Container(classes="session-list"):
                    self._compose_session_list()

                with Horizontal(classes="session-buttons"):
                    yield Button("New Session", variant="success", id="new-session")
                    yield Button("Load Session", variant="primary", id="load-session")
                    yield Button("Delete Session", variant="error", id="delete-session")
                    yield Button("Close", variant="default", id="close")

        def _compose_session_list(self) -> Generator[Any, None, None]:
            """Compose session list."""
            sessions = memory_manager.list_sessions()

            for session in sessions:
                date_str = f"{session['updated_at']:.0f}"  # Simple timestamp display
                item = ListItem(
                    Label(
                        f"{session['title']} ({session['message_count']} messages) - {date_str}"
                    )
                )
                item.session_id = session["id"]  # type: ignore[attr-defined]
                yield item

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press events."""
            if event.button.id == "close":
                self.dismiss()
            elif event.button.id == "new-session":
                memory_manager.create_session("New Session")
                self._compose_session_list()
            elif event.button.id == "load-session":
                # Load selected session
                selected = self.query_one(ListView).highlighted_child
                if selected and hasattr(selected, "session_id"):
                    memory_manager.load_session(selected.session_id)
                    self.dismiss()
            elif event.button.id == "delete-session":
                self.action_delete_session()

        def action_delete_session(self) -> None:
            """Delete selected session."""
            selected = self.query_one(ListView).highlighted_child
            if selected and hasattr(selected, "session_id"):
                memory_manager.delete_session(selected.session_id)
                self._compose_session_list()

    class ModelPickerScreen(ModalScreen):
        """Model picker screen."""

        DEFAULT_CSS = """
        ModelPickerScreen {
            align: center middle;
        }
        
        .model-container {
            width: 60;
            height: 15;
            border: thick $primary;
            background: $surface;
        }
        
        .model-title {
            text-align: center;
            text-style: bold;
            color: $primary;
            padding: 1;
        }
        
        .model-options {
            height: 8;
            margin: 1;
        }
        
        .model-buttons {
            height: 3;
            align: bottom middle;
        }
        
        .model-buttons Button {
            width: 12;
            margin: 0 1;
        }
        """

        def __init__(self, current_mode: str = "plan") -> None:
            super().__init__()
            self.current_mode = current_mode
            self.selected_model: Optional[str] = None

        def compose(self) -> Any:
            with Container(classes="model-container"):
                yield Label(
                    f"🤖 Select {self.current_mode.upper()} Model",
                    classes="model-title",
                )

                with Container(classes="model-options"):
                    models = self._get_available_models()
                    for model in models:
                        yield Button(model, id=f"model-{model}")

                with Horizontal(classes="model-buttons"):
                    yield Button("Select", variant="success", id="select")
                    yield Button("Cancel", variant="error", id="cancel")

        def _get_available_models(self) -> List[str]:
            """Get available models based on configuration."""
            config = config_manager.load_config()

            if self.current_mode == "plan":
                return [
                    config.models.plan_model_openai,
                    config.models.plan_model_zhipu,
                    config.models.plan_model_anthropic,
                ]
            else:
                return [
                    config.models.build_model_openai,
                    config.models.build_model_zhipu,
                    config.models.build_model_anthropic,
                ]

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press events."""
            if event.button.id == "select":
                if self.selected_model:
                    self.dismiss(self.selected_model)
            elif event.button.id == "cancel":
                self.dismiss()
            elif event.button.id and event.button.id.startswith("model-"):
                self.selected_model = event.button.id.replace("model-", "")


# Fallback classes when Textual is not available
class SettingsScreen:  # type: ignore[no-redef]
    """Fallback settings screen."""

    def __init__(self) -> None:
        print("Settings screen requires Textual to be installed.")

    def __call__(self) -> "SettingsScreen":
        return self


class SessionManagerScreen:  # type: ignore[no-redef]
    """Fallback session manager screen."""

    def __init__(self) -> None:
        print("Session manager requires Textual to be installed.")

    def __call__(self) -> "SessionManagerScreen":
        return self


class ModelPickerScreen:  # type: ignore[no-redef]
    """Fallback model picker screen."""

    def __init__(self, current_mode: str = "plan") -> None:
        print("Model picker requires Textual to be installed.")

    def __call__(self) -> "ModelPickerScreen":
        return self
