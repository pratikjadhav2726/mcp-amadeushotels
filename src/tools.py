"""
MCP tools for Amadeus Hotels API integration.
"""

import asyncio
import logging
from datetime import date
from typing import List, Optional, Dict, Any

from mcp.server.fastmcp import FastMCP
from mcp.types import Tool, TextContent

try:
    from .amadeus_client import AmadeusClient, AmadeusAPIError, AmadeusAuthenticationError, AmadeusRateLimitError
    from .models import HotelsListRequest, HotelOffersRequest, HotelBookingRequest
    from .config import get_app_settings
    from .cache import AmadeusCache
    from .performance_monitor import get_performance_monitor, track_operation
except ImportError:
    # Handle direct execution
    from amadeus_client import AmadeusClient, AmadeusAPIError, AmadeusAuthenticationError, AmadeusRateLimitError
    from models import HotelsListRequest, HotelOffersRequest, HotelBookingRequest
    from config import get_app_settings
    from cache import AmadeusCache
    from performance_monitor import get_performance_monitor, track_operation

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
            pool_size=self.settings.client_pool_size,
        )
        
        # Initialize cache if enabled
        if self.settings.enable_caching:
            self.cache = AmadeusCache(
                max_size=self.settings.cache_max_size,
                default_ttl=self.settings.cache_ttl
            )
            logger.info(f"Cache enabled with max_size={self.settings.cache_max_size}, ttl={self.settings.cache_ttl}s")
        else:
            self.cache = None
            logger.info("Cache disabled")
        
        # Initialize performance monitor
        self.performance_monitor = get_performance_monitor()
    
    @track_operation("search_hotels_by_location")
    async def search_hotels_by_location(
        self,
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
            
            # Make API call (with caching if enabled)
            if self.cache:
                response = await self.cache.get_or_set(
                    "search_hotels_by_location",
                    self.client.search_hotels_by_location,
                    request,
                    ttl=self.settings.cache_ttl
                )
            else:
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

    async def search_hotel_offers(
        self,
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
            
            # Make API call (with caching if enabled)
            if self.cache:
                response = await self.cache.get_or_set(
                    "search_hotel_offers",
                    self.client.search_hotel_offers,
                    request,
                    ttl=self.settings.cache_ttl
                )
            else:
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
    
    async def search_hotels_by_multiple_locations(
        self,
        locations: List[Dict[str, Any]],
        radius: Optional[int] = 5,
        radius_unit: Optional[str] = "KM",
        amenities: Optional[List[str]] = None,
        ratings: Optional[List[str]] = None,
        chain_codes: Optional[List[str]] = None,
        hotel_source: Optional[str] = "ALL",
    ) -> str:
        """
        Search for hotels near multiple locations concurrently.
        
        Args:
            locations: List of location dictionaries with 'latitude' and 'longitude' keys
            radius: Search radius in the specified units (default: 5)
            radius_unit: Unit for radius - "KM" or "MILE" (default: "KM")
            amenities: List of desired amenities (e.g., ["SWIMMING_POOL", "SPA", "WIFI"])
            ratings: Hotel star ratings (1-5)
            chain_codes: Hotel chain codes (2-character codes)
            hotel_source: Hotel source - "BEDBANK", "DIRECTCHAIN", or "ALL" (default: "ALL")
        
        Returns:
            JSON string containing hotel information for all locations
        """
        try:
            # Validate inputs
            if not locations:
                return "Error: At least one location is required"
            
            # Validate each location
            for i, location in enumerate(locations):
                if 'latitude' not in location or 'longitude' not in location:
                    return f"Error: Location {i} missing latitude or longitude"
                
                lat, lon = location['latitude'], location['longitude']
                if not -90 <= lat <= 90:
                    return f"Error: Location {i} latitude must be between -90 and 90 degrees"
                if not -180 <= lon <= 180:
                    return f"Error: Location {i} longitude must be between -180 and 180 degrees"
            
            if radius and radius <= 0:
                return "Error: Radius must be positive"
            
            # Create requests for all locations
            requests = []
            for location in locations:
                request = HotelsListRequest(
                    latitude=location['latitude'],
                    longitude=location['longitude'],
                    radius=radius,
                    radius_unit=radius_unit,
                    amenities=amenities,
                    ratings=ratings,
                    chain_codes=chain_codes,
                    hotel_source=hotel_source,
                )
                requests.append(request)
            
            # Make concurrent API calls
            responses = await self.client.search_hotels_by_locations_concurrent(requests)
            
            # Format response
            all_hotels_data = []
            total_hotels = 0
            
            for i, response in enumerate(responses):
                location_hotels = []
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
                        "search_location_index": i,
                    }
                    location_hotels.append(hotel_info)
                
                all_hotels_data.extend(location_hotels)
                total_hotels += len(location_hotels)
            
            result = {
                "hotels": all_hotels_data,
                "total_count": total_hotels,
                "locations_searched": len(locations),
                "search_params": {
                    "radius": radius,
                    "radius_unit": radius_unit,
                    "amenities": amenities,
                    "ratings": ratings,
                    "chain_codes": chain_codes,
                    "hotel_source": hotel_source,
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
    
    async def search_hotel_offers_batch(
        self,
        hotel_offer_requests: List[Dict[str, Any]],
    ) -> str:
        """
        Search for hotel offers for multiple requests concurrently.
        
        Args:
            hotel_offer_requests: List of hotel offer request dictionaries
        
        Returns:
            JSON string containing hotel offers for all requests
        """
        try:
            # Validate inputs
            if not hotel_offer_requests:
                return "Error: At least one hotel offer request is required"
            
            # Validate and create requests
            requests = []
            for i, req_data in enumerate(hotel_offer_requests):
                # Validate required fields
                required_fields = ['hotel_ids', 'check_in_date', 'check_out_date']
                for field in required_fields:
                    if field not in req_data:
                        return f"Error: Request {i} missing required field: {field}"
                
                # Parse dates
                try:
                    check_in = date.fromisoformat(req_data['check_in_date'])
                    check_out = date.fromisoformat(req_data['check_out_date'])
                except ValueError as e:
                    return f"Error: Request {i} invalid date format - {str(e)}"
                
                if check_out <= check_in:
                    return f"Error: Request {i} check-out date must be after check-in date"
                
                # Create request
                request = HotelOffersRequest(
                    hotel_ids=req_data['hotel_ids'],
                    adults=req_data.get('adults', 1),
                    check_in_date=check_in,
                    check_out_date=check_out,
                    room_quantity=req_data.get('room_quantity', 1),
                    currency=req_data.get('currency'),
                    price_range=req_data.get('price_range'),
                    payment_policy=req_data.get('payment_policy', 'NONE'),
                    board_type=req_data.get('board_type'),
                    include_closed=req_data.get('include_closed', False),
                    best_rate_only=req_data.get('best_rate_only', True),
                    lang=req_data.get('lang'),
                )
                requests.append(request)
            
            # Make concurrent API calls
            responses = await self.client.search_hotel_offers_batch(requests)
            
            # Format response
            all_offers_data = []
            total_hotels = 0
            
            for i, response in enumerate(responses):
                request_offers = []
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
                        "request_index": i,
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
                    
                    request_offers.append(hotel_offers)
                
                all_offers_data.extend(request_offers)
                total_hotels += len(request_offers)
            
            result = {
                "hotel_offers": all_offers_data,
                "total_hotels": total_hotels,
                "requests_processed": len(hotel_offer_requests),
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
    
    async def get_cache_stats(self) -> str:
        """
        Get cache statistics and performance metrics.
        
        Returns:
            JSON string containing cache statistics
        """
        try:
            if not self.cache:
                return "Cache is disabled"
            
            stats = self.cache.stats()
            
            result = {
                "cache_enabled": True,
                "statistics": stats,
                "performance_metrics": {
                    "hit_rate_percentage": round(stats['hit_rate'] * 100, 2),
                    "total_requests": stats['total_requests'],
                    "cache_hits": stats['hit_count'],
                    "cache_misses": stats['miss_count'],
                }
            }
            
            import json
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return f"Error: {str(e)}"
    
    async def clear_cache(self) -> str:
        """
        Clear the cache.
        
        Returns:
            Status message
        """
        try:
            if not self.cache:
                return "Cache is disabled"
            
            self.cache.clear()
            return "✅ Cache cleared successfully"
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return f"Error: {str(e)}"
    
    async def get_performance_stats(self) -> str:
        """
        Get performance statistics for multithreaded operations.
        
        Returns:
            JSON string containing performance metrics
        """
        try:
            summary = self.performance_monitor.get_summary()
            
            result = {
                "performance_summary": summary,
                "active_operations": len(self.performance_monitor.get_active_operations()),
                "multithreading_enabled": True,
                "client_pool_size": self.settings.client_pool_size,
                "max_concurrent_requests": self.settings.max_concurrent_requests,
                "cache_enabled": self.settings.enable_caching,
            }
            
            import json
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return f"Error: {str(e)}"
    
    # DISABLED: Hotel Booking v2 functionality
    # This tool is implemented but disabled for security and compliance reasons
    # Uncomment and enable only when proper payment processing and compliance measures are in place
    
    # async def book_hotel(
    #     self,
    #     offer_id: str,
    #     guests: List[Dict[str, Any]],
    #     room_associations: List[Dict[str, Any]],
    #     payment: Dict[str, Any],
    #     travel_agent: Optional[Dict[str, Any]] = None,
    # ) -> str:
    #     """
    #     Book a hotel using Hotel Booking v2 API (DISABLED).
    #     
    #     Args:
    #         offer_id: Hotel offer ID from search results
    #         guests: List of guest information
    #         room_associations: Room to guest associations
    #         payment: Payment information
    #         travel_agent: Optional travel agent information
    #     
    #     Returns:
    #         JSON string containing booking confirmation
    #     """
    #     try:
    #         # Validate inputs
    #         if not offer_id:
    #             return "Error: Offer ID is required"
    #         if not guests:
    #             return "Error: At least one guest is required"
    #         if not room_associations:
    #             return "Error: Room associations are required"
    #         if not payment:
    #             return "Error: Payment information is required"
    #         
    #         # Create request
    #         request = HotelBookingRequest(
    #             offer_id=offer_id,
    #             guests=guests,
    #             room_associations=room_associations,
    #             payment=payment,
    #             travel_agent=travel_agent,
    #         )
    #         
    #         # Make API call
    #         response = await self.client.book_hotel(request)
    #         
    #         # Format response
    #         result = {
    #             "booking_confirmation": response.data,
    #             "status": "success",
    #             "message": "Hotel booking completed successfully"
    #         }
    #         
    #         import json
    #         return json.dumps(result, indent=2)
    #         
    #     except AmadeusAuthenticationError as e:
    #         logger.error(f"Authentication error: {e}")
    #         return f"Error: Authentication failed - {str(e)}"
    #     except AmadeusRateLimitError as e:
    #         logger.error(f"Rate limit error: {e}")
    #         return f"Error: Rate limit exceeded - {str(e)}"
    #     except AmadeusAPIError as e:
    #         logger.error(f"API error: {e}")
    #         return f"Error: {str(e)}"
    #     except Exception as e:
    #         logger.error(f"Unexpected error: {e}")
    #         return f"Error: Unexpected error occurred - {str(e)}"
    
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
            return await self.search_hotels_by_location(
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                radius_unit=radius_unit,
                amenities=amenities,
                ratings=ratings,
                chain_codes=chain_codes,
                hotel_source=hotel_source,
            )
        
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
            return await self.search_hotel_offers(
                hotel_ids=hotel_ids,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                adults=adults,
                room_quantity=room_quantity,
                currency=currency,
                price_range=price_range,
                payment_policy=payment_policy,
                board_type=board_type,
                include_closed=include_closed,
                best_rate_only=best_rate_only,
                lang=lang,
            )
        
        @mcp.tool()
        async def health_check() -> str:
            """
            Check the health status of the Amadeus API connection.
            
            Returns:
                Status message indicating API connectivity
            """
            return await self.health_check()
        
        # DISABLED: Hotel Booking v2 tool registration
        # This tool is implemented but disabled for security and compliance reasons
        # Uncomment and enable only when proper payment processing and compliance measures are in place
        
        # @mcp.tool()
        # async def book_hotel(
        #     offer_id: str,
        #     guests: List[Dict[str, Any]],
        #     room_associations: List[Dict[str, Any]],
        #     payment: Dict[str, Any],
        #     travel_agent: Optional[Dict[str, Any]] = None,
        # ) -> str:
        #     """
        #     Book a hotel using Hotel Booking v2 API (DISABLED).
        #     
        #     Args:
        #         offer_id: Hotel offer ID from search results
        #         guests: List of guest information
        #         room_associations: Room to guest associations
        #         payment: Payment information
        #         travel_agent: Optional travel agent information
        #     
        #     Returns:
        #         JSON string containing booking confirmation
        #     """
        #     return await self.book_hotel(
        #         offer_id=offer_id,
        #         guests=guests,
        #         room_associations=room_associations,
        #         payment=payment,
        #         travel_agent=travel_agent,
        #     )
