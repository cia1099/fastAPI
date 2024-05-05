from fastapi import Request, status
from httpx import AsyncClient
import pytest
from storeapi.database import user_table, database
from storeapi import security


def test_password_hashes():
    password = "password"
    assert security.verify_password(password, security.get_password_hash(password))


@pytest.mark.parametrize(
    "expired_time,token_type",
    [
        (security.access_token_expire_minutes(), "access"),
        (security.confirmation_token_expire_minutes(), "confirmation"),
    ],
)
def test_get_subject_for_token_type_valid(expired_time: int, token_type: str):
    email = "test@example.com"
    token = security.create_access_token(email, expired_time)
    assert email == security.get_subject_for_token_type(token, token_type)


@pytest.mark.parametrize(
    "expired_time,token_type",
    [
        (security.access_token_expire_minutes(), "confirmation"),
        (security.confirmation_token_expire_minutes(), "access"),
    ],
)
def test_get_subject_for_token_type_wrong_type(expired_time, token_type):
    email = "test@example.com"
    token = security.create_access_token(email, expired_time)
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, token_type)
    assert "Token has incorrect type, expected" in exc_info.value.detail


def test_get_subject_for_token_type_expired(mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    email = "test@example.com"
    token = security.create_access_token(email, security.access_token_expire_minutes())
    with pytest.raises(security.HTTPException) as exc_info:
        security.get_subject_for_token_type(token, "access")
    assert "Token has expired" == exc_info.value.detail


@pytest.mark.anyio
async def test_get_user(registered_user: dict):
    user = await security.get_user(registered_user["email"])

    assert user.email == registered_user["email"]
    assert user.id == registered_user["id"]


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
    assert res.status_code == security.status.HTTP_201_CREATED
    assert {"token_type": "bearer"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_authenticate_user_not_found(async_client: AsyncClient):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


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
    assert {"detail": "Invalid email or password"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_get_current_user(registered_user: dict, async_client: AsyncClient):
    res = await async_client.post("/login", json=registered_user)
    token = res.json()["access_token"]
    # token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user.email == registered_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_get_current_user_invalid_token(registered_user: dict):
    token = security.create_access_token(registered_user["email"], 1440)
    with pytest.raises(security.HTTPException):
        await security.get_current_user(token)


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    spy = mocker.spy(Request, "url_for")
    await async_client.post(
        "/register", json={"email": "test@example.net", "password": "1234"}
    )
    confirm_url = str(spy.spy_return)
    res = await async_client.get(confirm_url)
    assert res.status_code == 200
    assert "You're confirmed" in res.json()["detail"]


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient):
    res = await async_client.get("/confirm/invalid_token")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
