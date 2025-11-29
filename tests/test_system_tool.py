"""
Tests for OpsPilot System Tools
"""

import pytest
from opspilot.agent.tools.system import SystemTool


@pytest.fixture
def system_tool():
    """Create a SystemTool instance for testing."""
    return SystemTool()


@pytest.mark.asyncio
async def test_execute_simple_command(system_tool):
    """Test executing a simple command."""
    result = await system_tool.execute_command("echo 'Hello, World!'")

    assert result["success"] is True
    assert result["return_code"] == 0
    assert "Hello, World!" in result["stdout"]


@pytest.mark.asyncio
async def test_execute_command_with_error(system_tool):
    """Test executing a command that fails."""
    result = await system_tool.execute_command("ls /nonexistent_directory_xyz123")

    assert result["success"] is False
    assert result["return_code"] != 0


@pytest.mark.asyncio
async def test_command_timeout(system_tool):
    """Test that commands timeout properly."""
    result = await system_tool.execute_command("sleep 10", timeout=0.5)

    assert result["success"] is False
    assert "timed out" in result["error"].lower()


@pytest.mark.asyncio
async def test_dangerous_command_detection(system_tool):
    """Test that dangerous commands are detected."""
    # Test with confirmation callback
    confirmed = False

    async def mock_confirmation(command, keyword):
        nonlocal confirmed
        confirmed = True
        return False  # Reject the command

    system_tool.confirmation_callback = mock_confirmation

    result = await system_tool.execute_command("rm -rf /tmp/test")

    # Should have triggered confirmation
    assert confirmed is True
    # Should be blocked
    assert result["success"] is False


@pytest.mark.asyncio
async def test_dangerous_command_allowed(system_tool):
    """Test that dangerous commands can be allowed."""
    import os
    import tempfile

    async def mock_confirmation(command, keyword):
        return True  # Allow the command

    system_tool.confirmation_callback = mock_confirmation

    # Create a test file to remove
    with tempfile.NamedTemporaryFile(delete=False) as f:
        test_file = f.name

    # Use Python to delete file (cross-platform)
    result = await system_tool.execute_command(
        f'python -c "import os; os.remove(\'{test_file}\')"'
    )

    # Should succeed since we allowed it
    assert result["success"] is True


@pytest.mark.asyncio
async def test_working_directory(system_tool):
    """Test executing command in specific directory."""
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # Use Python to get current directory (cross-platform)
        result = await system_tool.execute_command(
            'python -c "import os; print(os.getcwd())"', working_directory=tmpdir
        )

        assert result["success"] is True
        # Normalize paths for comparison (handles Windows backslash vs forward slash)
        assert os.path.normpath(tmpdir) in os.path.normpath(result["stdout"])


@pytest.mark.asyncio
async def test_check_command_exists(system_tool):
    """Test checking if a command exists."""
    # Most systems should have 'ls'
    exists = await system_tool.check_command_exists("ls")
    assert exists is True

    # This command should not exist
    exists = await system_tool.check_command_exists("nonexistent_command_xyz123")
    assert exists is False


def test_get_system_info(system_tool):
    """Test getting system information."""
    info = system_tool.get_system_info()

    assert "platform" in info
    assert "cwd" in info
    assert "home" in info
    assert "user" in info


def test_dangerous_keywords_list(system_tool):
    """Test that dangerous keywords are properly defined."""
    assert "rm" in system_tool.dangerous_keywords
    assert "sudo" in system_tool.dangerous_keywords
    assert "kubectl" in system_tool.dangerous_keywords
    assert "docker rm" in system_tool.dangerous_keywords


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
