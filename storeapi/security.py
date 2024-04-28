import logging
from storeapi.database import database, user_table

logger = logging.getLogger(__name__)


async def get_user(email: str):
    logger.info("Fetched user from database", extra={"email": email})
    query = user_table.select().where(user_table.c.email == email)
    logger.debug(query)
    result = await database.fetch_one(query)
    if result:
        return result
    logger.info("Not found email", extra={"email": email})
