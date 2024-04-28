import logging

from fastapi import APIRouter, HTTPException, status

from storeapi.database import database, user_table
from storeapi.models.user import UserIn, User
from storeapi.security import get_user

from storeapi.models.post import UserPostIn

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/register", status_code=201, response_model=User)
async def register(user: UserIn):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )

    logger.info("Register a new user", extra={"email": user.email})
    # hashed_password = get_password_hash(user.password)
    data = user.model_dump()
    query = user_table.insert().values(email=user.email, password=user.password)

    logger.debug(query)

    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}
