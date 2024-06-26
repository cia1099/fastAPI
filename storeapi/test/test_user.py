from multiprocessing import Process
import pytest
from fastapi import Request, status, BackgroundTasks
from httpx import AsyncClient

from storeapi import security


@pytest.mark.anyio
async def test_get_user(confirmed_user: dict):
    user = await security.get_user(confirmed_user["email"])

    assert user.email == confirmed_user["email"]
    assert user.id == confirmed_user["id"]


@pytest.mark.anyio
async def test_get_user_not_found():
    user = await security.get_user("test@example.net")
    assert user is None


@pytest.mark.anyio
async def test_login_user(confirmed_user: dict, async_client: AsyncClient):
    # user = await security.authenticate_user(
    #     registered_user["email"], registered_user["password"]
    # )
    # assert user.email == registered_user["email"]
    res = await async_client.post("/login", json=confirmed_user)
    assert res.status_code == security.status.HTTP_201_CREATED
    assert {"token_type": "bearer"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_fail_cookie_login(async_client: AsyncClient):
    res = await async_client.get("/login/cookies")
    assert res.status_code == 401
    assert res.json()["detail"] == "Cookie not found"


@pytest.mark.anyio
async def test_cookie_login(confirmed_user: dict, async_client: AsyncClient):
    _ = await async_client.post("/login", json=confirmed_user)
    res = await async_client.get("/login/cookies")
    assert res.status_code == 202
    assert {"token_type": "bearer"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_authenticate_user_not_found(async_client: AsyncClient):
    with pytest.raises(security.HTTPException):
        await security.authenticate_user("test@example.net", "1234")


@pytest.mark.anyio
async def test_authenticate_user_wrong_password(
    registered_user: dict, async_client: AsyncClient
):
    """
    By Http protocol do not raise exception
    """
    # with pytest.raises(security.HTTPException):
    #     await security.authenticate_user(registered_user["email"], "wrong password")
    res = await async_client.post(
        "/login", json={"email": "test@example.net", "password": "wrong password"}
    )
    assert res.status_code == 401
    assert {"detail": "Invalid email or password"}.items() <= res.json().items()


@pytest.mark.anyio
async def test_get_current_user(confirmed_user: dict, async_client: AsyncClient):
    res = await async_client.post("/login", json=confirmed_user)
    token = res.json()["access_token"]
    # token = security.create_access_token(registered_user["email"])
    user = await security.get_current_user(token)
    assert user.email == confirmed_user["email"]


@pytest.mark.anyio
async def test_get_current_user_invalid_token():
    with pytest.raises(security.HTTPException):
        await security.get_current_user("invalid token")


@pytest.mark.anyio
async def test_authenticate_user_not_confirmed(registered_user: dict):
    with pytest.raises(security.HTTPException) as exc_info:
        await security.authenticate_user(
            registered_user["email"], registered_user["password"]
        )
    assert exc_info.value.detail == "User has not confirmed email"


@pytest.mark.anyio
async def test_confirm_user(async_client: AsyncClient, mocker):
    # spy = mocker.spy(Request, "url_for")
    # spy = mocker.spy(BackgroundTasks, "add_task")
    spy = mocker.spy(Process, "__init__")
    await async_client.post(
        "/register", json={"email": "test@example.net", "password": "1234"}
    )
    # confirm_url = str(spy.spy_return)
    # confirm_url = str(spy.call_args[1]["confirmation_url"])
    confirm_url = str(spy.call_args[1]["args"][1])
    res = await async_client.get(confirm_url)
    assert res.status_code == 200
    assert "You're confirmed" in res.json()["detail"]


@pytest.mark.anyio
async def test_confirm_email_token_expired(async_client: AsyncClient, mocker):
    mocker.patch("storeapi.security.confirmation_token_expire_minutes", return_value=-1)
    # spy = mocker.spy(BackgroundTasks, "add_task")
    spy = mocker.spy(Process, "__init__")
    await async_client.post(
        "/register", json={"email": "test@example.net", "password": "1234"}
    )
    # confirm_url = str(spy.call_args[1]["confirmation_url"])
    confirm_url = str(spy.call_args[1]["args"][1])
    res = await async_client.get(confirm_url)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Token has expired" in res.json()["detail"]


@pytest.mark.anyio
async def test_expired_token(async_client: AsyncClient, confirmed_user: dict, mocker):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    await async_client.post("/login", json=confirmed_user)
    res = await async_client.get("/login/cookies")
    assert res.status_code == 401
    assert res.json()["detail"] == "Token has expired"
    res2 = await async_client.get("/login/cookies")
    assert res2.json()["detail"] == "Cookie not found"
    assert res2.status_code == 401


@pytest.mark.anyio
async def test_invalid_confirm_user(async_client: AsyncClient):
    res = await async_client.get("/confirm/invalid_token")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
