"""
OpsPilot TUI Application

Simple CLI interface - Textual TUI support coming soon.
"""

# Import our modules
try:
    from opspilot.agent.core import AgentCore, AgentMode
    from opspilot.agent.memory import memory_manager
    from opspilot.agent.tools.system import system_tool
    from opspilot.agent.tools.files import file_tool
    from opspilot.config import config_manager
except ImportError:
    # Fallback for development
    class AgentMode:
        PLAN = "plan"
        BUILD = "build"

    class AgentCore:
        def __init__(self):
            self.mode = AgentMode.PLAN
            self.usage_stats = {
                "total_tokens": 0,
                "total_cost": 0.0,
                "requests_count": 0,
                "current_context_tokens": 0,
            }

        def switch_mode(self, mode):
            self.mode = mode

        def register_tool(self, tool):
            pass

        async def process(self, message):
            # Simulate some usage
            self.usage_stats["total_tokens"] += len(message.split()) * 10
            self.usage_stats["total_cost"] += 0.001
            self.usage_stats["requests_count"] += 1
            self.usage_stats["current_context_tokens"] = len(message.split()) * 5
            return f"Mock response to: {message}"

        def get_usage_stats(self):
            return self.usage_stats.copy()

    class memory_manager:
        @staticmethod
        def create_session(title):
            return "session_id"

        @staticmethod
        def add_message(role, content):
            class MockMessage:
                role = role
                content = content
                timestamp = 0

            return MockMessage()

        @staticmethod
        def get_messages():
            return []

        @staticmethod
        def list_sessions():
            return []

        @staticmethod
        def delete_session(session_id):
            pass

        @staticmethod
        def load_session(session_id):
            return True

    class system_tool:
        confirmation_callback = None

    class file_tool:
        pass

    class config_manager:
        @staticmethod
        def load_config():
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
        def save_config(config):
            pass

        @staticmethod
        def is_subscription_mode():
            return False

        @staticmethod
        def get_model_for_mode(mode):
            return "mock-model"


class ConfirmationDialog:
    """Confirmation dialog for dangerous commands."""

    def __init__(self, command: str, keyword: str):
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


class SimpleTUI:
    """Simple CLI-based TUI fallback."""

    def __init__(self):
        self.agent = AgentCore()
        self.mode = AgentMode.PLAN
        self._setup_agent_tools()

    def _setup_agent_tools(self):
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

    def run(self):
        """Run the simple CLI interface."""
        print("🤖 OpsPilot CLI Mode")
        print(
            "Commands: 'plan'/'build' to switch mode, 'stats' to show usage, 'quit' to exit"
        )
        print("-" * 70)

        while True:
            try:
                # Get usage stats
                usage = self.agent.get_usage_stats()
                mode_indicator = (
                    "📋 PLAN" if self.mode == AgentMode.PLAN else "🔨 BUILD"
                )
                stats_indicator = f"TOKENS: {usage['total_tokens']} | COST: ${usage['total_cost']:.4f}"

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

    def _show_detailed_stats(self):
        """Show detailed usage statistics."""
        usage = self.agent.get_usage_stats()
        print("\n📊 Usage Statistics")
        print("=" * 30)
        print(f"Total Tokens: {usage['total_tokens']:,}")
        print(f"Total Cost: ${usage['total_cost']:.4f}")
        print(f"Requests Made: {usage['requests_count']}")
        print(f"Current Context: {usage['current_context_tokens']} tokens")
        print(
            f"Average Cost/Request: ${usage['total_cost'] / max(usage['requests_count'], 1):.4f}"
        )
        print()


def create_app():
    """Create and return the OpsPilot application."""
    return SimpleTUI()
