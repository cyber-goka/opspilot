"""
OpsPilot Memory Management

Handles chat history persistence, conversation context management,
and session state for the agent.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

from ..config import config_manager


@dataclass
class ChatMessage:
    """Represents a single chat message."""

    id: str
    role: str  # "user", "assistant", "system", "tool"
    content: str
    timestamp: float
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessage":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ConversationSession:
    """Represents a conversation session."""

    id: str
    title: str
    created_at: float
    updated_at: float
    messages: List[ChatMessage]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "messages": [msg.to_dict() for msg in self.messages],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationSession":
        """Create from dictionary."""
        messages = [ChatMessage.from_dict(msg) for msg in data["messages"]]
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data["created_at"],
            updated_at=data["updated_at"],
            messages=messages,
            metadata=data["metadata"],
        )


class MemoryManager:
    """Manages chat history and conversation sessions."""

    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize memory manager.

        Args:
            storage_dir: Directory for storing conversation history
        """
        if storage_dir:
            self.storage_dir = Path(storage_dir)
        else:
            self.storage_dir = Path.home() / ".opspilot" / "conversations"

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[ConversationSession] = None
        self.max_messages_per_session = 1000
        self.max_sessions = 50

    def create_session(self, title: str = "New Conversation") -> str:
        """
        Create a new conversation session.

        Args:
            title: Session title

        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        now = time.time()

        session = ConversationSession(
            id=session_id,
            title=title,
            created_at=now,
            updated_at=now,
            messages=[],
            metadata={
                "mode": "plan",
                "model": config_manager.get_model_for_mode("plan"),
                "auth_mode": (
                    "subscription" if config_manager.is_subscription_mode() else "byok"
                ),
            },
        )

        self.current_session = session
        self._save_session(session)

        return session_id

    def load_session(self, session_id: str) -> bool:
        """
        Load an existing session.

        Args:
            session_id: ID of session to load

        Returns:
            True if successful, False otherwise
        """
        session_file = self.storage_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.current_session = ConversationSession.from_dict(data)
            return True

        except Exception:
            return False

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: ID of session to delete

        Returns:
            True if successful, False otherwise
        """
        session_file = self.storage_dir / f"{session_id}.json"

        try:
            if session_file.exists():
                session_file.unlink()

            if self.current_session and self.current_session.id == session_id:
                self.current_session = None

            return True

        except Exception:
            return False

    def add_message(
        self,
        role: str,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        tool_call_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Add a message to the current session.

        Args:
            role: Message role ("user", "assistant", "system", "tool")
            content: Message content
            tool_calls: Tool calls made by the assistant
            tool_call_id: Tool call ID for tool responses
            metadata: Additional metadata

        Returns:
            Message ID
        """
        if not self.current_session:
            self.create_session()

        message_id = str(uuid.uuid4())
        now = time.time()

        message = ChatMessage(
            id=message_id,
            role=role,
            content=content,
            timestamp=now,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            metadata=metadata or {},
        )

        if self.current_session:
            self.current_session.messages.append(message)
            self.current_session.updated_at = now

            # Trim messages if too many
            if len(self.current_session.messages) > self.max_messages_per_session:
                # Keep system messages and recent messages
                system_messages = [
                    msg for msg in self.current_session.messages if msg.role == "system"
                ]
                recent_messages = self.current_session.messages[
                    -(self.max_messages_per_session - len(system_messages)) :
                ]
                self.current_session.messages = system_messages + recent_messages

            self._save_session(self.current_session)

        return message_id

    def get_messages(
        self, limit: Optional[int] = None, include_system: bool = True
    ) -> List[ChatMessage]:
        """
        Get messages from current session.

        Args:
            limit: Maximum number of messages to return
            include_system: Whether to include system messages

        Returns:
            List of messages
        """
        if not self.current_session:
            return []

        messages = self.current_session.messages

        if not include_system:
            messages = [msg for msg in messages if msg.role != "system"]

        if limit:
            messages = messages[-limit:]

        return messages

    def get_conversation_context(
        self, max_tokens: int = 8000, include_system: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get conversation context for AI model.

        Args:
            max_tokens: Maximum tokens for context
            include_system: Whether to include system message

        Returns:
            List of messages in OpenAI format
        """
        messages = self.get_messages(include_system=include_system)

        # Convert to OpenAI format
        context = []
        for msg in messages:
            context.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls,
                    "tool_call_id": msg.tool_call_id,
                }
            )

        return context

    def update_session_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Update current session metadata.

        Args:
            metadata: New metadata to merge
        """
        if not self.current_session:
            return

        self.current_session.metadata.update(metadata)
        self.current_session.updated_at = time.time()
        self._save_session(self.current_session)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions.

        Returns:
            List of session summaries
        """
        sessions = []

        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                sessions.append(
                    {
                        "id": data["id"],
                        "title": data["title"],
                        "created_at": data["created_at"],
                        "updated_at": data["updated_at"],
                        "message_count": len(data["messages"]),
                        "metadata": data.get("metadata", {}),
                    }
                )

            except Exception:
                continue

        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x["updated_at"], reverse=True)

        return sessions

    def cleanup_old_sessions(self) -> int:
        """
        Clean up old sessions, keeping only the most recent ones.

        Returns:
            Number of sessions deleted
        """
        sessions = self.list_sessions()

        if len(sessions) <= self.max_sessions:
            return 0

        # Delete oldest sessions
        sessions_to_delete = sessions[self.max_sessions :]
        deleted_count = 0

        for session in sessions_to_delete:
            if self.delete_session(session["id"]):
                deleted_count += 1

        return deleted_count

    def export_session(self, session_id: str, format: str = "json") -> Optional[str]:
        """
        Export session to various formats.

        Args:
            session_id: ID of session to export
            format: Export format ("json", "markdown", "txt")

        Returns:
            Exported content or None if failed
        """
        if not self.load_session(session_id):
            return None

        if not self.current_session:
            return None

        if format == "json":
            return json.dumps(self.current_session.to_dict(), indent=2)

        elif format == "markdown":
            lines = [
                f"# {self.current_session.title}",
                f"*Created: {datetime.fromtimestamp(self.current_session.created_at)}*",
                f"*Updated: {datetime.fromtimestamp(self.current_session.updated_at)}*",
                "",
                "---",
                "",
            ]

            for msg in self.current_session.messages:
                if msg.role == "system":
                    continue

                role_emoji = {"user": "👤", "assistant": "🤖", "tool": "🔧"}.get(
                    msg.role, "•"
                )
                timestamp = datetime.fromtimestamp(msg.timestamp).strftime("%H:%M:%S")

                lines.append(f"## {role_emoji} {msg.role.title()} ({timestamp})")
                lines.append("")
                lines.append(msg.content)
                lines.append("")

            return "\n".join(lines)

        elif format == "txt":
            lines = [f"Conversation: {self.current_session.title}"]
            lines.append("=" * 50)
            lines.append("")

            for msg in self.current_session.messages:
                if msg.role == "system":
                    continue

                timestamp = datetime.fromtimestamp(msg.timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                lines.append(f"[{timestamp}] {msg.role.upper()}:")
                lines.append(msg.content)
                lines.append("")

            return "\n".join(lines)

        return None

    def _save_session(self, session: ConversationSession) -> None:
        """Save session to file."""
        session_file = self.storage_dir / f"{session.id}.json"

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about sessions."""
        sessions = self.list_sessions()

        total_messages = sum(s["message_count"] for s in sessions)
        total_size = 0

        for session_file in self.storage_dir.glob("*.json"):
            total_size += session_file.stat().st_size

        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "total_size_bytes": total_size,
            "current_session_id": (
                self.current_session.id if self.current_session else None
            ),
            "storage_dir": str(self.storage_dir),
        }


# Global memory manager instance
memory_manager = MemoryManager()
