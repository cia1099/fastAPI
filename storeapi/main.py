from contextlib import asynccontextmanager
from fastapi import FastAPI
from storeapi.database import database
from storeapi.routers.posts import router as posts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
app.include_router(posts_router)


@app.get("/hello")
async def root():
    return {"message": "Hello World"}
