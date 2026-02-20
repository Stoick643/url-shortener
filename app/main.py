from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from app.database import init_db
from app.routes import auth, links, redirect, stats

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="URL Shortener API",
    description="Self-hosted TinyURL competitor with analytics – lightweight and private.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def landing_page():
    return (STATIC_DIR / "index.html").read_text()


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Include routers - order matters: specific paths before catch-all /{short_code}
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(stats.router)
app.include_router(redirect.router)
