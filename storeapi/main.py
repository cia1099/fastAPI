import logging
from asgi_correlation_id import CorrelationIdMiddleware
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.exception_handlers import http_exception_handler
from storeapi.database import database
from storeapi.routers.posts import router as posts_router
from storeapi.routers.users import router as users_router
from storeapi.routers.upload import router as upload_router

from storeapi.logging_conf import configure_logging
from storeapi.jaeger import jaeger_exporter, tracer
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from starlette_exporter import PrometheusMiddleware, handle_metrics

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
app.include_router(users_router)
app.include_router(upload_router)
# PrometheusMiddleware used to monitor endpoints
app.add_middleware(PrometheusMiddleware, app_name="prometheus")
app.add_route("/metrics", handle_metrics)

span_processor = BatchSpanProcessor(jaeger_exporter)
tracer.add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer)
LoggingInstrumentor().instrument(set_logging_format=True)


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
