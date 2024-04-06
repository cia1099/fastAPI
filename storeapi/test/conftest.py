import os
from typing import AsyncGenerator, Generator
import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

os.environ["ENV_STATE"] = "test"
from storeapi.database import database  # noqa: E402(tell ruff)
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
    yield
    await database.disconnect()


@pytest.fixture()
async def async_client(client: TestClient) -> AsyncGenerator:
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url=client.base_url
    ) as ac:
        yield ac
