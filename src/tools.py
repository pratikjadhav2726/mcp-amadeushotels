"""
MCP tools for Amadeus Hotels API integration.
"""

import logging
from datetime import date
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

try:
    from .amadeus_client import AmadeusClient, AmadeusAPIError, AmadeusAuthenticationError, AmadeusRateLimitError
    from .models import HotelsListRequest, HotelOffersRequest
    from .config import get_app_settings
except ImportError:
    # Handle direct execution
    from amadeus_client import AmadeusClient, AmadeusAPIError, AmadeusAuthenticationError, AmadeusRateLimitError
    from models import HotelsListRequest, HotelOffersRequest
    from config import get_app_settings

logger = logging.getLogger(__name__)


class AmadeusHotelsTools:
    """MCP tools for Amadeus Hotels API."""
    
    def __init__(self):
        self.settings = get_app_settings()
        self.client = AmadeusClient(
            api_key=self.settings.amadeus_api_key,
            api_secret=self.settings.amadeus_api_secret,
            base_url=self.settings.amadeus_base_url,
            timeout=self.settings.api_timeout,
            max_retries=self.settings.max_retries,
        )
    
    async def health_check(self) -> str:
        """
        Check the health status of the Amadeus API connection.
        
        Returns:
            Status message indicating API connectivity
        """
        try:
            is_healthy = await self.client.health_check()
            if is_healthy:
                return "✅ Amadeus API is accessible and authentication is working"
            else:
                return "❌ Amadeus API is not accessible or authentication failed"
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return f"❌ Health check failed: {str(e)}"
    
    def register_tools(self, mcp: FastMCP) -> None:
        """Register all tools with the MCP server."""
        
        @mcp.tool()
        async def search_hotels_by_location(
            latitude: float,
            longitude: float,
            radius: Optional[int] = 5,
            radius_unit: Optional[str] = "KM",
            amenities: Optional[List[str]] = None,
            ratings: Optional[List[str]] = None,
            chain_codes: Optional[List[str]] = None,
            hotel_source: Optional[str] = "ALL",
        ) -> str:
            """
            Search for hotels near a specific location with distance information.
            
            Args:
                latitude: Latitude coordinate of the search point
                longitude: Longitude coordinate of the search point
                radius: Search radius in the specified units (default: 5)
                radius_unit: Unit for radius - "KM" or "MILE" (default: "KM")
                amenities: List of desired amenities (e.g., ["SWIMMING_POOL", "SPA", "WIFI"])
                ratings: Hotel star ratings (1-5)
                chain_codes: Hotel chain codes (2-character codes)
                hotel_source: Hotel source - "BEDBANK", "DIRECTCHAIN", or "ALL" (default: "ALL")
            
            Returns:
                JSON string containing hotel information with distances
            """
            try:
                # Validate inputs
                if not -90 <= latitude <= 90:
                    return "Error: Latitude must be between -90 and 90 degrees"
                if not -180 <= longitude <= 180:
                    return "Error: Longitude must be between -180 and 180 degrees"
                if radius and radius <= 0:
                    return "Error: Radius must be positive"
                
                # Create request
                request = HotelsListRequest(
                    latitude=latitude,
                    longitude=longitude,
                    radius=radius,
                    radius_unit=radius_unit,
                    amenities=amenities,
                    ratings=ratings,
                    chain_codes=chain_codes,
                    hotel_source=hotel_source,
                )
                
                # Make API call
                response = await self.client.search_hotels_by_location(request)
                
                # Format response
                hotels_data = []
                for hotel in response.data:
                    hotel_info = {
                        "hotel_id": hotel.hotel_id,
                        "name": hotel.name,
                        "chain_code": hotel.chain_code,
                        "latitude": hotel.geo_code.latitude,
                        "longitude": hotel.geo_code.longitude,
                        "country_code": hotel.address.country_code if hotel.address else None,
                        "distance": {
                            "value": hotel.distance.value,
                            "unit": hotel.distance.unit,
                        } if hotel.distance else None,
                    }
                    hotels_data.append(hotel_info)
                
                result = {
                    "hotels": hotels_data,
                    "total_count": len(hotels_data),
                    "search_params": {
                        "latitude": latitude,
                        "longitude": longitude,
                        "radius": radius,
                        "radius_unit": radius_unit,
                    },
                }
                
                import json
                return json.dumps(result, indent=2)
                
            except AmadeusAuthenticationError as e:
                logger.error(f"Authentication error: {e}")
                return f"Error: Authentication failed - {str(e)}"
            except AmadeusRateLimitError as e:
                logger.error(f"Rate limit error: {e}")
                return f"Error: Rate limit exceeded - {str(e)}"
            except AmadeusAPIError as e:
                logger.error(f"API error: {e}")
                return f"Error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return f"Error: Unexpected error occurred - {str(e)}"
        
        @mcp.tool()
        async def search_hotel_offers(
            hotel_ids: List[str],
            check_in_date: str,
            check_out_date: str,
            adults: Optional[int] = 1,
            room_quantity: Optional[int] = 1,
            currency: Optional[str] = None,
            price_range: Optional[str] = None,
            payment_policy: Optional[str] = "NONE",
            board_type: Optional[str] = None,
            include_closed: Optional[bool] = False,
            best_rate_only: Optional[bool] = True,
            lang: Optional[str] = None,
        ) -> str:
            """
            Search for hotel offers with pricing and availability information.
            
            Args:
                hotel_ids: List of Amadeus hotel IDs (8-character codes)
                check_in_date: Check-in date in YYYY-MM-DD format
                check_out_date: Check-out date in YYYY-MM-DD format
                adults: Number of adult guests (default: 1)
                room_quantity: Number of rooms (default: 1)
                currency: Currency code (e.g., "USD", "EUR", "GBP")
                price_range: Price range filter (e.g., "100-300", "-300", "100")
                payment_policy: Payment policy - "GUARANTEE", "DEPOSIT", or "NONE" (default: "NONE")
                board_type: Board type - "ROOM_ONLY", "BREAKFAST", "HALF_BOARD", "FULL_BOARD", "ALL_INCLUSIVE"
                include_closed: Include sold out properties (default: False)
                best_rate_only: Return only best rates (default: True)
                lang: Language code (e.g., "EN", "FR", "ES")
            
            Returns:
                JSON string containing hotel offers with pricing information
            """
            try:
                # Validate inputs
                if not hotel_ids:
                    return "Error: At least one hotel ID is required"
                if adults and not (1 <= adults <= 9):
                    return "Error: Number of adults must be between 1 and 9"
                if room_quantity and not (1 <= room_quantity <= 9):
                    return "Error: Number of rooms must be between 1 and 9"
                
                # Parse dates
                try:
                    check_in = date.fromisoformat(check_in_date)
                    check_out = date.fromisoformat(check_out_date)
                except ValueError as e:
                    return f"Error: Invalid date format - {str(e)}"
                
                if check_out <= check_in:
                    return "Error: Check-out date must be after check-in date"
                
                # Create request
                request = HotelOffersRequest(
                    hotel_ids=hotel_ids,
                    adults=adults,
                    check_in_date=check_in,
                    check_out_date=check_out,
                    room_quantity=room_quantity,
                    currency=currency,
                    price_range=price_range,
                    payment_policy=payment_policy,
                    board_type=board_type,
                    include_closed=include_closed,
                    best_rate_only=best_rate_only,
                    lang=lang,
                )
                
                # Make API call
                response = await self.client.search_hotel_offers(request)
                
                # Format response
                offers_data = []
                for item in response.data:
                    hotel_offers = {
                        "hotel": {
                            "hotel_id": item.hotel.hotel_id,
                            "name": item.hotel.name,
                            "chain_code": item.hotel.chain_code,
                            "city_code": item.hotel.city_code,
                            "latitude": item.hotel.latitude,
                            "longitude": item.hotel.longitude,
                        },
                        "available": item.available,
                        "offers": [],
                    }
                    
                    for offer in item.offers:
                        offer_info = {
                            "offer_id": offer.id,
                            "check_in_date": offer.check_in_date.isoformat(),
                            "check_out_date": offer.check_out_date.isoformat(),
                            "rate_code": offer.rate_code,
                            "room": {
                                "type": offer.room.type,
                                "category": offer.room.type_estimated.category if offer.room.type_estimated else None,
                                "beds": offer.room.type_estimated.beds if offer.room.type_estimated else None,
                                "bed_type": offer.room.type_estimated.bed_type if offer.room.type_estimated else None,
                                "description": offer.room.description.text if offer.room.description else None,
                            },
                            "guests": {
                                "adults": offer.guests.adults,
                            },
                            "price": {
                                "currency": offer.price.currency,
                                "base": offer.price.base,
                                "total": offer.price.total,
                            },
                            "policies": {
                                "payment_type": offer.policies.payment_type if offer.policies else None,
                                "cancellation_type": offer.policies.cancellation.type if offer.policies and offer.policies.cancellation else None,
                                "cancellation_description": offer.policies.cancellation.description.text if offer.policies and offer.policies.cancellation and offer.policies.cancellation.description else None,
                            } if offer.policies else None,
                        }
                        hotel_offers["offers"].append(offer_info)
                    
                    offers_data.append(hotel_offers)
                
                result = {
                    "hotel_offers": offers_data,
                    "total_hotels": len(offers_data),
                    "search_params": {
                        "hotel_ids": hotel_ids,
                        "check_in_date": check_in_date,
                        "check_out_date": check_out_date,
                        "adults": adults,
                        "room_quantity": room_quantity,
                    },
                }
                
                import json
                return json.dumps(result, indent=2)
                
            except AmadeusAuthenticationError as e:
                logger.error(f"Authentication error: {e}")
                return f"Error: Authentication failed - {str(e)}"
            except AmadeusRateLimitError as e:
                logger.error(f"Rate limit error: {e}")
                return f"Error: Rate limit exceeded - {str(e)}"
            except AmadeusAPIError as e:
                logger.error(f"API error: {e}")
                return f"Error: {str(e)}"
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                return f"Error: Unexpected error occurred - {str(e)}"
        
        @mcp.tool()
        async def health_check() -> str:
            """
            Check the health status of the Amadeus API connection.
            
            Returns:
                Status message indicating API connectivity
            """
            try:
                is_healthy = await self.client.health_check()
                if is_healthy:
                    return "✅ Amadeus API is accessible and authentication is working"
                else:
                    return "❌ Amadeus API is not accessible or authentication failed"
            except Exception as e:
                logger.error(f"Health check error: {e}")
                return f"❌ Health check failed: {str(e)}"
