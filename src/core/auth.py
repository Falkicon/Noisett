"""Authentication middleware for Noisett API.

Phase 8: Microsoft Entra ID JWT validation for FastAPI.

Authentication is optional by default (migration period). Set AUTH_REQUIRED=true
to enforce authentication on all protected endpoints.

Environment Variables:
    AZURE_TENANT_ID: Microsoft Entra ID tenant ID
    AZURE_CLIENT_ID: Application (client) ID from Azure AD app registration
    AUTH_REQUIRED: If "true", authentication is required (default: false)
"""

import base64
import json
import logging
import os
from datetime import UTC, datetime

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.types import User

# Set up logging
logger = logging.getLogger(__name__)

# Configuration
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


class AuthConfig:
    """Authentication configuration."""
    
    tenant_id: str = AZURE_TENANT_ID
    client_id: str = AZURE_CLIENT_ID
    required: bool = AUTH_REQUIRED
    
    @property
    def is_configured(self) -> bool:
        """Check if auth is properly configured."""
        return bool(self.tenant_id and self.client_id)
    
    @property
    def issuer(self) -> str:
        """Get the expected JWT issuer URL."""
        return f"https://login.microsoftonline.com/{self.tenant_id}/v2.0"
    
    @property
    def jwks_url(self) -> str:
        """Get the JWKS (JSON Web Key Set) URL for token validation."""
        return f"https://login.microsoftonline.com/{self.tenant_id}/discovery/v2.0/keys"


auth_config = AuthConfig()


async def validate_jwt(token: str) -> User | None:
    """Validate JWT token and extract user info.
    
    Args:
        token: JWT access token from Authorization header
        
    Returns:
        User object if valid, None if invalid
        
    Note:
        Full JWT validation with JWKS requires 'pyjwt[crypto]'.
        For production, set AZURE_TENANT_ID and AZURE_CLIENT_ID to enable
        full cryptographic validation against Microsoft's JWKS endpoint.
        
    Security:
        - Validates token structure (3-part JWT)
        - Validates signature using JWKS (when configured)
        - Validates issuer and audience claims
        - Validates expiration time
    """
    if not token:
        return None
    
    try:
        # Check basic JWT structure first
        parts = token.split(".")
        if len(parts) != 3:
            logger.warning("Invalid JWT structure: expected 3 parts, got %d", len(parts))
            return None
        
        # Decode payload for claim validation
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        
        payload_json = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(payload_json)
        
        # If auth is configured, perform full cryptographic validation
        if auth_config.is_configured:
            try:
                import jwt
                from jwt import PyJWKClient
                
                # Fetch signing keys from Microsoft's JWKS endpoint
                jwks_client = PyJWKClient(auth_config.jwks_url)
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                
                # Validate token with cryptographic verification
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["RS256"],
                    audience=auth_config.client_id,
                    issuer=auth_config.issuer,
                )
                logger.debug("JWT cryptographically validated for user: %s", payload.get("oid"))
                
            except ImportError:
                logger.warning(
                    "pyjwt[crypto] not installed - falling back to basic validation. "
                    "Install with: pip install pyjwt[crypto]"
                )
            except jwt.ExpiredSignatureError:
                logger.warning("JWT expired")
                return None
            except jwt.InvalidAudienceError:
                logger.warning("JWT invalid audience - expected %s", auth_config.client_id)
                return None
            except jwt.InvalidIssuerError:
                logger.warning("JWT invalid issuer - expected %s", auth_config.issuer)
                return None
            except jwt.PyJWTError as e:
                logger.warning("JWT validation failed: %s", str(e))
                return None
        else:
            # No auth configured - basic validation only (development mode)
            logger.debug("Auth not configured - using basic JWT validation")
            
            # Check expiration (exp is Unix timestamp)
            exp = payload.get("exp")
            if exp:
                exp_datetime = datetime.fromtimestamp(exp, tz=UTC)
                if datetime.now(UTC) > exp_datetime:
                    logger.warning("JWT expired at %s", exp_datetime.isoformat())
                    return None
        
        # Extract user info from standard Entra ID claims
        user_id = payload.get("oid") or payload.get("sub")  # Object ID or Subject
        email = payload.get("email") or payload.get("preferred_username", "")
        name = payload.get("name", "")
        
        if not user_id:
            logger.warning("JWT missing user identifier (oid or sub claim)")
            return None
        
        return User(
            user_id=user_id,
            email=email,
            name=name,
        )
        
    except json.JSONDecodeError as e:
        logger.warning("JWT payload is not valid JSON: %s", str(e))
        return None
    except Exception as e:
        # Log unexpected errors for debugging
        logger.error("Unexpected error validating JWT: %s", str(e), exc_info=True)
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_auth_optional: str | None = Header(None, alias="X-Auth-Optional"),
) -> User | None:
    """FastAPI dependency to get the current authenticated user.
    
    Args:
        credentials: Bearer token from Authorization header
        x_auth_optional: If "true", skip auth even when AUTH_REQUIRED
        
    Returns:
        User object if authenticated, None if auth is optional and not provided
        
    Raises:
        HTTPException 401: If authentication is required but not provided/invalid
        
    Usage:
        @app.get("/api/history")
        async def get_history(user: User = Depends(get_current_user)):
            if user:
                # Authenticated request
            else:
                # Anonymous request (only if auth is optional)
    """
    # Check if auth is optional for this request
    auth_optional = x_auth_optional and x_auth_optional.lower() == "true"
    
    # If no credentials provided
    if not credentials:
        if AUTH_REQUIRED and not auth_optional:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required",
                    "suggestion": "Sign in with your Microsoft account",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    
    # Validate the token
    user = await validate_jwt(credentials.credentials)
    
    if not user:
        if AUTH_REQUIRED and not auth_optional:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "TOKEN_INVALID",
                    "message": "Invalid or expired token",
                    "suggestion": "Sign out and sign in again",
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return None
    
    return user


async def require_auth(
    user: User | None = Depends(get_current_user),
) -> User:
    """FastAPI dependency that requires authentication.
    
    Use this for endpoints that must have a user, regardless of AUTH_REQUIRED setting.
    
    Args:
        user: User from get_current_user dependency
        
    Returns:
        Authenticated User object
        
    Raises:
        HTTPException 401: If not authenticated
        
    Usage:
        @app.post("/api/favorites/add")
        async def add_favorite(user: User = Depends(require_auth)):
            # user is guaranteed to be authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "UNAUTHORIZED",
                "message": "Authentication required for this action",
                "suggestion": "Sign in with your Microsoft account",
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_anonymous_user_id() -> str:
    """Get a user ID for anonymous users (migration period).
    
    During the migration period when auth is optional, anonymous users
    get a consistent ID based on the session. In a real implementation,
    this could use a cookie or local storage ID.
    
    Returns:
        Static "anonymous" user ID
    """
    return "anonymous"


# Export for easy imports
__all__ = [
    "auth_config",
    "AuthConfig",
    "get_current_user",
    "require_auth",
    "get_anonymous_user_id",
    "validate_jwt",
    "User",
]
