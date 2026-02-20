from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class Link(SQLModel, table=True):
    __tablename__ = "links"

    id: Optional[int] = Field(default=None, primary_key=True)
    short_code: str = Field(max_length=30, unique=True, index=True)
    original_url: str
    is_vanity: bool = Field(default=False)
    is_active: bool = Field(default=True)
    expires_at: Optional[datetime] = Field(default=None)
    max_clicks: Optional[int] = Field(default=None)
    total_clicks: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    clicks: list["Click"] = Relationship(back_populates="link")


class Click(SQLModel, table=True):
    __tablename__ = "clicks"

    id: Optional[int] = Field(default=None, primary_key=True)
    link_id: int = Field(foreign_key="links.id", index=True)
    ip_hash: str = Field(max_length=64)
    referrer: Optional[str] = Field(default=None)
    country: str = Field(default="unknown", max_length=10)
    clicked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    link: Optional[Link] = Relationship(back_populates="clicks")
