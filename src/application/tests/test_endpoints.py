import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient

# ---------- MOCKED APP FIXTURE ----------

@pytest_asyncio.fixture(scope="function")
async def mock_app_client():
    # Define mock FastAPI app
    app = FastAPI()

    @app.get("/")
    async def read_root():
        return {"message": "Mocked!"}

    @app.post("/test-db")
    async def create_user(name: str):
        return {"message": f"User '{name}' mocked", "user_id": 1}

    # Return an AsyncClient with the mock app
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# ---------- MOCKED TESTS ONLY ----------

@pytest.mark.asyncio
async def test_root_endpoint(mock_app_client):
    response = await mock_app_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Mocked!"}


@pytest.mark.asyncio
async def test_create_user(mock_app_client):
    response = await mock_app_client.post("/test-db", params={"name": "Alice"})
    assert response.status_code == 200
    assert response.json()["message"] == "User 'Alice' mocked"
    assert response.json()["user_id"] == 1
