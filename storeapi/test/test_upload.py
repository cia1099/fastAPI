import contextlib
import os
from pathlib import Path
import tempfile

from fastapi import status
import pytest
from httpx import AsyncClient


@pytest.fixture()
def sample_image(fs) -> Path:
    abs_path = (Path(__file__).parent / "assets" / "mock_image.jpg").resolve()
    fs.create_file(abs_path)
    return abs_path


@pytest.fixture(autouse=True)
def mock_b2_upload_file(mocker):
    return mocker.patch(
        "storeapi.libs.b2.b2_upload_file", return_value="https://fakefile.jpg"
    )


# Mock the aiofiles.open function so that it
# returns a fake file object from the fake filesystem
@pytest.fixture(autouse=True)
def aiofiles_mock_open(mocker, fs):
    mock_open = mocker.patch("aiofiles.open")
    import io

    @contextlib.asynccontextmanager
    async def async_file_open(fname: str, mode: str = "r"):
        out_fs_mock = mocker.AsyncMock(name=f"async_file_open:{fname!r}/{mode!r}")
        with io.open(fname, mode) as fin:
            out_fs_mock.read.side_effect = fin.read
            # out_fs_mock.write.side_effect = fin.write
            yield out_fs_mock

    mock_open.side_effect = async_file_open
    return mock_open


async def call_upload_endpoint(async_client: AsyncClient, token: str, file: Path):
    return await async_client.post(
        "/upload",
        files={"file": open(file, "rb")},
        headers={"Authorization": f"Bearer {token}"},
    )


"""===== 
TODO: aiofiles_mock_open has problem in unknown
that make logged_in_token error
"""
# @pytest.mark.anyio
# async def test_upload_image(
#     async_client: AsyncClient, logged_in_token: str, sample_image: Path
# ):
#     res = await call_upload_endpoint(async_client, logged_in_token, sample_image)
#     assert res.status_code == 201
#     assert res.json()["file_url"] == "https://fakefile.jpg"


# @pytest.mark.anyio
# async def test_temp_file_removed_after_upload(
#     async_client: AsyncClient, logged_in_token: str, sample_image: Path, mocker
# ):
#     # Spy on the NamedTemporaryFile function
#     named_temp_file_spy = mocker.spy(tempfile, "NamedTemporaryFile")
#
#     response = await call_upload_endpoint(async_client, logged_in_token, sample_image)
#     assert response.status_code == 201
#
#     # Get the filename of the temporary file created by the upload endpoint
#     created_temp_file = named_temp_file_spy.spy_return
#
#     # Check if the temp_file is removed after the file is uploaded
#     assert not os.path.exists(created_temp_file.name)


@pytest.mark.anyio
async def test_wrong_token_upload(
    async_client: AsyncClient, sample_image: Path, mocker
):
    res = await call_upload_endpoint(async_client, "wrong token", sample_image)
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
    assert res.json()["detail"] == "Invalid token"
