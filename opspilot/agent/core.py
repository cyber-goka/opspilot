"""
OpsPilot Agent Core

Implements the Think-Act loop with Plan/Build mode switching.
Manages AI interactions and tool orchestration.
"""

import json
from typing import List, Dict, Any, Optional, Literal, Callable
from dataclasses import dataclass
from enum import Enum

try:
    from litellm import acompletion, completion
except ImportError:
    # Fallback for development
    class MockMessage:
        def __init__(self) -> None:
            self.content = "Mock response - litellm not installed"
            self.tool_calls = None

    class MockChoice:
        @property
        def message(self) -> MockMessage:
            return MockMessage()

    class MockResponse:
        @property
        def choices(self) -> List[MockChoice]:
            return [MockChoice()]

    async def acompletion(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse()

    def sync_completion(*args: Any, **kwargs: Any) -> MockResponse:
        return MockResponse()

    def completion(*args: Any, **kwargs: Any) -> Any:
        class MockResponse:
            def choice(self) -> Dict[str, Any]:
                return {"message": {"content": "Mock response - litellm not installed"}}

        return MockResponse()


from ..config import config_manager


class AgentMode(Enum):
    """Agent operation modes."""

    PLAN = "plan"
    BUILD = "build"


@dataclass
class Tool:
    """Represents an available tool for the agent."""

    name: str
    description: str
    parameters: Dict[str, Any]
    function: Callable
    requires_build_mode: bool = False


@dataclass
class Message:
    """Represents a chat message."""

    role: Literal["user", "assistant", "system", "tool"]
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None


class AgentCore:
    """Core agent logic implementing Think-Act loop."""

    def __init__(self) -> None:
        self.config = config_manager.load_config()
        self.mode = AgentMode.PLAN
        self.tools: Dict[str, Tool] = {}
        self.messages: List[Message] = []
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_count": 0,
            "current_context_tokens": 0,
        }
        self._setup_default_tools()

    def _setup_default_tools(self) -> None:
        """Setup default tools based on available modules."""
        # These will be populated when tools are imported
        pass

    def _track_usage(self, response: Any) -> None:
        """Track usage statistics from litellm response."""
        try:
            # Extract usage information
            usage = getattr(response, "usage", None)
            if usage:
                # Get token counts
                prompt_tokens = getattr(usage, "prompt_tokens", 0)
                completion_tokens = getattr(usage, "completion_tokens", 0)
                total_tokens = getattr(usage, "total_tokens", 0)

                # Update statistics
                self.usage_stats["total_tokens"] += total_tokens
                self.usage_stats["requests_count"] += 1

                # Calculate cost
                cost = self._calculate_cost(
                    config_manager.get_model_for_mode(self.mode.value),
                    prompt_tokens,
                    completion_tokens,
                )
                self.usage_stats["total_cost"] += cost

                # Update current context tokens (approximate)
                self.usage_stats["current_context_tokens"] = prompt_tokens

        except Exception:
            # Don't fail if usage tracking fails
            pass

    def _calculate_cost(
        self, model: str, prompt_tokens: int, completion_tokens: int
    ) -> float:
        """Calculate cost for the given model and token usage."""
        # Cost per 1K tokens (approximate rates)
        costs = {
            # OpenAI models
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-3.5-turbo": {"prompt": 0.0015, "completion": 0.002},
            # Zhipu models
            "glm-4-plus": {"prompt": 0.1, "completion": 0.1},
            "glm-4-flash": {"prompt": 0.01, "completion": 0.01},
            # Anthropic models
            "claude-3-sonnet-20240229": {"prompt": 0.015, "completion": 0.075},
            "claude-3-haiku-20240307": {"prompt": 0.005, "completion": 0.025},
            # OpenRouter models (approximate)
            "openai/gpt-4o": {"prompt": 0.005, "completion": 0.015},
            "anthropic/claude-3-haiku": {"prompt": 0.005, "completion": 0.025},
        }

        # Default cost if model not found
        default_cost = {"prompt": 0.01, "completion": 0.02}

        model_cost = costs.get(model, default_cost)

        prompt_cost = (prompt_tokens / 1000) * model_cost["prompt"]
        completion_cost = (completion_tokens / 1000) * model_cost["completion"]

        return prompt_cost + completion_cost

    def register_tool(self, tool: Any) -> None:
        """Register a new tool with the agent."""
        if isinstance(tool, dict):
            tool_obj = Tool(**tool)
        else:
            tool_obj = tool
        self.tools[tool_obj.name] = tool_obj

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools based on current mode."""
        available_tools = []

        for tool in self.tools.values():
            if tool.requires_build_mode and self.mode == AgentMode.PLAN:
                continue

            available_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
            )

        return available_tools

    def switch_mode(self, mode: AgentMode) -> None:
        """Switch between Plan and Build modes."""
        self.mode = mode

    def add_message(
        self,
        role: Literal["user", "assistant", "system", "tool"],
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
    ) -> None:
        """Add a message to the conversation history."""
        message = Message(
            role=role, content=content, tool_calls=tool_calls, tool_call_id=tool_call_id
        )
        self.messages.append(message)

    async def think(self, user_input: str) -> str:
        """Process user input and generate a response (Think phase)."""
        # Add user message to history
        self.add_message("user", user_input)

        # Get system prompt based on mode
        system_prompt = self._get_system_prompt()

        # Prepare messages for AI
        messages = [
            {"role": "system", "content": system_prompt},
            *[{"role": msg.role, "content": msg.content} for msg in self.messages],
        ]

        # Get available tools
        tools = self.get_available_tools()

        try:
            # Call AI model
            response = await acompletion(
                model=config_manager.get_model_for_mode(self.mode.value),
                messages=messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                **config_manager.get_litellm_config(),
            )

            # Extract response content
            assistant_message = response.choices[0].message

            # Track usage statistics
            self._track_usage(response)

            # Add assistant response to history
            self.add_message(
                "assistant",
                assistant_message.content or "",
                assistant_message.tool_calls,
            )

            return assistant_message.content or ""

        except Exception as e:
            error_msg = f"AI Error: {str(e)}"
            self.add_message("assistant", error_msg)
            return error_msg

    async def act(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute tool calls (Act phase)."""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            tool_args = json.loads(tool_call["function"]["arguments"])
            tool_call_id = tool_call.get("id", "unknown")

            try:
                # Execute tool
                tool = self.tools[tool_name]
                result = await tool.function(**tool_args)

                # Add tool result message
                self.add_message("tool", str(result), tool_call_id=tool_call_id)

                results.append({"tool_call_id": tool_call_id, "result": str(result)})

            except Exception as e:
                error_result = f"Tool Error: {str(e)}"

                self.add_message("tool", error_result, tool_call_id=tool_call_id)

                results.append({"tool_call_id": tool_call_id, "result": error_result})

        return results

    async def process(self, user_input: str) -> str:
        """Main Think-Act loop processing."""
        # Think phase
        response = await self.think(user_input)

        # Check if there are tool calls to execute
        last_message = self.messages[-1] if self.messages else None
        if last_message and last_message.tool_calls:
            # Act phase
            await self.act(last_message.tool_calls)

            # Think again with tool results
            response = await self.think("")  # Empty input to continue conversation

        return response

    def _get_system_prompt(self) -> str:
        """Get system prompt based on current mode."""
        if self.mode == AgentMode.PLAN:
            return """You are OpsPilot, a DevOps assistant in PLAN MODE.

PLAN MODE RULES:
- You can ONLY read files and gather information
- You CANNOT execute shell commands, write files, or make changes
- Your goal is to create a detailed step-by-step plan
- Focus on analysis, planning, and providing clear instructions
- Use available tools to gather information before creating plans

Available tools: File reading tools only

Create comprehensive plans that include:
1. Current state analysis
2. Step-by-step implementation plan
3. Potential risks and mitigations
4. Prerequisites and dependencies

When your plan is complete, inform the user they can switch to BUILD MODE to execute it."""

        else:  # BUILD MODE
            return """You are OpsPilot, a DevOps assistant in BUILD MODE.

BUILD MODE RULES:
- You can execute shell commands and modify files
- You have full system access to implement DevOps tasks
- Always explain what you're doing before taking action
- Be cautious with destructive operations
- Verify success of each operation

Available tools: Full system access including shell commands and file operations

Your approach:
1. Explain the action you're about to take
2. Execute the command or make the change
3. Verify the result
4. Report success or failure with details

Safety reminders:
- Double-check commands before execution
- Use confirmation for dangerous operations
- Provide clear feedback on results"""

    def clear_history(self) -> None:
        """Clear conversation history."""
        self.messages = []

    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation."""
        return {
            "mode": self.mode.value,
            "message_count": len(self.messages),
            "available_tools": len(self.get_available_tools()),
            "current_model": config_manager.get_model_for_mode(self.mode.value),
            "auth_mode": (
                "subscription" if config_manager.is_subscription_mode() else "byok"
            ),
            "usage_stats": self.usage_stats,
        }

    def get_usage_stats(self) -> Dict[str, Any]:
        """Get current usage statistics."""
        return self.usage_stats.copy()

    def reset_usage_stats(self) -> None:
        """Reset usage statistics."""
        self.usage_stats = {
            "total_tokens": 0,
            "total_cost": 0.0,
            "requests_count": 0,
            "current_context_tokens": 0,
        }


# Global agent instance
agent_core = AgentCore()
