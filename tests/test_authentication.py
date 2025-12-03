"""
Tests for authentication middleware using MCP SDK's BearerAuthBackend.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette.responses import JSONResponse
from starlette.routing import Route

from src.main import (
    SimpleTokenVerifier,
    ConditionalAuthMiddleware,
)
from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend


class TestSimpleTokenVerifier:
    """Test cases for SimpleTokenVerifier."""
    
    @pytest.fixture
    def verifier(self):
        """Create a token verifier with test API keys."""
        return SimpleTokenVerifier(valid_api_keys=["test-key-1", "test-key-2", "valid-api-key"])
    
    @pytest.mark.asyncio
    async def test_verify_valid_token(self, verifier):
        """Test verification of a valid token."""
        access_token = await verifier.verify_token("test-key-1")
        assert access_token is not None
        assert access_token.token == "test-key-1"
        assert access_token.client_id.startswith("user_")
    
    @pytest.mark.asyncio
    async def test_verify_invalid_token(self, verifier):
        """Test verification of an invalid token."""
        user = await verifier.verify_token("invalid-key")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_verify_empty_token(self, verifier):
        """Test verification of an empty token."""
        user = await verifier.verify_token("")
        assert user is None
    
    @pytest.mark.asyncio
    async def test_verify_different_valid_tokens(self, verifier):
        """Test that different valid tokens produce different client IDs."""
        token1 = await verifier.verify_token("test-key-1")
        token2 = await verifier.verify_token("test-key-2")
        
        assert token1 is not None
        assert token2 is not None
        assert token1.client_id != token2.client_id


class TestConditionalAuthMiddleware:
    """Test cases for ConditionalAuthMiddleware."""
    
    @pytest.fixture
    def auth_backend(self):
        """Create a BearerAuthBackend with test verifier."""
        verifier = SimpleTokenVerifier(valid_api_keys=["test-key-1", "valid-api-key"])
        return BearerAuthBackend(token_verifier=verifier)
    
    @pytest.fixture
    def test_app(self, auth_backend):
        """Create a test Starlette app with authentication middleware."""
        async def protected_endpoint(request):
            return JSONResponse({"message": "protected", "user": str(request.scope.get("user"))})
        
        async def public_endpoint(request):
            return JSONResponse({"message": "public"})
        
        app = Starlette(
            routes=[
                Route("/protected", protected_endpoint),
                Route("/public", public_endpoint),
                Route("/", public_endpoint),  # Add root as public
            ]
        )
        app.add_middleware(ConditionalAuthMiddleware, auth_backend=auth_backend)
        return app
    
    def test_public_path_root(self, auth_backend):
        """Test that root path is considered public."""
        middleware = ConditionalAuthMiddleware(MagicMock(), auth_backend)
        assert middleware._is_public_path("/") is True
    
    def test_public_path_health(self, auth_backend):
        """Test that health endpoints are considered public."""
        middleware = ConditionalAuthMiddleware(MagicMock(), auth_backend)
        assert middleware._is_public_path("/health") is True
        assert middleware._is_public_path("/healthz") is True
    
    def test_public_path_register(self, auth_backend):
        """Test that register endpoint is considered public."""
        middleware = ConditionalAuthMiddleware(MagicMock(), auth_backend)
        assert middleware._is_public_path("/register") is True
    
    def test_public_path_well_known(self, auth_backend):
        """Test that well-known endpoints are considered public."""
        middleware = ConditionalAuthMiddleware(MagicMock(), auth_backend)
        assert middleware._is_public_path("/.well-known/openid-configuration") is True
        assert middleware._is_public_path("/mcp/.well-known/openid-configuration") is True
    
    def test_protected_path(self, auth_backend):
        """Test that other paths are considered protected."""
        middleware = ConditionalAuthMiddleware(MagicMock(), auth_backend)
        assert middleware._is_public_path("/mcp/sessions") is False
        assert middleware._is_public_path("/api/data") is False
    
    def test_public_endpoint_no_auth(self, test_app):
        """Test that public endpoints work without authentication."""
        client = TestClient(test_app)
        # Test root endpoint which is in PUBLIC_PATHS
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "public"
    
    def test_protected_endpoint_no_auth(self, test_app):
        """Test that protected endpoints require authentication."""
        client = TestClient(test_app)
        response = client.get("/protected")
        assert response.status_code == 401
        assert "Unauthorized" in response.text
        assert "Missing Authorization header" in response.text
    
    def test_protected_endpoint_valid_token(self, test_app):
        """Test that protected endpoints work with valid token."""
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer test-key-1"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "protected"
        # The user object is an AuthenticatedUser or AuthCredentials, just verify it exists
        user_str = str(response.json()["user"])
        assert user_str is not None
        # Just verify authentication worked - the user object exists
        assert len(user_str) > 0
    
    def test_protected_endpoint_invalid_token(self, test_app):
        """Test that protected endpoints reject invalid tokens."""
        client = TestClient(test_app)
        response = client.get(
            "/protected",
            headers={"Authorization": "Bearer invalid-key"}
        )
        assert response.status_code == 401
        assert "Unauthorized" in response.text
    
    def test_protected_endpoint_malformed_header(self, test_app):
        """Test that protected endpoints reject malformed Authorization headers."""
        client = TestClient(test_app)
        # Missing "Bearer " prefix
        response = client.get(
            "/protected",
            headers={"Authorization": "test-key-1"}
        )
        assert response.status_code == 401
    
    def test_options_request_allowed(self, test_app):
        """Test that OPTIONS requests are allowed without authentication."""
        client = TestClient(test_app)
        response = client.options("/protected")
        assert response.status_code == 200 or response.status_code == 405  # 405 is also acceptable


class TestMCPAuthenticationIntegration:
    """Integration tests for MCP authentication with actual server setup."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = MagicMock()
        settings.auth_enabled = True
        settings.api_keys = ["test-key-1", "test-key-2"]
        settings.host = "127.0.0.1"
        settings.port = 3000
        settings.log_level = "INFO"
        settings.amadeus_base_url = "https://test.api.amadeus.com"
        return settings
    
    @pytest.mark.asyncio
    async def test_token_verifier_integration(self, mock_settings):
        """Test token verifier integration with settings."""
        verifier = SimpleTokenVerifier(mock_settings.api_keys)
        
        # Test valid keys
        for key in mock_settings.api_keys:
            user = await verifier.verify_token(key)
            assert user is not None
        
        # Test invalid key
        user = await verifier.verify_token("invalid-key")
        assert user is None
    
    def test_public_paths_list(self):
        """Test that all expected public paths are in the list."""
        from src.main import ConditionalAuthMiddleware
        from mcp.server.auth.middleware.bearer_auth import BearerAuthBackend
        
        verifier = SimpleTokenVerifier(["test-key"])
        backend = BearerAuthBackend(token_verifier=verifier)
        middleware = ConditionalAuthMiddleware(MagicMock(), backend)
        
        # Check all public paths
        public_paths = [
            "/",
            "/health",
            "/healthz",
            "/favicon.ico",
            "/register",
            "/.well-known/openid-configuration",
            "/mcp/.well-known/openid-configuration",
        ]
        
        for path in public_paths:
            assert middleware._is_public_path(path), f"{path} should be public"
        
        # Check protected paths
        protected_paths = [
            "/mcp/sessions",
            "/mcp/requests",
            "/api/data",
        ]
        
        for path in protected_paths:
            assert not middleware._is_public_path(path), f"{path} should be protected"


class TestBearerTokenFormat:
    """Test cases for Bearer token format handling."""
    
    @pytest.fixture
    def verifier(self):
        """Create a token verifier."""
        return SimpleTokenVerifier(valid_api_keys=["valid-key"])
    
    @pytest.fixture
    def auth_backend(self, verifier):
        """Create a BearerAuthBackend."""
        return BearerAuthBackend(token_verifier=verifier)
    
    @pytest.mark.asyncio
    async def test_bearer_token_extraction(self, auth_backend):
        """Test that Bearer tokens are correctly extracted from headers."""
        from starlette.requests import Request
        
        # Create a mock request with Bearer token
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [(b"authorization", b"Bearer valid-key")],
        }
        request = Request(scope)
        
        result = await auth_backend.authenticate(request)
        assert result is not None
        assert result[0] is not None  # User object
        assert result[1] is not None  # Auth info (AccessToken)
    
    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, auth_backend):
        """Test handling of missing Authorization header."""
        from starlette.requests import Request
        
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/test",
            "headers": [],
        }
        request = Request(scope)
        
        result = await auth_backend.authenticate(request)
        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

