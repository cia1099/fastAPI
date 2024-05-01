import logging

from fastapi import APIRouter, HTTPException, Request
from storeapi.database import comment_table, database, post_table
from storeapi.models.post import (
    Comment,
    CommentIn,
    UserPost,
    UserPostIn,
    UserPostWithComments,
)
from storeapi.models.user import User
from storeapi.security import get_current_user, oauth2_scheme

router = APIRouter()

logger = logging.getLogger(__name__)


async def find_post(post_id: int):
    logger.info(f"Finding post with id {post_id}")
    query = post_table.select().where(post_table.c.id == post_id)
    logger.debug(query)
    return await database.fetch_one(query)


@router.post("/post", response_model=UserPost, status_code=201)
async def create_post(post: UserPostIn, request: Request):
    logger.info("Create a post")
    current_user: User = await get_current_user(await oauth2_scheme(request))  # noqa
    data = post.model_dump()  # previously .dict()
    query = post_table.insert().values(data)
    logger.debug(query)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post", response_model=list[UserPost])
async def get_all_posts():
    # really confused extra argument in logging.LogRecord
    logger.info("Getting all posts", extra={"email": "5566@gmail.com"})
    query = post_table.select()
    logger.debug(query, extra={"email": "sadadadad@example.net"})
    return await database.fetch_all(query)


@router.post("/comment", response_model=Comment, status_code=201)
async def create_comment(comment: CommentIn, request: Request):
    logger.debug("Create a Comment")
    current_user: User = await get_current_user(await oauth2_scheme(request))  # noqa
    post = await find_post(comment.post_id)
    if not post:
        # logger.error(f"Post with id {comment.post_id} not found")
        raise HTTPException(
            status_code=404, detail="Post id:%d not found" % comment.post_id
        )

    data = comment.model_dump()  # previously .dict()
    query = comment_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}


@router.get("/post/{post_id}/comment", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    logger.info("Getting comments on post %d" % post_id)
    query = comment_table.select().where(comment_table.c.post_id == post_id)
    logger.debug(query)
    return await database.fetch_all(query)


@router.get("/post/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    """
    Endpoint for retrieving all commnent by a specific post id
    :param: post_id: int
    :return: {UserPostWithComments}
    """
    logger.info("Getting post %d and its comments" % post_id)
    post = await find_post(post_id)
    if not post:
        # logger.error("Post with post id %d not found" % post_id)
        raise HTTPException(status_code=404, detail="Post id:%d not found" % post_id)

    return {
        "post": post,
        "comments": await get_comments_on_post(post_id),
    }
