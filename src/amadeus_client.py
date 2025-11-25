"""
Amadeus API client for hotels services using the official SDK.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from contextlib import asynccontextmanager

from amadeus import Client, Response
from amadeus.client.errors import ResponseError, ClientError, ServerError, NetworkError, AuthenticationError

try:
    from .models import (
        HotelsListRequest,
        HotelsListResponse,
        HotelOffersRequest,
        HotelOffersResponse,
        HotelBookingRequest,
        HotelBookingResponse,
        AmadeusErrorResponse,
    )
except ImportError:
    # Handle direct execution
    from models import (
        HotelsListRequest,
        HotelsListResponse,
        HotelOffersRequest,
        HotelOffersResponse,
        HotelBookingRequest,
        HotelBookingResponse,
        AmadeusErrorResponse,
    )

logger = logging.getLogger(__name__)


class AmadeusAPIError(Exception):
    """Base exception for Amadeus API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, error_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class AmadeusAuthenticationError(AmadeusAPIError):
    """Authentication error with Amadeus API."""
    pass


class AmadeusRateLimitError(AmadeusAPIError):
    """Rate limit exceeded error."""
    pass


class AmadeusClientPool:
    """Thread-safe pool of Amadeus API clients for concurrent operations."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://test.api.amadeus.com",
        timeout: float = 30.0,
        max_retries: int = 3,
        pool_size: int = 5,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.pool_size = pool_size
        
        # Determine hostname based on base_url
        if 'test.api.amadeus.com' in base_url:
            hostname = 'test'
        elif 'api.amadeus.com' in base_url:
            hostname = 'production'
        else:
            hostname = 'test'  # Default to test environment
        
        # Create thread pool for concurrent operations
        self.executor = ThreadPoolExecutor(max_workers=pool_size, thread_name_prefix="amadeus-client")
        
        # Create client pool
        self._clients = []
        self._client_lock = threading.Lock()
        
        # Initialize clients
        for i in range(pool_size):
            client = Client(
                client_id=api_key,
                client_secret=api_secret,
                hostname=hostname,
                log_level='silent'
            )
            self._clients.append(client)
    
    def get_client(self) -> Client:
        """Get an available client from the pool."""
        with self._client_lock:
            if self._clients:
                return self._clients.pop()
            else:
                # Create a new client if pool is empty
                return Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret,
                    hostname='test' if 'test.api.amadeus.com' in self.base_url else 'production',
                    log_level='silent'
                )
    
    def return_client(self, client: Client) -> None:
        """Return a client to the pool."""
        with self._client_lock:
            if len(self._clients) < self.pool_size:
                self._clients.append(client)
    
    @asynccontextmanager
    async def get_client_context(self):
        """Context manager for getting and returning a client."""
        client = self.get_client()
        try:
            yield client
        finally:
            self.return_client(client)
    
    def shutdown(self):
        """Shutdown the client pool and executor."""
        self.executor.shutdown(wait=True)


class AmadeusClient:
    """Client for Amadeus Hotels API using the official SDK with multithreading support."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://test.api.amadeus.com",
        timeout: float = 30.0,
        max_retries: int = 3,
        pool_size: int = 5,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Initialize client pool for concurrent operations
        self.client_pool = AmadeusClientPool(
            api_key=api_key,
            api_secret=api_secret,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            pool_size=pool_size
        )
        
        # Keep a single client for backward compatibility
        self.client = self.client_pool.get_client()
    
    def _handle_sdk_error(self, error: Exception) -> None:
        """Convert SDK errors to our custom exceptions."""
        if isinstance(error, AuthenticationError):
            raise AmadeusAuthenticationError("Invalid API credentials")
        elif isinstance(error, ResponseError):
            # Try to extract error details from the response
            if hasattr(error, 'response') and error.response:
                try:
                    error_data = error.response.body
                    if isinstance(error_data, dict) and 'errors' in error_data:
                        error_list = error_data['errors']
                        if error_list:
                            first_error = error_list[0]
                            status_code = first_error.get('status', error.response.status_code)
                            error_code = first_error.get('code')
                            title = first_error.get('title', 'Unknown error')
                            detail = first_error.get('detail', 'No details available')
                            
                            if status_code == 429:
                                raise AmadeusRateLimitError(f"Rate limit exceeded: {title} - {detail}")
                            else:
                                raise AmadeusAPIError(f"Amadeus API error: {title} - {detail}", status_code, error_code)
                except (KeyError, TypeError, AttributeError):
                    pass
            
            # Fallback error handling
            if error.response and error.response.status_code == 429:
                raise AmadeusRateLimitError("Rate limit exceeded")
            elif error.response and error.response.status_code == 401:
                raise AmadeusAuthenticationError("Authentication failed")
            else:
                status_code = error.response.status_code if error.response else None
                raise AmadeusAPIError(f"API error: {str(error)}", status_code)
        elif isinstance(error, (NetworkError, ClientError)):
            raise AmadeusAPIError(f"Network error: {str(error)}")
        else:
            raise AmadeusAPIError(f"Unexpected error: {str(error)}")
    
    async def search_hotels_by_location(self, request: HotelsListRequest) -> HotelsListResponse:
        """Search for hotels by location using the SDK."""
        try:
            # Prepare parameters for the SDK call
            params = {
                "latitude": request.latitude,
                "longitude": request.longitude,
                "radius": request.radius,
                "radiusUnit": request.radius_unit,
            }
            
            # Add optional parameters
            if request.chain_codes:
                params["chainCodes"] = ",".join(request.chain_codes)
            if request.amenities:
                params["amenities"] = ",".join(request.amenities)
            if request.ratings:
                params["ratings"] = ",".join(request.ratings)
            if request.hotel_source:
                params["hotelSource"] = request.hotel_source
            
            # Make the API call using the SDK
            response = self.client.reference_data.locations.hotels.by_geocode.get(**params)
            
            # Convert SDK response to our model
            # The SDK returns the data directly, so we need to wrap it in the expected format
            response_data = {
                "data": response.data,
                "meta": {}  # SDK doesn't return meta, so we provide empty dict
            }
            return HotelsListResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error searching hotels by location: {e}")
            self._handle_sdk_error(e)
    
    async def search_hotel_offers(self, request: HotelOffersRequest) -> HotelOffersResponse:
        """Search for hotel offers using the SDK."""
        try:
            # Prepare parameters for the SDK call
            params = {
                "hotelIds": ",".join(request.hotel_ids),
                "adults": request.adults,
                "checkInDate": request.check_in_date.strftime("%Y-%m-%d"),
                "checkOutDate": request.check_out_date.strftime("%Y-%m-%d"),
                "roomQuantity": request.room_quantity,
                "paymentPolicy": request.payment_policy,
                "bestRateOnly": request.best_rate_only,
                "includeClosed": request.include_closed,
            }
            
            # Add optional parameters
            if request.currency:
                params["currency"] = request.currency
            if request.price_range:
                params["priceRange"] = request.price_range
            if request.board_type:
                params["boardType"] = request.board_type
            if request.lang:
                params["lang"] = request.lang
            
            # Make the API call using the SDK
            response = self.client.shopping.hotel_offers_search.get(**params)
            
            # Convert SDK response to our model
            # The SDK returns the data directly, so we need to wrap it in the expected format
            response_data = {
                "data": response.data
            }
            return HotelOffersResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error searching hotel offers: {e}")
            self._handle_sdk_error(e)
    
    async def health_check(self) -> bool:
        """Check if the API is accessible using the SDK."""
        try:
            # Try to make a simple API call to test connectivity
            # We'll use the hotels by geocode endpoint with a simple test
            test_response = self.client.reference_data.locations.hotels.by_geocode.get(
                latitude=40.41436995,
                longitude=-3.69170868,
                radius=1
            )
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def search_hotels_by_locations_concurrent(self, requests: List[HotelsListRequest]) -> List[HotelsListResponse]:
        """Search for hotels by multiple locations concurrently."""
        async def search_single_location(request: HotelsListRequest) -> HotelsListResponse:
            """Search hotels for a single location."""
            async with self.client_pool.get_client_context() as client:
                # Prepare parameters for the SDK call
                params = {
                    "latitude": request.latitude,
                    "longitude": request.longitude,
                    "radius": request.radius,
                    "radiusUnit": request.radius_unit,
                }
                
                # Add optional parameters
                if request.chain_codes:
                    params["chainCodes"] = ",".join(request.chain_codes)
                if request.amenities:
                    params["amenities"] = ",".join(request.amenities)
                if request.ratings:
                    params["ratings"] = ",".join(request.ratings)
                if request.hotel_source:
                    params["hotelSource"] = request.hotel_source
                
                # Make the API call using the SDK
                response = client.reference_data.locations.hotels.by_geocode.get(**params)
                
                # Convert SDK response to our model
                response_data = {
                    "data": response.data,
                    "meta": {}  # SDK doesn't return meta, so we provide empty dict
                }
                return HotelsListResponse(**response_data)
        
        # Execute all searches concurrently
        tasks = [search_single_location(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions and return successful results
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error searching location {i}: {result}")
                # Return empty response for failed requests
                responses.append(HotelsListResponse(data=[], meta={}))
            else:
                responses.append(result)
        
        return responses
    
    async def search_hotel_offers_batch(self, requests: List[HotelOffersRequest]) -> List[HotelOffersResponse]:
        """Search for hotel offers for multiple requests concurrently."""
        async def search_single_offer(request: HotelOffersRequest) -> HotelOffersResponse:
            """Search hotel offers for a single request."""
            async with self.client_pool.get_client_context() as client:
                # Prepare parameters for the SDK call
                params = {
                    "hotelIds": ",".join(request.hotel_ids),
                    "adults": request.adults,
                    "checkInDate": request.check_in_date.strftime("%Y-%m-%d"),
                    "checkOutDate": request.check_out_date.strftime("%Y-%m-%d"),
                    "roomQuantity": request.room_quantity,
                    "paymentPolicy": request.payment_policy,
                    "bestRateOnly": request.best_rate_only,
                    "includeClosed": request.include_closed,
                }
                
                # Add optional parameters
                if request.currency:
                    params["currency"] = request.currency
                if request.price_range:
                    params["priceRange"] = request.price_range
                if request.board_type:
                    params["boardType"] = request.board_type
                if request.lang:
                    params["lang"] = request.lang
                
                # Make the API call using the SDK
                response = client.shopping.hotel_offers_search.get(**params)
                
                # Convert SDK response to our model
                response_data = {
                    "data": response.data
                }
                return HotelOffersResponse(**response_data)
        
        # Execute all searches concurrently
        tasks = [search_single_offer(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions and return successful results
        responses = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error searching offers {i}: {result}")
                # Return empty response for failed requests
                responses.append(HotelOffersResponse(data=[]))
            else:
                responses.append(result)
        
        return responses
    
    def shutdown(self):
        """Shutdown the client pool."""
        self.client_pool.shutdown()
    
    # DISABLED: Hotel Booking v2 functionality
    # This method is implemented but disabled for security and compliance reasons
    # Uncomment and enable only when proper payment processing and compliance measures are in place
    
    # async def book_hotel(self, request: HotelBookingRequest) -> HotelBookingResponse:
    #     """Book a hotel using Hotel Booking v2 API (DISABLED)."""
    #     try:
    #         # Prepare booking data for the SDK
    #         booking_data = {
    #             "offerId": request.offer_id,
    #             "guests": [guest.dict(by_alias=True) for guest in request.guests],
    #             "roomAssociations": [room.dict(by_alias=True) for room in request.room_associations],
    #             "payment": request.payment.dict(by_alias=True),
    #         }
    #         
    #         # Add travel agent if provided
    #         if request.travel_agent:
    #             booking_data["travelAgent"] = request.travel_agent.dict(by_alias=True)
    #         
    #         # Make the booking API call using the SDK
    #         response = self.client.booking.hotel_orders.post(booking_data)
    #         
    #         # Convert SDK response to our model
    #         response_data = {
    #             "data": response.data
    #         }
    #         return HotelBookingResponse(**response_data)
    #         
    #     except Exception as e:
    #         logger.error(f"Error booking hotel: {e}")
    #         self._handle_sdk_error(e)