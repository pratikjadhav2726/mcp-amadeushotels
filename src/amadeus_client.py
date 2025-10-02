"""
Amadeus API client for hotels services.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import date

import httpx
from pydantic import ValidationError

try:
    from .models import (
        HotelsListRequest,
        HotelsListResponse,
        HotelOffersRequest,
        HotelOffersResponse,
        AmadeusErrorResponse,
    )
except ImportError:
    # Handle direct execution
    from models import (
        HotelsListRequest,
        HotelsListResponse,
        HotelOffersRequest,
        HotelOffersResponse,
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


class AmadeusClient:
    """Client for Amadeus Hotels API."""
    
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://test.api.amadeus.com",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None
        
    async def _get_access_token(self) -> str:
        """Get or refresh access token."""
        import time
        
        # Check if we have a valid token
        if self._access_token and self._token_expires_at and time.time() < self._token_expires_at:
            return self._access_token
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/security/oauth2/token",
                    data={
                        "grant_type": "client_credentials",
                        "client_id": self.api_key,
                        "client_secret": self.api_secret,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                
                token_data = response.json()
                self._access_token = token_data["access_token"]
                # Set expiration time (subtract 60 seconds for safety)
                expires_in = token_data.get("expires_in", 1800)  # Default 30 minutes
                self._token_expires_at = time.time() + expires_in - 60
                
                logger.debug("Successfully obtained access token")
                return self._access_token
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise AmadeusAuthenticationError("Invalid API credentials")
                raise AmadeusAPIError(f"Failed to get access token: {e.response.status_code}")
            except httpx.RequestError as e:
                raise AmadeusAPIError(f"Network error while getting access token: {str(e)}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> Dict[str, Any]:
        """Make authenticated request to Amadeus API."""
        token = await self._get_access_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.amadeus+json",
        }
        
        url = f"{self.base_url}{endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                if method.upper() == "GET":
                    response = await client.get(url, headers=headers, params=params)
                else:
                    response = await client.request(method, url, headers=headers, json=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    if retry_count < self.max_retries:
                        retry_after = int(response.headers.get("Retry-After", 1))
                        logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                        await asyncio.sleep(retry_after)
                        return await self._make_request(method, endpoint, params, retry_count + 1)
                    else:
                        raise AmadeusRateLimitError("Rate limit exceeded, max retries reached")
                
                # Handle authentication errors
                if response.status_code == 401:
                    # Token might be expired, try to refresh
                    if retry_count == 0:
                        self._access_token = None
                        self._token_expires_at = None
                        return await self._make_request(method, endpoint, params, retry_count + 1)
                    else:
                        raise AmadeusAuthenticationError("Authentication failed")
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                # Try to parse error response
                try:
                    error_data = e.response.json()
                    error_response = AmadeusErrorResponse(**error_data)
                    error = error_response.errors[0] if error_response.errors else None
                    
                    if error:
                        raise AmadeusAPIError(
                            f"Amadeus API error: {error.title} - {error.detail or 'No details'}",
                            status_code=error.status,
                            error_code=error.code,
                        )
                    else:
                        raise AmadeusAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
                        
                except (ValidationError, KeyError):
                    raise AmadeusAPIError(f"HTTP {e.response.status_code}: {e.response.text}")
                    
            except httpx.RequestError as e:
                raise AmadeusAPIError(f"Network error: {str(e)}")
    
    async def search_hotels_by_location(self, request: HotelsListRequest) -> HotelsListResponse:
        """Search for hotels by location."""
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
        
        try:
            response_data = await self._make_request("GET", "/v1/reference-data/locations/hotels/by-geocode", params)
            return HotelsListResponse(**response_data)
        except ValidationError as e:
            logger.error(f"Validation error parsing hotels list response: {e}")
            raise AmadeusAPIError(f"Invalid response format: {str(e)}")
    
    async def search_hotel_offers(self, request: HotelOffersRequest) -> HotelOffersResponse:
        """Search for hotel offers."""
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
        
        try:
            response_data = await self._make_request("GET", "/v3/shopping/hotel-offers", params)
            return HotelOffersResponse(**response_data)
        except ValidationError as e:
            logger.error(f"Validation error parsing hotel offers response: {e}")
            raise AmadeusAPIError(f"Invalid response format: {str(e)}")
    
    async def health_check(self) -> bool:
        """Check if the API is accessible."""
        try:
            await self._get_access_token()
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
