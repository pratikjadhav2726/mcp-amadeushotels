I want to create a mcp server to get list of hotels in a geocode or city and how far are they from the location.


this is api reference of amadeus hotels list api: the tool should take use of this:
 Name	Description
latitude *
number
(query)
The latitude of the searched geographical point expressed in geometric degrees.

Example : 41.397158

41.397158
longitude *
number
(query)
The longitude of the searched geographical point expressed in geometric degrees.

Example : 2.160873

2.160873
radius
integer
(query)
Maximum distance from the geographical coordinates expressed in defined units. The default unit is metric kilometer.

Default value : 5

5
radiusUnit
string
(query)
Unit of measurement used to express the radius. It can be either metric kilometer or imperial mile.

Available values : KM, MILE

Default value : KM


KM
chainCodes
array[string]
(query)
Array of hotel chain codes. Each code is a string consisted of 2 capital alphabetic characters.

amenities
array[string]
(query)
List of amenities.

Available values : SWIMMING_POOL, SPA, FITNESS_CENTER, AIR_CONDITIONING, RESTAURANT, PARKING, PETS_ALLOWED, AIRPORT_SHUTTLE, BUSINESS_CENTER, DISABLED_FACILITIES, WIFI, MEETING_ROOMS, NO_KID_ALLOWED, TENNIS, GOLF, KITCHEN, ANIMAL_WATCHING, BABY-SITTING, BEACH, CASINO, JACUZZI, SAUNA, SOLARIUM, MASSAGE, VALET_PARKING, BAR or LOUNGE, KIDS_WELCOME, NO_PORN_FILMS, MINIBAR, TELEVISION, WI-FI_IN_ROOM, ROOM_SERVICE, GUARDED_PARKG, SERV_SPEC_MENU

--SWIMMING_POOLSPAFITNESS_CENTERAIR_CONDITIONINGRESTAURANTPARKINGPETS_ALLOWEDAIRPORT_SHUTTLEBUSINESS_CENTERDISABLED_FACILITIESWIFIMEETING_ROOMSNO_KID_ALLOWEDTENNISGOLFKITCHENANIMAL_WATCHINGBABY-SITTINGBEACHCASINOJACUZZISAUNASOLARIUMMASSAGEVALET_PARKINGBAR or LOUNGEKIDS_WELCOMENO_PORN_FILMSMINIBARTELEVISIONWI-FI_IN_ROOMROOM_SERVICEGUARDED_PARKGSERV_SPEC_MENU
ratings
array[string]
(query)
Hotel stars. Up to four values can be requested at the same time in a comma separated list.

Available values : 1, 2, 3, 4, 5

--12345
hotelSource
string
(query)
Hotel source with values BEDBANK for aggregators, DIRECTCHAIN for GDS/Distribution and ALL for both.

Available values : BEDBANK, DIRECTCHAIN, ALL

Default value : ALL


ALL
Responses
Code	Description	Links
200	
OK

Media type

application/vnd.amadeus+json
Controls Accept header.
Examples

Successful Reply
Example Value
Schema
{
  "data": [
    {
      "chainCode": "OI",
      "iataCode": "SXD",
      "dupeId": 700118746,
      "name": "HOTEL OMEGA - VALBONNE",
      "hotelId": "OISXD968",
      "geoCode": {
        "latitude": 43.61428,
        "longitude": 7.05464
      },
      "address": {
        "countryCode": "FR"
      },
      "distance": {
        "value": 0.73,
        "unit": "KM"
      }
    },
    {
      "chainCode": "DH",
      "iataCode": "SCR",
      "dupeId": 505001770,
      "name": "CHECK SINGLE CIF DHSCRMS8",
      "hotelId": "DHSCRMS8",
      "geoCode": {
        "latitude": 43.62215,
        "longitude": 7.04024
      },
      "distance": {
        "value": 0.82,
        "unit": "KM"
      }
    },
    {
      "chainCode": "DH",
      "iataCode": "VLI",
      "dupeId": 504621595,
      "name": "CHECK SINGLE CIF DHVLIMS8",
      "hotelId": "DHVLIMS8",
      "geoCode": {
        "latitude": 43.62215,
        "longitude": 7.04024
      },
      "distance": {
        "value": 0.82,
        "unit": "KM"
      }
    },
    {
      "chainCode": "DH",
      "iataCode": "AET",
      "dupeId": 504621441,
      "name": "CHECK SINGLE CIF DHAETMS8",
      "hotelId": "DHAETMS8",
      "geoCode": {
        "latitude": 43.62215,
        "longitude": 7.04024
      },
      "address": {
        "countryCode": "US"
      },
      "distance": {
        "value": 0.82,
        "unit": "KM"
      }
    },
    {
      "chainCode": "DH",
      "iataCode": "NYC",
      "dupeId": 504621445,
      "name": "CHECK SINGLE CIF DHNYCMS8",
      "hotelId": "DHNYCMS8",
      "geoCode": {
        "latitude": 43.62215,
        "longitude": 7.04024
      },
      "address": {
        "countryCode": "US"
      },
      "distance": {
        "value": 0.82,
        "unit": "KM"
      }
    }
  ],
  "meta": {
    "count": 5,
    "links": {
      "self": "http://test.api.amadeus.com/reference-data/locations/hotels/by-geocode?latitude=43.61999752&longitude=7.0499998&radius=1"
    }
  }
}
No links
400	
Bad Request

Code	Title
00001	CHECK FORMAT
00477	INVALID FORMAT
00009	CHECK CITY CODE
01157	INVALID CITY CODE
03237	PROPERTY CODE NOT FOUND IN SYSTEM
01257	INVALID PROPERTY CODE
00895	NOTHING FOUND FOR REQUESTED CITY
01271	GUEST RECORD NOT FOUND
11126	NO PROPERTIES FOUND FOR RP/DI REQUESTED
Media type

application/vnd.amadeus+json
Examples

Invalid Format
Example Value
Schema
{
  "errors": [
    {
      "status": 400,
      "code": 477,
      "title": "INVALID FORMAT",
      "detail": "invalid query parameter format",
      "source": {
        "parameter": "longitude",
        "example": 41.397158
      }
    }
  ]
}
No links
500	
Internal Server Error

Media type

application/vnd.amadeus+json
Example Value
Schema
{
  "errors": [
    {
      "status": 500,
      "code": 141,
      "title": "SYSTEM ERROR HAS OCCURRED"
    }
  ]
}


2nd tool should take use of the hotel search api to find the price of the hotels with the number of guests:

shopping


GET
/shopping/hotel-offers
getMultiHotelOffers
Parameters
Name	Description
hotelIds *
array[string]
(query)
Amadeus property codes on 8 chars. Mandatory parameter for a search by predefined list of hotels.

Example : List [ "MCLONGHM" ]

MCLONGHM
adults
integer($int32)
(query)
Number of adult guests (1-9) per room.

Default value : 1

Example : 1

1
checkInDate
string($date)
(query)
Check-in date of the stay (hotel local date). Format YYYY-MM-DD. The lowest accepted value is the present date (no dates in the past). If not present, the default value will be today's date in the GMT time zone.

Example : 2023-11-22

2023-11-22
checkOutDate
string($date)
(query)
Check-out date of the stay (hotel local date). Format YYYY-MM-DD. The lowest accepted value is checkInDate+1. If not present, it will default to checkInDate +1.

checkOutDate
countryOfResidence
string
(query)
Code of the country of residence of the traveler expressed using ISO 3166-1 format.

countryOfResidence
roomQuantity
integer($int32)
(query)
Number of rooms requested (1-9).

Default value : 1

1
priceRange
string
(query)
Filter hotel offers by price per night interval (ex: 200-300 or -300 or 100).
It is mandatory to include a currency when this field is set.

priceRange
currency
string
(query)
Use this parameter to request a specific currency. ISO currency code (http://www.iso.org/iso/home/standards/currency_codes.htm).
If a hotel does not support the requested currency, the prices for the hotel will be returned in the local currency of the hotel.

currency
paymentPolicy
string
(query)
Filter the response based on a specific payment type. NONE means all types (default).

Available values : GUARANTEE, DEPOSIT, NONE

Default value : NONE


NONE
boardType
string
(query)
Filter response based on available meals:
* ROOM_ONLY = Room Only
* BREAKFAST = Breakfast
* HALF_BOARD = Diner & Breakfast (only for Aggregators)
* FULL_BOARD = Full Board (only for Aggregators)
* ALL_INCLUSIVE = All Inclusive (only for Aggregators)

Available values : ROOM_ONLY, BREAKFAST, HALF_BOARD, FULL_BOARD, ALL_INCLUSIVE


--
includeClosed
boolean
(query)
Show all properties (include sold out) or available only. For sold out properties, please check availability on other dates.


--
bestRateOnly
boolean
(query)
Used to return only the cheapest offer per hotel or all available offers.

Default value : true


true
lang
string
(query)
Requested language of descriptive texts.
Examples: FR , fr , fr-FR.
If a language is not available the text will be returned in english.
ISO language code (https://www.iso.org/iso-639-language-codes.html).

lang
Responses
Response content type

application/vnd.amadeus+json
Code	Description
200	
OK

Example Value
Model
{
  "data": [
    {
      "type": "hotel-offers",
      "hotel": {
        "type": "hotel",
        "hotelId": "MCLONGHM",
        "chainCode": "MC",
        "dupeId": "700031300",
        "name": "JW Marriott Grosvenor House London",
        "cityCode": "LON",
        "latitude": 51.50988,
        "longitude": -0.15509
      },
      "available": true,
      "offers": [
        {
          "id": "TSXOJ6LFQ2",
          "checkInDate": "2023-11-22",
          "checkOutDate": "2023-11-23",
          "rateCode": "V  ",
          "rateFamilyEstimated": {
            "code": "PRO",
            "type": "P"
          },
          "room": {
            "type": "ELE",
            "typeEstimated": {
              "category": "EXECUTIVE_ROOM",
              "beds": 1,
              "bedType": "DOUBLE"
            },
            "description": {
              "text": "Prepay Non-refundable Non-changeable, prepay in full\nExecutive King Room, Executive Lounge Access,\n1 King, 35sqm/377sqft-40sqm/430sqft, Wireless",
              "lang": "EN"
            }
          },
          "guests": {
            "adults": 1
          },
          "price": {
            "currency": "GBP",
            "base": "716.00",
            "total": "716.00",
            "variations": {
              "average": {
                "base": "716.00"
              },
              "changes": [
                {
                  "startDate": "2023-11-22",
                  "endDate": "2023-11-23",
                  "total": "716.00"
                }
              ]
            }
          },
          "policies": {
            "paymentType": "deposit",
            "cancellation": {
              "description": {
                "text": "NON-REFUNDABLE RATE"
              },
              "type": "FULL_STAY"
            }
          },
          "self": "https://test.api.amadeus.com/v3/shopping/hotel-offers/TSXOJ6LFQ2"
        }
      ],
      "self": "https://test.api.amadeus.com/v3/shopping/hotel-offers?hotelIds=MCLONGHM&adults=1&checkInDate=2023-11-22&paymentPolicy=NONE&roomQuantity=1"
    }
  ]
}
400	
Bad request:

Code	Title
23	PASSENGER TYPE NOT SUPPORTED
61	INVALID CURRENCY CODE
137	INVALID ADULTS OCCUPANCY REQUESTED
145	DURATION PERIOD OR DATES INCORRECT
195	SERVICE RESTRICTION
249	INVALID RATE CODE
377	MAX STAY DURATION IS EXCEEDED
381	INVALID CHECK-IN DATE
382	INVALID CHECK-OUT DATE
383	INVALID CITY CODE
392	INVALID HOTEL CODE
397	INVALID NUMBER OF ADULTS
400	INVALID PROPERTY CODE
404	CHECK_OUT DATE MUST BE FURTHER IN THE FUTURE THAN CHECK-IN DATE
424	NO HOTELS FOUND WHICH MATCH THIS INPUT
431	CHECK-OUT DATE IS TOO FAR IN THE FUTURE THAN CHECK-IN DATE
424	NO HOTELS FOUND WHICH MATCH THIS INPUT
431	CHECK-OUT DATE IS TOO FAR IN THE FUTURE
450	INVALID PROVIDER RESPONSE
451	INVALID CREDENTIALS
562	RESTRICTED ACCESS FOR THE REQUESTED RATES AND CHAINS
784	PROVIDER TIME OUT
790	RATE SECURITY NOT LOADED
Example Value
Model
{
  "errors": [
    {
      "status": 0,
      "code": 0,
      "title": "string",
      "detail": "string",
      "source": {
        "parameter": "string",
        "pointer": "string",
        "example": "string"
      },
      "documentation": "string"
    }
  ]
}
500	
Internal server error.

Example Value
Model
{
  "errors": [
    {
      "status": 0,
      "code": 0,
      "title": "string",
      "detail": "string",
      "source": {
        "parameter": "string",
        "pointer": "string",
        "example": "string"
      },
      "documentation": "string"
    }
  ]
}


example snippet for the stremable http transport:
"""
Run from the repository root:
    uv run examples/snippets/servers/streamable_config.py
"""

from mcp.server.fastmcp import FastMCP

# Stateful server (maintains session state)
mcp = FastMCP("StatefulServer")

# Other configuration options:
# Stateless server (no session persistence)
# mcp = FastMCP("StatelessServer", stateless_http=True)

# Stateless server (no session persistence, no sse stream with supported client)
# mcp = FastMCP("StatelessServer", stateless_http=True, json_response=True)


# Add a simple tool to demonstrate the server
@mcp.tool()
def greet(name: str = "World") -> str:
    """Greet someone by name."""
    return f"Hello, {name}!"


# Run server with streamable_http transport
if __name__ == "__main__":
    mcp.run(transport="streamable-http")

#2
"""
Basic example showing how to mount StreamableHTTP server in Starlette.

Run from the repository root:
    uvicorn examples.snippets.servers.streamable_http_basic_mounting:app --reload
"""

from starlette.applications import Starlette
from starlette.routing import Mount

from mcp.server.fastmcp import FastMCP

# Create MCP server
mcp = FastMCP("My App")


@mcp.tool()
def hello() -> str:
    """A simple hello tool"""
    return "Hello from MCP!"


# Mount the StreamableHTTP server to the existing ASGI server
app = Starlette(
    routes=[
        Mount("/", app=mcp.streamable_http_app()),
    ]
)

#3
import contextlib
import logging
from collections.abc import AsyncIterator
from typing import Any

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from pydantic import AnyUrl
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

from .event_store import InMemoryEventStore

# Configure logging
logger = logging.getLogger(__name__)


@click.command()
@click.option("--port", default=3000, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
def main(
    port: int,
    log_level: str,
    json_response: bool,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    app = Server("mcp-streamable-http-demo")

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        ctx = app.request_context
        interval = arguments.get("interval", 1.0)
        count = arguments.get("count", 5)
        caller = arguments.get("caller", "unknown")

        # Send the specified number of notifications with the given interval
        for i in range(count):
            # Include more detailed message for resumability demonstration
            notification_msg = f"[{i + 1}/{count}] Event from '{caller}' - Use Last-Event-ID to resume if disconnected"
            await ctx.session.send_log_message(
                level="info",
                data=notification_msg,
                logger="notification_stream",
                # Associates this notification with the original request
                # Ensures notifications are sent to the correct response stream
                # Without this, notifications will either go to:
                # - a standalone SSE stream (if GET request is supported)
                # - nowhere (if GET request isn't supported)
                related_request_id=ctx.request_id,
            )
            logger.debug(f"Sent notification {i + 1}/{count} for caller: {caller}")
            if i < count - 1:  # Don't wait after the last notification
                await anyio.sleep(interval)

        # This will send a resource notificaiton though standalone SSE
        # established by GET request
        await ctx.session.send_resource_updated(uri=AnyUrl("http:///test_resource"))
        return [
            types.TextContent(
                type="text",
                text=(f"Sent {count} notifications with {interval}s interval for caller: {caller}"),
            )
        ]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="start-notification-stream",
                description=("Sends a stream of notifications with configurable count and interval"),
                inputSchema={
                    "type": "object",
                    "required": ["interval", "count", "caller"],
                    "properties": {
                        "interval": {
                            "type": "number",
                            "description": "Interval between notifications in seconds",
                        },
                        "count": {
                            "type": "number",
                            "description": "Number of notifications to send",
                        },
                        "caller": {
                            "type": "string",
                            "description": ("Identifier of the caller to include in notifications"),
                        },
                    },
                },
            )
        ]

    # Create event store for resumability
    # The InMemoryEventStore enables resumability support for StreamableHTTP transport.
    # It stores SSE events with unique IDs, allowing clients to:
    #   1. Receive event IDs for each SSE message
    #   2. Resume streams by sending Last-Event-ID in GET requests
    #   3. Replay missed events after reconnection
    # Note: This in-memory implementation is for demonstration ONLY.
    # For production, use a persistent storage solution.
    event_store = InMemoryEventStore()

    # Create the session manager with our app and event store
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=event_store,  # Enable resumability
        json_response=json_response,
    )

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(scope: Scope, receive: Receive, send: Send) -> None:
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
        allow_methods=["GET", "POST", "DELETE"],  # MCP streamable HTTP methods
        expose_headers=["Mcp-Session-Id"],
    )

    import uvicorn

    uvicorn.run(starlette_app, host="127.0.0.1", port=port)

    return 0