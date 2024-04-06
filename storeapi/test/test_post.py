from httpx import AsyncClient
import pytest


async def create_post(body: str, aclient: AsyncClient) -> dict:
    response = await aclient.post("/post", json={"body": body})
    return response.json()


async def create_comment(body: str, post_id: int, aclient: AsyncClient) -> dict:
    response = await aclient.post("/comment", json={"body": body, "post_id": post_id})
    return response.json()


@pytest.fixture()
async def created_post(async_client: AsyncClient):
    return await create_post("Test post", async_client)


@pytest.fixture()
async def created_comment(async_client: AsyncClient, created_post: dict):
    return await create_comment("Test comment", 0, async_client)


@pytest.mark.anyio
async def test_create_post(async_client: AsyncClient):
    body = "Test Post"
    res = await async_client.post("/post", json={"body": body})
    assert res.status_code == 201
    assert {"id": 0, "body": body}.items() <= res.json().items()
    assert res.json()["id"] == 0


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    res = await async_client.get("/post")
    assert res.status_code == 200
    assert res.json() == [created_post]
    assert len(res.json()) == 1


@pytest.mark.anyio
async def test_create_comment(async_client: AsyncClient, created_post: dict):
    body = "Test Comment"
    res = await async_client.post(
        "/comment",
        json={
            "body": body,
            "post_id": created_post["id"],
        },
    )
    assert res.status_code == 201
    assert {"id": 0, "body": body}.items() <= res.json().items()
    assert res.json()["id"] == 0
    assert res.json()["post_id"] == 0


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
    assert res.json()["post"]["id"] == 0
    assert res.json()["comments"] == [created_comment]


@pytest.mark.anyio
async def test_not_found_post_with_comments(
    async_client: AsyncClient, created_comment: dict
):
    res = await async_client.get(f"/post/2")
    assert res.status_code == 404
