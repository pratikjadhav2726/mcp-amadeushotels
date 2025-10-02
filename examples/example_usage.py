"""
Example usage of the Amadeus Hotels MCP server.

Run this example with:
    uv run examples/example_usage.py
"""

import asyncio
import json
from datetime import date, timedelta

from src.amadeus_client import AmadeusClient
from src.models import HotelsListRequest, HotelOffersRequest


async def example_hotel_search():
    """Example of searching for hotels and getting offers."""
    
    # Initialize client (you'll need to set your actual API credentials)
    client = AmadeusClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
        base_url="https://test.api.amadeus.com"
    )
    
    print("🔍 Searching for hotels near Times Square, NYC...")
    
    # Search for hotels near Times Square
    hotels_request = HotelsListRequest(
        latitude=40.7589,  # Times Square latitude
        longitude=-73.9851,  # Times Square longitude
        radius=2,  # 2km radius
        amenities=["WIFI", "FITNESS_CENTER"],  # Look for hotels with WiFi and gym
        ratings=["4", "5"],  # 4-5 star hotels only
    )
    
    try:
        hotels_response = await client.search_hotels_by_location(hotels_request)
        
        print(f"✅ Found {len(hotels_response.data)} hotels:")
        for hotel in hotels_response.data[:3]:  # Show first 3 hotels
            print(f"  🏨 {hotel.name}")
            print(f"     ID: {hotel.hotel_id}")
            print(f"     Distance: {hotel.distance.value} {hotel.distance.unit}")
            print(f"     Location: {hotel.geo_code.latitude}, {hotel.geo_code.longitude}")
            print()
        
        # Get offers for the first hotel
        if hotels_response.data:
            first_hotel = hotels_response.data[0]
            print(f"💰 Getting offers for {first_hotel.name}...")
            
            # Set dates for next week
            check_in = date.today() + timedelta(days=7)
            check_out = check_in + timedelta(days=2)
            
            offers_request = HotelOffersRequest(
                hotel_ids=[first_hotel.hotel_id],
                check_in_date=check_in,
                check_out_date=check_out,
                adults=2,
                room_quantity=1,
                currency="USD",
                best_rate_only=True,
            )
            
            offers_response = await client.search_hotel_offers(offers_request)
            
            if offers_response.data and offers_response.data[0].offers:
                offer = offers_response.data[0].offers[0]
                print(f"✅ Found offer:")
                print(f"  💵 Price: {offer.price.total} {offer.price.currency}")
                print(f"  📅 Check-in: {offer.check_in_date}")
                print(f"  📅 Check-out: {offer.check_out_date}")
                print(f"  🛏️  Room: {offer.room.type}")
                print(f"  👥 Guests: {offer.guests.adults} adults")
            else:
                print("❌ No offers found for this hotel")
                
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_health_check():
    """Example of checking API health."""
    client = AmadeusClient(
        api_key="your_api_key_here",
        api_secret="your_api_secret_here",
    )
    
    print("🏥 Checking API health...")
    is_healthy = await client.health_check()
    
    if is_healthy:
        print("✅ API is healthy and accessible")
    else:
        print("❌ API is not accessible")


if __name__ == "__main__":
    print("🚀 Amadeus Hotels API Example")
    print("=" * 50)
    
    # Note: You need to set your actual API credentials in the client initialization
    print("⚠️  Note: Update the API credentials in this script before running")
    print()
    
    # Run examples
    asyncio.run(example_health_check())
    print()
    asyncio.run(example_hotel_search())
