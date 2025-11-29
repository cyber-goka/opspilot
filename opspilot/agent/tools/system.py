"""
OpsPilot System Tools

Secure subprocess execution with safety gates and confirmation dialogs.
Provides shell command execution capabilities for DevOps tasks.
"""

import asyncio
import subprocess
import shlex
from typing import Dict, Any, Optional, List, Callable, Awaitable
from pathlib import Path
import os


class SystemTool:
    """Secure system tool for subprocess execution."""

    def __init__(
        self,
        confirmation_callback: Optional[Callable[[str, str], Awaitable[bool]]] = None,
    ):
        """
        Initialize system tool.

        Args:
            confirmation_callback: Function to call for dangerous command confirmation
        """
        self.confirmation_callback = confirmation_callback
        self.running_processes: Dict[str, subprocess.Popen] = {}

        # Dangerous command keywords
        self.dangerous_keywords = {
            "rm",
            "delete",
            "del",
            "format",
            "fdisk",
            "mkfs",
            "systemctl",
            "service",
            "init",
            "shutdown",
            "reboot",
            "kubectl",
            "helm",
            "docker rm",
            "docker kill",
            "chmod 777",
            "chown",
            "sudo",
            "su",
            "passwd",
            "crontab",
            "at",
            "batch",
            "nohup",
        }

    async def execute_command(
        self,
        command: str,
        timeout: float = 30.0,
        capture_output: bool = True,
        working_directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a shell command securely.

        Args:
            command: Command to execute
            timeout: Command timeout in seconds
            capture_output: Whether to capture stdout/stderr
            working_directory: Directory to execute command in

        Returns:
            Dictionary with execution results
        """
        # Ensure timeout is a float
        timeout = float(timeout)

        # Safety check
        if not await self._safety_check(command):
            return {
                "success": False,
                "error": "Command blocked by safety check",
                "command": command,
            }

        try:
            # Prepare command
            if isinstance(command, str):
                args = shlex.split(command)
            else:
                args = [str(arg) for arg in command]  # type: ignore[unreachable]

            # Set working directory
            cwd = Path(working_directory) if working_directory else Path.cwd()

            # Execute command
            if capture_output:
                result = await asyncio.wait_for(
                    self._capture_output(args, cwd), timeout=timeout
                )
            else:
                result = await asyncio.wait_for(
                    self._interactive_execution(args, cwd), timeout=timeout
                )

            return result

        except asyncio.TimeoutError:
            return {
                "success": False,
                "error": f"Command timed out after {timeout} seconds",
                "command": command,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "command": command}

    async def _safety_check(self, command: str) -> bool:
        """
        Perform safety check on command.

        Args:
            command: Command to check

        Returns:
            True if command is safe, False otherwise
        """
        command_lower = command.lower()

        # Check for dangerous keywords
        for keyword in self.dangerous_keywords:
            if keyword in command_lower:
                # Request confirmation
                if self.confirmation_callback:
                    return await self._request_confirmation(command, keyword)
                else:
                    # Log warning but allow
                    return True

        return True

    async def _request_confirmation(self, command: str, keyword: str) -> bool:
        """
        Request user confirmation for dangerous command.

        Args:
            command: The dangerous command
            keyword: The dangerous keyword that was detected

        Returns:
            True if user confirms, False otherwise
        """
        if self.confirmation_callback:
            return await self.confirmation_callback(command, keyword)

        # Default to safe behavior
        return False

    async def _capture_output(self, args: List[str], cwd: Path) -> Dict[str, Any]:
        """Execute command and capture output."""
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": stdout.decode("utf-8", errors="replace"),
                "stderr": stderr.decode("utf-8", errors="replace"),
                "command": " ".join(args) if hasattr(shlex, "join") else " ".join(args),
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(args) if hasattr(shlex, "join") else " ".join(args),
            }

    async def _interactive_execution(
        self, args: List[str], cwd: Path
    ) -> Dict[str, Any]:
        """Execute command interactively."""
        try:
            process = await asyncio.create_subprocess_exec(*args, cwd=cwd)

            await process.communicate()

            return {
                "success": process.returncode == 0,
                "return_code": process.returncode,
                "stdout": "",
                "stderr": "",
                "command": " ".join(args) if hasattr(shlex, "join") else " ".join(args),
            }
        except Exception as e:
            return {
                "success": False,
                "return_code": -1,
                "stdout": "",
                "stderr": str(e),
                "command": " ".join(args) if hasattr(shlex, "join") else " ".join(args),
            }

    async def kill_process(self, process_id: str) -> bool:
        """
        Kill a running process.

        Args:
            process_id: ID of the process to kill

        Returns:
            True if successful, False otherwise
        """
        if process_id not in self.running_processes:
            return False

        try:
            process = self.running_processes[process_id]
            process.terminate()

            # Wait for graceful termination
            import time

            start_time = time.time()
            while time.time() - start_time < 5.0:
                if process.poll() is not None:
                    break
                await asyncio.sleep(0.1)

            if process.poll() is None:
                # Force kill if still running
                process.kill()
                # Wait a bit more for the kill to take effect
                await asyncio.sleep(0.5)

            del self.running_processes[process_id]
            return True

        except Exception:
            return False

    def get_process_list(self) -> List[Dict[str, Any]]:
        """Get list of running processes."""
        return [
            {
                "id": pid,
                "command": " ".join(process.args),  # type: ignore[arg-type]
                "pid": process.pid,
            }
            for pid, process in self.running_processes.items()
        ]

    async def check_command_exists(self, command: str) -> bool:
        """
        Check if a command exists on the system.

        Args:
            command: Command to check

        Returns:
            True if command exists, False otherwise
        """
        try:
            result = await asyncio.create_subprocess_exec(
                "which",
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await result.communicate()
            return result.returncode == 0
        except Exception:
            return False

    def get_system_info(self) -> Dict[str, Any]:
        """Get basic system information."""
        return {
            "platform": os.name,
            "cwd": str(Path.cwd()),
            "home": str(Path.home()),
            "user": os.getenv("USER", "unknown"),
            "shell": os.getenv("SHELL", "unknown"),
        }


# Tool definition for agent integration
def get_system_tool_definition() -> Dict[str, Any]:
    """Get tool definition for system operations."""
    return {
        "type": "function",
        "function": {
            "name": "execute_command",
            "description": "Execute a shell command securely with safety checks",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Shell command to execute",
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Command timeout in seconds (default: 30)",
                        "default": 30.0,
                    },
                    "capture_output": {
                        "type": "boolean",
                        "description": "Whether to capture command output (default: true)",
                        "default": True,
                    },
                    "working_directory": {
                        "type": "string",
                        "description": "Directory to execute command in (default: current directory)",
                    },
                },
                "required": ["command"],
            },
        },
    }


# Global system tool instance
system_tool = SystemTool()
