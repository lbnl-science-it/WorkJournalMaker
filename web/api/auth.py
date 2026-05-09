# ABOUTME: REST API endpoints for authentication (login, refresh, logout, profile).
# ABOUTME: Delegates to the active AuthProvider via app.state.

from fastapi import APIRouter, HTTPException, Request, Depends, status
from pydantic import BaseModel

from web.auth import get_current_user, User

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserProfile(BaseModel):
    id: str
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, request: Request):
    """Authenticate with username/password and receive a token pair."""
    provider = request.app.state.auth_provider
    try:
        pair = await provider.authenticate({
            "username": body.username,
            "password": body.password,
        })
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest, request: Request):
    """Exchange a refresh token for a new token pair."""
    provider = request.app.state.auth_provider
    try:
        pair = await provider.refresh_token(body.refresh_token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    return TokenResponse(access_token=pair.access_token, refresh_token=pair.refresh_token)


@router.post("/logout")
async def logout(
    body: LogoutRequest,
    request: Request,
    user: User = Depends(get_current_user),
):
    """Revoke a refresh token (logout)."""
    provider = request.app.state.auth_provider
    await provider.revoke_token(body.refresh_token)
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserProfile)
async def me(user: User = Depends(get_current_user)):
    """Return the current user's profile."""
    return UserProfile(id=user.id, username=user.username, role=user.role)
