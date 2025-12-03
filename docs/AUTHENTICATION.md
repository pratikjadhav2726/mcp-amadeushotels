# MCP Server Authentication Implementation

This document describes the authentication implementation for the Amadeus Hotels MCP server using the official MCP SDK.

## Overview

The server now includes built-in authentication using the official MCP SDK's authentication components:
- `mcp.server.auth.provider.TokenVerifier` - Token verification protocol
- `mcp.server.auth.middleware.bearer_auth` - Bearer token authentication middleware

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

### 2. JWT Authentication (Ready for Implementation)

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
python -m src.main --disable-auth

# Other options remain the same
python -m src.main --port 8080 --host 0.0.0.0
```

## Implementation Details

### TokenVerifier Class

```python
class SimpleTokenVerifier(TokenVerifier):
    """Simple token verifier for API key authentication."""
    
    def __init__(self, valid_api_keys: list[str]):
        self.valid_api_keys = set(valid_api_keys)
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify the provided token and return user claims."""
        if token in self.valid_api_keys:
            return {
                "authenticated": True,
                "token": token,
                "user_id": f"user_{hash(token) % 10000}",
                "role": "api_user"
            }
        return None
```

### Server Integration

The authentication middleware is applied to the MCP server:

```python
if settings.auth_enabled:
    token_verifier = SimpleTokenVerifier(settings.api_keys)
    app = bearer_auth(app, token_verifier)
```

## Usage Examples

### 1. Starting the Server with Authentication

```bash
# Using environment variables
export AUTH_ENABLED=true
export API_KEYS="my-secure-key,another-key"
python -m src.main

# Using command line (disable auth)
python -m src.main --disable-auth
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

**Unauthorized (401):**
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing authentication token"
}
```

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

Run the authentication test:

```bash
python test_auth.py
```

This will test:
- Configuration loading
- Token verification with valid/invalid keys
- User claims generation

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
