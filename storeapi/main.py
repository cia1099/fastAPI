from fastapi import FastAPI
from storeapi.routers.posts import router as posts_router

app = FastAPI()
app.include_router(posts_router)


@app.get("/hello")
async def root():
    return {"message": "Hello World"}


aa = {
    "dasdadadad": "sadasdasdasdadad",
    "sdasdad": 123,
    "sdada": 5555555,
    "daddasd": 4444447777777774444444444,
}
