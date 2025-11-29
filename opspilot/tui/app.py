"""
OpsPilot TUI Application

Full-featured Textual TUI with split-screen interface.
"""

from typing import Any, Dict, Union

# Check if Textual is available
try:
    from textual.app import App, ComposeResult
    from textual.containers import Container, Horizontal
    from textual.widgets import (
        Header,
        Footer,
        Input,
        Button,
        Static,
        Label,
        RichLog,
    )
    from textual.binding import Binding
    from textual.screen import ModalScreen
    from rich.markdown import Markdown
    from rich.panel import Panel

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

# Import our modules
try:
    from opspilot.agent.core import AgentCore, AgentMode
    from opspilot.agent.memory import memory_manager
    from opspilot.agent.tools.system import system_tool
    from opspilot.agent.tools.files import file_tool
    from opspilot.config import config_manager
except ImportError:
    # Fallback for development - type: ignore comments for mock classes
    class AgentMode:  # type: ignore[no-redef]
        PLAN = "plan"
        BUILD = "build"

    class AgentCore:  # type: ignore[no-redef]
        def __init__(self) -> None:
            self.mode = AgentMode.PLAN
            self.usage_stats: Dict[str, Any] = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "requests_count": 0,
                "current_context_tokens": 0,
            }

        def switch_mode(self, mode: Any) -> None:
            self.mode = mode

        def register_tool(self, tool: Any) -> None:
            pass

        async def process(self, message: str) -> str:
            # Simulate some usage
            self.usage_stats["total_tokens"] += len(message.split()) * 10
            self.usage_stats["total_cost"] += 0.001
            self.usage_stats["requests_count"] += 1
            self.usage_stats["current_context_tokens"] = len(message.split()) * 5
            return f"Mock response to: {message}"

        def get_usage_stats(self) -> Dict[str, Any]:
            return self.usage_stats.copy()

    class memory_manager:  # type: ignore[no-redef]
        @staticmethod
        def create_session(title: str) -> str:
            return "session_id"

        @staticmethod
        def add_message(role: str, content: str) -> Any:
            class MockMessage:
                role = role
                content = content
                timestamp = 0

            return MockMessage()

        @staticmethod
        def get_messages() -> list[Any]:
            return []

        @staticmethod
        def list_sessions() -> list[Any]:
            return []

        @staticmethod
        def delete_session(session_id: str) -> None:
            pass

        @staticmethod
        def load_session(session_id: str) -> bool:
            return True

    class system_tool:  # type: ignore[no-redef]
        confirmation_callback = None

    class file_tool:  # type: ignore[no-redef]
        pass

    class config_manager:  # type: ignore[no-redef]
        @staticmethod
        def load_config() -> Any:
            class MockConfig:
                auth = type(
                    "Auth",
                    (),
                    {
                        "api_key": None,
                        "provider": "zhipu",
                    },
                )()
                models = type("Models", (), {})()
                max_tokens = 4000
                temperature = 0.7
                timeout = 30

            return MockConfig()

        @staticmethod
        def save_config(config: Any) -> None:
            pass

        @staticmethod
        def is_subscription_mode() -> bool:
            return False

        @staticmethod
        def get_model_for_mode(mode: str) -> str:
            return "mock-model"


# Confirmation Dialog for Dangerous Commands
if TEXTUAL_AVAILABLE:

    class ConfirmationDialog(ModalScreen[bool]):
        """Modal dialog for confirming dangerous commands."""

        DEFAULT_CSS = """
        ConfirmationDialog {
            align: center middle;
        }

        #dialog {
            width: 60;
            height: 11;
            border: thick $warning;
            background: $surface;
        }

        #dialog-title {
            dock: top;
            height: 3;
            content-align: center middle;
            text-style: bold;
            color: $warning;
        }

        #dialog-content {
            padding: 1;
            height: auto;
        }

        #dialog-buttons {
            dock: bottom;
            height: 3;
            align: center middle;
        }

        #dialog-buttons Button {
            margin: 0 1;
        }
        """

        BINDINGS = [
            Binding("y", "confirm", "Yes", show=True),
            Binding("n", "cancel", "No", show=True),
            Binding("escape", "cancel", "Cancel", show=False),
        ]

        def __init__(self, command: str, keyword: str):
            super().__init__()
            self.command = command
            self.keyword = keyword

        def compose(self) -> ComposeResult:
            with Container(id="dialog"):
                yield Label("⚠️  DANGEROUS COMMAND DETECTED", id="dialog-title")
                yield Container(
                    Label(f"Keyword: {self.keyword}"),
                    Label(f"Command: {self.command}"),
                    Label(""),
                    Label("Do you want to proceed?"),
                    id="dialog-content",
                )
                with Horizontal(id="dialog-buttons"):
                    yield Button("Yes (y)", variant="success", id="yes")
                    yield Button("No (n)", variant="error", id="no")

        def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press."""
            if event.button.id == "yes":
                self.dismiss(True)
            else:
                self.dismiss(False)

        def action_confirm(self) -> None:
            """Confirm action."""
            self.dismiss(True)

        def action_cancel(self) -> None:
            """Cancel action."""
            self.dismiss(False)

    class OpsPilotTUI(App):
        """OpsPilot Textual TUI Application."""

        CSS_PATH = "styles.tcss"

        BINDINGS = [
            Binding("tab", "toggle_mode", "Toggle Mode", show=True),
            Binding("ctrl+s", "show_settings", "Settings", show=True),
            Binding("ctrl+n", "new_session", "New Session", show=True),
            Binding("ctrl+q", "quit", "Quit", show=True),
            Binding("f1", "show_help", "Help", show=True),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.agent = AgentCore()
            self.mode = AgentMode.PLAN
            self._setup_agent_tools()
            self._processing = False

            # Set confirmation callback for dangerous commands
            system_tool.confirmation_callback = self._show_confirmation_dialog

        def _setup_agent_tools(self) -> None:
            """Setup agent tools."""
            # Register file tools
            self.agent.register_tool(
                {
                    "name": "read_file",
                    "description": "Read file contents safely",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string"},
                            "encoding": {"type": "string", "default": "utf-8"},
                            "offset": {"type": "integer", "default": 0},
                            "limit": {"type": "integer"},
                        },
                        "required": ["file_path"],
                    },
                    "function": file_tool.read_file,
                    "requires_build_mode": False,
                }
            )

            # Register system tool
            self.agent.register_tool(
                {
                    "name": "execute_command",
                    "description": "Execute shell command securely",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {"type": "string"},
                            "timeout": {"type": "number", "default": 30.0},
                            "capture_output": {"type": "boolean", "default": True},
                            "working_directory": {"type": "string"},
                        },
                        "required": ["command"],
                    },
                    "function": system_tool.execute_command,
                    "requires_build_mode": True,
                }
            )

        def compose(self) -> ComposeResult:
            """Create UI layout."""
            yield Header()

            with Horizontal():
                # Left pane - Chat history (30%)
                with Container(id="chat-pane"):
                    yield Static("💬 Chat History", classes="pane-title")
                    yield RichLog(id="chat-history", wrap=True, highlight=True)
                    with Horizontal(id="input-container"):
                        yield Input(
                            placeholder="Type your message...", id="message-input"
                        )
                        yield Button("Send", variant="success", id="send-button")

                # Right pane - Terminal output (70%)
                with Container(id="terminal-pane"):
                    yield Static("🖥️  Terminal Output", classes="pane-title")
                    yield RichLog(id="terminal-output", wrap=True, highlight=True)

            yield Footer()

        def on_mount(self) -> None:
            """Handle mount event."""
            # Create initial session
            memory_manager.create_session("New Conversation")

            # Update footer
            self._update_footer()

            # Welcome message
            terminal = self.query_one("#terminal-output", RichLog)
            terminal.write(
                Panel(
                    "[bold green]Welcome to OpsPilot![/bold green]\n\n"
                    "🔹 Press [bold]Tab[/bold] to toggle between Plan/Build modes\n"
                    "🔹 Press [bold]Ctrl+S[/bold] for settings\n"
                    "🔹 Press [bold]Ctrl+N[/bold] for new session\n"
                    "🔹 Press [bold]F1[/bold] for help\n"
                    "🔹 Type your message and press Enter or click Send",
                    title="🚀 OpsPilot TUI",
                    border_style="green",
                )
            )

            # Show current mode
            self._log_terminal(f"Current mode: {self._get_mode_display()}")

            # Focus on input
            self.query_one("#message-input", Input).focus()

        def _update_footer(self) -> None:
            """Update footer with current status."""
            usage = self.agent.get_usage_stats()
            config = config_manager.load_config()
            model = config_manager.get_model_for_mode(self.mode.value)

            mode_display = self._get_mode_display()
            auth_status = "🔑 API Key Set" if config.auth.api_key else "❌ No API Key"

            footer_text = (
                f"{mode_display} | "
                f"Model: {model} | "
                f"{auth_status} | "
                f"Tokens: {usage['total_tokens']:,} | "
                f"Cost: ${usage['total_cost']:.4f}"
            )

            # Note: Footer text is set via the Footer widget automatically
            # We'll update it through the screen title
            self.sub_title = footer_text

        def _get_mode_display(self) -> str:
            """Get display string for current mode."""
            if self.mode == AgentMode.PLAN:
                return "📋 PLAN MODE"
            else:
                return "🔨 BUILD MODE"

        def _log_chat(self, role: str, content: str) -> None:
            """Add message to chat history."""
            chat = self.query_one("#chat-history", RichLog)

            if role == "user":
                chat.write(
                    Panel(
                        content,
                        title="👤 You",
                        border_style="blue",
                        padding=(0, 1),
                    )
                )
            elif role == "assistant":
                chat.write(
                    Panel(
                        Markdown(content),
                        title="🤖 OpsPilot",
                        border_style="green",
                        padding=(0, 1),
                    )
                )
            elif role == "tool":
                chat.write(
                    Panel(
                        content,
                        title="🔧 Tool",
                        border_style="yellow",
                        padding=(0, 1),
                    )
                )
            elif role == "system":
                chat.write(
                    Panel(
                        content,
                        title="⚙️  System",
                        border_style="red",
                        padding=(0, 1),
                    )
                )

        def _log_terminal(self, message: str, style: str = "info") -> None:
            """Add message to terminal output."""
            terminal = self.query_one("#terminal-output", RichLog)

            if style == "success":
                terminal.write(f"[bold green]✓[/bold green] {message}")
            elif style == "error":
                terminal.write(f"[bold red]✗[/bold red] {message}")
            elif style == "warning":
                terminal.write(f"[bold yellow]⚠[/bold yellow] {message}")
            else:
                terminal.write(f"[dim]•[/dim] {message}")

        async def _show_confirmation_dialog(self, command: str, keyword: str) -> bool:
            """Show confirmation dialog for dangerous commands."""
            return await self.push_screen_wait(ConfirmationDialog(command, keyword))

        async def on_button_pressed(self, event: Button.Pressed) -> None:
            """Handle button press."""
            if event.button.id == "send-button":
                await self._send_message()

        async def on_input_submitted(self, event: Input.Submitted) -> None:
            """Handle input submission."""
            if event.input.id == "message-input":
                await self._send_message()

        async def _send_message(self) -> None:
            """Send user message and get response."""
            if self._processing:
                return

            message_input = self.query_one("#message-input", Input)
            user_message = message_input.value.strip()

            if not user_message:
                return

            # Clear input
            message_input.value = ""

            # Mark as processing
            self._processing = True
            self._log_terminal("Processing message...", "info")

            try:
                # Add user message to chat
                self._log_chat("user", user_message)
                memory_manager.add_message("user", user_message)

                # Process with agent
                self._log_terminal(f"Thinking in {self.mode.value.upper()} mode...")

                response = await self.agent.process(user_message)

                # Add assistant response to chat
                self._log_chat("assistant", response)
                memory_manager.add_message("assistant", response)

                # Log to terminal
                self._log_terminal("Response generated", "success")

                # Update footer with new usage stats
                self._update_footer()

            except Exception as e:
                error_msg = f"Error: {str(e)}"
                self._log_chat("system", error_msg)
                self._log_terminal(error_msg, "error")

            finally:
                self._processing = False

        def action_toggle_mode(self) -> None:
            """Toggle between Plan and Build modes."""
            if self.mode == AgentMode.PLAN:
                self.mode = AgentMode.BUILD
                self.agent.switch_mode(AgentMode.BUILD)
            else:
                self.mode = AgentMode.PLAN
                self.agent.switch_mode(AgentMode.PLAN)

            # Log mode change
            self._log_terminal(f"Switched to {self._get_mode_display()}", "success")
            self._update_footer()

        def action_show_settings(self) -> None:
            """Show settings screen."""
            self._log_terminal("Settings screen not yet implemented", "warning")

        def action_new_session(self) -> None:
            """Create new conversation session."""
            memory_manager.create_session("New Conversation")
            self.agent.clear_history()

            # Clear chat history display
            chat = self.query_one("#chat-history", RichLog)
            chat.clear()

            # Clear terminal output
            terminal = self.query_one("#terminal-output", RichLog)
            terminal.clear()

            self._log_terminal("New session created", "success")
            self._update_footer()

        def action_show_help(self) -> None:
            """Show help information."""
            terminal = self.query_one("#terminal-output", RichLog)
            terminal.write(
                Panel(
                    """[bold]OpsPilot TUI Help[/bold]

[bold cyan]Keyboard Shortcuts:[/bold cyan]
• Tab             - Toggle between Plan/Build modes
• Ctrl+S          - Open settings
• Ctrl+N          - Create new session
• Ctrl+Q          - Quit application
• F1              - Show this help
• Enter           - Send message

[bold cyan]Modes:[/bold cyan]
• Plan Mode  (📋) - Safe planning, read-only operations
• Build Mode (🔨) - Full execution, write operations

[bold cyan]Features:[/bold cyan]
• Split-screen interface with chat and terminal output
• Automatic dangerous command detection
• Persistent conversation history
• Token usage and cost tracking

[bold cyan]Tips:[/bold cyan]
• Use Plan mode to analyze and create plans
• Switch to Build mode to execute changes
• Check the footer for usage statistics
""",
                    title="Help",
                    border_style="cyan",
                )
            )

        async def action_quit(self) -> None:
            """Quit the application."""
            self.exit()

else:
    # Fallback when Textual is not available
    class ConfirmationDialog:  # type: ignore[no-redef]
        """Confirmation dialog for dangerous commands."""

        def __init__(self, command: str, keyword: str) -> None:
            self.command = command
            self.keyword = keyword
            self.confirmed = False

        async def confirm(self) -> bool:
            """Show dialog and return confirmation result."""
            print(f"⚠️  DANGEROUS COMMAND DETECTED: {self.keyword}")
            print(f"Command: {self.command}")
            response = input("Do you want to proceed? (y/N): ").strip().lower()
            self.confirmed = response == "y"
            return self.confirmed


# Simple CLI fallback
class SimpleTUI:
    """Simple CLI-based TUI fallback."""

    def __init__(self) -> None:
        self.agent = AgentCore()
        self.mode = AgentMode.PLAN
        self._setup_agent_tools()

    def _setup_agent_tools(self) -> None:
        """Setup agent tools."""
        # Register file tools
        self.agent.register_tool(
            {
                "name": "read_file",
                "description": "Read file contents safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "encoding": {"type": "string", "default": "utf-8"},
                        "offset": {"type": "integer", "default": 0},
                        "limit": {"type": "integer"},
                    },
                    "required": ["file_path"],
                },
                "function": file_tool.read_file,
                "requires_build_mode": False,
            }
        )

        # Register system tool
        self.agent.register_tool(
            {
                "name": "execute_command",
                "description": "Execute shell command securely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"},
                        "timeout": {"type": "number", "default": 30.0},
                        "capture_output": {"type": "boolean", "default": True},
                        "working_directory": {"type": "string"},
                    },
                    "required": ["command"],
                },
                "function": system_tool.execute_command,
                "requires_build_mode": True,
            }
        )

    def run(self) -> None:
        """Run the simple CLI interface."""
        print("🤖 OpsPilot CLI Mode")
        print(
            "Commands: 'plan'/'build' to switch mode, "
            "'stats' to show usage, 'quit' to exit"
        )
        print("-" * 70)

        while True:
            try:
                # Get usage stats
                usage = self.agent.get_usage_stats()
                mode_indicator = (
                    "📋 PLAN" if self.mode == AgentMode.PLAN else "🔨 BUILD"
                )
                stats_indicator = (
                    f"TOKENS: {usage['total_tokens']} | "
                    f"COST: ${usage['total_cost']:.4f}"
                )

                user_input = input(f"{mode_indicator} [{stats_indicator}]> ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                elif user_input.lower() == "plan":
                    self.mode = AgentMode.PLAN
                    self.agent.switch_mode(self.mode)
                    print("📋 Switched to PLAN mode")

                elif user_input.lower() == "build":
                    self.mode = AgentMode.BUILD
                    self.agent.switch_mode(self.mode)
                    print("🔨 Switched to BUILD mode")

                elif user_input.lower() == "stats":
                    self._show_detailed_stats()

                else:
                    # Process message through agent
                    print("🤔 Processing...")
                    import asyncio

                    response = asyncio.run(self.agent.process(user_input))
                    print(f"🤖 {response}")

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")

    def _show_detailed_stats(self) -> None:
        """Show detailed usage statistics."""
        usage = self.agent.get_usage_stats()
        print("\n📊 Usage Statistics")
        print("=" * 30)
        print(f"Total Tokens: {usage['total_tokens']:,}")
        print(f"Total Cost: ${usage['total_cost']:.4f}")
        print(f"Requests Made: {usage['requests_count']}")
        print(f"Current Context: {usage['current_context_tokens']} tokens")
        avg_cost = usage["total_cost"] / max(usage["requests_count"], 1)
        print(f"Average Cost/Request: ${avg_cost:.4f}")
        print()


def create_app() -> Union["OpsPilotTUI", SimpleTUI]:
    """Create and return the OpsPilot application."""
    if TEXTUAL_AVAILABLE:
        return OpsPilotTUI()
    else:
        return SimpleTUI()
