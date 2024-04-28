from pydantic import BaseModel, ConfigDict


class UserIn(BaseModel):
    email: str
    password: str


class User(UserIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
