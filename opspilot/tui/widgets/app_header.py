from typing import TYPE_CHECKING, cast
from importlib.metadata import version
from rich.markup import escape
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.signal import Signal
from textual.widget import Widget
from textual.widgets import Label

from rich.text import Text
from opspilot.tui.config import OpsPilotChatModel
from opspilot.tui.models import get_model
from opspilot.tui.runtime_config import RuntimeConfig


if TYPE_CHECKING:
    from opspilot.tui.app import OpsPilot


class AppHeader(Widget):
    COMPONENT_CLASSES = {"app-title", "app-subtitle"}

    def __init__(
        self,
        config_signal: Signal[RuntimeConfig],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes, disabled=disabled)
        self.config_signal: Signal[RuntimeConfig] = config_signal
        self.opspilot = cast("OpsPilot", self.app)

    def on_mount(self) -> None:
        def on_config_change(config: RuntimeConfig) -> None:
            self._update_selected_model(config.selected_model)

        self.config_signal.subscribe(self, on_config_change)

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="cl-header-container"):
                yield Label(
                    Text("OpsPilot") + Text(" v" + version("opspilot"), style="dim"),
                    id="opspilot-title",
                )
            model_name_or_id = (
                self.opspilot.runtime_config.selected_model.id
                or self.opspilot.runtime_config.selected_model.name
            )
            model = get_model(model_name_or_id, self.opspilot.launch_config)
            yield Label(self._get_selected_model_link_text(model), id="model-label")

    def _get_selected_model_link_text(self, model: OpsPilotChatModel) -> str:
        return f"[@click=screen.options]{escape(model.display_name or model.name)}[/]"

    def _update_selected_model(self, model: OpsPilotChatModel) -> None:
        print(self.opspilot.runtime_config)
        model_label = self.query_one("#model-label", Label)
        model_label.update(self._get_selected_model_link_text(model))
