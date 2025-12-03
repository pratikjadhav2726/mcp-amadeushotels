# Repository Structure

This document describes the organization of the MCP Amadeus Hotels repository.

## Directory Structure

```
mcp-amadeushotels/
├── .github/                    # GitHub configuration
│   ├── workflows/             # CI/CD workflows
│   │   └── ci.yml             # Continuous Integration workflow
│   ├── ISSUE_TEMPLATE/        # Issue templates
│   │   ├── bug_report.md      # Bug report template
│   │   └── feature_request.md # Feature request template
│   └── PULL_REQUEST_TEMPLATE.md # Pull request template
│
├── docs/                       # Documentation
│   ├── AUTHENTICATION.md      # Authentication guide
│   ├── DEPLOYMENT.md          # Deployment guide
│   ├── HOTEL_BOOKING_V2.md    # Hotel booking v2 documentation
│   ├── MULTITHREADING_IMPLEMENTATION.md # Multithreading docs
│   ├── PROJECT_SUMMARY.md     # Project overview
│   ├── STRUCTURE.md           # This file
│   └── plan.md                # Original project plan
│
├── examples/                   # Usage examples
│   ├── example_usage.py       # Basic usage example
│   └── multithreading_example.py # Multithreading example
│
├── scripts/                    # Utility scripts
│   └── (utility scripts)
│
├── src/                        # Source code
│   ├── __init__.py
│   ├── main.py                # Main server entry point
│   ├── config.py              # Configuration management
│   ├── models.py              # Pydantic data models
│   ├── amadeus_client.py      # Amadeus API client
│   ├── tools.py               # MCP tools implementation
│   ├── cache.py               # Caching implementation
│   └── performance_monitor.py # Performance monitoring
│
├── tests/                      # Test files
│   ├── test_data/             # Test data files
│   └── test_amadeus_hotels.py # Unit tests
│
├── .gitignore                 # Git ignore rules
├── CHANGELOG.md               # Changelog
├── CODE_OF_CONDUCT.md         # Code of conduct
├── CONTRIBUTING.md            # Contributing guidelines
├── docker-compose.yml         # Docker Compose configuration
├── Dockerfile                 # Docker image definition
├── env.example                # Environment variables template
├── LICENSE                    # MIT License
├── pyproject.toml             # Project configuration
├── README.md                  # Main documentation
├── render.yaml                # Render deployment config
├── requirements.txt          # Python dependencies
├── run_server.py              # Server startup script
└── uv.lock                    # Dependency lock file
```

## Key Files

### Root Level Files

- **README.md**: Main project documentation and getting started guide
- **LICENSE**: MIT License
- **CONTRIBUTING.md**: Guidelines for contributors
- **CODE_OF_CONDUCT.md**: Community code of conduct
- **CHANGELOG.md**: Version history and changes
- **pyproject.toml**: Project metadata and dependencies
- **requirements.txt**: Python dependencies (for compatibility)
- **Dockerfile**: Container image definition
- **docker-compose.yml**: Docker Compose configuration
- **env.example**: Environment variables template
- **run_server.py**: Server startup script

### Source Code (`src/`)

- **main.py**: Main MCP server entry point with FastMCP integration
- **config.py**: Configuration management using Pydantic Settings
- **models.py**: Pydantic data models for type safety
- **amadeus_client.py**: Amadeus API client wrapper
- **tools.py**: MCP tool implementations
- **cache.py**: Response caching with TTL support
- **performance_monitor.py**: Performance metrics and monitoring

### Documentation (`docs/`)

All project documentation is organized in the `docs/` directory:

- **AUTHENTICATION.md**: Authentication setup and usage
- **DEPLOYMENT.md**: Deployment guides for various platforms
- **MULTITHREADING_IMPLEMENTATION.md**: Concurrent operations documentation
- **PROJECT_SUMMARY.md**: High-level project overview
- **STRUCTURE.md**: This file - repository structure documentation

### Tests (`tests/`)

- **test_amadeus_hotels.py**: Unit tests for the MCP server
- **test_data/**: Test data files (JSON fixtures, etc.)

### Examples (`examples/`)

- **example_usage.py**: Basic usage examples
- **multithreading_example.py**: Concurrent operation examples

### GitHub Configuration (`.github/`)

- **workflows/ci.yml**: CI/CD pipeline for testing and building
- **ISSUE_TEMPLATE/**: Templates for bug reports and feature requests
- **PULL_REQUEST_TEMPLATE.md**: Template for pull requests

## Best Practices

1. **Documentation**: All documentation is in `docs/` directory
2. **Tests**: All tests are in `tests/` directory
3. **Examples**: Usage examples are in `examples/` directory
4. **Configuration**: CI/CD and GitHub templates are in `.github/`
5. **Source Code**: All application code is in `src/` directory
6. **Scripts**: Utility scripts are in `scripts/` directory

## Adding New Files

When adding new files:

- **Documentation**: Add to `docs/` directory
- **Tests**: Add to `tests/` directory
- **Examples**: Add to `examples/` directory
- **Source Code**: Add to `src/` directory
- **Scripts**: Add to `scripts/` directory
- **GitHub Templates**: Add to `.github/` directory

## Open Source Standards

This repository follows open source best practices:

- ✅ Clear directory structure
- ✅ Comprehensive documentation
- ✅ Contributing guidelines
- ✅ Code of conduct
- ✅ License file
- ✅ Changelog
- ✅ CI/CD workflows
- ✅ Issue and PR templates
- ✅ Proper .gitignore
- ✅ README with badges and links

