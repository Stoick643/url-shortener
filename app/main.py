from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routes import auth, links, redirect, stats


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


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok"}


# Include routers - order matters: specific paths before catch-all /{short_code}
app.include_router(auth.router)
app.include_router(links.router)
app.include_router(stats.router)
app.include_router(redirect.router)
