from __future__ import annotations
from typing import TYPE_CHECKING, cast


from rich.markup import escape
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Footer, RadioSet, RadioButton, Static, Input, Label

from opspilot.tui.config import OpsPilotChatModel
from opspilot.tui.locations import config_file, theme_directory
from opspilot.tui.runtime_config import RuntimeConfig
from opspilot.tui.database.database import sqlite_file_name
from opspilot.tui.api_keys_manager import save_api_keys

if TYPE_CHECKING:
    from opspilot.tui.app import OpsPilot


class ModelRadioButton(RadioButton):
    def __init__(
        self,
        model: OpsPilotChatModel,
        label: str | Text = "",
        value: bool = False,
        button_first: bool = True,
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            label,
            value,
            button_first,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self.model = model


class OptionsModal(ModalScreen[RuntimeConfig]):
    BINDINGS = [
        Binding("q", "app.quit", "Quit", show=False),
        Binding("escape", "app.pop_screen", "Close options", key_display="esc"),
    ]

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.opspilot = cast("OpsPilot", self.app)
        self.runtime_config = self.opspilot.runtime_config

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="form-scrollable") as vs:
            vs.border_title = "Session Options"
            vs.can_focus = False
            with RadioSet(id="available-models") as models_rs:
                selected_model = self.runtime_config.selected_model
                models_rs.border_title = "Available Models"
                for model in self.opspilot.launch_config.all_models:
                    label = f"{escape(model.display_name or model.name)}"
                    provider = model.provider
                    if provider:
                        label += f" [i]by[/] {provider}"

                    ids_defined = selected_model.id and model.id
                    same_id = ids_defined and selected_model.id == model.id
                    same_name = selected_model.name == model.name
                    is_selected = same_id or same_name
                    yield ModelRadioButton(
                        model=model,
                        value=is_selected,
                        label=label,
                    )

            with Vertical(id="api-keys-section"):
                yield Label("[b]API Keys[/b] [dim](optional - falls back to env vars)[/]")
                yield Label("[dim]Get keys at:[/]")
                yield Label("  • [@click='app.open_link(\"https://platform.openai.com/api-keys\")'][u]OpenAI[/][/] | [@click='app.open_link(\"https://console.anthropic.com/settings/keys\")'][u]Anthropic[/][/] | [@click='app.open_link(\"https://aistudio.google.com/app/apikey\")'][u]Google[/][/]")
                yield Label("  • [@click='app.open_link(\"https://platform.deepseek.com/api_keys\")'][u]DeepSeek[/][/] | [@click='app.open_link(\"https://openrouter.ai/keys\")'][u]OpenRouter[/][/]")
                yield Label("")

                # Get existing API keys
                api_keys = self.opspilot.launch_config.api_keys

                yield Label("[dim]OpenAI[/]", classes="api-key-label")
                yield Input(
                    placeholder="sk-...",
                    value=api_keys.get("OpenAI", ""),
                    password=True,
                    id="openai-api-key",
                    classes="api-key-input"
                )

                yield Label("[dim]Anthropic[/]", classes="api-key-label")
                yield Input(
                    placeholder="sk-ant-...",
                    value=api_keys.get("Anthropic", ""),
                    password=True,
                    id="anthropic-api-key",
                    classes="api-key-input"
                )

                yield Label("[dim]Google[/]", classes="api-key-label")
                yield Input(
                    placeholder="AI...",
                    value=api_keys.get("Google", ""),
                    password=True,
                    id="google-api-key",
                    classes="api-key-input"
                )

                yield Label("[dim]DeepSeek[/]", classes="api-key-label")
                yield Input(
                    placeholder="sk-...",
                    value=api_keys.get("DeepSeek", ""),
                    password=True,
                    id="deepseek-api-key",
                    classes="api-key-input"
                )

                yield Label("[dim]OpenRouter[/]", classes="api-key-label")
                yield Input(
                    placeholder="sk-or-v1-...",
                    value=api_keys.get("OpenRouter", ""),
                    password=True,
                    id="openrouter-api-key",
                    classes="api-key-input"
                )

        yield Footer()

    def on_mount(self) -> None:
        selected_model_rs = self.query_one("#available-models", RadioSet)
        self.apply_overridden_subtitles(selected_model_rs)

    @on(RadioSet.Changed)
    def update_state(self, event: RadioSet.Changed) -> None:
        selected_model_rs = self.query_one("#available-models", RadioSet)
        if selected_model_rs.pressed_button is None:
            selected_model_rs._selected = 0
            assert selected_model_rs.pressed_button is not None

        model_button = cast(ModelRadioButton, selected_model_rs.pressed_button)
        model = model_button.model
        self.opspilot.runtime_config = self.opspilot.runtime_config.model_copy(
            update={
                "selected_model": model,
            }
        )

        self.apply_overridden_subtitles(selected_model_rs)
        self.refresh()

    def apply_overridden_subtitles(
        self, selected_model_rs: RadioSet
    ) -> None:
        if (
            self.opspilot.launch_config.default_model
            != self.opspilot.runtime_config.selected_model.id
            and self.opspilot.launch_config.default_model
            != self.opspilot.runtime_config.selected_model.name
        ):
            selected_model_rs.border_subtitle = "overrides config"
        else:
            selected_model_rs.border_subtitle = ""

    @on(Input.Changed)
    def save_api_key_on_change(self, event: Input.Changed) -> None:
        """Save API keys when they're changed."""
        input_id = event.input.id

        # Map input IDs to provider names
        provider_map = {
            "openai-api-key": "OpenAI",
            "anthropic-api-key": "Anthropic",
            "google-api-key": "Google",
            "deepseek-api-key": "DeepSeek",
            "openrouter-api-key": "OpenRouter",
        }

        if input_id in provider_map:
            # Get all current API key values
            api_keys = {}
            for input_id, provider in provider_map.items():
                try:
                    input_widget = self.query_one(f"#{input_id}", Input)
                    value = input_widget.value.strip()
                    if value:
                        api_keys[provider] = value
                except Exception:
                    pass

            # Save to file
            try:
                save_api_keys(api_keys)
                # Reload the launch config to pick up the new keys
                from opspilot.tui.api_keys_manager import load_api_keys
                self.opspilot.launch_config = self.opspilot.launch_config.model_copy(
                    update={"api_keys": load_api_keys()}
                )
            except Exception as e:
                self.app.notify(
                    f"Failed to save API key: {e}",
                    title="Error",
                    severity="error",
                )
