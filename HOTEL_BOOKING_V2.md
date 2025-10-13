# Hotel Booking v2 Implementation (DISABLED)

## Overview
The Hotel Booking v2 functionality has been implemented but is currently **DISABLED** for security and compliance reasons. This document outlines what was added and how to enable it when ready.

## What Was Added

### 1. Models (`src/models.py`)
Added comprehensive Pydantic models for hotel booking:

- `GuestContact` - Guest contact information (phone, email)
- `GuestName` - Guest name with title, first/last name
- `Guest` - Complete guest information
- `TravelAgent` - Travel agent information
- `RoomAssociation` - Room to guest associations
- `PaymentCard` - Payment card details
- `Payment` - Payment information
- `HotelBookingRequest` - Complete booking request
- `HotelBookingResponse` - Booking response

### 2. Client Method (`src/amadeus_client.py`)
Added `book_hotel()` method (commented out):

```python
# async def book_hotel(self, request: HotelBookingRequest) -> HotelBookingResponse:
#     """Book a hotel using Hotel Booking v2 API (DISABLED)."""
```

The method:
- Prepares booking data for the Amadeus SDK
- Calls `self.client.booking.hotel_orders.post(booking_data)`
- Converts SDK response to our Pydantic model
- Handles errors appropriately

### 3. Tool Implementation (`src/tools.py`)
Added `book_hotel()` tool method (commented out):

```python
# async def book_hotel(
#     self,
#     offer_id: str,
#     guests: List[Dict[str, Any]],
#     room_associations: List[Dict[str, Any]],
#     payment: Dict[str, Any],
#     travel_agent: Optional[Dict[str, Any]] = None,
# ) -> str:
```

The tool:
- Validates all required inputs
- Creates `HotelBookingRequest` object
- Calls the client's booking method
- Returns formatted JSON response
- Handles all error cases

### 4. Tool Registration (`src/tools.py`)
Added MCP tool registration (commented out):

```python
# @mcp.tool()
# async def book_hotel(...) -> str:
```

### 5. Main Server Integration (`src/main.py`)
Added tool definition and handler (commented out):

- Tool schema definition in `list_tools()`
- Tool handler in `call_tool()`

## Current Status: DISABLED

All booking functionality is **commented out** and **disabled** for the following reasons:

1. **Security**: Payment processing requires PCI DSS compliance
2. **Compliance**: Hotel booking involves financial transactions
3. **Risk Management**: Prevents accidental bookings in test environment
4. **Legal**: Booking creates binding contracts

## How to Enable (When Ready)

### Prerequisites
Before enabling booking functionality, ensure you have:

1. **PCI DSS Compliance**: For handling payment card data
2. **Production Environment**: Switch from test to production Amadeus API
3. **Error Handling**: Comprehensive booking error management
4. **Logging**: Detailed audit trail for all bookings
5. **Testing**: Thorough testing in sandbox environment
6. **Legal Review**: Terms of service and liability considerations

### Steps to Enable

1. **Uncomment the client method** in `src/amadeus_client.py`:
   ```python
   async def book_hotel(self, request: HotelBookingRequest) -> HotelBookingResponse:
   ```

2. **Uncomment the tool method** in `src/tools.py`:
   ```python
   async def book_hotel(self, ...) -> str:
   ```

3. **Uncomment the tool registration** in `src/tools.py`:
   ```python
   @mcp.tool()
   async def book_hotel(...) -> str:
   ```

4. **Uncomment the tool definition** in `src/main.py`:
   ```python
   types.Tool(name="book_hotel", ...)
   ```

5. **Uncomment the tool handler** in `src/main.py`:
   ```python
   elif name == "book_hotel":
       result = await tools.book_hotel(**arguments)
   ```

6. **Update environment variables**:
   ```env
   AMADEUS_BASE_URL=https://api.amadeus.com  # Production URL
   ```

### Testing the Booking Tool

When enabled, the booking tool can be called with:

```json
{
  "offer_id": "hotel_offer_id_from_search",
  "guests": [
    {
      "name": {
        "firstName": "John",
        "lastName": "Doe"
      },
      "contact": {
        "email": "john.doe@example.com",
        "phone": "+1234567890"
      }
    }
  ],
  "room_associations": [
    {
      "roomId": "room_id",
      "guestIds": ["guest_id"]
    }
  ],
  "payment": {
    "method": "CREDIT_CARD",
    "card": {
      "vendorCode": "VI",
      "cardNumber": "4111111111111111",
      "expiryDate": "12/25"
    }
  }
}
```

## Security Considerations

### Payment Data Handling
- **Never log payment card data**
- **Use secure tokenization** for card storage
- **Implement PCI DSS compliance**
- **Use HTTPS for all communications**

### Booking Validation
- **Validate all guest information**
- **Verify room availability** before booking
- **Implement booking confirmation** workflow
- **Handle booking cancellations** properly

### Error Handling
- **Graceful failure** for booking errors
- **Clear error messages** for users
- **Audit trail** for all booking attempts
- **Rollback procedures** for failed bookings

## Monitoring and Logging

When enabled, implement:

1. **Booking Success/Failure Metrics**
2. **Payment Processing Logs** (without sensitive data)
3. **Guest Information Audit Trail**
4. **API Rate Limiting Monitoring**
5. **Error Rate Tracking**

## Support

For questions about enabling booking functionality:
- Review Amadeus Hotel Booking v2 API documentation
- Consult with legal/compliance teams
- Test thoroughly in sandbox environment
- Implement proper monitoring and alerting

---

**⚠️ IMPORTANT**: This functionality is disabled by default for security reasons. Only enable when you have proper compliance measures in place.
