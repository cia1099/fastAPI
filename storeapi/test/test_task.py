import httpx
import pytest
from databases import Database

from storeapi.database import post_table
from storeapi.models.post import UserPost
from storeapi.security import get_current_user
from storeapi.tasks import (
    APIResponseError,
    send_simple_message,
    _generate_cute_creature_api,
    generate_and_add_to_post,
)


@pytest.mark.anyio
async def test_send_simple_message(mock_tasks_httpx_client):
    await send_simple_message("test@example.net", "Test Subject", "Test Body")
    mock_tasks_httpx_client.post.assert_called()


@pytest.mark.anyio
async def test_send_simple_message_api_error(mock_tasks_httpx_client):
    mock_tasks_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError, match="API request failed with status code"):
        await send_simple_message("test@example.com", "Test Subject", "Test Body")


@pytest.mark.anyio
async def test_generate_cute_creature_api_success(mock_tasks_httpx_client):
    json_data = {"output_url": "https://example.com/image.jpg"}
    mock_tasks_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )
    res = await _generate_cute_creature_api("A cat")
    assert res == json_data


@pytest.mark.anyio
async def test_generate_cute_creature_api_server_error(mock_tasks_httpx_client):
    mock_tasks_httpx_client.post.return_value = httpx.Response(
        status_code=500, content="", request=httpx.Request("POST", "//")
    )
    with pytest.raises(
        APIResponseError, match="API request failed with status code 500"
    ):
        await _generate_cute_creature_api("A cat")


@pytest.mark.anyio
async def test_generate_cute_creature_api_json_error(mock_tasks_httpx_client):
    mock_tasks_httpx_client.post.return_value = httpx.Response(
        status_code=200, content="Not JSON", request=httpx.Request("POST", "//")
    )

    with pytest.raises(APIResponseError, match="API response parsing failed"):
        await _generate_cute_creature_api("A cat")


@pytest.mark.anyio
async def test_generate_and_add_to_post_success(
    mock_tasks_httpx_client,
    async_client: httpx.AsyncClient,
    logged_in_token: str,
    db: Database,
):
    json_data = {"output_url": "https://example.com/image.jpg"}

    mock_tasks_httpx_client.post.return_value = httpx.Response(
        status_code=200, json=json_data, request=httpx.Request("POST", "//")
    )
    # created a post
    post_res = await async_client.post(
        "/post",
        json={"body": "Test to generate image"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    user = await get_current_user(logged_in_token)
    await generate_and_add_to_post(
        user.email, post_res.json()["id"], "/post/1", db, "A cat"
    )
    # Check that after the background task runs, the post has been updated
    query = post_table.select().where(post_table.c.id == post_res.json()["id"])
    updated_post = await db.fetch_one(query)

    assert updated_post.image_url == json_data["output_url"]
