"""
OpsPilot Main Entry Point

CLI application entry point using Typer.
Provides command-line interface for OpsPilot DevOps assistant.
"""

import asyncio
import sys
from typing import Optional
from pathlib import Path

try:
    import typer
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    TYPER_AVAILABLE = True
except ImportError:
    TYPER_AVAILABLE = False
    print("Error: Typer is required. Install with: pip install typer rich")
    sys.exit(1)

# Import our modules
try:
    from opspilot.tui.app import create_app
    from opspilot.config import config_manager
    from opspilot.agent.memory import memory_manager
    from opspilot.agent.core import AgentMode
except ImportError as e:
    print(f"Import error: {e}")
    print("Please install OpsPilot properly: pip install -e .")
    sys.exit(1)

# Create Typer app
app = typer.Typer(
    name="opspilot",
    help="OpsPilot - AI-powered DevOps assistant",
    add_completion=False,
    no_args_is_help=True,
)

# Console for rich output
console = Console()


@app.command()
def start(
    session: Optional[str] = typer.Option(
        None, "--session", "-s", help="Session ID to load"
    ),
    mode: str = typer.Option(
        "plan", "--mode", "-m", help="Start mode (plan or build)", show_choices=True
    ),
    config_file: Optional[str] = typer.Option(
        None, "--config", "-c", help="Custom config file path"
    ),
) -> None:
    """
    Start OpsPilot TUI application.

    This launches the main Textual-based user interface with split-screen
    layout for chat history and terminal output.
    """
    try:
        # Validate mode
        if mode.lower() not in ["plan", "build"]:
            console.print(
                Panel(
                    Text("❌ Invalid mode. Use 'plan' or 'build'", style="red"),
                    title="Error",
                    border_style="red",
                )
            )
            raise typer.Exit(1)

        # Load custom config if specified
        if config_file:
            config_path = Path(config_file)
            if not config_path.exists():
                console.print(
                    Panel(
                        Text(f"❌ Config file not found: {config_file}", style="red"),
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

            # Update config manager to use custom file
            config_manager.config_file = config_path

        # Load session if specified
        if session:
            if not memory_manager.load_session(session):
                console.print(
                    Panel(
                        Text(f"❌ Session not found: {session}", style="red"),
                        title="Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(1)

        # Create and run app
        console.print(
            Panel(
                Text("🚀 Starting OpsPilot...", style="green"),
                title="OpsPilot",
                border_style="green",
            )
        )

        # Create app instance
        app_instance = create_app()

        # Set initial mode
        if hasattr(app_instance, "agent"):
            target_mode = AgentMode.PLAN if mode.lower() == "plan" else AgentMode.BUILD
            app_instance.agent.switch_mode(target_mode)
            if hasattr(app_instance, "mode"):
                app_instance.mode = target_mode

        # Run the app
        if hasattr(app_instance, "run"):
            app_instance.run()
        else:
            # Fallback for simple CLI mode
            app_instance.run()

    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    except Exception as e:
        console.print(
            Panel(
                Text(f"❌ Error starting OpsPilot: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def config(
    show: bool = typer.Option(False, "--show", "-s", help="Show current configuration"),
    edit: bool = typer.Option(False, "--edit", "-e", help="Edit configuration"),
    reset: bool = typer.Option(
        False, "--reset", "-r", help="Reset configuration to defaults"
    ),
) -> None:
    """
    Manage OpsPilot configuration.

    View, edit, or reset the configuration file containing
    API keys, model settings, and application preferences.
    """
    try:
        if show:
            config_data = config_manager.load_config()

            # Display configuration
            config_text = []
            config_text.append("📋 OpsPilot Configuration")
            config_text.append("=" * 40)

            # Authentication
            config_text.append("\n🔐 Authentication:")
            config_text.append(f"  Provider: {config_data.auth.provider}")
            config_text.append(
                f"  API Key: {'*' * 20 if config_data.auth.api_key else 'Not set'}"
            )

            # Models
            config_text.append(f"\n🤖 Models:")
            provider = config_data.auth.provider
            config_text.append(
                f"  Plan Model ({provider}): {config_manager.get_model_for_mode('plan')}"
            )
            config_text.append(
                f"  Build Model ({provider}): {config_manager.get_model_for_mode('build')}"
            )

            # Settings
            config_text.append(f"\n⚙️  Settings:")
            config_text.append(f"  Max Tokens: {config_data.max_tokens}")
            config_text.append(f"  Temperature: {config_data.temperature}")
            config_text.append(f"  Timeout: {config_data.timeout}s")

            console.print(
                Panel(
                    Text("\n".join(config_text)),
                    title="Configuration",
                    border_style="blue",
                )
            )

        elif edit:
            config_file = config_manager.config_file
            console.print(
                Panel(
                    Text(f"📝 Opening config file: {config_file}", style="yellow"),
                    title="Edit Configuration",
                    border_style="yellow",
                )
            )

            # Try to open with default editor
            import os

            editor = os.getenv("EDITOR", "nano")
            os.system(f"{editor} {config_file}")

        elif reset:
            if typer.confirm("⚠️  This will reset all configuration. Are you sure?"):
                # Remove config file
                config_file = config_manager.config_file
                if config_file.exists():
                    config_file.unlink()

                # Reload defaults
                config_manager.load_config()

                console.print(
                    Panel(
                        Text("✅ Configuration reset to defaults", style="green"),
                        title="Reset Complete",
                        border_style="green",
                    )
                )
            else:
                console.print("❌ Reset cancelled")

        else:
            console.print(
                Panel(
                    Text("Use --show, --edit, or --reset", style="yellow"),
                    title="Configuration",
                    border_style="yellow",
                )
            )

    except Exception as e:
        console.print(
            Panel(
                Text(f"❌ Error managing configuration: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def sessions(
    list: bool = typer.Option(True, "--list", "-l", help="List all sessions"),
    delete: Optional[str] = typer.Option(
        None, "--delete", "-d", help="Delete session by ID"
    ),
    export: Optional[str] = typer.Option(
        None, "--export", "-e", help="Export session by ID"
    ),
    format: str = typer.Option(
        "json",
        "--format",
        "-f",
        help="Export format (json, markdown, txt)",
        show_choices=True,
    ),
) -> None:
    """
    Manage conversation sessions.

    List, delete, or export conversation sessions.
    """
    try:
        if list:
            sessions = memory_manager.list_sessions()

            if not sessions:
                console.print(
                    Panel(
                        Text("No sessions found", style="yellow"),
                        title="Sessions",
                        border_style="yellow",
                    )
                )
                return

            # Display sessions
            session_text = []
            session_text.append("📚 Conversation Sessions")
            session_text.append("=" * 40)

            for i, session in enumerate(sessions, 1):
                import datetime

                created = datetime.datetime.fromtimestamp(session["created_at"])
                updated = datetime.datetime.fromtimestamp(session["updated_at"])

                session_text.append(f"\n{i}. {session['title']}")
                session_text.append(f"   ID: {session['id']}")
                session_text.append(f"   Messages: {session['message_count']}")
                session_text.append(f"   Created: {created.strftime('%Y-%m-%d %H:%M')}")
                session_text.append(f"   Updated: {updated.strftime('%Y-%m-%d %H:%M')}")

            console.print(
                Panel(
                    Text("\n".join(session_text)), title="Sessions", border_style="blue"
                )
            )

        elif delete:
            if memory_manager.delete_session(delete):
                console.print(
                    Panel(
                        Text(f"✅ Session deleted: {delete}", style="green"),
                        title="Delete Complete",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        Text(f"❌ Session not found: {delete}", style="red"),
                        title="Error",
                        border_style="red",
                    )
                )

        elif export:
            content = memory_manager.export_session(export, format)
            if content:
                # Save to file
                filename = f"session_{export}.{format}"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)

                console.print(
                    Panel(
                        Text(f"✅ Session exported to: {filename}", style="green"),
                        title="Export Complete",
                        border_style="green",
                    )
                )
            else:
                console.print(
                    Panel(
                        Text(f"❌ Session not found: {export}", style="red"),
                        title="Error",
                        border_style="red",
                    )
                )

        else:
            console.print(
                Panel(
                    Text("Use --list, --delete, or --export", style="yellow"),
                    title="Sessions",
                    border_style="yellow",
                )
            )

    except Exception as e:
        console.print(
            Panel(
                Text(f"❌ Error managing sessions: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def stats() -> None:
    """Show usage statistics."""
    try:
        from .agent.core import agent_core

        usage = agent_core.get_usage_stats()

        stats_text = []
        stats_text.append("📊 Usage Statistics")
        stats_text.append("=" * 30)
        stats_text.append(f"Total Tokens Used: {usage['total_tokens']:,}")
        stats_text.append(f"Total Cost: ${usage['total_cost']:.4f}")
        stats_text.append(f"API Requests: {usage['requests_count']}")
        stats_text.append(f"Current Context: {usage['current_context_tokens']} tokens")

        if usage["requests_count"] > 0:
            avg_cost = usage["total_cost"] / usage["requests_count"]
            stats_text.append(f"Average Cost/Request: ${avg_cost:.4f}")

        console.print(
            Panel(
                Text("\n".join(stats_text)),
                title="Usage Statistics",
                border_style="blue",
            )
        )

    except Exception as e:
        console.print(
            Panel(
                Text(f"❌ Error getting statistics: {str(e)}", style="red"),
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Show OpsPilot version information."""
    try:
        # Try to get version from package
        try:
            from . import __version__

            version = __version__
        except ImportError:
            version = "0.1.0"

        console.print(
            Panel(
                Text(f"OpsPilot v{version}", style="green"),
                title="Version",
                border_style="green",
            )
        )

    except Exception as e:
        console.print(f"Error getting version: {str(e)}")
        raise typer.Exit(1)


@app.callback()
def main(
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose output"
    ),
) -> None:
    """
    OpsPilot - AI-powered DevOps assistant.

    A sophisticated CLI tool for DevOps operations with AI assistance.
    Features Plan/Build modes, secure command execution, and
    conversation history management.
    """
    if verbose:
        import logging

        logging.basicConfig(level=logging.DEBUG)
        console.print("🔧 Verbose mode enabled")


def main_cli():
    """Main entry point for CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!")
    except Exception as e:
        console.print(f"❌ Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()
