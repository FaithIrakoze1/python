from urllib.parse import urlencode
import os
from pathlib import Path

import requests as http_requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
import crud
from auth import verify_google_token, create_access_token


router = APIRouter(prefix="/auth", tags=["auth"])

# Ensure env/.env is loaded even if database isn't imported first.
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / "env" / ".env"
load_dotenv(dotenv_path=ENV_PATH)

TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"


def _get_redirect_uri() -> str:
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    if not redirect_uri:
        # This must exactly match the "Authorized redirect URI" in Google Cloud Console.
        redirect_uri = "http://127.0.0.1:8000/api/auth/google/callback"
    return redirect_uri


@router.get("/google")
def google_login():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        raise HTTPException(status_code=500, detail="GOOGLE_CLIENT_ID is not configured")

    params = {
        "client_id": client_id,
        "redirect_uri": _get_redirect_uri(),
        "response_type": "code",
        "scope": "openid email profile",
        # Include these only if you want refresh tokens:
        # "access_type": "offline",
        # "prompt": "consent",
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)


@router.get("/google/callback")
def google_callback(
    code: str | None = None,
    error: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Handle Google's redirect back to us.
    Exchange ?code=... for tokens, verify id_token,
    upsert the user, and issue our own JWT.
    """
    if error:
        raise HTTPException(status_code=400, detail=f"Google auth error: {error}")
    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' in callback")

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="Google client credentials not configured")

    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": _get_redirect_uri(),
        "grant_type": "authorization_code",
    }

    token_resp = http_requests.post(TOKEN_ENDPOINT, data=data, timeout=10)
    if not token_resp.ok:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to exchange code with Google: {token_resp.text}",
        )

    token_data = token_resp.json()
    id_token_str = token_data.get("id_token")
    if not id_token_str:
        raise HTTPException(status_code=502, detail="Missing id_token from Google response")

    # Verify Google's ID token and extract user info.
    claims = verify_google_token(id_token_str)
    google_sub = claims.get("sub")
    email = claims.get("email")
    name = claims.get("name")

    if not google_sub or not email:
        raise HTTPException(status_code=502, detail="Google token missing required claims")

    # Get or create user in our DB.
    user = crud.get_or_create_user_by_google_sub(db, google_sub=google_sub, email=email, name=name)

    # Issue our own JWT for this user.
    access_token = create_access_token(user_id=user.user_id, email=user.email)

    # Redirect to app with token in fragment (memory-only: frontend reads, stores in variable).
    frontend_url = os.getenv("FRONTEND_URL", "http://127.0.0.1:8000")
    return RedirectResponse(url=f"{frontend_url}/#token={access_token}")

