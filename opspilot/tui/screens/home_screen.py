from typing import TYPE_CHECKING, cast
from textual import on
from textual.app import ComposeResult
from textual.binding import Binding
from textual.events import ScreenResume
from textual.screen import Screen
from textual.signal import Signal
from textual.widgets import Footer

from opspilot.tui.runtime_config import RuntimeConfig
from opspilot.tui.widgets.chat_list import ChatList
from opspilot.tui.widgets.prompt_input import PromptInput
from opspilot.tui.chats_manager import ChatsManager
from opspilot.tui.widgets.app_header import AppHeader
from opspilot.tui.screens.chat_screen import ChatScreen
from opspilot.tui.widgets.chat_options import OptionsModal
from opspilot.tui.widgets.welcome import Welcome

if TYPE_CHECKING:
    from opspilot.tui.app import OpsPilot


class HomePromptInput(PromptInput):
    BINDINGS = [Binding("escape", "app.quit", "Quit", key_display="esc")]


class HomeScreen(Screen[None]):
    CSS = """\
ChatList {
    height: 1fr;
    width: 1fr;
    background: $background 15%;
}
"""

    BINDINGS = [
        Binding(
            "ctrl+j",
            "send_message",
            "Send message",
            priority=True,
            key_display="↵",
            tooltip="Send a message to the chosen LLM. Press [b u]enter[/] to send, "
            "or [b u]shift+enter[/] to add a new line.",
        ),
        Binding(
            "o,ctrl+o",
            "options",
            "Options",
            key_display="^o",
            tooltip="Change the model and check where OpsPilot"
            " is storing your data.",
        ),
    ]

    def __init__(
        self,
        config_signal: Signal[RuntimeConfig],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.config_signal = config_signal
        self.opspilot = cast("OpsPilot", self.app)

    def on_mount(self) -> None:
        self.chats_manager = ChatsManager()

    def compose(self) -> ComposeResult:
        yield AppHeader(self.config_signal)
        yield HomePromptInput(id="home-prompt")
        yield ChatList()
        yield Welcome()
        yield Footer()

    @on(ScreenResume)
    async def reload_screen(self) -> None:
        chat_list = self.query_one(ChatList)
        await chat_list.reload_and_refresh()
        self.show_welcome_if_required()

    @on(ChatList.ChatOpened)
    async def open_chat_screen(self, event: ChatList.ChatOpened):
        chat_id = event.chat.id
        assert chat_id is not None
        chat = await self.chats_manager.get_chat(chat_id)
        await self.app.push_screen(ChatScreen(chat))

    @on(ChatList.CursorEscapingTop)
    def cursor_escaping_top(self):
        self.query_one(HomePromptInput).focus()

    @on(PromptInput.PromptSubmitted)
    async def create_new_chat(self, event: PromptInput.PromptSubmitted) -> None:
        text = event.text
        await self.opspilot.launch_chat(  # type: ignore
            prompt=text,
            model=self.opspilot.runtime_config.selected_model,
        )

    @on(PromptInput.CursorEscapingBottom)
    async def move_focus_below(self) -> None:
        self.focus_next(ChatList)

    def action_send_message(self) -> None:
        prompt_input = self.query_one(PromptInput)
        prompt_input.action_submit_prompt()

    def action_focus_prompt(self) -> None:
        """Focus the prompt input."""
        self.query_one(HomePromptInput).focus()

    async def action_options(self) -> None:
        await self.app.push_screen(
            OptionsModal(),
            callback=self.update_config,
        )

    def update_config(self, runtime_config: RuntimeConfig) -> None:
        app = cast("OpsPilot", self.app)
        app.runtime_config = runtime_config

    def show_welcome_if_required(self) -> None:
        chat_list = self.query_one(ChatList)
        if chat_list.option_count == 0:
            welcome = self.query_one(Welcome)
            welcome.display = "block"
        else:
            welcome = self.query_one(Welcome)
            welcome.display = "none"
