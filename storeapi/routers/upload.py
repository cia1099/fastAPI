import logging
import tempfile
from typing import Annotated

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile, status, Depends
from storeapi.libs.b2 import b2_upload_file
from storeapi.security import get_current_user
from storeapi.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_file(
    file: UploadFile, current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            temp_name = temp_file.name
            logger.info(f"Saving uploaded file temporarily to {temp_name}")
            async with aiofiles.open(temp_name, "wb") as f:
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)
            file_url = b2_upload_file(local_file=temp_name, file_name=file.filename)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error uploading the file",
        )
    return {"detail": f"Successfully uploaded {file.filename}", "file_url": file_url}
