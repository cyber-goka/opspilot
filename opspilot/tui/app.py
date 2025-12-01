from __future__ import annotations

import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App
from textual.binding import Binding
from textual.reactive import Reactive, reactive
from textual.signal import Signal

from opspilot.tui.chats_manager import ChatsManager
from opspilot.tui.models import ChatData, ChatMessage
from opspilot.tui.config import OpsPilotChatModel, LaunchConfig
from opspilot.tui.runtime_config import RuntimeConfig
from opspilot.tui.screens.chat_screen import ChatScreen
from opspilot.tui.screens.help_screen import HelpScreen
from opspilot.tui.screens.home_screen import HomeScreen
from opspilot.tui.themes import BUILTIN_THEMES, Theme, load_user_themes
from opspilot.agent import AgentCore

if TYPE_CHECKING:
    from litellm.types.completion import (
        ChatCompletionUserMessageParam,
        ChatCompletionSystemMessageParam,
    )


class OpsPilot(App[None]):
    ENABLE_COMMAND_PALETTE = False
    CSS_PATH = Path(__file__).parent / "opspilot.scss"
    BINDINGS = [
        Binding("q", "app.quit", "Quit", show=False),
        Binding("f1,?", "help", "Help"),
    ]

    # Use textual-dark as base theme, we'll override with custom theme colors
    DEFAULT_CSS = """
    App {
        background: $surface;
    }
    """

    def __init__(self, config: LaunchConfig, startup_prompt: str = ""):
        self.launch_config = config

        available_themes: dict[str, Theme] = BUILTIN_THEMES.copy()
        available_themes |= load_user_themes()

        self.themes: dict[str, Theme] = available_themes

        self._runtime_config = RuntimeConfig(
            selected_model=config.default_model_object,
            system_prompt=config.system_prompt,
        )
        self.runtime_config_signal = Signal[RuntimeConfig](
            self, "runtime-config-updated"
        )
        """Widgets can subscribe to this signal to be notified of
        when the user has changed configuration at runtime (e.g. using the UI)."""

        self.startup_prompt = startup_prompt
        """OpsPilot can be launched with a prompt on startup via a command line option.

        This is a convenience which will immediately load the chat interface and
        put users into the chat window, rather than going to the home screen.
        """

        # Initialize the OpsPilot agent with TUI config for API keys
        self.agent = AgentCore(launch_config=config)

        # Custom theme name (not a Textual theme, used for our color system)
        self.app_theme: str | None = None

        super().__init__()

    @property
    def runtime_config(self) -> RuntimeConfig:
        return self._runtime_config

    @runtime_config.setter
    def runtime_config(self, new_runtime_config: RuntimeConfig) -> None:
        self._runtime_config = new_runtime_config
        self.runtime_config_signal.publish(self.runtime_config)

    async def on_mount(self) -> None:
        await self.push_screen(HomeScreen(self.runtime_config_signal))
        self.app_theme = self.launch_config.theme
        if self.startup_prompt:
            await self.launch_chat(
                prompt=self.startup_prompt,
                model=self.runtime_config.selected_model,
            )

    async def launch_chat(self, prompt: str, model: OpsPilotChatModel) -> None:
        current_time = datetime.datetime.now(datetime.timezone.utc)
        system_message: ChatCompletionSystemMessageParam = {
            "content": self.runtime_config.system_prompt,
            "role": "system",
        }
        user_message: ChatCompletionUserMessageParam = {
            "content": prompt,
            "role": "user",
        }
        chat = ChatData(
            id=None,
            title=None,
            create_timestamp=None,
            model=model,
            messages=[
                ChatMessage(
                    message=system_message,
                    timestamp=current_time,
                    model=model,
                ),
                ChatMessage(
                    message=user_message,
                    timestamp=current_time,
                    model=model,
                ),
            ],
        )
        chat.id = await ChatsManager.create_chat(chat_data=chat)
        await self.push_screen(ChatScreen(chat))

    async def action_help(self) -> None:
        if isinstance(self.screen, HelpScreen):
            self.pop_screen()
        else:
            await self.push_screen(HelpScreen())

    def action_open_link(self, url: str) -> None:
        """Open a URL in the default browser."""
        import webbrowser
        try:
            webbrowser.open(url)
        except Exception:
            self.notify(
                f"Could not open URL: {url}",
                title="Error",
                severity="error",
            )

    def get_css_variables(self) -> dict[str, str]:
        if self.app_theme:
            theme = self.themes.get(self.app_theme)
            if theme:
                color_system = theme.to_color_system().generate()
            else:
                color_system = {}
        else:
            color_system = {}

        return {**super().get_css_variables(), **color_system}

    def watch_app_theme(self, theme: str | None) -> None:
        """Watch for changes to app_theme and update CSS."""
        self.refresh_css(animate=False)
        if hasattr(self, "screen"):
            self.screen._update_styles()

    async def on_unmount(self) -> None:
        """Cleanup when app is closing."""
        try:
            # Close LiteLLM async clients to avoid RuntimeWarning
            from litellm import close_litellm_async_clients
            await close_litellm_async_clients()
        except Exception:
            pass  # Ignore cleanup errors

    @property
    def theme_object(self) -> Theme | None:
        """Get the current theme object."""
        try:
            return self.themes[self.app_theme] if self.app_theme else None
        except KeyError:
            return None


if __name__ == "__main__":
    app = OpsPilot(LaunchConfig())
    app.run()
