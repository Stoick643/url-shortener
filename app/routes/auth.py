from fastapi import APIRouter, HTTPException, status

from app.auth import create_access_token, verify_admin_credentials
from app.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """Authenticate admin and return a JWT token."""
    if not verify_admin_credentials(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token(subject=request.username)
    return TokenResponse(access_token=token)
