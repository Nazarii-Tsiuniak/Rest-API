from fastapi import APIRouter, Depends, HTTPException, status

from schemas.auth import TokenRefreshRequest, TokenRequest, TokenResponse
from services.auth_service import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    verify_token,
)
from services.rate_limiter import rate_limit_anonymous

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=200,
    dependencies=[Depends(rate_limit_anonymous)],
)
def issue_tokens(payload: TokenRequest):
    if not authenticate_user(payload.username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    return TokenResponse(
        access_token=create_access_token(payload.username),
        refresh_token=create_refresh_token(payload.username),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=200,
    dependencies=[Depends(rate_limit_anonymous)],
)
def refresh_tokens(payload: TokenRefreshRequest):
    username = verify_token(payload.refresh_token, "refresh")
    return TokenResponse(
        access_token=create_access_token(username),
        refresh_token=create_refresh_token(username),
    )
