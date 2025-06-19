import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from server import app as real_app, get_db, User

DATABASE_URL_TEST = "sqlite+aiosqlite:///:memory:"

# Create a separate engine for test DB
test_engine = create_async_engine(DATABASE_URL_TEST, echo=True)
TestSessionLocal = sessionmaker(
    test_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
Base = declarative_base()

# Override the get_db dependency
async def override_get_db():
    async with TestSessionLocal() as session:
        yield session

# Apply the override
real_app.dependency_overrides[get_db] = override_get_db

@pytest_asyncio.fixture(scope="function")
async def async_test_client():
    # Ensure tables exist
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.create_all)

    async with AsyncClient(app=real_app, base_url="http://test") as client:
        yield client

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(User.metadata.drop_all)

@pytest.mark.asyncio
async def test_root_endpoint(async_test_client):
    response = await async_test_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Dummy ver is!"}

@pytest.mark.asyncio
async def test_create_user(async_test_client):
    response = await async_test_client.post("/test-db", params={"name": "Alice"})
    assert response.status_code == 200
    assert response.json()["message"].startswith("User 'Alice' inserted successfully")
    assert "user_id" in response.json()
