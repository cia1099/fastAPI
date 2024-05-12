from httpx import AsyncClient
from fastapi import status
import pytest
from storeapi import security
from storeapi.routers.posts import PostSorting


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


async def like_post(post_id: int, aclient: AsyncClient, logged_in_token: str) -> dict:
    res = await aclient.post(
        "/like",
        json={"post_id": post_id},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return res.json()


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
async def test_create_post(
    async_client: AsyncClient, registered_user: dict, logged_in_token: str
):
    body = "Test Post"
    res = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert res.status_code == 201
    assert {
        "id": 1,
        "body": body,
        "user_id": registered_user["id"],
        "image_url": None,
    }.items() <= res.json().items()
    assert res.json()["id"] == 1


@pytest.mark.anyio
async def test_create_post_expired_token(
    async_client: AsyncClient, confirmed_user: dict, mocker
):
    mocker.patch("storeapi.security.access_token_expire_minutes", return_value=-1)
    token = security.create_access_token(confirmed_user["email"], "access")
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
    assert res.json() == [{**created_post, "likes": 0}]
    assert len(res.json()) == 1


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting,expected_order",
    [(PostSorting.new.value, [2, 1]), (PostSorting.old.value, [1, 2])],
)
async def test_get_all_posts_sorting(
    async_client: AsyncClient,
    logged_in_token: str,
    sorting: str,
    expected_order: list[int],
):
    await create_post("Post 1", async_client, logged_in_token)
    await create_post("Post 2", async_client, logged_in_token)
    res = await async_client.get("/post", params={"sorting": sorting})
    assert res.status_code == 200
    assert [post["id"] for post in res.json()] == expected_order


@pytest.mark.anyio
async def test_get_all_post_wrong_sorting(async_client: AsyncClient):
    res = await async_client.get("/post", params={"sorting": "wrong"})
    assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_get_all_posts_sort_likes(
    async_client: AsyncClient, logged_in_token: str
):
    await create_post("Post 1", async_client, logged_in_token)
    await create_post("Post 2", async_client, logged_in_token)
    await like_post(1, async_client, logged_in_token)
    res = await async_client.get(
        "/post", params={"sorting": PostSorting.most_likes.value}
    )
    assert res.status_code == 200
    assert [post["id"] for post in res.json()] == [1, 2]


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
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
    assert {
        "id": 1,
        "body": body,
        "user_id": registered_user["id"],
    }.items() <= res.json().items()
    assert res.json()["id"] == 1
    assert res.json()["post_id"] == created_post["id"]  # 1


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
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    res = await async_client.get(f'/post/{created_comment["post_id"]}')
    assert res.status_code == 200
    # assert res.json()["post"]["id"] == 1
    # assert res.json()["comments"] == [created_comment]
    assert (
        res.json().items()
        >= {
            "post": {**created_post, "likes": 0},
            "comments": [created_comment],
        }.items()
    )


@pytest.mark.anyio
async def test_not_found_post_with_comments(
    async_client: AsyncClient, created_comment: dict
):
    res = await async_client.get(f"/post/2")
    assert res.status_code == 404


@pytest.mark.anyio
async def test_post_like(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    res = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    assert res.status_code == 201
    assert {
        "id": 1,
        "post_id": created_post["id"],
        "user_id": created_post["user_id"],
    }.items() <= res.json().items()
