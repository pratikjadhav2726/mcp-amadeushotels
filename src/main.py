"""
Main MCP server for Amadeus Hotels API integration.
"""

import logging
import sys
from typing import Optional

import click
from mcp.server.fastmcp import FastMCP

try:
    from .config import get_app_settings, setup_logging
    from .tools import AmadeusHotelsTools
except ImportError:
    # Handle direct execution
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from config import get_app_settings, setup_logging
    from tools import AmadeusHotelsTools

logger = logging.getLogger(__name__)


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server."""
    settings = get_app_settings()
    
    # Create MCP server
    mcp = FastMCP("AmadeusHotelsServer")
    
    # Initialize tools
    tools = AmadeusHotelsTools()
    tools.register_tools(mcp)
    
    return mcp


@click.command()
@click.option(
    "--port",
    default=None,
    type=int,
    help="Port to run the server on (overrides environment variable)",
)
@click.option(
    "--host",
    default=None,
    help="Host to bind the server to (overrides environment variable)",
)
@click.option(
    "--log-level",
    default=None,
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level (overrides environment variable)",
)
@click.option(
    "--transport",
    default="streamable-http",
    type=click.Choice(["stdio", "streamable-http"]),
    help="Transport method to use",
)
def main(
    port: Optional[int],
    host: Optional[str],
    log_level: Optional[str],
    transport: str,
) -> None:
    """Run the Amadeus Hotels MCP server."""
    try:
        # Get settings
        settings = get_app_settings()
        
        # Override settings with command line arguments
        if port is not None:
            settings.port = port
        if host is not None:
            settings.host = host
        if log_level is not None:
            settings.log_level = log_level
        
        # Setup logging
        setup_logging(settings.log_level)
        
        logger.info(f"Starting Amadeus Hotels MCP server on {settings.host}:{settings.port}")
        logger.info(f"Using transport: {transport}")
        logger.info(f"Amadeus API base URL: {settings.amadeus_base_url}")
        
        # Create and run server
        mcp = create_mcp_server()
        
        if transport == "stdio":
            logger.info("Running with stdio transport")
            mcp.run(transport="stdio")
        else:
            logger.info(f"Running with streamable-http transport on {settings.host}:{settings.port}")
            mcp.run(transport="streamable-http")
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
