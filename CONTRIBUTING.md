# Contributing to OpsPilot

Thank you for your interest in contributing to OpsPilot! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and collaborative environment for all contributors.

## Getting Started

### Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/opspilot.git
   cd opspilot
   ```

2. **Create Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Install Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Creating a Branch

Create a feature branch from `main`:

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### Making Changes

1. **Write Code**
   - Follow PEP 8 style guidelines
   - Add type hints to function signatures
   - Write clear, concise docstrings
   - Keep functions focused and testable

2. **Add Tests**
   - Write tests for new functionality
   - Ensure existing tests pass
   - Aim for high test coverage

3. **Run Tests**
   ```bash
   pytest tests/ -v
   ```

4. **Check Code Quality**
   ```bash
   # Format code
   black opspilot/ tests/

   # Check linting
   flake8 opspilot/ tests/

   # Type checking
   mypy opspilot/
   ```

### Commit Messages

Write clear, descriptive commit messages:

```
feat: add session export functionality

- Added export_session method to MemoryManager
- Support JSON, Markdown, and TXT formats
- Added tests for export functionality
```

Use conventional commit prefixes:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/changes
- `refactor:` - Code refactoring
- `style:` - Code style changes
- `chore:` - Maintenance tasks

### Submitting Changes

1. **Push to Your Fork**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create Pull Request**
   - Go to the OpsPilot repository on GitHub
   - Click "New Pull Request"
   - Select your fork and branch
   - Fill in the PR template with details about your changes

3. **Address Review Feedback**
   - Respond to reviewer comments
   - Make requested changes
   - Push updates to your branch

## Code Style Guidelines

### Python Code

- Follow PEP 8 style guide
- Use Black for code formatting (line length: 88)
- Use type hints for function parameters and returns
- Write descriptive docstrings (Google style)

Example:
```python
def process_command(
    command: str, timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Execute a shell command securely.

    Args:
        command: Shell command to execute
        timeout: Maximum execution time in seconds

    Returns:
        Dictionary with execution results including stdout, stderr, and return code

    Raises:
        ValueError: If command is empty or invalid
    """
    # Implementation here
```

### Documentation

- Keep README.md up to date
- Document new features in docstrings
- Add examples for complex functionality
- Update CHANGELOG.md with notable changes

## Testing Guidelines

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_<module_name>.py`
- Use descriptive test function names
- Include docstrings explaining what each test does
- Use fixtures for common setup

Example:
```python
import pytest
from opspilot.agent.core import AgentCore

@pytest.fixture
def agent():
    """Create an AgentCore instance for testing."""
    return AgentCore()

def test_mode_switching(agent):
    """Test that agent can switch between Plan and Build modes."""
    assert agent.mode == AgentMode.PLAN
    agent.switch_mode(AgentMode.BUILD)
    assert agent.mode == AgentMode.BUILD
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=opspilot --cov-report=html

# Run specific test file
pytest tests/test_agent_core.py

# Run specific test
pytest tests/test_agent_core.py::test_mode_switching
```

## Project Structure

```
opspilot/
├── opspilot/
│   ├── __init__.py
│   ├── main.py           # CLI entry point
│   ├── config.py         # Configuration management
│   ├── agent/
│   │   ├── core.py       # Agent Think-Act loop
│   │   ├── memory.py     # Session management
│   │   └── tools/
│   │       ├── system.py # Shell execution
│   │       └── files.py  # File operations
│   └── tui/
│       ├── app.py        # TUI application
│       └── screens.py    # Modal dialogs
├── tests/                # Test suite
├── .github/
│   └── workflows/        # CI/CD workflows
└── docs/                 # Documentation
```

## Adding New Features

### Adding a New Tool

1. Create tool function in appropriate module
2. Add tool definition with parameters
3. Register tool with agent
4. Add tests for the tool
5. Document tool usage

### Adding a New Command

1. Add command function to `main.py`
2. Use Typer decorators for CLI integration
3. Add help text and examples
4. Add tests for the command
5. Update README with usage

## Release Process

Releases are automated via GitHub Actions:

1. Update version in `opspilot/__init__.py`
2. Update CHANGELOG.md
3. Create and push a version tag:
   ```bash
   git tag -a v0.2.0 -m "Release v0.2.0"
   git push origin v0.2.0
   ```
4. GitHub Actions will build and publish to PyPI

## Getting Help

- **Questions**: Open a [Discussion](https://github.com/cyber-goka/opspilot/discussions)
- **Bugs**: Open an [Issue](https://github.com/cyber-goka/opspilot/issues)
- **Features**: Open an [Issue](https://github.com/cyber-goka/opspilot/issues) with feature request

## Recognition

Contributors will be recognized in:
- CHANGELOG.md for their contributions
- README.md contributors section
- GitHub contributors page

Thank you for contributing to OpsPilot!
