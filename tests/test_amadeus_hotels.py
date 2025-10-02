"""
Basic tests for the Amadeus Hotels MCP server.
"""

import pytest
import asyncio
from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

from src.models import HotelsListRequest, HotelOffersRequest
from src.amadeus_client import AmadeusClient, AmadeusAPIError
from src.tools import AmadeusHotelsTools


class TestAmadeusClient:
    """Test cases for AmadeusClient."""
    
    @pytest.fixture
    def client(self):
        return AmadeusClient(
            api_key="test_key",
            api_secret="test_secret",
            base_url="https://test.api.amadeus.com"
        )
    
    @pytest.mark.asyncio
    async def test_search_hotels_by_location_success(self, client):
        """Test successful hotel search by location."""
        mock_response = {
            "data": [
                {
                    "hotelId": "TEST123",
                    "name": "Test Hotel",
                    "geoCode": {"latitude": 40.7128, "longitude": -74.0060},
                    "distance": {"value": 1.5, "unit": "KM"}
                }
            ],
            "meta": {"count": 1}
        }
        
        with patch.object(client, '_make_request', return_value=mock_response):
            request = HotelsListRequest(
                latitude=40.7128,
                longitude=-74.0060,
                radius=5
            )
            response = await client.search_hotels_by_location(request)
            
            assert len(response.data) == 1
            assert response.data[0].hotel_id == "TEST123"
            assert response.data[0].name == "Test Hotel"
    
    @pytest.mark.asyncio
    async def test_search_hotel_offers_success(self, client):
        """Test successful hotel offers search."""
        mock_response = {
            "data": [
                {
                    "type": "hotel-offers",
                    "hotel": {
                        "hotelId": "TEST123",
                        "name": "Test Hotel",
                        "latitude": 40.7128,
                        "longitude": -74.0060
                    },
                    "available": True,
                    "offers": [
                        {
                            "id": "OFFER123",
                            "checkInDate": "2024-01-01",
                            "checkOutDate": "2024-01-02",
                            "room": {"type": "STANDARD"},
                            "guests": {"adults": 2},
                            "price": {
                                "currency": "USD",
                                "base": "100.00",
                                "total": "120.00"
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch.object(client, '_make_request', return_value=mock_response):
            request = HotelOffersRequest(
                hotel_ids=["TEST123"],
                check_in_date=date(2024, 1, 1),
                check_out_date=date(2024, 1, 2),
                adults=2
            )
            response = await client.search_hotel_offers(request)
            
            assert len(response.data) == 1
            assert response.data[0].hotel.hotel_id == "TEST123"
            assert len(response.data[0].offers) == 1
            assert response.data[0].offers[0].price.currency == "USD"


class TestAmadeusHotelsTools:
    """Test cases for AmadeusHotelsTools."""
    
    @pytest.fixture
    def tools(self):
        with patch('src.tools.get_app_settings') as mock_settings:
            mock_settings.return_value.amadeus_api_key = "test_key"
            mock_settings.return_value.amadeus_api_secret = "test_secret"
            mock_settings.return_value.amadeus_base_url = "https://test.api.amadeus.com"
            mock_settings.return_value.api_timeout = 30.0
            mock_settings.return_value.max_retries = 3
            return AmadeusHotelsTools()
    
    @pytest.mark.asyncio
    async def test_search_hotels_by_location_tool(self, tools):
        """Test the search_hotels_by_location tool."""
        mock_response = {
            "data": [
                {
                    "hotelId": "TEST123",
                    "name": "Test Hotel",
                    "geoCode": {"latitude": 40.7128, "longitude": -74.0060},
                    "distance": {"value": 1.5, "unit": "KM"}
                }
            ],
            "meta": {"count": 1}
        }
        
        with patch.object(tools.client, 'search_hotels_by_location', return_value=mock_response):
            result = await tools.search_hotels_by_location(
                latitude=40.7128,
                longitude=-74.0060,
                radius=5
            )
            
            assert "hotels" in result
            assert "total_count" in result
            assert "search_params" in result
    
    @pytest.mark.asyncio
    async def test_search_hotel_offers_tool(self, tools):
        """Test the search_hotel_offers tool."""
        mock_response = {
            "data": [
                {
                    "type": "hotel-offers",
                    "hotel": {
                        "hotelId": "TEST123",
                        "name": "Test Hotel"
                    },
                    "available": True,
                    "offers": [
                        {
                            "id": "OFFER123",
                            "checkInDate": "2024-01-01",
                            "checkOutDate": "2024-01-02",
                            "room": {"type": "STANDARD"},
                            "guests": {"adults": 2},
                            "price": {
                                "currency": "USD",
                                "base": "100.00",
                                "total": "120.00"
                            }
                        }
                    ]
                }
            ]
        }
        
        with patch.object(tools.client, 'search_hotel_offers', return_value=mock_response):
            result = await tools.search_hotel_offers(
                hotel_ids=["TEST123"],
                check_in_date="2024-01-01",
                check_out_date="2024-01-02",
                adults=2
            )
            
            assert "hotel_offers" in result
            assert "total_hotels" in result
            assert "search_params" in result


if __name__ == "__main__":
    pytest.main([__file__])
