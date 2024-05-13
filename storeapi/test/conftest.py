import os
from typing import AsyncGenerator, Generator
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport, Response, Request
from unittest.mock import AsyncMock, Mock

# trick for test environment, we import database after setting
os.environ["ENV_STATE"] = "test"
from storeapi.database import database, user_table  # noqa: E402(tell ruff)
from storeapi.main import app  # noqa: E402(tell ruff)


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture()
def client() -> Generator:
    yield TestClient(app)


@pytest.fixture(autouse=True)
async def db() -> AsyncGenerator:
    """
    Because we have set DB_FORCE_ROLL_BACK in config.py
    The database will not change in test condition
    """
    await database.connect()
    yield database
    await database.disconnect()


@pytest.fixture
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac


@pytest.fixture
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.fixture
async def confirmed_user(async_client: AsyncClient, registered_user: dict) -> dict:
    query = (
        user_table.update()
        .where(user_table.c.email == registered_user["email"])
        .values(confirmed=True)
    )
    await database.execute(query)
    return registered_user


@pytest.fixture
async def logged_in_token(async_client: AsyncClient, confirmed_user: dict) -> str:
    response = await async_client.post("/login", json=confirmed_user)
    return response.json()["access_token"]


@pytest.fixture(autouse=True)
def mock_tasks_httpx_client(mocker) -> Mock:
    """
    Fixture to mock the HTTPX client so that we never make any
    real HTTP requests (especially important when registering users).
    """
    mocked_client = mocker.patch("storeapi.tasks.httpx.AsyncClient")

    mocked_async_client = Mock()
    response = Response(status_code=200, content="", request=Request("POST", "//"))
    mocked_async_client.post = AsyncMock(return_value=response)
    mocked_client.return_value.__aenter__.return_value = mocked_async_client

    return mocked_async_client
