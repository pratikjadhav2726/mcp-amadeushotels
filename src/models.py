"""
Pydantic models for Amadeus Hotels API requests and responses.
"""

from datetime import date
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, validator


class GeoCode(BaseModel):
    """Geographic coordinates."""
    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")


class Address(BaseModel):
    """Hotel address information."""
    country_code: Optional[str] = Field(None, alias="countryCode", description="ISO country code")


class Distance(BaseModel):
    """Distance information."""
    value: float = Field(..., description="Distance value")
    unit: str = Field(..., description="Distance unit (KM or MILE)")


class Hotel(BaseModel):
    """Hotel information from hotels list API."""
    chain_code: Optional[str] = Field(None, alias="chainCode", description="Hotel chain code")
    iata_code: Optional[str] = Field(None, alias="iataCode", description="IATA code")
    dupe_id: Optional[int] = Field(None, alias="dupeId", description="Duplicate ID")
    name: str = Field(..., description="Hotel name")
    hotel_id: str = Field(..., alias="hotelId", description="Amadeus hotel ID")
    geo_code: GeoCode = Field(..., alias="geoCode", description="Hotel coordinates")
    address: Optional[Address] = Field(None, description="Hotel address")
    distance: Optional[Distance] = Field(None, description="Distance from search point")


class HotelsListResponse(BaseModel):
    """Response from hotels list API."""
    data: List[Hotel] = Field(..., description="List of hotels")
    meta: Dict[str, Any] = Field(..., description="Response metadata")


class HotelsListRequest(BaseModel):
    """Request parameters for hotels list API."""
    latitude: float = Field(..., description="Latitude of search point")
    longitude: float = Field(..., description="Longitude of search point")
    radius: Optional[int] = Field(5, description="Search radius in specified units")
    radius_unit: Optional[str] = Field("KM", description="Unit for radius (KM or MILE)")
    chain_codes: Optional[List[str]] = Field(None, description="Hotel chain codes")
    amenities: Optional[List[str]] = Field(None, description="Desired amenities")
    ratings: Optional[List[str]] = Field(None, description="Hotel star ratings")
    hotel_source: Optional[str] = Field("ALL", description="Hotel source (BEDBANK, DIRECTCHAIN, ALL)")

    @validator('radius_unit')
    def validate_radius_unit(cls, v):
        if v not in ['KM', 'MILE']:
            raise ValueError('radius_unit must be either KM or MILE')
        return v

    @validator('hotel_source')
    def validate_hotel_source(cls, v):
        if v not in ['BEDBANK', 'DIRECTCHAIN', 'ALL']:
            raise ValueError('hotel_source must be BEDBANK, DIRECTCHAIN, or ALL')
        return v

    @validator('ratings')
    def validate_ratings(cls, v):
        if v:
            valid_ratings = ['1', '2', '3', '4', '5']
            for rating in v:
                if rating not in valid_ratings:
                    raise ValueError(f'Rating must be one of {valid_ratings}')
        return v


class RoomTypeEstimated(BaseModel):
    """Estimated room type information."""
    category: Optional[str] = Field(None, description="Room category")
    beds: Optional[int] = Field(None, description="Number of beds")
    bed_type: Optional[str] = Field(None, alias="bedType", description="Type of bed")


class RoomDescription(BaseModel):
    """Room description."""
    text: str = Field(..., description="Description text")
    lang: str = Field(..., description="Language code")


class Room(BaseModel):
    """Room information."""
    type: str = Field(..., description="Room type code")
    type_estimated: Optional[RoomTypeEstimated] = Field(None, alias="typeEstimated")
    description: Optional[RoomDescription] = Field(None, description="Room description")


class Guests(BaseModel):
    """Guest information."""
    adults: int = Field(..., description="Number of adult guests")


class PriceVariations(BaseModel):
    """Price variations."""
    average: Optional[Dict[str, str]] = Field(None, description="Average price")
    changes: Optional[List[Dict[str, Any]]] = Field(None, description="Price changes")


class Price(BaseModel):
    """Price information."""
    currency: str = Field(..., description="Currency code")
    base: str = Field(..., description="Base price")
    total: str = Field(..., description="Total price")
    variations: Optional[PriceVariations] = Field(None, description="Price variations")


class CancellationPolicy(BaseModel):
    """Cancellation policy."""
    description: Optional[Dict[str, str]] = Field(None, description="Policy description")
    type: Optional[str] = Field(None, description="Policy type")


class Policies(BaseModel):
    """Hotel policies."""
    payment_type: Optional[str] = Field(None, alias="paymentType", description="Payment type")
    cancellation: Optional[CancellationPolicy] = Field(None, description="Cancellation policy")


class HotelOffer(BaseModel):
    """Individual hotel offer."""
    id: str = Field(..., description="Offer ID")
    check_in_date: date = Field(..., alias="checkInDate", description="Check-in date")
    check_out_date: date = Field(..., alias="checkOutDate", description="Check-out date")
    rate_code: Optional[str] = Field(None, alias="rateCode", description="Rate code")
    rate_family_estimated: Optional[Dict[str, str]] = Field(None, alias="rateFamilyEstimated")
    room: Room = Field(..., description="Room information")
    guests: Guests = Field(..., description="Guest information")
    price: Price = Field(..., description="Price information")
    policies: Optional[Policies] = Field(None, description="Hotel policies")


class HotelOffersHotel(BaseModel):
    """Hotel information in offers response."""
    type: str = Field(..., description="Type")
    hotel_id: str = Field(..., alias="hotelId", description="Hotel ID")
    chain_code: Optional[str] = Field(None, alias="chainCode", description="Chain code")
    dupe_id: Optional[str] = Field(None, alias="dupeId", description="Duplicate ID")
    name: str = Field(..., description="Hotel name")
    city_code: Optional[str] = Field(None, alias="cityCode", description="City code")
    latitude: Optional[float] = Field(None, description="Latitude")
    longitude: Optional[float] = Field(None, description="Longitude")


class HotelOffersResponseItem(BaseModel):
    """Individual hotel offers response item."""
    type: str = Field(..., description="Response type")
    hotel: HotelOffersHotel = Field(..., description="Hotel information")
    available: bool = Field(..., description="Availability status")
    offers: List[HotelOffer] = Field(..., description="Available offers")


class HotelOffersResponse(BaseModel):
    """Response from hotel offers API."""
    data: List[HotelOffersResponseItem] = Field(..., description="Hotel offers data")


class HotelOffersRequest(BaseModel):
    """Request parameters for hotel offers API."""
    hotel_ids: List[str] = Field(..., description="List of Amadeus hotel IDs")
    adults: Optional[int] = Field(1, description="Number of adult guests")
    check_in_date: date = Field(..., description="Check-in date")
    check_out_date: date = Field(..., description="Check-out date")
    room_quantity: Optional[int] = Field(1, description="Number of rooms")
    currency: Optional[str] = Field(None, description="Currency code")
    price_range: Optional[str] = Field(None, description="Price range filter")
    payment_policy: Optional[str] = Field("NONE", description="Payment policy filter")
    board_type: Optional[str] = Field(None, description="Board type filter")
    include_closed: Optional[bool] = Field(False, description="Include sold out properties")
    best_rate_only: Optional[bool] = Field(True, description="Return only best rates")
    lang: Optional[str] = Field(None, description="Language code")

    @validator('payment_policy')
    def validate_payment_policy(cls, v):
        if v not in ['GUARANTEE', 'DEPOSIT', 'NONE']:
            raise ValueError('payment_policy must be GUARANTEE, DEPOSIT, or NONE')
        return v

    @validator('board_type')
    def validate_board_type(cls, v):
        if v and v not in ['ROOM_ONLY', 'BREAKFAST', 'HALF_BOARD', 'FULL_BOARD', 'ALL_INCLUSIVE']:
            raise ValueError('board_type must be one of: ROOM_ONLY, BREAKFAST, HALF_BOARD, FULL_BOARD, ALL_INCLUSIVE')
        return v

    @validator('check_out_date')
    def validate_check_out_date(cls, v, values):
        if 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('check_out_date must be after check_in_date')
        return v


class AmadeusError(BaseModel):
    """Amadeus API error response."""
    status: int = Field(..., description="HTTP status code")
    code: int = Field(..., description="Error code")
    title: str = Field(..., description="Error title")
    detail: Optional[str] = Field(None, description="Error detail")
    source: Optional[Dict[str, Any]] = Field(None, description="Error source")
    documentation: Optional[str] = Field(None, description="Documentation link")


class AmadeusErrorResponse(BaseModel):
    """Amadeus API error response wrapper."""
    errors: List[AmadeusError] = Field(..., description="List of errors")


# Hotel Booking v2 Models (DISABLED - for future implementation)

class GuestContact(BaseModel):
    """Guest contact information."""
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")


class GuestName(BaseModel):
    """Guest name information."""
    title: Optional[str] = Field(None, description="Title (Mr, Mrs, etc.)")
    first_name: str = Field(..., alias="firstName", description="First name")
    last_name: str = Field(..., alias="lastName", description="Last name")


class Guest(BaseModel):
    """Guest information for booking."""
    contact: Optional[GuestContact] = Field(None, description="Contact information")
    name: GuestName = Field(..., description="Guest name")


class TravelAgent(BaseModel):
    """Travel agent information."""
    name: Optional[str] = Field(None, description="Travel agent name")
    code: Optional[str] = Field(None, description="Travel agent code")


class RoomAssociation(BaseModel):
    """Room association for booking."""
    room_id: str = Field(..., alias="roomId", description="Room ID")
    guest_ids: List[str] = Field(..., alias="guestIds", description="Guest IDs")


class PaymentCard(BaseModel):
    """Payment card information."""
    vendor_code: str = Field(..., alias="vendorCode", description="Card vendor code")
    card_number: str = Field(..., alias="cardNumber", description="Card number")
    expiry_date: str = Field(..., alias="expiryDate", description="Expiry date (MM/YY)")


class Payment(BaseModel):
    """Payment information."""
    method: str = Field(..., description="Payment method")
    card: Optional[PaymentCard] = Field(None, description="Card information")


class HotelBookingRequest(BaseModel):
    """Request for hotel booking."""
    offer_id: str = Field(..., alias="offerId", description="Hotel offer ID")
    guests: List[Guest] = Field(..., description="List of guests")
    travel_agent: Optional[TravelAgent] = Field(None, alias="travelAgent", description="Travel agent info")
    room_associations: List[RoomAssociation] = Field(..., alias="roomAssociations", description="Room associations")
    payment: Payment = Field(..., description="Payment information")


class HotelBookingResponse(BaseModel):
    """Response from hotel booking API."""
    data: Dict[str, Any] = Field(..., description="Booking response data")
