# MCP Server Authentication Implementation

This document describes the authentication implementation for the Amadeus Hotels MCP server using the official MCP SDK (v1.23.0+).

## Overview

The server uses the official MCP SDK's built-in authentication components:
- `mcp.server.auth.provider.TokenVerifier` - Token verification protocol
- `mcp.server.auth.middleware.bearer_auth.BearerAuthBackend` - Bearer token authentication backend
- `mcp.server.auth.provider.AccessToken` - Access token model

## Authentication Methods

### 1. API Key Authentication (Implemented)

The server uses a simple API key authentication system where clients must provide a valid API key in the `Authorization` header.

**Request Format:**
```
Authorization: Bearer your-api-key-here
```

**Configuration:**
- Set `AUTH_ENABLED=true` in your environment
- Configure `API_KEYS` with comma-separated valid API keys
- Example: `API_KEYS=key1,key2,key3`

### 2. Public Endpoints

The following endpoints are publicly accessible and do not require authentication:
- `/` - Root endpoint for health checks
- `/health` - Health check endpoint
- `/healthz` - Alternative health check endpoint
- `/favicon.ico` - Favicon
- `/register` - MCP client registration endpoint
- `/.well-known/*` - OAuth/OpenID discovery endpoints
- `/mcp/.well-known/*` - MCP OAuth/OpenID discovery endpoints

All other endpoints under `/mcp/` require valid Bearer token authentication.

### 3. JWT Authentication (Ready for Implementation)

The configuration includes JWT secret support for future JWT token validation.

## Configuration

### Environment Variables

```bash
# Authentication Configuration
AUTH_ENABLED=true
API_KEYS=default-api-key,your-secure-api-key-here
JWT_SECRET=your-jwt-secret-key-here
```

### Command Line Options

```bash
# Disable authentication (not recommended for production)
uv run python -m src.main --disable-auth

# Other options remain the same
uv run python -m src.main --port 8080 --host 0.0.0.0
```

## Implementation Details

### TokenVerifier Class

The `SimpleTokenVerifier` implements the MCP SDK's `TokenVerifier` protocol and returns `AccessToken` objects:

```python
class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for API key authentication using MCP SDK's TokenVerifier protocol."""
    
    def __init__(self, valid_api_keys: list[str]):
        self.valid_api_keys = set(valid_api_keys)
    
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """Verify the provided token and return AccessToken compatible with MCP SDK's BearerAuthBackend."""
        if token in self.valid_api_keys:
            from mcp.server.auth.provider import AccessToken
            return AccessToken(
                token=token,
                client_id=f"user_{hash(token) % 10000}",
                scopes=["api_access"],
                expires_at=None  # API keys don't expire
            )
        return None
```

### Conditional Authentication Middleware

The `ConditionalAuthMiddleware` wraps the SDK's `BearerAuthBackend` and handles public vs protected paths:

```python
class ConditionalAuthMiddleware(BaseHTTPMiddleware):
    """Middleware that conditionally applies authentication based on path."""
    
    def __init__(self, app, auth_backend):
        super().__init__(app)
        self.auth_backend = auth_backend
    
    async def dispatch(self, request, call_next):
        # Skip authentication for public paths
        if self._is_public_path(request.url.path):
            return await call_next(request)
        
        # Apply authentication for protected paths using SDK's BearerAuthBackend
        auth_result = await self.auth_backend.authenticate(request)
        # ... handle authentication result
```

### Server Integration

The authentication middleware is applied to the Starlette app:

```python
if settings.auth_enabled:
    token_verifier = SimpleTokenVerifier(settings.api_keys)
    auth_backend = BearerAuthBackend(token_verifier=token_verifier)
    
    starlette_app.add_middleware(
        ConditionalAuthMiddleware,
        auth_backend=auth_backend
    )
```

## Usage Examples

### 1. Starting the Server with Authentication

```bash
# Using environment variables
export AUTH_ENABLED=true
export API_KEYS="my-secure-key,another-key"
uv run python -m src.main

# Using command line (disable auth)
uv run python -m src.main --disable-auth
```

### 2. Client Requests

**With Authentication:**
```bash
curl -H "Authorization: Bearer my-secure-key" \
     -H "Content-Type: application/json" \
     -X POST http://localhost:3000/mcp \
     -d '{"method": "tools/list"}'
```

**Without Authentication (if disabled):**
```bash
curl -H "Content-Type: application/json" \
     -X POST http://localhost:3000/mcp \
     -d '{"method": "tools/list"}'
```

### 3. Error Responses

**Unauthorized - Missing Authorization Header (401):**
```
Unauthorized: Missing Authorization header. Please include 'Authorization: Bearer <api_key>' header.
```

**Unauthorized - Invalid Token (401):**
```
Unauthorized: Invalid API key.
```

Both responses include the `WWW-Authenticate: Bearer` header.

## Security Considerations

1. **API Key Management:**
   - Use strong, randomly generated API keys
   - Rotate keys regularly
   - Store keys securely (environment variables, not in code)

2. **Transport Security:**
   - Always use HTTPS in production
   - Configure proper CORS settings

3. **Logging:**
   - Authentication events are logged
   - Monitor for failed authentication attempts

4. **Rate Limiting:**
   - Consider implementing rate limiting for authentication endpoints
   - Monitor for brute force attempts

## Testing

Run the authentication tests:

```bash
# Run all authentication tests
uv run pytest tests/test_authentication.py -v

# Run specific test classes
uv run pytest tests/test_authentication.py::TestSimpleTokenVerifier -v
uv run pytest tests/test_authentication.py::TestConditionalAuthMiddleware -v
```

The test suite covers:
- Token verification with valid/invalid/empty tokens
- Public path detection and access
- Protected endpoint authentication requirements
- Bearer token format handling
- Integration with MCP SDK components

## Future Enhancements

1. **JWT Token Support:**
   - Implement JWT token validation using the configured JWT secret
   - Add token expiration handling

2. **OAuth Integration:**
   - Integrate with external OAuth providers
   - Support for OAuth 2.1 and OpenID Connect

3. **Role-Based Access Control:**
   - Implement different access levels based on user roles
   - Tool-level permissions

4. **Audit Logging:**
   - Enhanced logging for security events
   - Integration with security monitoring systems
