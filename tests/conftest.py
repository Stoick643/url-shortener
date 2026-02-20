import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

from app.auth import create_access_token
from app.config import settings
from app.database import get_session
from app.main import app
from app.rate_limit import reset_rate_limits

# Use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite://"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create tables before each test and drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
    reset_rate_limits()


async def override_get_session():
    async with test_session() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def admin_token():
    """Generate a valid admin JWT token."""
    return create_access_token(subject=settings.ADMIN_USERNAME)


@pytest.fixture
def auth_headers(admin_token):
    """Authorization headers with admin JWT."""
    return {"Authorization": f"Bearer {admin_token}"}
