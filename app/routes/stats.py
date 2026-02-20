from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.auth import verify_token
from app.database import get_session
from app.models import Click, Link
from app.schemas import ClickResponse, StatsResponse

router = APIRouter(tags=["Stats"])


@router.get("/links/{short_code}/stats", response_model=StatsResponse)
async def get_link_stats(
    short_code: str,
    _admin: str = Depends(verify_token),
    session: AsyncSession = Depends(get_session),
):
    """Get click analytics for a link. Admin only."""
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()
    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    # Unique clicks
    unique_result = await session.execute(
        select(func.count(func.distinct(Click.ip_hash))).where(Click.link_id == link.id)
    )
    unique_clicks = unique_result.scalar_one()

    # All clicks
    clicks_result = await session.execute(
        select(Click).where(Click.link_id == link.id).order_by(Click.clicked_at.desc())
    )
    clicks = clicks_result.scalars().all()

    return StatsResponse(
        short_code=link.short_code,
        original_url=link.original_url,
        total_clicks=link.total_clicks,
        unique_clicks=unique_clicks,
        clicks=[
            ClickResponse(
                ip_hash=c.ip_hash,
                referrer=c.referrer,
                country=c.country,
                clicked_at=c.clicked_at,
            )
            for c in clicks
        ],
    )
