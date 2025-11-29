"""
OpsPilot File Tools

File reading, writing, and directory operations for the agent.
Provides secure file access with proper error handling.
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import mimetypes
import json
import yaml


class FileTool:
    """File operations tool for the agent."""

    def __init__(self, base_path: Optional[str] = None):
        """
        Initialize file tool.

        Args:
            base_path: Base path for file operations (default: current directory)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

        # Restricted paths for security
        self.restricted_paths = {
            "/etc",
            "/sys",
            "/proc",
            "/dev",
            "/boot",
            "/root",
            "/var/log",
            "/var/lib",
            "/usr/bin",
            "/usr/sbin",
            "/bin",
            "/sbin",
        }

    async def read_file(
        self,
        file_path: str,
        encoding: str = "utf-8",
        offset: int = 0,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Read file contents safely.

        Args:
            file_path: Path to the file to read
            encoding: File encoding (default: utf-8)
            offset: Line offset to start reading from
            limit: Maximum number of lines to read

        Returns:
            Dictionary with file contents and metadata
        """
        try:
            full_path = self._resolve_path(file_path)

            # Security check
            if not self._is_path_safe(full_path):
                return {
                    "success": False,
                    "error": "Access denied - path is restricted",
                    "file_path": file_path,
                }

            # Check if file exists
            if not full_path.exists():
                return {
                    "success": False,
                    "error": "File not found",
                    "file_path": file_path,
                }

            # Check if it's a file
            if not full_path.is_file():
                return {
                    "success": False,
                    "error": "Path is not a file",
                    "file_path": file_path,
                }

            # Get file info
            file_info = self._get_file_info(full_path)

            # Read file content
            if file_info["size"] > 10 * 1024 * 1024:  # 10MB limit
                return {
                    "success": False,
                    "error": "File too large (max 10MB)",
                    "file_path": file_path,
                    "file_info": file_info,
                }

            # Determine if file is binary
            if self._is_binary_file(full_path):
                with open(full_path, "rb") as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "encoding": "binary",
                    "file_info": file_info,
                    "file_path": file_path,
                }

            # Read text file
            with open(full_path, "r", encoding=encoding, errors="replace") as f:
                lines = f.readlines()

            # Apply offset and limit
            if offset > 0 or limit is not None:
                end = (offset + limit) if limit else None
                lines = lines[offset:end]

            content = "".join(lines)

            return {
                "success": True,
                "content": content,
                "encoding": encoding,
                "lines_read": len(lines),
                "total_lines": len(
                    open(
                        full_path, "r", encoding=encoding, errors="replace"
                    ).readlines()
                ),
                "file_info": file_info,
                "file_path": file_path,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "file_path": file_path}

    async def write_file(
        self,
        file_path: str,
        content: Union[str, bytes],
        encoding: str = "utf-8",
        create_dirs: bool = True,
        backup: bool = True,
    ) -> Dict[str, Any]:
        """
        Write content to file safely.

        Args:
            file_path: Path to the file to write
            content: Content to write (string or bytes)
            encoding: File encoding for text content (default: utf-8)
            create_dirs: Create parent directories if they don't exist
            backup: Create backup of existing file

        Returns:
            Dictionary with operation result
        """
        try:
            full_path = self._resolve_path(file_path)

            # Security check
            if not self._is_path_safe(full_path):
                return {
                    "success": False,
                    "error": "Access denied - path is restricted",
                    "file_path": file_path,
                }

            # Create parent directories if needed
            if create_dirs:
                full_path.parent.mkdir(parents=True, exist_ok=True)

            # Create backup if file exists
            backup_path = None
            if backup and full_path.exists():
                backup_path = full_path.with_suffix(full_path.suffix + ".backup")
                shutil.copy2(full_path, backup_path)

            # Write content
            if isinstance(content, bytes):
                with open(full_path, "wb") as f:
                    f.write(content)
                encoding_used = "binary"
            else:
                with open(full_path, "w", encoding=encoding) as f:
                    f.write(content)
                encoding_used = encoding

            return {
                "success": True,
                "file_path": file_path,
                "encoding": encoding_used,
                "bytes_written": len(content)
                if isinstance(content, bytes)
                else len(content.encode(encoding)),
                "backup_path": str(backup_path) if backup_path else None,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "file_path": file_path}

    async def list_directory(
        self, dir_path: str = ".", show_hidden: bool = False, recursive: bool = False
    ) -> Dict[str, Any]:
        """
        List directory contents.

        Args:
            dir_path: Directory path to list
            show_hidden: Include hidden files
            recursive: List recursively

        Returns:
            Dictionary with directory listing
        """
        try:
            full_path = self._resolve_path(dir_path)

            # Security check
            if not self._is_path_safe(full_path):
                return {
                    "success": False,
                    "error": "Access denied - path is restricted",
                    "dir_path": dir_path,
                }

            if not full_path.exists():
                return {
                    "success": False,
                    "error": "Directory not found",
                    "dir_path": dir_path,
                }

            if not full_path.is_dir():
                return {
                    "success": False,
                    "error": "Path is not a directory",
                    "dir_path": dir_path,
                }

            items = []

            if recursive:
                for item in full_path.rglob("*"):
                    if not show_hidden and item.name.startswith("."):
                        continue
                    items.append(self._get_item_info(item))
            else:
                for item in full_path.iterdir():
                    if not show_hidden and item.name.startswith("."):
                        continue
                    items.append(self._get_item_info(item))

            return {
                "success": True,
                "dir_path": dir_path,
                "items": items,
                "total_items": len(items),
            }

        except Exception as e:
            return {"success": False, "error": str(e), "dir_path": dir_path}

    async def delete_file(
        self, file_path: str, confirm: bool = False
    ) -> Dict[str, Any]:
        """
        Delete a file or directory.

        Args:
            file_path: Path to delete
            confirm: Confirmation flag (must be True for deletion)

        Returns:
            Dictionary with operation result
        """
        if not confirm:
            return {
                "success": False,
                "error": "Deletion requires explicit confirmation",
                "file_path": file_path,
            }

        try:
            full_path = self._resolve_path(file_path)

            # Security check
            if not self._is_path_safe(full_path):
                return {
                    "success": False,
                    "error": "Access denied - path is restricted",
                    "file_path": file_path,
                }

            if not full_path.exists():
                return {
                    "success": False,
                    "error": "Path not found",
                    "file_path": file_path,
                }

            if full_path.is_file():
                full_path.unlink()
                deleted_type = "file"
            elif full_path.is_dir():
                shutil.rmtree(full_path)
                deleted_type = "directory"
            else:
                return {
                    "success": False,
                    "error": "Unknown path type",
                    "file_path": file_path,
                }

            return {
                "success": True,
                "file_path": file_path,
                "deleted_type": deleted_type,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "file_path": file_path}

    def _resolve_path(self, file_path: str) -> Path:
        """Resolve file path relative to base path."""
        path = Path(file_path)
        if not path.is_absolute():
            path = self.base_path / path
        return path.resolve()

    def _is_path_safe(self, path: Path) -> bool:
        """Check if path is safe for access."""
        path_str = str(path)

        # Check against restricted paths
        for restricted in self.restricted_paths:
            if path_str.startswith(restricted):
                return False

        # Ensure path doesn't try to go above base path
        try:
            path.relative_to(self.base_path)
        except ValueError:
            # Path is outside base path, but might still be safe
            # Allow user home directory and temp directory
            allowed_prefixes = ["/home/", "/tmp/", "/var/tmp/"]
            if not any(path_str.startswith(prefix) for prefix in allowed_prefixes):
                return False

        return True

    def _get_file_info(self, path: Path) -> Dict[str, Any]:
        """Get file metadata."""
        stat = path.stat()

        return {
            "size": stat.st_size,
            "modified": stat.st_mtime,
            "created": stat.st_ctime,
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "mime_type": mimetypes.guess_type(str(path))[0] or "unknown",
            "extension": path.suffix,
        }

    def _get_item_info(self, path: Path) -> Dict[str, Any]:
        """Get item info for directory listing."""
        info = self._get_file_info(path)
        info.update(
            {
                "name": path.name,
                "path": str(path),
                "relative_path": str(path.relative_to(self.base_path)),
            }
        )
        return info

    def _is_binary_file(self, path: Path) -> bool:
        """Check if file is binary."""
        try:
            with open(path, "rb") as f:
                chunk = f.read(1024)
                return b"\0" in chunk
        except Exception:
            return True


# Tool definitions for agent integration
def get_file_tool_definitions() -> List[Dict[str, Any]]:
    """Get tool definitions for file operations."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read file contents safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8",
                        },
                        "offset": {
                            "type": "integer",
                            "description": "Line offset to start reading from",
                            "default": 0,
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of lines to read",
                        },
                    },
                    "required": ["file_path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Write content to file safely",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write",
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file",
                        },
                        "encoding": {
                            "type": "string",
                            "description": "File encoding (default: utf-8)",
                            "default": "utf-8",
                        },
                        "create_dirs": {
                            "type": "boolean",
                            "description": "Create parent directories if needed",
                            "default": True,
                        },
                        "backup": {
                            "type": "boolean",
                            "description": "Create backup of existing file",
                            "default": True,
                        },
                    },
                    "required": ["file_path", "content"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "List directory contents",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "dir_path": {
                            "type": "string",
                            "description": "Directory path to list",
                            "default": ".",
                        },
                        "show_hidden": {
                            "type": "boolean",
                            "description": "Include hidden files",
                            "default": False,
                        },
                        "recursive": {
                            "type": "boolean",
                            "description": "List recursively",
                            "default": False,
                        },
                    },
                    "required": [],
                },
            },
        },
    ]


# Global file tool instance
file_tool = FileTool()
