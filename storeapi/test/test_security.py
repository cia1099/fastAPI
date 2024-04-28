from httpx import AsyncClient
import pytest
from storeapi.database import user_table, database
from storeapi import security


@pytest.fixture()
async def registered_user(async_client: AsyncClient) -> dict:
    user_details = {"email": "test@example.net", "password": "1234"}
    await async_client.post("/register", json=user_details)
    query = user_table.select().where(user_table.c.email == user_details["email"])
    user = await database.fetch_one(query)
    user_details["id"] = user.id
    return user_details


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]
    assert user.id == registered_user["id"]
    # assert user is None


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.net")
    assert user is None
