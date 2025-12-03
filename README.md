# MCP Amadeus Hotels Server

[![CI](https://github.com/your-username/mcp-amadeushotels/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/mcp-amadeushotels/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

A Model Context Protocol (MCP) server that provides access to Amadeus Hotels APIs for finding hotels by location and getting pricing information. This server uses the official [Amadeus Python SDK](https://github.com/amadeus4dev/amadeus-python) for reliable API integration.

## Features

- **Hotel List Tool**: Find hotels by geocode/city with distance information
- **Hotel Search Tool**: Get hotel prices and availability for specific hotels
- **Concurrent Operations**: Multi-location search and batch processing for improved performance
- **Caching**: Intelligent response caching with TTL support
- **Performance Monitoring**: Real-time metrics and statistics
- Built with FastMCP for optimal performance
- Uses official Amadeus Python SDK for robust API integration
- Comprehensive error handling and validation
- Type-safe with Pydantic models
- Docker support for easy deployment

## Installation

```bash
# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

## Configuration

Create a `.env` file with your Amadeus API credentials and optional authentication settings:

```env
# Amadeus API Configuration
AMADEUS_API_KEY=your_api_key_here
AMADEUS_API_SECRET=your_api_secret_here
AMADEUS_BASE_URL=https://test.api.amadeus.com

# Server Authentication (optional, enabled by default)
AUTH_ENABLED=true
API_KEYS=your-secure-api-key-1,your-secure-api-key-2
```

See [Authentication Documentation](docs/AUTHENTICATION.md) for detailed authentication setup.

## Usage

### Setup

1. **Install uv** (if not already installed):
   ```bash
   # On Windows (PowerShell)
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or with pip
   pip install uv
   ```

2. **Get Amadeus API credentials**:
   - Sign up at [Amadeus for Developers](https://developers.amadeus.com/)
   - Create a new app and get your API key and secret

3. **Configure environment**:
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your credentials
   AMADEUS_API_KEY=your_actual_api_key
   AMADEUS_API_SECRET=your_actual_api_secret
   ```

4. **Install dependencies**:
   ```bash
   uv sync
   ```

### Run the server

```bash
# Run with streamable HTTP transport (default)
uv run src/main.py

# Run with custom port and host
uv run src/main.py --port 3001 --host 0.0.0.0

# Run with stdio transport
uv run src/main.py --transport stdio

# Run with debug logging
uv run src/main.py --log-level DEBUG
```

### Alternative startup methods

```bash
# Using the startup script
uv run run_server.py

# Direct module execution
uv run -m src.main
```

### Available Tools

#### 1. `search_hotels_by_location`
Find hotels near a specific location with distance information.

**Parameters:**
- `latitude` (required): Latitude coordinate
- `longitude` (required): Longitude coordinate  
- `radius` (optional): Search radius in kilometers (default: 5)
- `radius_unit` (optional): Unit for radius - "KM" or "MILE" (default: "KM")
- `amenities` (optional): List of desired amenities
- `ratings` (optional): Hotel star ratings (1-5)
- `chain_codes` (optional): Hotel chain codes

#### 2. `search_hotel_offers`
Get pricing and availability for specific hotels.

**Parameters:**
- `hotel_ids` (required): List of Amadeus hotel IDs
- `check_in_date` (required): Check-in date (YYYY-MM-DD)
- `check_out_date` (required): Check-out date (YYYY-MM-DD)
- `adults` (optional): Number of adult guests (default: 1)
- `room_quantity` (optional): Number of rooms (default: 1)
- `currency` (optional): Currency code (e.g., "USD", "EUR")
- `price_range` (optional): Price range filter (e.g., "100-300")

## Examples

### Basic Hotel Search

```python
# Example: Find hotels near Times Square
result = await search_hotels_by_location(
    latitude=40.7589,
    longitude=-73.9851,
    radius=2,
    amenities=["WIFI", "FITNESS_CENTER"],
    ratings=["4", "5"]
)
```

### Hotel Offers Search

```python
# Example: Get pricing for a specific hotel
result = await search_hotel_offers(
    hotel_ids=["MCLONGHM"],
    check_in_date="2024-01-15",
    check_out_date="2024-01-17",
    adults=2,
    currency="USD"
)
```

### Health Check

```python
# Check API connectivity
status = await health_check()
```

See `examples/example_usage.py` for a complete working example.

## Development

```bash
# Run tests
uv run pytest

# Format code
uv run black src/

# Lint code
uv run ruff check src/

# Type check
uv run mypy src/

# Run example
uv run examples/example_usage.py
```

## Documentation

- [Installation Guide](docs/)
- [Authentication](docs/AUTHENTICATION.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Multithreading Implementation](docs/MULTITHREADING_IMPLEMENTATION.md)
- [Project Summary](docs/PROJECT_SUMMARY.md)

## API Reference

This server integrates with the following Amadeus APIs using the official Python SDK:
- [Hotels List API](https://developers.amadeus.com/self-service/category/hotel/api-doc/hotel-list)
- [Hotel Offers API](https://developers.amadeus.com/self-service/category/hotel/api-doc/hotel-offers)

The server uses the [Amadeus Python SDK](https://github.com/amadeus4dev/amadeus-python) (v12.0.0+) which provides:
- Automatic authentication and token management
- Built-in error handling and retry logic
- Rate limiting protection
- Consistent API response handling

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on:

- Code of Conduct
- Development setup
- Coding standards
- Pull request process

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/your-username/mcp-amadeushotels/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/mcp-amadeushotels/discussions)

## Acknowledgments

- [Amadeus for Developers](https://developers.amadeus.com/) for the Hotels API
- [Model Context Protocol](https://modelcontextprotocol.io/) for the MCP specification
- All contributors who help improve this project
