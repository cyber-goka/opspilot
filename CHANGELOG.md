# Changelog

All notable changes to OpsPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

## [0.2.0] - 2025-12-02

### Added
- **API Key Management System**: Comprehensive multi-provider API key management
  - Secure storage with 0600 file permissions in `~/.config/opspilot/api_keys.json`
  - Support for 5 providers: OpenAI, Anthropic, Google, DeepSeek, OpenRouter
  - Password-masked input fields in options modal
  - Auto-save on change functionality
  - Environment variable fallback support
  - Clickable links to get API keys from providers
- **Thinking Animation**: Visual feedback while waiting for LLM responses
  - Positioned between chat messages and input for better UX
  - "✨ Agent is thinking..." indicator with loading animation
- **Auto-scroll Feature**: Automatically scroll to latest message after agent responses
- **Complete TUI Implementation**: Full-featured terminal user interface
  - New screens: Home, Chat, Help, Chat Details, Rename Chat
  - New widgets: ChatList, Chatbox, PromptInput, ChatOptions, ChatHeader
  - Database integration for chat persistence (SQLite with aiosqlite)
  - Theme support with custom color system
  - SCSS styling with responsive layout
  - Usage statistics display (tokens, context, cost)
- **Updated AI Models to 2025 Versions**:
  - OpenAI: GPT-4o, GPT-4o Mini, o1 Preview, o1 Mini
  - Anthropic: Claude Sonnet 4.5, Opus 4.5, Opus 4.1
  - Google: Gemini 2.5 Pro/Flash, Gemini 1.5 Pro
  - DeepSeek: DeepSeek V3, DeepSeek Reasoner
  - Zhipu: GLM-4.6 via OpenRouter

### Changed
- Refactored TUI architecture into modular screens and widgets
- Updated model naming to follow LiteLLM conventions
- Improved options modal to be scrollable for future extensibility
- Enhanced chat header to display real-time usage statistics

### Fixed
- **API Key Loading**: Fixed LaunchConfig to properly load API keys from file on initialization
- **RuntimeWarning**: Added proper async cleanup handler for LiteLLM clients on app close
- **Linting Issues**: Removed all unused imports and variables
  - Fixed unused `completion_tokens` variable in agent/core.py
  - Removed unused imports across 5 files (app.py, chat_list.py, chat_options.py, chatbox.py)
- **Test Failures**: Updated 3 tests to match new model configuration
  - All 39 tests now passing
- **Code Formatting**: Applied Black formatting to entire codebase (47 files)

### Technical Improvements
- Integrated LaunchConfig with AgentCore for API key access
- Implemented clickable URLs in TUI with `action_open_link()`
- Added proper async cleanup for LiteLLM async clients
- Updated test suite to match new model names and configuration

## [0.1.2] - 2025-11-29

### Fixed
- **Critical**: Fixed all remaining CSS errors (19 total) preventing app startup
  - Replaced `scrollbars: vertical` with `overflow-y: scroll`
  - Removed unsupported `font-family: monospace`
  - Removed unsupported `border-radius` property
  - Fixed `border-style` syntax (changed to `border: double`)
  - Fixed Input cursor background color (changed from `$text` to `$accent`)
  - Removed unsupported `box-shadow` property
  - Fixed `align` property order (changed to `center bottom`)

## [0.1.1] - 2025-11-29

### Fixed
- **Critical**: Removed unsupported CSS features from styles.tcss that prevented app startup
  - Removed @media queries (not supported in Textual CSS)
  - Removed @keyframes animations
  - Removed transition properties
  - Removed pseudo-elements and outline properties
  - Fixes "Expected selector or end of file" error on startup

### Added
- Initial project structure
- Agent core with Think-Act loop
- Plan and Build mode switching
- Multi-provider LLM support (OpenAI, ZhipuAI, Anthropic, OpenRouter)
- Configuration management with YAML
- Session management and persistence
- File operations tools
- System command execution with safety gates
- Dangerous command detection and confirmation
- Simple CLI interface
- Comprehensive test suite
- CI/CD workflows for testing and linting
- Pre-commit hooks configuration
- MIT License

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- Fixed duplicate `_interactive_execution` method in system.py

### Security
- Implemented safety gates for dangerous commands
- Command timeout controls
- Working directory restrictions

## [0.1.0] - 2025-11-29

### Added
- **Full Textual TUI**: Split-screen interface with chat history and terminal output
- **AI Agent Core**: Think-Act loop with Plan/Build dual-mode operation
- **Multi-provider Support**: OpenAI, Anthropic, Zhipu AI, OpenRouter integration via LiteLLM
- **File Operations Tool**: Secure file reading, writing, and directory listing
- **System Tool**: Safe command execution with dangerous command detection
- **Session Management**: Save, load, export conversation history (JSON, Markdown, TXT)
- **Configuration CLI**: Interactive settings management with multiple providers
- **Usage Tracking**: Token usage and cost monitoring
- **Type Safety**: Comprehensive type annotations (mypy compliant)
- **Test Suite**: 39+ tests with pytest and pytest-asyncio
- **CI/CD Workflows**: Automated testing, linting, and PyPI releases
- **PyPI Package**: Published to https://pypi.org/project/opspilot/

### Security
- Dangerous command detection with confirmation dialogs
- Restricted path protection (prevents access to /etc, /sys, /proc, etc.)
- Sandboxed subprocess execution with timeouts
- File operation safety checks and automatic backups

[Unreleased]: https://github.com/cyber-goka/opspilot/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/cyber-goka/opspilot/compare/v0.1.2...v0.2.0
[0.1.2]: https://github.com/cyber-goka/opspilot/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/cyber-goka/opspilot/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cyber-goka/opspilot/releases/tag/v0.1.0
