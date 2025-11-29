"""
Tests for OpsPilot Agent Core
"""

import pytest
from opspilot.agent.core import AgentCore, AgentMode, Tool


def test_agent_initialization():
    """Test agent core initialization."""
    agent = AgentCore()
    assert agent.mode == AgentMode.PLAN
    assert len(agent.messages) == 0
    assert agent.usage_stats["total_tokens"] == 0


def test_mode_switching():
    """Test switching between Plan and Build modes."""
    agent = AgentCore()

    assert agent.mode == AgentMode.PLAN

    agent.switch_mode(AgentMode.BUILD)
    assert agent.mode == AgentMode.BUILD

    agent.switch_mode(AgentMode.PLAN)
    assert agent.mode == AgentMode.PLAN


def test_add_message():
    """Test adding messages to conversation history."""
    agent = AgentCore()

    agent.add_message("user", "Hello")
    assert len(agent.messages) == 1
    assert agent.messages[0].role == "user"
    assert agent.messages[0].content == "Hello"

    agent.add_message("assistant", "Hi there!")
    assert len(agent.messages) == 2


def test_clear_history():
    """Test clearing conversation history."""
    agent = AgentCore()

    agent.add_message("user", "Test message 1")
    agent.add_message("assistant", "Response 1")
    assert len(agent.messages) == 2

    agent.clear_history()
    assert len(agent.messages) == 0


def test_tool_registration():
    """Test registering tools with the agent."""
    agent = AgentCore()

    async def mock_tool(**kwargs):
        return "Mock result"

    tool = Tool(
        name="mock_tool",
        description="A mock tool for testing",
        parameters={"type": "object", "properties": {}},
        function=mock_tool,
        requires_build_mode=False,
    )

    agent.register_tool(tool)
    assert "mock_tool" in agent.tools


def test_get_available_tools_plan_mode():
    """Test that only non-build tools are available in Plan mode."""
    agent = AgentCore()

    async def plan_tool(**kwargs):
        return "Plan result"

    async def build_tool(**kwargs):
        return "Build result"

    agent.register_tool(
        Tool(
            name="plan_tool",
            description="Plan mode tool",
            parameters={"type": "object"},
            function=plan_tool,
            requires_build_mode=False,
        )
    )

    agent.register_tool(
        Tool(
            name="build_tool",
            description="Build mode tool",
            parameters={"type": "object"},
            function=build_tool,
            requires_build_mode=True,
        )
    )

    # In Plan mode, only plan_tool should be available
    agent.switch_mode(AgentMode.PLAN)
    available = agent.get_available_tools()
    tool_names = [t["function"]["name"] for t in available]

    assert "plan_tool" in tool_names
    assert "build_tool" not in tool_names


def test_get_available_tools_build_mode():
    """Test that all tools are available in Build mode."""
    agent = AgentCore()

    async def plan_tool(**kwargs):
        return "Plan result"

    async def build_tool(**kwargs):
        return "Build result"

    agent.register_tool(
        Tool(
            name="plan_tool",
            description="Plan mode tool",
            parameters={"type": "object"},
            function=plan_tool,
            requires_build_mode=False,
        )
    )

    agent.register_tool(
        Tool(
            name="build_tool",
            description="Build mode tool",
            parameters={"type": "object"},
            function=build_tool,
            requires_build_mode=True,
        )
    )

    # In Build mode, both tools should be available
    agent.switch_mode(AgentMode.BUILD)
    available = agent.get_available_tools()
    tool_names = [t["function"]["name"] for t in available]

    assert "plan_tool" in tool_names
    assert "build_tool" in tool_names


def test_usage_stats():
    """Test usage statistics tracking."""
    agent = AgentCore()

    stats = agent.get_usage_stats()
    assert "total_tokens" in stats
    assert "total_cost" in stats
    assert "requests_count" in stats

    # Reset stats
    agent.reset_usage_stats()
    stats = agent.get_usage_stats()
    assert stats["total_tokens"] == 0
    assert stats["total_cost"] == 0.0


def test_conversation_summary():
    """Test getting conversation summary."""
    agent = AgentCore()
    agent.add_message("user", "Test")

    summary = agent.get_conversation_summary()
    assert summary["mode"] == "plan"
    assert summary["message_count"] == 1
    assert "current_model" in summary
    assert "usage_stats" in summary


if __name__ == "__main__":
    pytest.main([__file__])
