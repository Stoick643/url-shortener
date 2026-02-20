from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.auth import verify_token
from app.database import get_session
from app.models import Link
from app.rate_limit import check_rate_limit
from app.schemas import (
    LinkCreateRequest,
    LinkListResponse,
    LinkResponse,
    LinkUpdateRequest,
    MessageResponse,
)
from app.utils import build_short_url, generate_qr_code_base64, generate_short_code

router = APIRouter(tags=["Links"])


def _link_to_response(link: Link, include_qr: bool = False) -> LinkResponse:
    """Convert a Link model to a LinkResponse schema."""
    qr = None
    if include_qr:
        qr = generate_qr_code_base64(build_short_url(link.short_code))
    return LinkResponse(
        id=link.id,
        short_code=link.short_code,
        short_url=build_short_url(link.short_code),
        original_url=link.original_url,
        is_vanity=link.is_vanity,
        is_active=link.is_active,
        expires_at=link.expires_at,
        max_clicks=link.max_clicks,
        total_clicks=link.total_clicks,
        qr_code_base64=qr,
        created_at=link.created_at,
        updated_at=link.updated_at,
    )


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(check_rate_limit)],
)
async def create_link(
    request: LinkCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new short link. Rate-limited for unauthenticated users."""
    if request.custom_slug:
        short_code = request.custom_slug
        is_vanity = True
    else:
        short_code = generate_short_code()
        is_vanity = False

    # Check uniqueness
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    existing = result.scalars().first()
    if existing:
        if is_vanity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Slug '{short_code}' is already taken",
            )
        # Retry for generated codes (extremely unlikely collision)
        for _ in range(5):
            short_code = generate_short_code()
            result = await session.execute(select(Link).where(Link.short_code == short_code))
            if not result.scalars().first():
                break
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate unique short code",
            )

    link = Link(
        short_code=short_code,
        original_url=str(request.url),
        is_vanity=is_vanity,
        expires_at=request.expires_at,
        max_clicks=request.max_clicks,
    )
    session.add(link)
    await session.commit()
    await session.refresh(link)

    return _link_to_response(link, include_qr=True)


@router.get("/links", response_model=LinkListResponse)
async def list_links(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    _admin: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
):
    """List all links with pagination. Admin only."""
    offset = (page - 1) * per_page

    total_result = await session.execute(select(func.count(Link.id)))
    total = total_result.scalar_one()

    result = await session.execute(
        select(Link).order_by(Link.created_at.desc()).offset(offset).limit(per_page)
    )
    links = result.scalars().all()

    return LinkListResponse(
        links=[_link_to_response(link) for link in links],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/links/{short_code}", response_model=LinkResponse)
async def get_link(
    short_code: str,
    _admin: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
):
    """Get a single link by short code. Admin only."""
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")
    return _link_to_response(link, include_qr=True)


@router.patch("/links/{short_code}", response_model=LinkResponse)
async def update_link(
    short_code: str,
    request: LinkUpdateRequest,
    _admin: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
):
    """Update link expiry settings. Admin only."""
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if request.expires_at is not None:
        link.expires_at = request.expires_at
    if request.max_clicks is not None:
        link.max_clicks = request.max_clicks
    link.updated_at = datetime.now(timezone.utc)

    session.add(link)
    await session.commit()
    await session.refresh(link)

    return _link_to_response(link)


@router.delete("/links/{short_code}", response_model=MessageResponse)
async def delete_link(
    short_code: str,
    _admin: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
):
    """Soft-delete a link. Admin only."""
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    link.is_active = False
    link.updated_at = datetime.now(timezone.utc)
    session.add(link)
    await session.commit()

    return MessageResponse(message=f"Link '{short_code}' has been deleted")
