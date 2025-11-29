# OpsPilot - AI-powered DevOps Assistant

[![Tests](https://github.com/your-org/opspilot/workflows/Tests/badge.svg)](https://github.com/your-org/opspilot/actions)
[![Lint](https://github.com/your-org/opspilot/workflows/Lint/badge.svg)](https://github.com/your-org/opspilot/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

OpsPilot is a sophisticated CLI tool for DevOps operations with AI assistance, similar to OpenCode or Claude Code but specialized for DevOps tasks.

> **Note**: This project is in active development. The full TUI interface is planned but currently uses a simple CLI interface.

## Features

### 🔧 Simple Authentication
- Choose your AI provider (OpenAI, ZhipuAI, Anthropic, or OpenRouter)
- Provide your API key for the selected provider
- Automatic model selection for Plan/Build modes
- **OpenRouter**: Access to 100+ models from various providers

### 📋 Plan Mode vs Build Mode
- **Plan Mode**: Safe planning with reasoning models (GLM-4-Plus, GPT-4)
- **Build Mode**: Action-oriented with fast models (GLM-4-Flash, GPT-3.5)
- Toggle between modes with Tab key

### 🖥️ Split-Screen TUI Interface
- **Left Pane (30%)**: Chat history with user/AI messages
- **Right Pane (70%)**: Terminal output, logs, and markdown rendering
- **Footer**: Current mode, model name, authentication status, token usage, and cost

### 🛡️ Safety Gates
- Automatic detection of dangerous commands (`rm`, `kubectl apply`, `systemctl`, etc.)
- Confirmation dialogs before executing risky operations
- Secure subprocess execution with timeout controls

### 💾 Session Management
- Persistent conversation history
- Export sessions (JSON, Markdown, TXT)
- Session search and organization

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/opspilot.git
cd opspilot

# Install OpsPilot
pip install -e .
```

Or use the installation script:

```bash
python install.py
```

## Quick Start

```bash
# Install OpsPilot
pip install -e .

# Configure your API key (first time setup)
opspilot config --edit

# Start the TUI application
opspilot start

# Start with specific mode
opspilot start --mode build

# Load existing session
opspilot start --session <session-id>

# View configuration
opspilot config --show

# List sessions
opspilot sessions --list

# Show usage statistics
opspilot stats
```

## Configuration

OpsPilot uses `~/.opspilot/config.yaml` for configuration:

### Configuration Example
```yaml
auth:
  provider: zhipu  # Choose: openai, zhipu, anthropic, or openrouter
  api_key: your-api-key-here
```

**Note**: When using OpenRouter, you get access to models from multiple providers through a single API key. Popular models include GPT-4, Claude, Gemini, and many others.

### Environment Variables

You can also set configuration via environment variables:

```bash
export OPSPILOT_API_KEY="your-api-key"
export OPSPILOT_PROVIDER="zhipu"  # openai, zhipu, anthropic, or openrouter
```

### Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **ZhipuAI**: https://open.bigmodel.cn/
- **Anthropic**: https://console.anthropic.com/
- **OpenRouter**: https://openrouter.ai/keys (provides access to 100+ models)

## Usage Examples

### Plan Mode - Safe Planning
```
User: Help me deploy a Django application to Kubernetes

Assistant: I'll help you plan the Django deployment to Kubernetes. Let me analyze your current setup first.

[Reads Dockerfile, requirements.txt, current directory structure]

Based on my analysis, here's your deployment plan:

## Phase 1: Container Preparation
1. Optimize Dockerfile for production
2. Create .dockerignore file
3. Build and test container locally

## Phase 2: Kubernetes Manifests
1. Create Deployment manifest
2. Create Service manifest
3. Create Ingress configuration
4. Add ConfigMaps for environment variables

## Phase 3: Deployment Strategy
1. Create namespace
2. Apply ConfigMaps first
3. Deploy application
4. Configure monitoring

Switch to Build Mode (Ctrl+T) to execute this plan.
```

### Build Mode - Action Execution
```
User: Create the Kubernetes deployment manifest

Assistant: I'll create a Kubernetes deployment manifest for your Django application.

[Creates deployment.yaml with optimized settings]

✅ Created deployment.yaml with:
- 3 replicas with rolling updates
- Resource limits and requests
- Health checks configured
- Environment variables from ConfigMap

The deployment is ready. Would you like me to apply it to the cluster?
```

## CLI Commands

### Start Application
```bash
opspilot start [OPTIONS]
  --session, -s TEXT    Session ID to load
  --mode, -m TEXT       Start mode (plan|build)
  --config, -c TEXT      Custom config file path
```

### Configuration Management
```bash
opspilot config [OPTIONS]
  --show, -s           Show current configuration
  --edit, -e           Edit configuration file
  --reset, -r           Reset to defaults
```

### Session Management
```bash
opspilot sessions [OPTIONS]
  --list, -l           List all sessions
  --delete, -d TEXT     Delete session by ID
  --export, -e TEXT     Export session by ID
  --format, -f TEXT     Export format (json|markdown|txt)
```

### Usage Statistics
```bash
opspilot stats
# Shows token usage, cost, request count, and context size
```

## Architecture

```
opspilot/
├── opspilot/
│   ├── __init__.py      # Package initialization
│   ├── main.py          # CLI entry point
│   ├── config.py        # Configuration management
│   ├── agent/
│   │   ├── core.py      # Agent Think-Act loop
│   │   ├── memory.py    # Chat history
│   │   └── tools/
│   │       ├── system.py # Shell execution
│   │       └── files.py  # File operations
│   └── tui/
│       ├── app.py       # TUI application
│       ├── screens.py   # Modal dialogs
│       └── styles.tcss  # CSS styling
├── pyproject.toml       # Package configuration
├── requirements.txt     # Dependencies
├── install.py          # Installation script
└── README.md           # Documentation
```

## Development

### Setup Development Environment
```bash
# Clone repository
git clone https://github.com/your-org/opspilot.git
cd opspilot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with type checking
mypy opspilot/

# Format code
black opspilot/
```

### Project Structure
- **Agent Core**: Think-Act loop with mode switching
- **Tools System**: Secure file and shell operations
- **Memory Management**: Persistent conversation history
- **TUI Framework**: Rich terminal interface with Textual
- **Configuration**: Flexible authentication and model settings

## Safety Features

### Dangerous Command Detection
OpsPilot automatically detects and confirms commands containing:
- File deletion: `rm`, `delete`, `del`
- System changes: `systemctl`, `service`, `init`
- Container operations: `kubectl apply`, `docker rm`
- Permission changes: `chmod 777`, `chown`
- System administration: `sudo`, `passwd`, `crontab`

### Secure Execution
- Timeout controls for all commands
- Working directory restrictions
- Process isolation and cleanup
- Comprehensive error handling

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- 📖 [Documentation](https://docs.opspilot.com)
- 🐛 [Issue Tracker](https://github.com/your-org/opspilot/issues)
- 💬 [Discussions](https://github.com/your-org/opspilot/discussions)

---

**OpsPilot** - Your AI-powered DevOps companion 🚀