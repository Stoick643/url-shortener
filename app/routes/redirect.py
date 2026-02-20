from datetime import datetime, timezone

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_session
from app.models import Click, Link
from app.utils import build_short_url, generate_qr_code_bytes, hash_ip

STATIC_DIR = Path(__file__).parent.parent / "static"

router = APIRouter(tags=["Redirect"])


async def _get_active_link(short_code: str, session: AsyncSession) -> Link:
    """Fetch a link and validate it's active and not expired."""
    result = await session.execute(select(Link).where(Link.short_code == short_code))
    link = result.scalars().first()

    if not link:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Link not found")

    if not link.is_active:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has been deleted")

    # Check date expiry
    if link.expires_at:
        expires = link.expires_at if link.expires_at.tzinfo else link.expires_at.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > expires:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has expired")

    # Check max clicks expiry
    if link.max_clicks and link.total_clicks >= link.max_clicks:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has reached its click limit")

    return link


@router.get("/{short_code}/stats", response_class=HTMLResponse, include_in_schema=False)
async def stats_page(short_code: str):
    """Serve the public stats page for a short link."""
    return (STATIC_DIR / "stats.html").read_text()


@router.get("/{short_code}/qr", response_class=Response)
async def get_qr_code(
    short_code: str,
    session: AsyncSession = Depends(get_session),
):
    """Get QR code PNG image for a short link."""
    await _get_active_link(short_code, session)
    url = build_short_url(short_code)
    png_bytes = generate_qr_code_bytes(url)
    return Response(content=png_bytes, media_type="image/png")


@router.get("/{short_code}", response_class=RedirectResponse)
async def redirect_to_url(
    short_code: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    """Redirect to the original URL and record click analytics."""
    link = await _get_active_link(short_code, session)

    # Record click
    client_ip = request.client.host if request.client else "unknown"
    referrer = request.headers.get("referer")
    country = (
        request.headers.get("cf-ipcountry")
        or request.headers.get("x-country")
        or "unknown"
    )

    click = Click(
        link_id=link.id,
        ip_hash=hash_ip(client_ip),
        referrer=referrer,
        country=country,
    )
    session.add(click)

    # Increment counter
    link.total_clicks += 1
    session.add(link)

    await session.commit()

    return RedirectResponse(url=link.original_url, status_code=status.HTTP_302_FOUND)
