"""JWT authentication utilities and FastAPI dependencies."""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from src.config import settings

security = HTTPBearer(auto_error=False)


def create_access_token(user_id: str) -> str:
    """Create a JWT access token for the given user.

    Args:
        user_id: The user identifier to encode in the token.

    Returns:
        A signed JWT token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.jwt_expiration_minutes
    )
    payload = {
        "sub": user_id,
        "exp": expire,
    }
    token: str = jwt.encode(
        payload, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return token


def verify_token(token: str) -> str | None:
    """Verify a JWT token and return the user_id if valid.

    Args:
        token: The JWT token string to verify.

    Returns:
        The user_id (sub claim) if the token is valid, None otherwise.
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        user_id: str | None = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """FastAPI dependency that extracts and verifies the current user from a JWT.

    Args:
        credentials: The HTTP Bearer credentials extracted by FastAPI, or None
            if no Authorization header was provided.

    Returns:
        The user_id from the verified token.

    Raises:
        HTTPException: 401 if the token is invalid, expired, or missing.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = verify_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user_id
