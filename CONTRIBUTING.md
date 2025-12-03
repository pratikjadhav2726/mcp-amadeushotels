# Contributing to MCP Amadeus Hotels

Thank you for your interest in contributing to MCP Amadeus Hotels! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to a Code of Conduct that all contributors are expected to follow. Please read [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) before contributing.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

- **Clear and descriptive title**
- **Steps to reproduce** the issue
- **Expected behavior** vs **Actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Error messages** or logs (if applicable)
- **Screenshots** (if applicable)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

- **Clear and descriptive title**
- **Detailed description** of the proposed enhancement
- **Use case** - why is this enhancement useful?
- **Possible implementation** (if you have ideas)

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the coding standards** (see below)
3. **Write or update tests** for your changes
4. **Update documentation** as needed
5. **Ensure all tests pass** locally
6. **Submit a pull request** with a clear description

#### Pull Request Process

1. Update the README.md with details of changes if needed
2. Update the CHANGELOG.md with your changes
3. The PR will be reviewed by maintainers
4. Once approved, it will be merged

## Development Setup

### Prerequisites

- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Amadeus API credentials (for testing)

### Setup Steps

1. **Clone your fork:**
   ```bash
   git clone https://github.com/your-username/mcp-amadeushotels.git
   cd mcp-amadeushotels
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

3. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your Amadeus API credentials
   ```

4. **Run tests:**
   ```bash
   uv run pytest
   ```

## Coding Standards

### Code Style

- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all function signatures
- Maximum line length: 88 characters (Black default)
- Use meaningful variable and function names

### Formatting

We use automated formatting tools:

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/
```

### Testing

- Write tests for all new features
- Ensure existing tests continue to pass
- Aim for good test coverage
- Use descriptive test names

```bash
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

### Documentation

- Add docstrings to all public functions and classes
- Follow Google-style docstrings
- Update README.md if adding new features
- Update CHANGELOG.md for user-facing changes

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or updating tests
- `chore:` for maintenance tasks

Example:
```
feat: add concurrent hotel search by multiple locations

- Implement search_hotels_by_multiple_locations tool
- Add client pool for concurrent API calls
- Update documentation with usage examples
```

## Project Structure

```
mcp-amadeushotels/
├── src/                    # Source code
│   ├── __init__.py
│   ├── main.py            # Main server entry point
│   ├── config.py           # Configuration management
│   ├── models.py           # Pydantic data models
│   ├── amadeus_client.py   # Amadeus API client
│   ├── tools.py            # MCP tools implementation
│   ├── cache.py            # Caching implementation
│   └── performance_monitor.py  # Performance monitoring
├── tests/                  # Test files
├── examples/               # Usage examples
├── docs/                   # Documentation
├── .github/                # GitHub workflows and templates
└── scripts/                # Utility scripts
```

## Architecture Guidelines

### SOLID Principles

- **Single Responsibility**: Each class should have one clear purpose
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Derived classes must be substitutable for their base classes
- **Interface Segregation**: Many specific interfaces are better than one general interface
- **Dependency Inversion**: Depend on abstractions, not concretions

### Design Patterns

- Use dependency injection for configuration
- Implement proper error handling and logging
- Use async/await for I/O operations
- Implement caching where appropriate

## Questions?

If you have questions about contributing, please:

1. Check existing issues and discussions
2. Open a new issue with the `question` label
3. Reach out to maintainers

Thank you for contributing to MCP Amadeus Hotels! 🎉

