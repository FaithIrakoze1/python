"""
Google OAuth2 authentication with JWT.
Uses google-auth to verify Google's ID token, PyJWT for our app's tokens.
"""
from datetime import datetime, timedelta
import os
from pathlib import Path

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests

# Ensure env/.env is loaded even if database isn't imported first.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "env" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# Load from env - set these in your .env
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24

security = HTTPBearer()


def verify_google_token(id_token_string: str) -> dict:
    """Verify Google's ID token and return decoded claims. Raises ValueError if invalid."""
    if not GOOGLE_CLIENT_ID:
        raise ValueError("GOOGLE_CLIENT_ID is not configured")
    return id_token.verify_oauth2_token(
        id_token_string,
        requests.Request(),
        GOOGLE_CLIENT_ID,
    )


def create_access_token(user_id: int, email: str) -> str:
    """Create a JWT for our app."""
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify our app's JWT. Raises jwt.InvalidTokenError if invalid."""
    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """FastAPI dependency: require valid Bearer token and return decoded user info."""
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        email = payload.get("email")
        if not user_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )
        return {"user_id": int(user_id), "email": email}
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
