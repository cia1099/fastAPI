from pydantic import BaseModel, ConfigDict, Field


class UserPostIn(BaseModel):
    body: str = Field(
        description="user information",
        title="body",
    )


class UserPost(UserPostIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class CommentIn(BaseModel):
    body: str = Field(
        description="content of comment",
        min_length=1,
    )
    post_id: int = Field(
        description="certain post identify",
    )


class Comment(CommentIn):
    model_config = ConfigDict(from_attributes=True)

    id: int


class UserPostWithComments(BaseModel):
    post: UserPost
    comments: list[Comment]
