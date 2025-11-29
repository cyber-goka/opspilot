# Changelog

All notable changes to OpsPilot will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Initial release
- Basic CLI functionality
- Agent Think-Act loop
- Session management
- Configuration system

[Unreleased]: https://github.com/cyber-goka/opspilot/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/cyber-goka/opspilot/releases/tag/v0.1.0
