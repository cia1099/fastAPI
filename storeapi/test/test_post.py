from httpx import AsyncClient
import pytest
from storeapi import security


async def create_post(body: str, aclient: AsyncClient, logged_in_token: str) -> dict:
    response = await aclient.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_comment(
    body: str, post_id: int, aclient: AsyncClient, logged_in_token: str
) -> dict:
    response = await aclient.post(
        "/comment",
        json={"body": body, "post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient, logged_in_token: str):
    return await create_post("Test post", async_client, logged_in_token)


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    return await create_comment(
        "Test comment", created_post["id"], async_client, logged_in_token
    )


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient, logged_in_token: str):
    body = "Test Post"
    res = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert res.status_code == 201
    assert {"id": 1, "body": body}.items() <= res.json().items()
    assert res.json()["id"] == 1


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, registered_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(registered_user["email"])
    response = await async_client.post(
        "/post",
        json={"body": "Test Post"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # assert {"id": 1}.items() <= response.json().items()
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    res = await async_client.get("/post")
    assert res.status_code == 200
    assert res.json() == [created_post]
    assert len(res.json()) == 1


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    body = "Test Comment"
    res = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
        },
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert res.status_code == 201
    assert {"id": 1, "body": body}.items() <= res.json().items()
    assert res.json()["id"] == 1
    assert res.json()["post_id"] == 1


@pytest.mark.anyio
async def test_get_comments_on_post(async_client: AsyncClient, created_comment: dict):
    res = await async_client.get(f"/post/{created_comment['post_id']}/comment")
    assert res.status_code == 200
    assert res.json() == [created_comment]
    assert len(res.json()) == 1


@pytest.mark.anyio
async def test_get_comments_on_empty(async_client: AsyncClient, created_post: dict):
    res = await async_client.get(f"/post/{created_post['id']}/comment")
    assert res.status_code == 200
    assert res.json() == []
    assert len(res.json()) == 0


@pytest.mark.anyio
async def test_get_post_with_comments(async_client: AsyncClient, created_comment: dict):
    res = await async_client.get(f'/post/{created_comment["post_id"]}')
    assert res.status_code == 200
    assert res.json()["post"]["id"] == 1
    assert res.json()["comments"] == [created_comment]


@pytest.mark.anyio
async def test_not_found_post_with_comments(
    async_client: AsyncClient, created_comment: dict
):
    res = await async_client.get(f"/post/2")
    assert res.status_code == 404
