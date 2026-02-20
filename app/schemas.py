from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl, field_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LinkCreateRequest(BaseModel):
    url: HttpUrl
    custom_slug: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None

    @field_validator("custom_slug")
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        import re
        if not re.match(r"^[a-zA-Z0-9-]+$", v):
            raise ValueError("Slug must contain only alphanumeric characters and hyphens")
        if len(v) < 3 or len(v) > 30:
            raise ValueError("Slug must be between 3 and 30 characters")
        reserved = {"docs", "api", "admin", "auth", "health", "static"}
        if v.lower() in reserved:
            raise ValueError(f"Slug '{v}' is reserved")
        return v


class LinkUpdateRequest(BaseModel):
    expires_at: Optional[datetime] = None
    max_clicks: Optional[int] = None


class LinkResponse(BaseModel):
    id: int
    short_code: str
    short_url: str
    original_url: str
    is_vanity: bool
    is_active: bool
    expires_at: Optional[datetime]
    max_clicks: Optional[int]
    total_clicks: int
    qr_code_base64: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LinkListResponse(BaseModel):
    links: list[LinkResponse]
    total: int
    page: int
    per_page: int


class ClickResponse(BaseModel):
    ip_hash: str
    referrer: Optional[str]
    country: str
    clicked_at: datetime


class StatsResponse(BaseModel):
    short_code: str
    original_url: str
    total_clicks: int
    unique_clicks: int
    clicks: list[ClickResponse]


class MessageResponse(BaseModel):
    message: str
