from pydantic import BaseModel, ConfigDict

from opspilot.tui.config import OpsPilotChatModel


class RuntimeConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_model: OpsPilotChatModel
    system_prompt: str
