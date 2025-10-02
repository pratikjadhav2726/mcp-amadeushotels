"""
MCP Amadeus Hotels Server

A Model Context Protocol (MCP) server that provides access to Amadeus Hotels APIs
for finding hotels by location and getting pricing information.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .main import main, create_mcp_server
from .amadeus_client import AmadeusClient, AmadeusAPIError, AmadeusAuthenticationError, AmadeusRateLimitError
from .models import (
    HotelsListRequest,
    HotelsListResponse,
    HotelOffersRequest,
    HotelOffersResponse,
    Hotel,
    HotelOffer,
)
from .config import Settings, get_app_settings, setup_logging
from .tools import AmadeusHotelsTools

__all__ = [
    "main",
    "create_mcp_server",
    "AmadeusClient",
    "AmadeusAPIError",
    "AmadeusAuthenticationError",
    "AmadeusRateLimitError",
    "HotelsListRequest",
    "HotelsListResponse",
    "HotelOffersRequest",
    "HotelOffersResponse",
    "Hotel",
    "HotelOffer",
    "Settings",
    "get_app_settings",
    "setup_logging",
    "AmadeusHotelsTools",
]
