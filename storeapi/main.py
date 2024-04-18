import logging
from asgi_correlation_id import CorrelationIdMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from storeapi.database import database
from storeapi.routers.posts import router as posts_router

from storeapi.logging_conf import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
# CorrelationIdMiddleware used to identify whose request
app.add_middleware(CorrelationIdMiddleware)
app.include_router(posts_router)


@app.get("/hello")
async def root():
    return {"message": "Hello World"}


@app.exception_handler(HTTPException)
async def http_exception_handle_logging(req, e: HTTPException):
    """
    override this app.exception_handler
    we don't need to logger.error() before raise HTTPException
    """
    logger.error(f"HTTPException: {e.status_code} {e.detail}")
    return await http_exception_handler(req, e)
