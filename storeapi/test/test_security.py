from httpx import AsyncClient
import pytest
from storeapi.database import user_table, database
from storeapi import security


def test_password_hashes():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


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


@pytest.mark.anyio
async def test_login_user(registered_user: dict, async_client: AsyncClient):
    # user = await security.authenticate_user(
    #     registered_user["email"], registered_user["password"]
    # )
    # assert user.email == registered_user["email"]
    res = await async_client.post("/login", json=registered_user)
    assert res.status_code == 201
    assert {"token_type": "bearer"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_authenticate_user_not_found(async_client: AsyncClient):
    # with pytest.raises(security.HTTPException):
    # await security.authenticate_user("test@example.net", "1234")
    res = await async_client.post(
        "/login", json={"email": "test@example.net", "password": "1234"}
    )
    assert res.status_code == 401
    assert {"detail": "Could not validate credentials"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(
    registered_user: dict, async_client: AsyncClient
):
    # with pytest.raises(security.HTTPException):
    #     await security.authenticate_user(registered_user["email"], "wrong password")
    res = await async_client.post(
        "/login", json={"email": "test@example.net", "password": "wrong password"}
    )
    assert res.status_code == 401
    assert {"detail": "Could not validate credentials"}.items() <= res.json().items()
