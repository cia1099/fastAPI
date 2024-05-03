from pydantic import BaseModel, ConfigDict, Field


class UserPostIn(BaseModel):
    body: str = Field(
        description="user information",
        title="body",
    )


class UserPost(UserPostIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int


class UserPostWithLikes(UserPost):
    model_config = ConfigDict(from_attributes=True)

    likes: int


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
    user_id: int


class UserPostWithComments(BaseModel):
    post: UserPostWithLikes
    comments: list[Comment]


class PostLikeIn(BaseModel):
    post_id: int


class PostLike(PostLikeIn):
    id: int
    user_id: int
