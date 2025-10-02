"""
Main MCP server for Amadeus Hotels API integration.
"""

import contextlib
import logging
import sys
from collections.abc import AsyncIterator
from typing import Any, Optional

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
import uvicorn

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


class InMemoryEventStore:
    """Simple in-memory event store for demonstration."""
    
    def __init__(self):
        self.events = []
    
    async def store_event(self, event_id: str, event_data: dict):
        """Store an event."""
        self.events.append({"id": event_id, "data": event_data})
    
    async def get_events_since(self, last_event_id: str = None):
        """Get events since the last event ID."""
        if last_event_id is None:
            return self.events
        
        # Find the index of the last event ID
        for i, event in enumerate(self.events):
            if event["id"] == last_event_id:
                return self.events[i + 1:]
        
        return self.events


def create_mcp_server() -> Server:
    """Create and configure the MCP server."""
    settings = get_app_settings()
    
    # Create low-level MCP server
    app = Server("AmadeusHotelsServer")
    
    # Initialize tools
    tools = AmadeusHotelsTools()
    
    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Handle tool calls."""
        try:
            if name == "search_hotels_by_location":
                result = await tools.search_hotels_by_location(**arguments)
            elif name == "search_hotel_offers":
                result = await tools.search_hotel_offers(**arguments)
            elif name == "health_check":
                result = await tools.health_check()
            else:
                result = f"Unknown tool: {name}"
            
            return [types.TextContent(type="text", text=result)]
        except Exception as e:
            logger.error(f"Error executing tool {name}: {e}")
            return [types.TextContent(type="text", text=f"Error: {str(e)}")]
    
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List available tools."""
        return [
            types.Tool(
                name="search_hotels_by_location",
                description="Search for hotels near a specific location with distance information",
                inputSchema={
                    "type": "object",
                    "required": ["latitude", "longitude"],
                    "properties": {
                        "latitude": {"type": "number", "description": "Latitude coordinate"},
                        "longitude": {"type": "number", "description": "Longitude coordinate"},
                        "radius": {"type": "integer", "description": "Search radius in kilometers"},
                        "radius_unit": {"type": "string", "description": "Unit for radius (KM or MILE)"},
                        "amenities": {"type": "array", "items": {"type": "string"}, "description": "Desired amenities"},
                        "ratings": {"type": "array", "items": {"type": "string"}, "description": "Hotel star ratings"},
                        "chain_codes": {"type": "array", "items": {"type": "string"}, "description": "Hotel chain codes"},
                        "hotel_source": {"type": "string", "description": "Hotel source (BEDBANK, DIRECTCHAIN, ALL)"},
                    },
                },
            ),
            types.Tool(
                name="search_hotel_offers",
                description="Search for hotel offers with pricing and availability information",
                inputSchema={
                    "type": "object",
                    "required": ["hotel_ids", "check_in_date", "check_out_date"],
                    "properties": {
                        "hotel_ids": {"type": "array", "items": {"type": "string"}, "description": "List of Amadeus hotel IDs"},
                        "check_in_date": {"type": "string", "description": "Check-in date (YYYY-MM-DD)"},
                        "check_out_date": {"type": "string", "description": "Check-out date (YYYY-MM-DD)"},
                        "adults": {"type": "integer", "description": "Number of adult guests"},
                        "room_quantity": {"type": "integer", "description": "Number of rooms"},
                        "currency": {"type": "string", "description": "Currency code"},
                        "price_range": {"type": "string", "description": "Price range filter"},
                        "payment_policy": {"type": "string", "description": "Payment policy filter"},
                        "board_type": {"type": "string", "description": "Board type filter"},
                        "include_closed": {"type": "boolean", "description": "Include sold out properties"},
                        "best_rate_only": {"type": "boolean", "description": "Return only best rates"},
                        "lang": {"type": "string", "description": "Language code"},
                    },
                },
            ),
            types.Tool(
                name="health_check",
                description="Check the health status of the Amadeus API connection",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]
    
    return app


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
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def main(
    port: Optional[int],
    host: Optional[str],
    log_level: Optional[str],
    transport: str,
    json_response: bool,
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
        
        if transport == "stdio":
            logger.info("Running with stdio transport")
            # Create FastMCP server for stdio
            from mcp.server.fastmcp import FastMCP
            mcp = FastMCP("AmadeusHotelsServer")
            tools = AmadeusHotelsTools()
            tools.register_tools(mcp)
            mcp.run(transport="stdio")
        else:
            logger.info(f"Running with streamable-http transport on {settings.host}:{settings.port}")
            
            # Create low-level MCP server
            app = create_mcp_server()
            
            # Create event store for resumability
            event_store = InMemoryEventStore()
            
            # Create the session manager with our app and event store
            session_manager = StreamableHTTPSessionManager(
                app=app,
                event_store=event_store,  # Enable resumability
                json_response=json_response,
            )
            
            # ASGI handler for streamable HTTP connections
            async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
                # Handle OPTIONS requests for CORS preflight
                if scope["method"] == "OPTIONS":
                    headers = [
                        (b"access-control-allow-origin", b"*"),
                        (b"access-control-allow-methods", b"GET, POST, OPTIONS, DELETE"),
                        (b"access-control-allow-headers", b"*"),
                        (b"access-control-expose-headers", b"Mcp-Session-Id"),
                        (b"content-length", b"0"),
                    ]
                    await send({
                        "type": "http.response.start",
                        "status": 200,
                        "headers": headers,
                    })
                    await send({"type": "http.response.body", "body": b""})
                    return
                
                await session_manager.handle_request(scope, receive, send)
            
            @contextlib.asynccontextmanager
            async def lifespan(app: Starlette) -> AsyncIterator[None]:
                """Context manager for managing session manager lifecycle."""
                async with session_manager.run():
                    logger.info("Application started with StreamableHTTP session manager!")
                    try:
                        yield
                    finally:
                        logger.info("Application shutting down...")
            
            # Create an ASGI application using the transport
            starlette_app = Starlette(
                debug=True,
                routes=[
                    Mount("/mcp", app=handle_streamable_http),
                ],
                lifespan=lifespan,
            )
            
            # Wrap ASGI application with CORS middleware to expose Mcp-Session-Id header
            # for browser-based clients (ensures 500 errors get proper CORS headers)
            starlette_app = CORSMiddleware(
                starlette_app,
                allow_origins=["*"],  # Allow all origins - adjust as needed for production
                allow_methods=["GET", "POST", "OPTIONS", "DELETE"],  # MCP streamable HTTP methods
                allow_headers=["*"],
                expose_headers=["Mcp-Session-Id"],
            )
            
            uvicorn.run(starlette_app, host=settings.host, port=settings.port)
            
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
