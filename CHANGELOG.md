# Changelog

All notable changes to OpsPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

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

[Unreleased]: https://github.com/cyber-goka/opspilot/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/cyber-goka/opspilot/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/cyber-goka/opspilot/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/cyber-goka/opspilot/releases/tag/v0.1.0
