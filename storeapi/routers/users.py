import logging, asyncio
from multiprocessing import Process

from fastapi import APIRouter, BackgroundTasks, HTTPException, status, Request

from storeapi.database import database, user_table
from storeapi.models.user import UserIn, User
from storeapi.security import (
    get_user,
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_subject_for_token_type,
)
from storeapi import tasks

logger = logging.getLogger(__name__)
router = APIRouter()


def arun(email: str, url: str):
    asyncio.run(tasks.send_user_registration_email(email, url))


@router.post("/register", status_code=201)
async def register(user: UserIn, background_tasks: BackgroundTasks, request: Request):
    if await get_user(user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with that email already exists",
        )

    logger.info("Register a new user", extra={"email": user.email})
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    data = user.model_dump()
    query = user_table.insert().values(email=user.email, password=hashed_password)

    logger.debug(query)

    last_record_id = await database.execute(query)
    # return {**data, "id": last_record_id}
    token = create_access_token(user.email, "confirmation")
    # decode to URL from function name
    confirm_url = request.url_for("confirm_email", token=token)

    p = Process(target=arun, args=(user.email, str(confirm_url)))
    p.daemon = True  # detached ref.https://stackoverflow.com/questions/49123439/python-how-to-run-process-in-detached-mode
    p.start()
    logger.debug(
        "Submitting background task to send email",
        extra={"confirm_url": confirm_url},
    )

    # background_tasks.add_task(
    #     tasks.send_user_registration_email,
    #     user.email,
    #     confirmation_url=str(confirm_url),
    # )
    return {
        "detail": "User created. Please confirm your email.",
        # "confirmation_url": request.url_for("confirm_email", token=token),
    }


@router.post("/login", status_code=status.HTTP_201_CREATED)
async def login(user: UserIn):
    user = await authenticate_user(user.email, user.password)
    access_token = create_access_token(user.email)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/confirm/{token}")
async def confirm_email(token: str):
    email = get_subject_for_token_type(token, "confirmation")
    query = (
        user_table.update().where(user_table.c.email == email).values(confirmed=True)
    )
    logger.debug(query)
    await database.execute(query)
    return {"detail": "You're confirmed"}
