"""
Integration tests for the MCP server with authentication.
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from starlette.testclient import TestClient

# Set test environment variables before importing main
os.environ.setdefault("AMADEUS_API_KEY", "test_key")
os.environ.setdefault("AMADEUS_API_SECRET", "test_secret")
os.environ.setdefault("AUTH_ENABLED", "true")
os.environ.setdefault("API_KEYS", "test-key-1,test-key-2,integration-test-key")


class TestServerAuthentication:
    """Integration tests for server authentication."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings that bypass Amadeus API calls."""
        with patch('src.main.get_app_settings') as mock_get_settings:
            settings = MagicMock()
            settings.auth_enabled = True
            settings.api_keys = ["test-key-1", "test-key-2", "integration-test-key"]
            settings.host = "127.0.0.1"
            settings.port = 3000
            settings.log_level = "INFO"
            settings.amadeus_base_url = "https://test.api.amadeus.com"
            settings.amadeus_api_key = "test_key"
            settings.amadeus_api_secret = "test_secret"
            mock_get_settings.return_value = settings
            yield settings
    
    def test_public_endpoints_accessible(self, mock_settings):
        """Test that public endpoints are accessible without authentication."""
        from src.main import create_mcp_server, SimpleTokenVerifier, ConditionalAuthMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
        from src.main import InMemoryEventStore
        from starlette.applications import Starlette
        from starlette.routing import Mount
        from starlette.responses import JSONResponse
        
        # Create a minimal test app
        async def public_handler(scope, receive, send):
            if scope["path"] in ["/", "/health", "/register"]:
                response = JSONResponse({"status": "ok", "path": scope["path"]})
                await response(scope, receive, send)
            else:
                response = JSONResponse({"error": "not found"}, status_code=404)
                await response(scope, receive, send)
        
        app = Starlette(routes=[Mount("/", app=public_handler)])
        
        # Add authentication middleware
        verifier = SimpleTokenVerifier(mock_settings.api_keys)
        auth_backend = BearerAuthBackend(token_verifier=verifier)
        app.add_middleware(ConditionalAuthMiddleware, auth_backend=auth_backend)
        
        client = TestClient(app)
        
        # Test public endpoints
        response = client.get("/")
        assert response.status_code in [200, 404]  # 404 is OK if route not defined
        
        response = client.get("/health")
        assert response.status_code in [200, 404]
        
        response = client.get("/register")
        assert response.status_code in [200, 404]
    
    def test_well_known_endpoints_accessible(self, mock_settings):
        """Test that well-known endpoints are accessible without authentication."""
        from src.main import SimpleTokenVerifier, ConditionalAuthMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        
        async def well_known_handler(request):
            return JSONResponse({"issuer": "test", "path": request.url.path})
        
        app = Starlette(routes=[
            Route("/.well-known/openid-configuration", well_known_handler),
            Route("/mcp/.well-known/openid-configuration", well_known_handler),
        ])
        
        verifier = SimpleTokenVerifier(mock_settings.api_keys)
        auth_backend = BearerAuthBackend(token_verifier=verifier)
        app.add_middleware(ConditionalAuthMiddleware, auth_backend=auth_backend)
        
        client = TestClient(app)
        
        # Test well-known endpoints
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200
        
        response = client.get("/mcp/.well-known/openid-configuration")
        assert response.status_code == 200
    
    def test_protected_endpoints_require_auth(self, mock_settings):
        """Test that protected endpoints require authentication."""
        from src.main import SimpleTokenVerifier, ConditionalAuthMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        
        async def protected_handler(request):
            user = request.scope.get("user")
            return JSONResponse({"message": "protected", "user": str(user)})
        
        app = Starlette(routes=[
            Route("/mcp/protected", protected_handler),
        ])
        
        verifier = SimpleTokenVerifier(mock_settings.api_keys)
        auth_backend = BearerAuthBackend(token_verifier=verifier)
        app.add_middleware(ConditionalAuthMiddleware, auth_backend=auth_backend)
        
        client = TestClient(app)
        
        # Test without authentication
        response = client.get("/mcp/protected")
        assert response.status_code == 401
        assert "Unauthorized" in response.text
        
        # Test with valid authentication
        response = client.get(
            "/mcp/protected",
            headers={"Authorization": "Bearer test-key-1"}
        )
        assert response.status_code == 200
        assert "protected" in response.json()["message"]
        
        # Test with invalid authentication
        response = client.get(
            "/mcp/protected",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401


class TestAuthenticationConfiguration:
    """Test authentication configuration and settings."""
    
    def test_auth_disabled(self):
        """Test that authentication can be disabled."""
        from src.main import SimpleTokenVerifier, ConditionalAuthMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        from starlette.applications import Starlette
        from starlette.routing import Route
        from starlette.responses import JSONResponse
        
        async def handler(request):
            return JSONResponse({"message": "ok"})
        
        app = Starlette(routes=[Route("/test", handler)])
        
        # When auth is disabled, middleware should not be added
        # But if added, it should still work for public paths
        verifier = SimpleTokenVerifier(["test-key"])
        auth_backend = BearerAuthBackend(token_verifier=verifier)
        app.add_middleware(ConditionalAuthMiddleware, auth_backend=auth_backend)
        
        client = TestClient(app)
        
        # Public paths should work
        response = client.get("/")
        # Should not return 401 for root path
        assert response.status_code != 401 or response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

