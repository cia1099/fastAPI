from json import JSONDecodeError
import logging
from databases import Database
import httpx

from storeapi.config import config
from storeapi.database import post_table


logger = logging.getLogger(__name__)


class APIResponseError(Exception):
    pass


async def send_simple_message(to: str, subject: str, body: str):
    logger.debug(f"Sending email to '{to.split('@')[0]}' with subject '{subject[:20]}'")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"https://api.mailgun.net/v3/{config.MAILGUN_DOMAIN}/messages",
                auth=("api", config.MAILGUN_API_KEY),
                data={
                    "from": f"Jose Salvatierra <mailgun@{config.MAILGUN_DOMAIN}>",
                    "to": [to],
                    "subject": subject,
                    "text": body,
                },
            )
            response.raise_for_status()

            logger.debug(response.content)

            return response
        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                f"API request failed with status code {err.response.status_code}"
            ) from err


def get_email_name(email: str) -> str:
    return email.split("@")[0]


async def send_user_registration_email(email: str, confirmation_url: str):
    if config.ENV_STATE == "dev":
        with open("send_email.txt", "w") as f:
            f.write("To verify multiprocess are available")
    return await send_simple_message(
        email,
        "Successfully signed up",
        (
            f"Hi {get_email_name(email)}! You have successfully signed up to the Stores REST API."
            " Please confirm your email by clicking on the"
            f" following link: {confirmation_url}"
        ),
    )


async def _generate_cute_creature_api(prompt: str):
    logger.debug("Generating cute creature")
    async with httpx.AsyncClient() as client:
        try:
            res = await client.post(
                url="https://api.deepai.org/api/text2img",
                data={"text": prompt},
                headers={"api-key": config.DEEPAI_API_KEY},
                timeout=60,
            )
            logger.debug(res)
            res.raise_for_status()
            return res.json()
        except httpx.HTTPStatusError as err:
            raise APIResponseError(
                f"API request failed with status code {err.response.status_code}"
            ) from err
        except (JSONDecodeError, TypeError) as err:
            raise APIResponseError("API response parsing failed") from err


async def generate_and_add_to_post(
    email: str,
    post_id: int,
    post_url: str,
    database: Database,
    prompt: str = "A blue british shorthair cat is sitting on a couch",
):
    try:
        res = await _generate_cute_creature_api(prompt)
    except APIResponseError:
        return await send_simple_message(
            email,
            "Error generating image",
            (
                f"Hi {get_email_name(email)}! Unfortunately there was an error generating an image"
                "for your post."
            ),
        )
    query = (
        post_table.update()
        .where(post_table.c.id == post_id)
        .values(image_url=res["output_url"])
    )
    logger.debug("Connecting to database to update post id %d" % post_id)
    db_id = await database.execute(query)
    assert db_id == post_id
    logger.debug("Database connection in background task closed")
    await send_simple_message(
        email,
        "Image generation completed",
        (
            f"Hi {get_email_name(email)}! Your image has been generated and added to your post."
            f" Please click on the following link to view it: {post_url}"
        ),
    )
    return res
