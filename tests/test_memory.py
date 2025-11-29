"""
Tests for OpsPilot Memory Management
"""

import pytest
import tempfile
import shutil
from opspilot.agent.memory import MemoryManager, ChatMessage


@pytest.fixture
def temp_storage():
    """Create a temporary storage directory for testing."""
    tmpdir = tempfile.mkdtemp()
    yield tmpdir
    # Clean up after test
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass


@pytest.fixture
def memory_manager():
    """Create a MemoryManager instance with isolated temporary storage."""
    # Create a unique temp directory for each test
    tmpdir = tempfile.mkdtemp()
    manager = MemoryManager(storage_dir=tmpdir)
    yield manager
    # Clean up after test
    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass


def test_create_session(memory_manager):
    """Test creating a new session."""
    session_id = memory_manager.create_session("Test Session")

    assert session_id is not None
    assert memory_manager.current_session is not None
    assert memory_manager.current_session.title == "Test Session"
    assert len(memory_manager.current_session.messages) == 0


def test_create_session_auto_title(memory_manager):
    """Test creating a session with auto-generated title."""
    session_id = memory_manager.create_session()

    assert session_id is not None
    assert memory_manager.current_session is not None
    # Default title is "New Conversation"
    assert memory_manager.current_session.title == "New Conversation"


def test_add_message(memory_manager):
    """Test adding messages to a session."""
    memory_manager.create_session("Test")

    msg_id = memory_manager.add_message("user", "Hello!")
    assert msg_id is not None
    assert len(memory_manager.current_session.messages) == 1
    assert memory_manager.current_session.messages[0].role == "user"
    assert memory_manager.current_session.messages[0].content == "Hello!"

    memory_manager.add_message("assistant", "Hi there!")
    assert len(memory_manager.current_session.messages) == 2


def test_get_messages(memory_manager):
    """Test retrieving messages from current session."""
    memory_manager.create_session("Test")

    memory_manager.add_message("user", "Message 1")
    memory_manager.add_message("assistant", "Message 2")
    memory_manager.add_message("user", "Message 3")

    messages = memory_manager.get_messages()
    assert len(messages) == 3
    assert messages[0].content == "Message 1"
    assert messages[2].content == "Message 3"


def test_load_session(memory_manager):
    """Test loading an existing session."""
    # Create and save a session
    session_id = memory_manager.create_session("Original Session")
    memory_manager.add_message("user", "Test message")

    # Clear current session
    memory_manager.current_session = None

    # Load it back
    success = memory_manager.load_session(session_id)
    assert success is True
    assert memory_manager.current_session.id == session_id
    assert memory_manager.current_session.title == "Original Session"
    assert len(memory_manager.current_session.messages) == 1


def test_load_nonexistent_session(memory_manager):
    """Test loading a session that doesn't exist."""
    success = memory_manager.load_session("nonexistent-id")
    assert success is False


def test_delete_session():
    """Test deleting a session."""
    # Create fresh memory manager with isolated storage
    tmpdir = tempfile.mkdtemp()
    try:
        manager = MemoryManager(storage_dir=tmpdir)

        session_id = manager.create_session("To Delete")

        # Verify it exists
        sessions = manager.list_sessions()
        assert len(sessions) == 1

        # Delete it
        success = manager.delete_session(session_id)
        assert success is True

        # Verify it's gone
        sessions = manager.list_sessions()
        assert len(sessions) == 0

        # Current session should be cleared
        assert manager.current_session is None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_list_sessions():
    """Test listing all sessions."""
    import time

    # Create fresh memory manager with isolated storage
    tmpdir = tempfile.mkdtemp()
    try:
        manager = MemoryManager(storage_dir=tmpdir)

        # Create multiple sessions
        manager.create_session("Session 1")
        manager.add_message("user", "Message in session 1")

        # Small delay to ensure different timestamps on Windows
        time.sleep(0.01)

        manager.create_session("Session 2")
        manager.add_message("user", "Message in session 2")

        sessions = manager.list_sessions()
        assert len(sessions) == 2

        # Sessions should be sorted by updated_at (most recent first)
        assert sessions[0]["title"] == "Session 2"
        assert sessions[1]["title"] == "Session 1"

        # Check metadata
        assert sessions[0]["message_count"] == 1
        assert "created_at" in sessions[0]
        assert "updated_at" in sessions[0]
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_export_session_json(memory_manager):
    """Test exporting a session as JSON."""
    session_id = memory_manager.create_session("Export Test")
    memory_manager.add_message("user", "Test message")

    exported = memory_manager.export_session(session_id, "json")

    assert exported is not None
    assert "Export Test" in exported
    assert "Test message" in exported


def test_export_session_markdown(memory_manager):
    """Test exporting a session as Markdown."""
    session_id = memory_manager.create_session("Markdown Export")
    memory_manager.add_message("user", "User message")
    memory_manager.add_message("assistant", "Assistant response")

    exported = memory_manager.export_session(session_id, "markdown")

    assert exported is not None
    assert "# Markdown Export" in exported
    assert "User message" in exported
    assert "Assistant response" in exported


def test_export_session_txt(memory_manager):
    """Test exporting a session as plain text."""
    session_id = memory_manager.create_session("Text Export")
    memory_manager.add_message("user", "Hello")

    exported = memory_manager.export_session(session_id, "txt")

    assert exported is not None
    assert "Text Export" in exported
    assert "Hello" in exported


def test_get_session_stats_no_session():
    """Test getting stats when no session is active."""
    # Create fresh memory manager with isolated storage
    tmpdir = tempfile.mkdtemp()
    try:
        manager = MemoryManager(storage_dir=tmpdir)

        stats = manager.get_session_stats()

        assert stats["total_sessions"] == 0
        assert stats["total_messages"] == 0
        assert stats["current_session_id"] is None
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_get_session_stats_with_session():
    """Test getting stats for an active session."""
    # Create fresh memory manager with isolated storage
    tmpdir = tempfile.mkdtemp()
    try:
        manager = MemoryManager(storage_dir=tmpdir)

        manager.create_session("Stats Test")
        manager.add_message("user", "Message 1")
        manager.add_message("assistant", "Message 2")
        manager.add_message("user", "Message 3")

        stats = manager.get_session_stats()

        assert stats["total_sessions"] == 1
        assert stats["total_messages"] == 3
        assert stats["current_session_id"] is not None
        assert "storage_dir" in stats
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_message_to_dict():
    """Test converting ChatMessage to dictionary."""
    import time
    import uuid

    now = time.time()

    msg = ChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        content="Test",
        timestamp=now,
    )

    data = msg.to_dict()
    assert data["role"] == "user"
    assert data["content"] == "Test"
    assert data["timestamp"] == now


def test_message_from_dict():
    """Test creating ChatMessage from dictionary."""
    import time
    import uuid

    now = time.time()
    msg_id = str(uuid.uuid4())

    data = {
        "id": msg_id,
        "role": "assistant",
        "content": "Response",
        "timestamp": now,
        "tool_calls": None,
        "tool_call_id": None,
        "metadata": None,
    }

    msg = ChatMessage.from_dict(data)
    assert msg.role == "assistant"
    assert msg.content == "Response"
    assert msg.timestamp == now


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
